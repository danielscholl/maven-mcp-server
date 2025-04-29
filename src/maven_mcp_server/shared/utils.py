"""
Utility functions for the Maven MCP Server.
Contains functions for validating input, parsing dependency strings, and calling the Maven Central API.
"""

import re
import requests
from typing import Dict, Any, Tuple, Optional, List

from maven_mcp_server.shared.data_types import ErrorCode, MavenError

# Maven Central Search API URL
MAVEN_CENTRAL_API = "https://search.maven.org/solrsearch/select"


def validate_dependency_format(dependency: str) -> Tuple[bool, Optional[MavenError]]:
    """
    Validate that a dependency string follows the format 'groupId:artifactId'.

    Args:
        dependency: The dependency string to validate.

    Returns:
        A tuple of (is_valid, error) where is_valid is a boolean indicating if the
        format is valid, and error is None if valid or a MavenError if invalid.
    """
    if not dependency:
        return False, MavenError(
            ErrorCode.MISSING_PARAMETER,
            "Dependency parameter is required."
        )
    
    if not re.match(r'^[^:]+:[^:]+$', dependency):
        return False, MavenError(
            ErrorCode.INVALID_INPUT_FORMAT,
            f"Dependency '{dependency}' does not match the required format 'groupId:artifactId'."
        )
    
    return True, None


def parse_dependency(dependency: str) -> Tuple[str, str]:
    """
    Parse a dependency string into groupId and artifactId.

    Args:
        dependency: The dependency string in format 'groupId:artifactId'.

    Returns:
        A tuple of (groupId, artifactId).
    """
    parts = dependency.split(':')
    return parts[0], parts[1]


