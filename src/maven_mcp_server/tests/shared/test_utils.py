"""
Tests for the utility functions in the shared module.
"""

import pytest
from maven_mcp_server.shared.utils import (
    validate_dependency_format, parse_dependency,
    query_maven_central, get_latest_version, check_version_exists
)
from maven_mcp_server.shared.data_types import ErrorCode


def test_validate_dependency_format_valid():
    """Test validation of valid dependency format."""
    is_valid, error = validate_dependency_format("org.apache.commons:commons-lang3")
    
    assert is_valid is True
    assert error is None


def test_validate_dependency_format_invalid():
    """Test validation of invalid dependency format."""
    is_valid, error = validate_dependency_format("invalid-format")
    
    assert is_valid is False
    assert error is not None
    assert error.code == ErrorCode.INVALID_INPUT_FORMAT


def test_validate_dependency_format_empty():
    """Test validation of empty dependency."""
    is_valid, error = validate_dependency_format("")
    
    assert is_valid is False
    assert error is not None
    assert error.code == ErrorCode.MISSING_PARAMETER


def test_parse_dependency():
    """Test parsing of dependency string."""
    group_id, artifact_id = parse_dependency("org.apache.commons:commons-lang3")
    
    assert group_id == "org.apache.commons"
    assert artifact_id == "commons-lang3"


def test_query_maven_central_success():
    """Test successful query to Maven Central."""
    params = {"q": "g:org.apache.commons AND a:commons-lang3"}
    response, error = query_maven_central(params)
    
    assert error is None
    assert "response" in response
    assert response["response"]["numFound"] > 0


def test_query_maven_central_nonexistent():
    """Test query for a nonexistent artifact."""
    params = {"q": "g:org.nonexistent AND a:artifact-nonexistent"}
    response, error = query_maven_central(params)
    
    assert error is None
    assert "response" in response
    assert response["response"]["numFound"] == 0


def test_get_latest_version_success():
    """Test successful retrieval of latest version."""
    latest_version, error = get_latest_version("org.apache.commons", "commons-lang3")
    
    assert error is None
    assert latest_version is not None
    assert isinstance(latest_version, str)


def test_get_latest_version_nonexistent():
    """Test retrieval for a nonexistent artifact."""
    latest_version, error = get_latest_version("org.nonexistent", "artifact-nonexistent")
    
    assert error is not None
    assert error.code == ErrorCode.DEPENDENCY_NOT_FOUND
    assert latest_version is None


def test_check_version_exists_success():
    """Test successful check of an existing version."""
    exists, error = check_version_exists("org.apache.commons", "commons-lang3", "3.12.0")
    
    assert error is None
    assert exists is True


def test_check_version_exists_nonexistent_version():
    """Test check for a nonexistent version of an existing artifact."""
    exists, error = check_version_exists("org.apache.commons", "commons-lang3", "999.999.999")
    
    assert error is not None
    assert error.code == ErrorCode.VERSION_NOT_FOUND
    assert exists is False


def test_check_version_exists_nonexistent_artifact():
    """Test check for a nonexistent artifact."""
    exists, error = check_version_exists("org.nonexistent", "artifact-nonexistent", "1.0.0")
    
    assert error is not None
    assert error.code == ErrorCode.DEPENDENCY_NOT_FOUND
    assert exists is False