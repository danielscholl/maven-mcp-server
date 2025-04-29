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
