"""
Tests for the get_maven_latest_version tool.
"""

import pytest
from maven_mcp_server.tools.version_exist import get_maven_latest_version
from maven_mcp_server.shared.data_types import ErrorCode


def test_get_maven_latest_version_success():
    """Test successful retrieval of the latest version of a dependency."""
    # Use a widely used and stable dependency for testing
    result = get_maven_latest_version("org.apache.commons:commons-lang3")
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]
    assert isinstance(result["result"]["latest_version"], str)
    # Don't assert specific version as it may change over time


def test_get_maven_latest_version_with_packaging():
    """Test retrieval with specific packaging."""
    result = get_maven_latest_version("org.apache.commons:commons-lang3", packaging="jar")
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]


def test_get_maven_latest_version_with_classifier():
    """Test retrieval with a classifier."""
    # Commons-lang3 doesn't have a sources classifier in Maven Central, so this should still return a result
    result = get_maven_latest_version("org.apache.commons:commons-lang3", packaging="jar", classifier="sources")
    
    # The test should pass even if no version is found with the classifier
    if result["status"] == "success":
        assert "latest_version" in result["result"]
    else:
        assert result["error"]["code"] in [ErrorCode.DEPENDENCY_NOT_FOUND, ErrorCode.MAVEN_API_ERROR]


def test_get_maven_latest_version_invalid_format():
    """Test with an invalid dependency format."""
    result = get_maven_latest_version("invalid-format")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT


def test_get_maven_latest_version_empty_dependency():
    """Test with an empty dependency."""
    result = get_maven_latest_version("")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.MISSING_PARAMETER


def test_get_maven_latest_version_nonexistent_dependency():
    """Test with a dependency that doesn't exist."""
    result = get_maven_latest_version("org.nonexistent:artifact-nonexistent")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND