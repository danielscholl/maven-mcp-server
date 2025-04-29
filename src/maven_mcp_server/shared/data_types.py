"""
Data types for the Maven MCP Server.
Contains error code enumerations and other shared data structures.
"""

from enum import Enum, auto
from typing import Dict, Any


class ErrorCode(str, Enum):
    """
    Error codes for the Maven MCP Server.
    Used to indicate the type of error that occurred during a request.
    """
    INVALID_INPUT_FORMAT = "INVALID_INPUT_FORMAT"  # Malformed dependency string
    MISSING_PARAMETER = "MISSING_PARAMETER"  # Required parameter missing
    DEPENDENCY_NOT_FOUND = "DEPENDENCY_NOT_FOUND"  # No versions found for the dependency
    VERSION_NOT_FOUND = "VERSION_NOT_FOUND"  # Version not found though dependency exists
    MAVEN_API_ERROR = "MAVEN_API_ERROR"  # Upstream Maven Central error (non‑200, network failure)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # Unhandled exception inside the server


class MavenError:
    """
    Error object for Maven MCP Server.
    Contains an error code and a human-readable message.
    """
    def __init__(self, code: ErrorCode, message: str):
        """
        Initialize a new MavenError.

        Args:
            code: The error code.
            message: A human-readable error message.
        """
        self.code = code
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the error to a dictionary representation.

        Returns:
            A dictionary with the error code and message.
        """
        return {
            "code": self.code,
            "message": self.message
        }


def create_success_response(tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a success response for an MCP tool.

    Args:
        tool_name: The name of the tool.
        result: The result of the tool execution.

    Returns:
        A dictionary with the success response.
    """
    return {
        "tool_name": tool_name,
        "status": "success",
        "result": result
    }


def create_error_response(tool_name: str, error: MavenError) -> Dict[str, Any]:
    """
    Create an error response for an MCP tool.

    Args:
        tool_name: The name of the tool.
        error: The error that occurred.

    Returns:
        A dictionary with the error response.
    """
    return {
        "tool_name": tool_name,
        "status": "error",
        "error": error.to_dict()
    }