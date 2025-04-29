"""
Module containing the get_maven_latest_version tool.
This tool returns the latest version of a Maven dependency.
"""

import logging
import re
import requests
from typing import Dict, Any, Optional, Tuple

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, query_maven_central

logger = logging.getLogger("maven-check")

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


def get_maven_latest_version(
    dependency: str,
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the latest version of a Maven dependency.

    Args:
        dependency: The dependency in the format 'groupId:artifactId'.
        packaging: The packaging type, defaults to 'jar'.
        classifier: The classifier, if any.

    Returns:
        A dictionary with the tool response containing either the latest version or an error.
    """
    logger.info(f"get_maven_latest_version called with: dependency={dependency}, packaging={packaging}, classifier={classifier}")
    
    # Validate the dependency format
    is_valid, error = validate_dependency_format(dependency)
    if not is_valid:
        logger.error(f"Invalid dependency format: {error.message if error else 'Unknown error'}")
        return create_error_response("get_maven_latest_version", error)
    
    # Parse the dependency
    group_id, artifact_id = parse_dependency(dependency)
    logger.info(f"Parsed dependency: group_id={group_id}, artifact_id={artifact_id}")
    
    # Get the latest version
    result = get_latest_version(group_id, artifact_id, packaging, classifier)
    logger.info(f"get_latest_version result: {result}")
    
    # Process the result
    if result.get("status") == "success":
        latest_version = result.get("result", {}).get("latest_version")
        logger.info(f"Latest version found: {latest_version}")
        return result
    elif result.get("status") == "error":
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Error getting latest version: {error_msg}")
        
        # Map error messages to appropriate error codes
        if "No documents found" in error_msg:
            return create_error_response("get_maven_latest_version",
                                      MavenError(ErrorCode.DEPENDENCY_NOT_FOUND, error_msg))
        else:
            return result
    else:
        logger.error("Unexpected response format")
        return {
            "status": "error",
            "error": {
                "message": "Unexpected response format"
            }
        }