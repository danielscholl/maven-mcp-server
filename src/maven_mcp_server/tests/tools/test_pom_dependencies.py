"""
Tests for Maven dependencies with POM packaging type.
"""

import pytest
from unittest.mock import patch, MagicMock
from maven_mcp_server.tools.version_exist import get_maven_latest_version
from maven_mcp_server.tools.check_version import check_maven_version_exists
from maven_mcp_server.tools.latest_by_semver import find_maven_latest_component_version
from maven_mcp_server.shared.data_types import ErrorCode


def test_auto_packaging_detection_dependencies():
    """Test that -dependencies artifacts automatically use POM packaging."""
    # We'll mock the get_latest_version function to verify it's called with pom packaging
    with patch('maven_mcp_server.tools.version_exist.get_latest_version') as mock_get_latest:
        # Set up the mock to return a success response
        mock_get_latest.return_value = {
            "status": "success",
            "result": {
                "latest_version": "3.2.0"
            }
        }
        
        # Call the function with a -dependencies artifact
        result = get_maven_latest_version("org.springframework.boot:spring-boot-dependencies")
        
        # Verify the mock was called with pom packaging
        mock_get_latest.assert_called_once()
        args, kwargs = mock_get_latest.call_args
        assert args[0] == "org.springframework.boot"  # group_id
        assert args[1] == "spring-boot-dependencies"  # artifact_id
        assert args[2] == "pom"  # packaging should be automatically set to pom
        assert kwargs == {}  # No other kwargs


def test_auto_packaging_detection_regular_artifact():
    """Test that regular artifacts use the specified packaging (jar by default)."""
    # We'll mock the get_latest_version function to verify it's called with jar packaging
    with patch('maven_mcp_server.tools.version_exist.get_latest_version') as mock_get_latest:
        # Set up the mock to return a success response
        mock_get_latest.return_value = {
            "status": "success",
            "result": {
                "latest_version": "3.13.0"
            }
        }
        
        # Call the function with a regular artifact
        result = get_maven_latest_version("org.springframework.boot:spring-boot")
        
        # Verify the mock was called with jar packaging
        mock_get_latest.assert_called_once()
        args, kwargs = mock_get_latest.call_args
        assert args[0] == "org.springframework.boot"  # group_id
        assert args[1] == "spring-boot"  # artifact_id
        assert args[2] == "jar"  # default packaging should be jar
        assert kwargs == {}  # No other kwargs


def test_check_version_exists_with_pom_dependency():
    """Test check_maven_version_exists with a -dependencies artifact."""
    # We'll mock the check_version_exists function to verify it's called with pom packaging
    with patch('maven_mcp_server.tools.check_version.check_version_exists') as mock_check_version:
        # Set up the mock to return a success response
        mock_check_version.return_value = {
            "status": "success",
            "result": {
                "exists": True
            }
        }
        
        # Call the function with a -dependencies artifact
        result = check_maven_version_exists(
            "org.springframework.boot:spring-boot-dependencies", 
            "3.2.0"
        )
        
        # Verify the mock was called with pom packaging
        mock_check_version.assert_called_once()
        args, kwargs = mock_check_version.call_args
        assert args[0] == "org.springframework.boot"  # group_id
        assert args[1] == "spring-boot-dependencies"  # artifact_id
        assert args[2] == "3.2.0"  # version
        assert args[3] == "pom"  # packaging should be automatically set to pom
        assert args[4] is None  # classifier


def test_find_latest_component_with_pom_dependency():
    """Test find_maven_latest_component_version with a -dependencies artifact."""
    # We'll mock the necessary functions
    with patch('maven_mcp_server.tools.latest_by_semver.get_latest_component_version') as mock_get_component:
        # Set up the mock to return a success response
        mock_get_component.return_value = {
            "status": "success",
            "result": {
                "latest_version": "3.2.0"
            }
        }
        
        # Also mock parse_semver to return a valid version tuple
        with patch('maven_mcp_server.tools.latest_by_semver.parse_semver') as mock_parse_semver:
            mock_parse_semver.return_value = (True, (3, 2, 0), None)
            
            # Call the function with a -dependencies artifact
            result = find_maven_latest_component_version(
                "org.springframework.boot:spring-boot-dependencies", 
                "3.2.0",
                "minor"
            )
            
            # Verify the mock was called with pom packaging
            mock_get_component.assert_called_once()
            args, kwargs = mock_get_component.call_args
            assert args[0] == "org.springframework.boot"  # group_id
            assert args[1] == "spring-boot-dependencies"  # artifact_id
            assert args[2] == (3, 2, 0)  # version tuple
            assert args[3] == "minor"  # target component
            assert args[4] == "pom"  # packaging should be automatically set to pom
            assert args[5] is None  # classifier


def test_explicitly_specified_packaging_overrides_auto_detection():
    """Test that explicitly specified packaging overrides auto-detection."""
    # We'll mock the get_latest_version function to verify it's called with the specified packaging
    with patch('maven_mcp_server.tools.version_exist.get_latest_version') as mock_get_latest:
        # Set up the mock to return a success response
        mock_get_latest.return_value = {
            "status": "success",
            "result": {
                "latest_version": "3.2.0"
            }
        }
        
        # Call the function with a -dependencies artifact but specify a different packaging
        result = get_maven_latest_version(
            "org.springframework.boot:spring-boot-dependencies", 
            packaging="war"  # This should override the auto-detection
        )
        
        # Verify the mock was called with the specified packaging, not the auto-detected one
        mock_get_latest.assert_called_once()
        args, kwargs = mock_get_latest.call_args
        assert args[0] == "org.springframework.boot"  # group_id
        assert args[1] == "spring-boot-dependencies"  # artifact_id
        assert args[2] == "pom"  # Should still be pom despite specifying war
        assert kwargs == {}  # No other kwargs