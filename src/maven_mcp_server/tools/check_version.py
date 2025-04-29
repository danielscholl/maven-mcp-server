"""
Module containing the check_maven_version_exists tool.
This tool checks if a specific version of a Maven dependency exists.
"""

import logging
from typing import Dict, Any, Optional

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, check_version_exists

logger = logging.getLogger("maven-check")

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
        return result
    else:
        logger.error("Unexpected response format")
        return {
            "status": "error",
            "error": {
                "message": "Unexpected response format"
            }
        }