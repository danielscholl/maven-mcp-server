"""
Utility functions for the Maven MCP Server.
Contains functions for validating input, parsing dependency strings, and calling the Maven Central API.
"""

import re
import requests
from typing import Dict, Any, Tuple, Optional, List

from maven_mcp_server.shared.data_types import ErrorCode, MavenError

# Maven Central Search API URLs
MAVEN_CENTRAL_API = "https://search.maven.org/solrsearch/select"
MAVEN_CENTRAL_REMOTE_CONTENT = "https://search.maven.org/remotecontent"
MAVEN_CENTRAL_REPO = "https://repo1.maven.org/maven2"


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


def check_direct_repository_access(group_id: str, artifact_id: str, version: str = None, packaging: str = "pom") -> Tuple[bool, List[str], Optional[MavenError]]:
    """
    Check if a dependency exists by directly accessing the Maven repository.
    This is useful for dependencies that aren't properly indexed by the search API.
    
    Args:
        group_id: The Maven group ID.
        artifact_id: The Maven artifact ID.
        version: Optional specific version to check. If None, tries to list available versions.
        packaging: The packaging type (default: "pom").
        
    Returns:
        A tuple of (exists, versions, error) where:
        - exists is a boolean indicating if the dependency exists
        - versions is a list of version strings (empty if version was specified)
        - error is None if successful or a MavenError if failed
    """
    # Convert groupId to path format (replace dots with slashes)
    group_path = group_id.replace('.', '/')
    
    try:
        if version:
            # Check if a specific version exists
            url = f"{MAVEN_CENTRAL_REPO}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.{packaging}"
            response = requests.head(url)
            return response.status_code == 200, [], None
        else:
            # Try to get metadata to find versions
            metadata_url = f"{MAVEN_CENTRAL_REPO}/{group_path}/{artifact_id}/maven-metadata.xml"
            response = requests.get(metadata_url)
            
            if response.status_code == 200:
                # Extract versions from metadata XML
                # This is a simple extraction and could be improved with proper XML parsing
                versions = []
                xml_content = response.text
                
                # Simple pattern matching for version tags
                import re
                version_matches = re.findall(r'<version>(.*?)</version>', xml_content)
                if version_matches:
                    versions = version_matches
                    
                # Simple pattern to extract latest version if available
                latest_match = re.search(r'<latest>(.*?)</latest>', xml_content)
                if latest_match:
                    # Ensure the latest version is first in the list
                    latest = latest_match.group(1)
                    if latest in versions:
                        versions.remove(latest)
                    versions.insert(0, latest)
                
                return True, versions, None
            else:
                return False, [], None
                
    except requests.exceptions.RequestException as e:
        return False, [], MavenError(
            ErrorCode.MAVEN_API_ERROR,
            f"Error accessing Maven Central Repository: {str(e)}"
        )
    except Exception as e:
        return False, [], MavenError(
            ErrorCode.INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )
