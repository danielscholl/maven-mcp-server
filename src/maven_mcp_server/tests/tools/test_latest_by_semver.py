"""
Tests for the find_maven_latest_component_version tool.
"""

import pytest
from maven_mcp_server.tools.latest_by_semver import find_maven_latest_component_version, parse_semver, validate_target_component
from maven_mcp_server.shared.data_types import ErrorCode


def test_parse_semver_valid():
    """Test successful parsing of a valid semantic version."""
    is_valid, version_tuple, error = parse_semver("1.2.3")
    
    assert is_valid is True
    assert version_tuple == (1, 2, 3)
    assert error is None


def test_parse_semver_invalid():
    """Test parsing of an invalid semantic version."""
    is_valid, version_tuple, error = parse_semver("1.2")
    
    assert is_valid is False
    assert version_tuple is None
    assert error is not None
    assert error.code == ErrorCode.INVALID_INPUT_FORMAT


def test_parse_semver_empty():
    """Test parsing of an empty semantic version."""
    is_valid, version_tuple, error = parse_semver("")
    
    assert is_valid is False
    assert version_tuple is None
    assert error is not None
    assert error.code == ErrorCode.MISSING_PARAMETER


def test_validate_target_component_valid():
    """Test validation of a valid target component."""
    is_valid, error = validate_target_component("major")
    
    assert is_valid is True
    assert error is None
    
    is_valid, error = validate_target_component("minor")
    
    assert is_valid is True
    assert error is None
    
    is_valid, error = validate_target_component("patch")
    
    assert is_valid is True
    assert error is None


def test_validate_target_component_invalid():
    """Test validation of an invalid target component."""
    is_valid, error = validate_target_component("release")
    
    assert is_valid is False
    assert error is not None
    assert error.code == ErrorCode.INVALID_INPUT_FORMAT


def test_validate_target_component_empty():
    """Test validation of an empty target component."""
    is_valid, error = validate_target_component("")
    
    assert is_valid is False
    assert error is not None
    assert error.code == ErrorCode.MISSING_PARAMETER


def test_find_maven_latest_component_version_major():
    """Test finding the latest major version."""
    # Use a widely used and stable dependency that has multiple major versions
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "3.0.0", "major"
    )
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]
    latest_version = result["result"]["latest_version"]
    
    # Don't assert specific version as it may change, but ensure it's properly formatted
    assert isinstance(latest_version, str)
    assert "." in latest_version


def test_find_maven_latest_component_version_minor():
    """Test finding the latest minor version within a major version."""
    # Use a dependency with multiple minor versions within a major version
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "3.0.0", "minor"
    )
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]
    latest_version = result["result"]["latest_version"]
    
    # The version should start with 3.x.y since we specified major=3
    assert latest_version.startswith("3.")


def test_find_maven_latest_component_version_patch():
    """Test finding the latest patch version within a major.minor version."""
    # Use a major and minor version that has multiple patch versions
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "3.12.0", "patch"
    )
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]
    latest_version = result["result"]["latest_version"]
    
    # The version should start with 3.12.x since we specified major=3, minor=12
    assert latest_version.startswith("3.12.")


def test_find_maven_latest_component_version_nonexistent_dependency():
    """Test with a dependency that doesn't exist."""
    result = find_maven_latest_component_version(
        "org.nonexistent:artifact-nonexistent", "1.0.0", "major"
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND


def test_find_maven_latest_component_version_nonexistent_version():
    """Test with a version that doesn't exist for the dependency."""
    # Use an extremely high version number that doesn't exist yet
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "999.0.0", "minor"
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.VERSION_NOT_FOUND


def test_find_maven_latest_component_version_invalid_format():
    """Test with an invalid dependency format."""
    result = find_maven_latest_component_version(
        "invalid-format", "1.0.0", "major"
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT


def test_find_maven_latest_component_version_invalid_target():
    """Test with an invalid target component."""
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "3.0.0", "release"
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT


def test_find_maven_latest_component_version_invalid_version():
    """Test with an invalid semantic version."""
    result = find_maven_latest_component_version(
        "org.apache.commons:commons-lang3", "3", "major"
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT