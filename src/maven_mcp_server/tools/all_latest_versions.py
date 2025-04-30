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
                
            # Try to parse the version in various formats
            
            # First try standard semver format
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                try:
                    v_major = int(match.group(1))
                    v_minor = int(match.group(2))
                    v_patch = int(match.group(3))
                    versions.append((v_major, v_minor, v_patch, version_str))
                    continue  # Successfully parsed, move to next version
                except ValueError:
                    pass  # Continue to next parsing attempt
            
            # Try calendar format (YYYYMMDD)
            if version_str.isdigit() and len(version_str) >= 8:
                try:
                    v_major = int(version_str[:4])   # Year
                    v_minor = int(version_str[4:6])  # Month
                    v_patch = int(version_str[6:8])  # Day
                    versions.append((v_major, v_minor, v_patch, version_str))
                    continue  # Successfully parsed, move to next version
                except ValueError:
                    pass  # Continue to next parsing attempt
            
            # Try simple numeric format (treat as major version)
            if version_str.isdigit():
                try:
                    v_major = int(version_str)
                    versions.append((v_major, 0, 0, version_str))
                    continue  # Successfully parsed, move to next version
                except ValueError:
                    pass  # Continue to next parsing attempt
            
            # Try partial semver (like "1.0" or just "1")
            parts = version_str.split('.')
            if parts:
                try:
                    # Start with zeros
                    v_major = v_minor = v_patch = 0
                    # Fill in with actual values where available
                    if len(parts) > 0:
                        v_major = int(parts[0])
                    if len(parts) > 1:
                        v_minor = int(parts[1])
                    if len(parts) > 2:
                        v_patch = int(parts[2])
                    versions.append((v_major, v_minor, v_patch, version_str))
                    continue  # Successfully parsed, move to next version
                except ValueError:
                    pass  # Skip this version
        
        if not versions:
            return {
                "status": "error",
                "error": {
                    "message": f"No valid versions found for {group_id}:{artifact_id} in Maven Central"
                }
            }
        
        input_major, input_minor, input_patch = version_tuple
        
        # For latest major version - get the highest across all versions
        all_versions = sorted(versions, reverse=True)
        latest_major_version = all_versions[0][3]
        
        # For non-semver versions like calendar dates, we may not have multiple major/minor versions
        # So we'll adjust our filtering logic to be more permissive
        
        # For latest minor version - get the highest minor within the input major version if possible
        minor_versions = [v for v in versions if v[0] == input_major]
        latest_minor_version = None
        if minor_versions:
            minor_versions.sort(key=lambda x: (x[1], x[2]), reverse=True)
            latest_minor_version = minor_versions[0][3]
        else:
            # If no versions with the same major version, use the overall latest version
            latest_minor_version = latest_major_version
        
        # For latest patch version - get the highest patch within the input major.minor version if possible
        patch_versions = [v for v in versions if v[0] == input_major and v[1] == input_minor]
        latest_patch_version = None
        if patch_versions:
            patch_versions.sort(key=lambda x: x[2], reverse=True)
            latest_patch_version = patch_versions[0][3]
        else:
            # If no versions with the same major.minor version, try to use the minor version
            # or fall back to the major version
            latest_patch_version = latest_minor_version
        
        # For consistency, always return all three components with the best values we could find
        
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
    Supports both standard semver (MAJOR.MINOR.PATCH) and non-semver formats (like calendar dates 20231013).
    
    Args:
        dependency: The dependency in the format 'groupId:artifactId'.
        version: The version string. Preferably in semantic version format (MAJOR.MINOR.PATCH),
                but other formats like dates (20231013) are also supported.
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
    
    # Parse the version - now handles non-semver formats
    is_valid, version_tuple, error = parse_semver(version)
    if not is_valid:
        logger.warning(f"Could not parse version '{version}' in any recognized format: {error.message}")
        # Instead of returning an error, we'll continue with a default version tuple
        # This allows us to at least return the latest version even if we can't do component-based comparisons
        version_tuple = (0, 0, 0)  # Default to all zeros
    else:
        logger.info(f"Parsed version '{version}' as tuple {version_tuple}")
    
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