def query_maven_central(params: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[MavenError]]:
    """
    Query the Maven Central Search API.

    Args:
        params: The query parameters to send to the API.

    Returns:
        A tuple of (response_data, error) where response_data is the JSON response
        from the API if successful, and error is None if successful or a MavenError if failed.
    """
    # Add default parameters if not already present
    if "wt" not in params:
        params["wt"] = "json"
    if "rows" not in params:
        params["rows"] = 100  # Get more rows to ensure we have all versions
    if "core" not in params:
        params["core"] = "gav"  # Use gav core for better version searching
    
    try:
        response = requests.get(MAVEN_CENTRAL_API, params=params)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return {}, MavenError(
            ErrorCode.MAVEN_API_ERROR,
            f"Error querying Maven Central: {str(e)}"
        )
    except Exception as e:
        return {}, MavenError(
            ErrorCode.INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings using semantic versioning rules.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2
    """
    # Split versions by dots and convert numeric parts to integers
    v1_parts = []
    v2_parts = []
    
    for part in version1.split('.'):
        # Split on non-numeric boundaries to handle versions like "3.0.0-RC1"
        numeric_parts = re.findall(r'\d+|\D+', part)
        v1_parts.extend([int(p) if p.isdigit() else p for p in numeric_parts])
    
    for part in version2.split('.'):
        numeric_parts = re.findall(r'\d+|\D+', part)
        v2_parts.extend([int(p) if p.isdigit() else p for p in numeric_parts])
    
    # Compare parts one by one
    for i in range(min(len(v1_parts), len(v2_parts))):
        # If both parts are integers, compare numerically
        if isinstance(v1_parts[i], int) and isinstance(v2_parts[i], int):
            if v1_parts[i] != v2_parts[i]:
                return 1 if v1_parts[i] > v2_parts[i] else -1
        # If types don't match, numeric comes first
        elif isinstance(v1_parts[i], int) and not isinstance(v2_parts[i], int):
            return 1
        elif not isinstance(v1_parts[i], int) and isinstance(v2_parts[i], int):
            return -1
        # If both are strings, compare alphabetically
        else:
            if v1_parts[i] != v2_parts[i]:
                # Special cases: prioritize releases over pre-releases
                if v1_parts[i].lower() in ['alpha', 'beta', 'rc', 'snapshot', 'm']:
                    return -1
                if v2_parts[i].lower() in ['alpha', 'beta', 'rc', 'snapshot', 'm']:
                    return 1
                return 1 if v1_parts[i] > v2_parts[i] else -1
    
    # If all parts so far are equal, the longer version is considered greater
    return 1 if len(v1_parts) > len(v2_parts) else (-1 if len(v1_parts) < len(v2_parts) else 0)


def get_latest_version(group_id: str, artifact_id: str, packaging: str = "jar",
                       classifier: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the latest version of a Maven artifact.

    Args:
        group_id: The Maven group ID.
        artifact_id: The Maven artifact ID.
        packaging: The packaging type (default: "jar").
        classifier: The classifier, if any.

    Returns:
        Dict containing the latest version or error information
    """
    try:
        # For BOM artifacts, use a more direct search approach with core=gav
        if artifact_id.endswith("-bom"):
            # Use gav core for proper search
            params = {
                "q": f"g:{group_id} AND a:{artifact_id}",
                "core": "gav",
                "rows": 20,
                "wt": "json"
            }
            
            response_data, error = query_maven_central(params)
            if error:
                return {
                    "status": "error",
                    "error": {
                        "message": error.message
                    }
                }
            
            docs = response_data.get("response", {}).get("docs", [])
            if not docs:
                return {
                    "status": "error",
                    "error": {
                        "message": f"No documents found for {group_id}:{artifact_id} in Maven Central"
                    }
                }
            
            # Sort versions to find the latest
            versions = []
            for doc in docs:
                version = doc.get("v")
                if version:
                    versions.append(version)
            
            if versions:
                # Sort versions using our comparison function and get the latest
                versions.sort(key=lambda x: [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', x)], reverse=True)
                return {
                    "status": "success",
                    "result": {
                        "latest_version": versions[0]
                    }
                }
            
            return {
                "status": "error",
                "error": {
                    "message": f"Could not find version information for {group_id}:{artifact_id} in Maven Central"
                }
            }
        
        # For regular artifacts, use the specified packaging
        query = f"g:{group_id} AND a:{artifact_id}"
        
        if packaging:
            query += f" AND p:{packaging}"
        if classifier:
            query += f" AND l:{classifier}"
            
        params = {
            "q": query,
            "core": "gav",
            "rows": 20,
            "wt": "json"
        }
        
        response_data, error = query_maven_central(params)
        if error:
            return {
                "status": "error",
                "error": {
                    "message": error.message
                }
            }
        
        docs = response_data.get("response", {}).get("docs", [])
        if not docs:
            return {
                "status": "error",
                "error": {
                    "message": f"No documents found for {group_id}:{artifact_id} in Maven Central"
                }
            }
        
        # Sort versions to find the latest
        versions = []
        for doc in docs:
            version = doc.get("v")
            if version:
                versions.append(version)
        
        if versions:
            # Sort versions using our comparison function and get the latest
            versions.sort(key=lambda x: [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', x)], reverse=True)
            return {
                "status": "success",
                "result": {
                    "latest_version": versions[0]
                }
            }
        
        return {
            "status": "error",
            "error": {
                "message": f"Could not find version information for {group_id}:{artifact_id} in Maven Central"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        }


def check_version_exists(group_id: str, artifact_id: str, version: str, packaging: str = "jar",
                        classifier: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if a specific version of a Maven artifact exists.

    Args:
        group_id: The Maven group ID.
        artifact_id: The Maven artifact ID.
        version: The version to check.
        packaging: The packaging type (default: "jar").
        classifier: The classifier, if any.

    Returns:
        Dict containing the existence status or error information
    """
    try:
        if not version:
            return {
                "status": "error",
                "error": {
                    "message": "Version parameter is required for check_maven_version_exists."
                }
            }
        
        query = f"g:{group_id} AND a:{artifact_id} AND v:{version}"
        
        if packaging:
            query += f" AND p:{packaging}"
        
        if classifier:
            query += f" AND l:{classifier}"
        
        params = {
            "q": query,
            "core": "gav",
            "rows": 1,
            "wt": "json"
        }
        
        response_data, error = query_maven_central(params)
        if error:
            return {
                "status": "error",
                "error": {
                    "message": error.message
                }
            }
        
        # Check if any results were found
        response = response_data.get("response", {})
        num_found = response.get("numFound", 0)
        
        if num_found == 0:
            # Check if the dependency exists at all
            result = get_latest_version(group_id, artifact_id, packaging, classifier)
            
            if result.get("status") == "error":
                return result
            
            # Dependency exists but this version doesn't
            return {
                "status": "success",
                "result": {
                    "exists": False
                }
            }
        
        return {
            "status": "success",
            "result": {
                "exists": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        }