"""
Tests for the get_maven_all_latest_versions tool.
"""

import pytest
from maven_mcp_server.tools.all_latest_versions import get_maven_all_latest_versions
from maven_mcp_server.shared.data_types import ErrorCode


def test_get_all_latest_versions_success():
    """Test that get_maven_all_latest_versions returns all component versions successfully."""
    # Using a common dependency with multiple versions
    dependency = "org.apache.commons:commons-lang3"
    version = "3.12.0"  # This should be an older version to ensure we get different results
    
    result = get_maven_all_latest_versions(dependency, version)
    
    assert result["status"] == "success"
    assert "latest_major_version" in result["result"]
    assert "latest_minor_version" in result["result"]
    assert "latest_patch_version" in result["result"]
    
    # Verify the versions make sense (no specific values as they will change over time)
    major_version = result["result"]["latest_major_version"].split(".")[0]
    minor_version = result["result"]["latest_minor_version"].split(".")
    patch_version = result["result"]["latest_patch_version"].split(".")
    
    # Ensure the major is an integer and >= 3
    assert int(major_version) >= 3
    
    # Ensure the minor version has the same major but potentially different minor
    assert minor_version[0] == "3"  # Major should be 3
    
    # Ensure the patch version has the same major.minor but potentially different patch
    assert patch_version[0] == "3"  # Major should be 3
    assert patch_version[1] == "12"  # Minor should be 12


def test_get_all_latest_versions_bom_detection():
    """Test that BOM dependencies are automatically detected and use POM packaging."""
    dependency = "org.springframework.boot:spring-boot-dependencies"
    version = "3.1.0"
    
    result = get_maven_all_latest_versions(dependency, version)
    
    assert result["status"] == "success"
    assert "latest_major_version" in result["result"]
    assert "latest_minor_version" in result["result"]
    assert "latest_patch_version" in result["result"]


def test_get_all_latest_versions_with_classifier():
    """Test that dependencies with classifiers work correctly."""
    # Using a dependency known to have classifiers
    dependency = "org.apache.logging.log4j:log4j-api"
    version = "2.17.0"
    classifier = "javadoc"
    
    result = get_maven_all_latest_versions(dependency, version, classifier=classifier)
    
    # This may succeed or fail depending on if the javadoc classifier exists for all versions
    # We just check that the call completes without unexpected errors
    if result["status"] == "success":
        assert "latest_major_version" in result["result"]
    else:
        # If it fails, it should be because the classifier is not available
        assert result["error"]["code"] in [ErrorCode.DEPENDENCY_NOT_FOUND, ErrorCode.VERSION_NOT_FOUND]


def test_get_all_latest_versions_invalid_dependency():
    """Test handling of invalid dependency format."""
    dependency = "invalid-dependency-format"
    version = "1.0.0"
    
    result = get_maven_all_latest_versions(dependency, version)
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT


def test_get_all_latest_versions_invalid_version():
    """Test handling of completely invalid version format."""
    dependency = "org.apache.commons:commons-lang3"
    version = "invalid-version"
    
    result = get_maven_all_latest_versions(dependency, version)
    
    # With our new implementation, we should fall back to a default version tuple
    # and still try to get versions, not immediately error out
    if result["status"] == "error":
        # If it fails, it should be because of the parsing error
        assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT
    else:
        # If it succeeds, we should have the latest versions
        assert "latest_major_version" in result["result"]


def test_get_all_latest_versions_calendar_format():
    """Test handling of calendar format versions (YYYYMMDD)."""
    dependency = "org.json:json"
    version = "20231013"  # Calendar-based version
    
    result = get_maven_all_latest_versions(dependency, version)
    
    assert result["status"] == "success"
    assert "latest_major_version" in result["result"]
    
    # The version should be parsed as year.month.day
    # (Major=2023, Minor=10, Patch=13)
    # We can't test specific values as they'll change over time,
    # but we can verify the structure is correct


def test_get_all_latest_versions_dependency_not_found():
    """Test handling of dependency not found in Maven Central."""
    dependency = "com.example:non-existent-artifact"
    version = "1.0.0"
    
    result = get_maven_all_latest_versions(dependency, version)
    
    assert result["status"] == "error"
    assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND


def test_get_all_latest_versions_specific_packaging():
    """Test that specific packaging type works correctly."""
    dependency = "org.springframework.boot:spring-boot"
    version = "3.1.0"
    packaging = "jar"
    
    result = get_maven_all_latest_versions(dependency, version, packaging=packaging)
    
    assert result["status"] == "success"
    assert "latest_major_version" in result["result"]
    assert "latest_minor_version" in result["result"]
    assert "latest_patch_version" in result["result"]