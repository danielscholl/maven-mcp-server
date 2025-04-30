"""
Module containing the find_maven_latest_component_version tool.
This tool returns the latest version of a Maven dependency based on the target component (major, minor, patch).
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response
from maven_mcp_server.shared.utils import validate_dependency_format, parse_dependency, query_maven_central

logger = logging.getLogger("maven-check")

def parse_semver(version: str) -> Tuple[bool, Optional[Tuple[int, int, int]], Optional[MavenError]]:
    """
    Parse a version string into its components.
    
    Args:
        version: The version string, preferably in semantic version format (MAJOR.MINOR.PATCH).
        
    Returns:
        A tuple of (is_valid, version_tuple, error) where:
        - is_valid is a boolean indicating if the parsing was successful
        - version_tuple is a tuple of (major, minor, patch) if successful, None otherwise
        - error is None if successful or a MavenError if parsing failed
    """
    if not version:
        return False, None, MavenError(
            ErrorCode.MISSING_PARAMETER,
            "Version parameter is required."
        )
    
    # Regular expression for semantic versioning (MAJOR.MINOR.PATCH)
    semver_pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-[\w.-]+)?(?:\+[\w.-]+)?$'
    match = re.match(semver_pattern, version)
    
    if match:
        try:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))
            return True, (major, minor, patch), None
        except Exception as e:
            return False, None, MavenError(
                ErrorCode.INTERNAL_SERVER_ERROR,
                f"Failed to parse version components: {str(e)}"
            )
    
    # Handle non-semver formats
    
    # Calendar-based versions (YYYYMMDD) like 20231013
    if version.isdigit():
        # For calendar versions, use year as major, month as minor, day as patch
        if len(version) >= 8:
            try:
                year = int(version[:4])
                month = int(version[4:6])
                day = int(version[6:8])
                # Validate that it looks like a real date
                if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    # Store the entire numeric value as major to ensure proper comparisons
                    numeric_value = int(version[:8])
                    # Return the date components, marking it as a date-based version
                    logger.info(f"Parsed calendar version {version} as {year}.{month}.{day} (date-based)")
                    return True, (year, month, day), None
            except Exception:
                pass
        # For other numeric versions, use the number as major, 0 for minor and patch
        try:
            major = int(version)
            minor = 0
            patch = 0
            logger.info(f"Parsed numeric version {version} as {major}.{minor}.{patch}")
            return True, (major, minor, patch), None
        except Exception:
            pass
    
    # Other non-standard formats - handle as best effort
    # For versions like "1.0", "1", etc.
    parts = version.split('.')
    if parts:
        try:
            # Start with zeros for each component
            major = minor = patch = 0
            # Fill in with actual values where available
            if len(parts) > 0:
                major = int(parts[0])
            if len(parts) > 1:
                minor = int(parts[1])
            if len(parts) > 2:
                patch = int(parts[2])
            logger.info(f"Parsed partial version {version} as {major}.{minor}.{patch}")
            return True, (major, minor, patch), None
        except Exception:
            pass
    
    # If all parsing attempts fail, return an error
    return False, None, MavenError(
        ErrorCode.INVALID_INPUT_FORMAT,
        f"Version '{version}' could not be parsed in any recognized format."
    )

def validate_target_component(target_component: str) -> Tuple[bool, Optional[MavenError]]:
    """
    Validate that the target component is one of the allowed values.
    
    Args:
        target_component: The target component value to validate.
        
    Returns:
        A tuple of (is_valid, error) where is_valid is a boolean indicating if the
        value is valid, and error is None if valid or a MavenError if invalid.
    """
    allowed_values = ["major", "minor", "patch"]
    
    if not target_component:
        return False, MavenError(
            ErrorCode.MISSING_PARAMETER,
            "Target component parameter is required."
        )
    
    if target_component not in allowed_values:
        return False, MavenError(
            ErrorCode.INVALID_INPUT_FORMAT,
            f"Target component '{target_component}' must be one of: {', '.join(allowed_values)}."
        )
    
    return True, None

def get_latest_component_version(
    group_id: str, 
    artifact_id: str, 
    version_tuple: Tuple[int, int, int],
    target_component: str,
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the latest version of a Maven artifact based on the target component.
    
    Args:
        group_id: The Maven group ID.
        artifact_id: The Maven artifact ID.
        version_tuple: A tuple of (major, minor, patch) of the input version.
        target_component: The component to find the latest version for (major, minor, or patch).
        packaging: The packaging type (default: "jar").
        classifier: The classifier, if any.
        
    Returns:
        Dict containing the latest version or error information
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
        date_based_versions = []  # Special handling for date-based versions
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
                    # Store date-based versions separately for special handling
                    year = int(version_str[:4])   # Year
                    month = int(version_str[4:6])  # Month
                    day = int(version_str[6:8])  # Day
                    # Verify this actually looks like a date
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        # For date-based versions, we'll use a large integer representing YYYYMMDD
                        # This ensures proper sorting
                        numeric_value = int(version_str[:8])
                        date_based_versions.append((numeric_value, 0, 0, version_str))
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
        
        # Combine regular versions and date-based versions
        if not versions and not date_based_versions:
            return {
                "status": "error",
                "error": {
                    "message": f"No valid versions found for {group_id}:{artifact_id} in Maven Central"
                }
            }
        
        # Determine if input version is likely a date-based version
        major, minor, patch = version_tuple
        is_input_date_based = False
        if isinstance(major, int) and 1900 <= major <= 2100:
            # Check if input looks like a year
            is_input_date_based = True
            logger.info(f"Detected input version {version_tuple} as date-based")
            
        # Handle date-based versions specifically for calendar versioning
        if is_input_date_based and date_based_versions:
            logger.info(f"Processing {len(date_based_versions)} date-based versions for a date-based input")
            # Sort by numeric value (YYYYMMDD) in descending order
            sorted_date_versions = sorted(date_based_versions, key=lambda x: x[0], reverse=True)
            
            # For date-based versions, we always return the latest date
            # regardless of the target component since dates don't have semantic meaning like semver
            return {
                "status": "success",
                "result": {
                    "latest_version": sorted_date_versions[0][3]
                }
            }
            
        # Process regular versions - standard approach
        # Filter versions based on the target component
        filtered_versions = []
        
        if target_component == "major":
            # Find the highest major version available
            filtered_versions = versions
        elif target_component == "minor":
            # Find the highest minor version within the given major version
            filtered_versions = [v for v in versions if v[0] == major]
            # For non-semver versions like calendar dates, we might not find exact major matches
            if not filtered_versions and versions:
                # If no exact major matches, just use all versions
                filtered_versions = versions
        elif target_component == "patch":
            # Find the highest patch version within the given major.minor version
            filtered_versions = [v for v in versions if v[0] == major and v[1] == minor]
            # For non-semver versions, we might not find exact major.minor matches
            if not filtered_versions and versions:
                # Try to find versions with just the major match
                major_filtered = [v for v in versions if v[0] == major]
                if major_filtered:
                    filtered_versions = major_filtered
                else:
                    # If no matches at all, just use all versions
                    filtered_versions = versions
        
        if not filtered_versions:
            # If no semver versions match but we have date-based versions, use those
            if date_based_versions:
                sorted_date_versions = sorted(date_based_versions, key=lambda x: x[0], reverse=True)
                return {
                    "status": "success",
                    "result": {
                        "latest_version": sorted_date_versions[0][3]
                    }
                }
            else:
                return {
                    "status": "error",
                    "error": {
                        "message": f"No versions matching the criteria found for {group_id}:{artifact_id} with {target_component}={version_tuple}"
                    }
                }
        
        # Sort filtered versions to find the latest
        if target_component == "major":
            # Sort by major version (descending)
            filtered_versions.sort(reverse=True)
        elif target_component == "minor":
            # Sort by minor version for the same major (descending)
            filtered_versions.sort(key=lambda x: (x[1], x[2]), reverse=True)
        elif target_component == "patch":
            # Sort by patch version for the same major.minor (descending)
            filtered_versions.sort(key=lambda x: x[2], reverse=True)
        
        # Return the latest version string
        return {
            "status": "success",
            "result": {
                "latest_version": filtered_versions[0][3]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        }

def find_maven_latest_component_version(
    dependency: str,
    version: str,
    target_component: str,
    packaging: str = "jar",
    classifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the latest version of a Maven dependency based on the target component.
    Supports both standard semver (MAJOR.MINOR.PATCH) and non-semver formats (like calendar dates 20231013).
    
    Args:
        dependency: The dependency in the format 'groupId:artifactId'.
        version: The version string. Preferably in semantic version format (MAJOR.MINOR.PATCH),
                but other formats like dates (20231013) are also supported.
        target_component: The component to find the latest version for (major, minor, or patch).
        packaging: The packaging type, defaults to 'jar'.
        classifier: The classifier, if any.
        
    Returns:
        A dictionary with the tool response containing either the latest version or an error.
    """
    tool_name = "find_maven_latest_component_version"
    logger.info(f"{tool_name} called with: dependency={dependency}, version={version}, " +
                f"target_component={target_component}, packaging={packaging}, classifier={classifier}")
    
    # Validate the dependency format
    is_valid, error = validate_dependency_format(dependency)
    if not is_valid:
        logger.error(f"Invalid dependency format: {error.message if error else 'Unknown error'}")
        return create_error_response(tool_name, error)
    
    # Validate the target component
    is_valid, error = validate_target_component(target_component)
    if not is_valid:
        logger.error(f"Invalid target component: {error.message if error else 'Unknown error'}")
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
    
    # Get the latest version based on the target component
    result = get_latest_component_version(
        group_id, artifact_id, version_tuple, target_component, actual_packaging, classifier
    )
    logger.info(f"get_latest_component_version result: {result}")
    
    # Process the result
    if result.get("status") == "success":
        latest_version = result.get("result", {}).get("latest_version")
        logger.info(f"Latest component version found: {latest_version}")
        return create_success_response(tool_name, {"latest_version": latest_version})
    elif result.get("status") == "error":
        error_msg = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Error getting latest component version: {error_msg}")
        
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