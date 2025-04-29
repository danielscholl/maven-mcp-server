"""
Tests for the check_maven_version_exists tool.
"""

import pytest
from maven_mcp_server.tools.check_version import check_maven_version_exists
from maven_mcp_server.shared.data_types import ErrorCode


def test_check_maven_version_exists_success():
    """Test successful checking of an existing version."""
    # Use a widely used and stable dependency with a known version
    result = check_maven_version_exists("org.apache.commons:commons-lang3", "3.12.0")
    
    assert result["status"] == "success"
    assert "exists" in result["result"]
    assert result["result"]["exists"] is True


def test_check_maven_version_exists_nonexistent_version():
    """Test checking a version that doesn't exist for an existing dependency."""
    result = check_maven_version_exists("org.apache.commons:commons-lang3", "999.999.999")
    
    # The current implementation returns success with exists=False when a version doesn't exist
    # rather than an error with VERSION_NOT_FOUND
    assert result["status"] == "success"
    assert "result" in result
    assert "exists" in result["result"]
    assert result["result"]["exists"] is False


def test_check_maven_version_exists_with_packaging():
    """Test checking with specific packaging."""
    result = check_maven_version_exists("org.apache.commons:commons-lang3", "3.12.0", packaging="jar")
    
    assert result["status"] == "success"
    assert "exists" in result["result"]
    assert result["result"]["exists"] is True


def test_check_maven_version_exists_with_classifier():
    """Test checking with a classifier."""
    # Test with sources classifier which might exist
    result = check_maven_version_exists("org.apache.commons:commons-lang3", "3.12.0", packaging="jar", classifier="sources")
    
    # Don't assert specific result as it may vary, but ensure the response format is correct
    if result["status"] == "success":
        assert "exists" in result["result"]
    else:
        assert result["error"]["code"] in [ErrorCode.VERSION_NOT_FOUND, ErrorCode.MAVEN_API_ERROR]


def test_check_maven_version_exists_invalid_format():
    """Test with an invalid dependency format."""
    result = check_maven_version_exists("invalid-format", "1.0.0")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT


def test_check_maven_version_exists_empty_dependency():
    """Test with an empty dependency."""
    result = check_maven_version_exists("", "1.0.0")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.MISSING_PARAMETER


def test_check_maven_version_exists_empty_version():
    """Test with an empty version."""
    result = check_maven_version_exists("org.apache.commons:commons-lang3", "")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.MISSING_PARAMETER


def test_check_maven_version_exists_nonexistent_dependency():
    """Test with a dependency that doesn't exist."""
    result = check_maven_version_exists("org.nonexistent:artifact-nonexistent", "1.0.0")
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND