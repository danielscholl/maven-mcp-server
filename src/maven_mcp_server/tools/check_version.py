"""
Module containing the check_maven_version_exists tool.
This tool checks if a specific version of a Maven dependency exists.
"""

import logging
from typing import Dict, Any, Optional

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, query_maven_central
from maven_mcp_server.tools.version_exist import get_latest_version

logger = logging.getLogger("maven-check")

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


def check_maven_version_exists(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if a specific version of a Maven dependency exists.

    Args:
        dependency: The dependency in the format 'groupId:artifactId'.
        version: The version to check.
        packaging: The packaging type, defaults to 'jar'.
        classifier: The classifier, if any.

    Returns:
        A dictionary with the tool response containing either the existence status or an error.
    """
    logger.info(f"check_maven_version_exists called with: dependency={dependency}, version={version}, packaging={packaging}, classifier={classifier}")
    
    # Validate the dependency format
    is_valid, error = validate_dependency_format(dependency)
    if not is_valid:
        logger.error(f"Invalid dependency format: {error.message if error else 'Unknown error'}")
        return create_error_response("check_maven_version_exists", error)
    
    # Parse the dependency
    group_id, artifact_id = parse_dependency(dependency)
    logger.info(f"Parsed dependency: group_id={group_id}, artifact_id={artifact_id}")
    
    # Check if the version exists
    result = check_version_exists(group_id, artifact_id, version, packaging, classifier)
    logger.info(f"check_version_exists result: {result}")
    
    # Process the result
    if result.get("status") == "success":
        exists = result.get("result", {}).get("exists")
        logger.info(f"Version exists: {exists}")
        return result
    elif result.get("status") == "error":
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Error checking version: {error_msg}")
        
        # Map error messages to appropriate error codes
        if "Version parameter is required" in error_msg:
            return create_error_response("check_maven_version_exists", 
                                      MavenError(ErrorCode.MISSING_PARAMETER, error_msg))
        elif "No documents found" in error_msg:
            return create_error_response("check_maven_version_exists",
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