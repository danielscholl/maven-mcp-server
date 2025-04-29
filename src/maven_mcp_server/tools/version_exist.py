"""
Module containing the get_maven_latest_version tool.
This tool returns the latest version of a Maven dependency.
"""

import logging
from typing import Dict, Any, Optional

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, get_latest_version

logger = logging.getLogger("maven-check")

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
        return result
    else:
        logger.error("Unexpected response format")
        return {
            "status": "error",
            "error": {
                "message": "Unexpected response format"
            }
        }