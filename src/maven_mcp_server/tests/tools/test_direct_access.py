"""
Tests for the direct repository access functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from maven_mcp_server.shared.utils import check_direct_repository_access
from maven_mcp_server.tools.version_exist import get_maven_latest_version


def test_check_direct_repository_access():
    """Test direct repository access for Maven artifacts."""
    # This is a real network test, so it may occasionally fail if network is down
    exists, versions, error = check_direct_repository_access(
        "org.springframework.boot", "spring-boot-dependencies"
    )
    
    assert error is None
    assert exists is True
    assert len(versions) > 0
    assert any(v.startswith("3.") for v in versions)


def test_spring_boot_dependencies_fallback():
    """Test the special handling for Spring Boot dependencies."""
    result = get_maven_latest_version("org.springframework.boot:spring-boot-dependencies")
    
    assert result["status"] == "success"
    assert "latest_version" in result["result"]
    assert isinstance(result["result"]["latest_version"], str)
    # Version should be in format like "3.x.x"
    assert result["result"]["latest_version"].startswith("3.")


@patch('maven_mcp_server.tools.version_exist.check_direct_repository_access')
@patch('maven_mcp_server.tools.version_exist.query_maven_central')
def test_fallback_mechanism(mock_query, mock_direct_access):
    """Test the fallback mechanism when the search API fails."""
    # Mock the search API to fail
    mock_query.return_value = ({
        "response": {"numFound": 0, "docs": []}
    }, None)
    
    # Mock the direct access to succeed
    mock_direct_access.return_value = (True, ["3.2.0", "3.1.0", "3.0.0"], None)
    
    # Call the function
    result = get_maven_latest_version("org.springframework.boot:spring-boot-dependencies")
    
    # Verify that direct access was attempted after search API failed
    mock_direct_access.assert_called_once()
    
    # Verify the result
    assert result["status"] == "success"
    assert result["result"]["latest_version"] == "3.2.0"