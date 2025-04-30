"""
Tests for date-based versioning in the latest version tools.
Specifically testing the org.json:json dependency with date-based versions (20231013, 20240303, etc.)
"""

import pytest
from unittest.mock import patch, MagicMock

from maven_mcp_server.tools.all_latest_versions import get_maven_all_latest_versions
from maven_mcp_server.tools.latest_by_semver import find_maven_latest_component_version
from maven_mcp_server.shared.utils import parse_dependency


class MockResponse:
    """
    Custom class for mocking the API response
    """
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data
        
    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

@pytest.fixture
def mock_requests_get():
    """
    Mock for requests.get to simulate API response with date-based versions
    """
    def _mock_get(url, params=None, **kwargs):
        # Create a response with date-based versions in random order
        # to ensure sorting works correctly
        return MockResponse(200, {
            "response": {
                "numFound": 6,
                "docs": [
                    {"id": "org.json:json:20151123", "g": "org.json", "a": "json", "v": "20151123", "p": "jar"},
                    {"id": "org.json:json:20220924", "g": "org.json", "a": "json", "v": "20220924", "p": "jar"},
                    {"id": "org.json:json:20230227", "g": "org.json", "a": "json", "v": "20230227", "p": "jar"},
                    {"id": "org.json:json:20231013", "g": "org.json", "a": "json", "v": "20231013", "p": "jar"},
                    {"id": "org.json:json:20240205", "g": "org.json", "a": "json", "v": "20240205", "p": "jar"},
                    {"id": "org.json:json:20240303", "g": "org.json", "a": "json", "v": "20240303", "p": "jar"},
                ]
            }
        })
    return _mock_get


@patch('requests.get')
def test_all_latest_versions_date_based(mock_get, mock_requests_get):
    """
    Test that get_maven_all_latest_versions correctly handles date-based versions
    """
    # Setup the mock to use our fixture
    mock_get.side_effect = mock_requests_get
    
    # Call the function with org.json:json and a date-based version
    result = get_maven_all_latest_versions("org.json:json", "20231013")
    
    # Print the result for debugging
    print(f"Test result: {result}")
    
    # Assert
    assert result["status"] == "success"
    assert result["result"]["latest_major_version"] == "20240303"
    assert result["result"]["latest_minor_version"] == "20240303"
    assert result["result"]["latest_patch_version"] == "20240303"


@patch('requests.get')
def test_latest_component_version_date_based_major(mock_get, mock_requests_get):
    """
    Test that find_maven_latest_component_version correctly handles date-based versions for major component
    """
    # Setup the mock
    mock_get.side_effect = mock_requests_get
    
    # Call the function with org.json:json and a date-based version
    result = find_maven_latest_component_version("org.json:json", "20231013", "major")
    
    # Assert
    assert result["status"] == "success"
    assert result["result"]["latest_version"] == "20240303"


@patch('requests.get')
def test_latest_component_version_date_based_minor(mock_get, mock_requests_get):
    """
    Test that find_maven_latest_component_version correctly handles date-based versions for minor component
    """
    # Setup the mock
    mock_get.side_effect = mock_requests_get
    
    # Call the function with org.json:json and a date-based version
    result = find_maven_latest_component_version("org.json:json", "20231013", "minor")
    
    # Assert
    assert result["status"] == "success"
    assert result["result"]["latest_version"] == "20240303"


@patch('requests.get')
def test_latest_component_version_date_based_patch(mock_get, mock_requests_get):
    """
    Test that find_maven_latest_component_version correctly handles date-based versions for patch component
    """
    # Setup the mock
    mock_get.side_effect = mock_requests_get
    
    # Call the function with org.json:json and a date-based version
    result = find_maven_latest_component_version("org.json:json", "20231013", "patch")
    
    # Assert
    assert result["status"] == "success"
    assert result["result"]["latest_version"] == "20240303"


@patch('requests.get')
def test_get_latest_version_date_based(mock_get, mock_requests_get):
    """
    Test that get_maven_latest_version correctly handles date-based versions
    """
    # Import here to avoid circular imports
    from maven_mcp_server.tools.version_exist import get_maven_latest_version
    
    # Setup the mock
    mock_get.side_effect = mock_requests_get
    
    # Call the function with org.json:json
    result = get_maven_latest_version("org.json:json")
    
    # Assert
    assert result["status"] == "success"
    assert result["result"]["latest_version"] == "20240303"