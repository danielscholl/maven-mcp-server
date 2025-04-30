"""
Module containing the get_maven_all_latest_versions tool.
This tool returns the latest versions for all semantic versioning components (major, minor, patch) in a single call.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, query_maven_central
from maven_mcp_server.tools.latest_by_semver import parse_semver

logger = logging.getLogger("maven-check")

def get_all_latest_versions(
    group_id: str, 
    artifact_id: str, 
    version_tuple: Tuple[int, int, int],
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the latest versions for all semantic versioning components (major, minor, patch).
    
    Args:
        group_id: The Maven group ID.
        artifact_id: The Maven artifact ID.
        version_tuple: A tuple of (major, minor, patch) of the input version.
        packaging: The packaging type (default: "jar").
        classifier: The classifier, if any.
        
    Returns:
        Dict containing the latest versions for each component or error information
    """
    try:
        query = f"g:{group_id} AND a:{artifact_id}"
        
        if packaging:
            query += f" AND p:{packaging}"
        
        if classifier:
            query += f" AND l:{classifier}"
            
        params = {
            "q": query,
            "core": "gav",
            "rows": 100,  # Get more results to ensure we capture all versions
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
        
        # Extract and parse all versions
        versions = []
        for doc in docs:
            version_str = doc.get("v")
            if not version_str:
                continue
                
            # Skip pre-release versions (containing - or alpha, beta, rc, etc.)
            # Only if they have a dash followed by pre-release indicator
            if "-" in version_str and any(x in version_str.lower() for x in ["alpha", "beta", "rc", "snapshot", "pre"]):
                continue
                
            # Try to parse the version as semver
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                try:
                    v_major = int(match.group(1))
                    v_minor = int(match.group(2))
                    v_patch = int(match.group(3))
                    versions.append((v_major, v_minor, v_patch, version_str))
                except ValueError:
                    # Skip versions that can't be properly parsed
                    continue
        
        if not versions:
            return {
                "status": "error",
                "error": {
                    "message": f"No valid semantic versions found for {group_id}:{artifact_id} in Maven Central"
                }
            }
        
        input_major, input_minor, input_patch = version_tuple
        
        # For latest major version - get the highest across all versions
        all_versions = sorted(versions, reverse=True)
        latest_major_version = all_versions[0][3]
        
        # For latest minor version - get the highest minor within the input major version
        minor_versions = [v for v in versions if v[0] == input_major]
        latest_minor_version = None
        if minor_versions:
            minor_versions.sort(key=lambda x: (x[1], x[2]), reverse=True)
            latest_minor_version = minor_versions[0][3]
        
        # For latest patch version - get the highest patch within the input major.minor version
        patch_versions = [v for v in versions if v[0] == input_major and v[1] == input_minor]
        latest_patch_version = None
        if patch_versions:
            patch_versions.sort(key=lambda x: x[2], reverse=True)
            latest_patch_version = patch_versions[0][3]
        
        # Check if we have at least one component version
        if not latest_minor_version and not latest_patch_version:
            return {
                "status": "error",
                "error": {
                    "message": f"No versions matching the criteria found for {group_id}:{artifact_id} with version={version_tuple}"
                }
            }
        
        # Return all available component versions
        result = {
            "status": "success",
            "result": {
                "latest_major_version": latest_major_version
            }
        }
        
        if latest_minor_version:
            result["result"]["latest_minor_version"] = latest_minor_version
        
        if latest_patch_version:
            result["result"]["latest_patch_version"] = latest_patch_version
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        }

def get_maven_all_latest_versions(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the latest versions for all semantic versioning components (major, minor, patch) in a single call.
    
    Args:
        dependency: The dependency in the format 'groupId:artifactId'.
        version: The version in semantic version format (MAJOR.MINOR.PATCH).
        packaging: The packaging type, defaults to 'jar'.
        classifier: The classifier, if any.
        
    Returns:
        A dictionary with the tool response containing either the latest versions or an error.
    """
    tool_name = "get_maven_all_latest_versions"
    logger.info(f"{tool_name} called with: dependency={dependency}, version={version}, " +
                f"packaging={packaging}, classifier={classifier}")
    
    # Validate the dependency format
    is_valid, error = validate_dependency_format(dependency)
    if not is_valid:
        logger.error(f"Invalid dependency format: {error.message if error else 'Unknown error'}")
        return create_error_response(tool_name, error)
    
    # Parse the version
    is_valid, version_tuple, error = parse_semver(version)
    if not is_valid:
        logger.error(f"Invalid semantic version: {error.message if error else 'Unknown error'}")
        return create_error_response(tool_name, error)
    
    # Parse the dependency
    group_id, artifact_id = parse_dependency(dependency)
    logger.info(f"Parsed dependency: group_id={group_id}, artifact_id={artifact_id}")
    
    # Auto-detect packaging type for BOM and dependencies artifacts
    actual_packaging = packaging
    if artifact_id.endswith("-dependencies") or artifact_id.endswith("-bom"):
        actual_packaging = "pom"
    logger.info(f"Using packaging type: {actual_packaging}")
    
    # Get all the latest versions
    result = get_all_latest_versions(
        group_id, artifact_id, version_tuple, actual_packaging, classifier
    )
    logger.info(f"get_all_latest_versions result: {result}")
    
    # Process the result
    if result.get("status") == "success":
        latest_versions = result.get("result", {})
        logger.info(f"All latest versions found: {latest_versions}")
        return create_success_response(tool_name, latest_versions)
    elif result.get("status") == "error":
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Error getting all latest versions: {error_msg}")
        
        # Map error messages to appropriate error codes
        if "No documents found" in error_msg:
            return create_error_response(tool_name,
                                      MavenError(ErrorCode.DEPENDENCY_NOT_FOUND, error_msg))
        elif "No versions matching the criteria" in error_msg:
            return create_error_response(tool_name,
                                      MavenError(ErrorCode.VERSION_NOT_FOUND, error_msg))
        else:
            return create_error_response(tool_name,
                                       MavenError(ErrorCode.INTERNAL_SERVER_ERROR, error_msg))
    else:
        logger.error("Unexpected response format")
        return create_error_response(tool_name,
                                   MavenError(ErrorCode.INTERNAL_SERVER_ERROR, "Unexpected response format"))