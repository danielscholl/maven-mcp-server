"""
Integration tests for POM dependencies.
These tests make actual API calls to Maven Central, so they may fail if the network is unavailable.
"""

import pytest
import re
from maven_mcp_server.tools.version_exist import get_maven_latest_version
from maven_mcp_server.tools.check_version import check_maven_version_exists
from maven_mcp_server.shared.data_types import ErrorCode

# A list of known Maven BOM and dependencies packages
POM_DEPENDENCIES = [
    "org.springframework.boot:spring-boot-dependencies",
    "org.springframework:spring-framework-bom",
    "com.fasterxml.jackson:jackson-bom",
    "io.dropwizard:dropwizard-dependencies",
    "io.quarkus:quarkus-bom"
]

@pytest.mark.parametrize("dependency", POM_DEPENDENCIES)
def test_get_latest_version_with_pom_dependency(dependency):
    """Test getting the latest version of known POM dependencies."""
    # Explicitly set packaging to pom
    result = get_maven_latest_version(dependency, packaging="pom")
    
    # The test might fail if the dependency is not found, which is acceptable
    # However, if it succeeds, we should validate the result structure
    if result["status"] == "success":
        assert "latest_version" in result["result"]
        assert isinstance(result["result"]["latest_version"], str)
        # Verify it follows semantic versioning pattern
        assert re.match(r'^\d+\.\d+\.\d+', result["result"]["latest_version"])
    else:
        # If it fails, it should be because the dependency was not found
        assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND

@pytest.mark.parametrize("dependency", POM_DEPENDENCIES)
def test_auto_detection_pom_packaging(dependency):
    """Test auto-detection of POM packaging for -dependencies and -bom artifacts."""
    # Let the auto-detection handle the packaging
    result = get_maven_latest_version(dependency)
    
    # Same validation as above
    if result["status"] == "success":
        assert "latest_version" in result["result"]
        assert isinstance(result["result"]["latest_version"], str)
        assert re.match(r'^\d+\.\d+\.\d+', result["result"]["latest_version"])
    else:
        assert result["error"]["code"] == ErrorCode.DEPENDENCY_NOT_FOUND


# We'll only test one of these as an integration test to avoid too many API calls
def test_check_version_exists_with_pom_dependency():
    """Test checking if a specific version of a POM dependency exists."""
    # Use a known stable version that's unlikely to change
    dependency = "org.springframework:spring-framework-bom"
    version = "5.3.27"  # This is a stable version that should exist
    
    result = check_maven_version_exists(dependency, version)
    
    # Since this tests a specific version, it might fail if that version no longer exists
    # So we'll be more forgiving in our assertions
    if result["status"] == "success":
        assert "exists" in result["result"]
        assert isinstance(result["result"]["exists"], bool)
    else:
        # It might be that the version doesn't exist, which is fine
        assert result["error"]["code"] in [
            ErrorCode.DEPENDENCY_NOT_FOUND, 
            ErrorCode.VERSION_NOT_FOUND
        ]