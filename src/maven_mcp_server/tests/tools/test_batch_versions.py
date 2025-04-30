"""
Tests for the batch_maven_versions_check tool.
"""

import pytest
from typing import Dict, Any, List

from maven_mcp_server.tools.batch_versions import batch_maven_versions_check
from maven_mcp_server.shared.data_types import ErrorCode


def test_batch_maven_versions_check_success() -> None:
    """Test the batch_maven_versions_check tool with multiple valid dependencies."""
    # Test input with multiple valid dependencies
    dependencies = [
        {
            "dependency": "org.apache.commons:commons-lang3",
            "version": "3.12.0"
        },
        {
            "dependency": "org.springframework.boot:spring-boot-dependencies",
            "version": "3.1.0"
        }
    ]
    
    result = batch_maven_versions_check(dependencies=dependencies)
    
    # Verify overall result
    assert result["status"] == "success"
    assert "result" in result
    assert "dependencies" in result["result"]
    assert "summary" in result["result"]
    
    # Verify summary
    summary = result["result"]["summary"]
    assert summary["total"] == 2
    assert summary["success"] == 2
    assert summary["failed"] == 0
    
    # Verify each dependency result
    dependency_results = result["result"]["dependencies"]
    assert len(dependency_results) == 2
    
    # First dependency
    assert dependency_results[0]["dependency"] == "org.apache.commons:commons-lang3"
    assert dependency_results[0]["status"] == "success"
    assert "result" in dependency_results[0]
    assert "latest_major_version" in dependency_results[0]["result"]
    assert "latest_minor_version" in dependency_results[0]["result"]
    assert "latest_patch_version" in dependency_results[0]["result"]
    
    # Second dependency
    assert dependency_results[1]["dependency"] == "org.springframework.boot:spring-boot-dependencies"
    assert dependency_results[1]["status"] == "success"
    assert "result" in dependency_results[1]
    assert "latest_major_version" in dependency_results[1]["result"]
    assert "latest_minor_version" in dependency_results[1]["result"]
    assert "latest_patch_version" in dependency_results[1]["result"]


def test_batch_maven_versions_check_partial_success() -> None:
    """Test the batch_maven_versions_check tool with a mix of valid and invalid dependencies."""
    # Test input with one valid and one invalid dependency
    dependencies = [
        {
            "dependency": "org.apache.commons:commons-lang3",
            "version": "3.12.0"
        },
        {
            "dependency": "invalid:dependency-format",
            "version": "1.0.0"
        }
    ]
    
    result = batch_maven_versions_check(dependencies=dependencies)
    
    # Verify overall result - should be partial_success
    assert result["status"] == "partial_success"
    assert "result" in result
    assert "dependencies" in result["result"]
    assert "summary" in result["result"]
    
    # Verify summary
    summary = result["result"]["summary"]
    assert summary["total"] == 2
    assert summary["success"] == 1
    assert summary["failed"] == 1
    
    # Verify each dependency result
    dependency_results = result["result"]["dependencies"]
    assert len(dependency_results) == 2
    
    # First dependency (should succeed)
    assert dependency_results[0]["dependency"] == "org.apache.commons:commons-lang3"
    assert dependency_results[0]["status"] == "success"
    assert "result" in dependency_results[0]
    
    # Second dependency (should fail)
    assert dependency_results[1]["dependency"] == "invalid:dependency-format"
    assert dependency_results[1]["status"] == "error"
    assert "error" in dependency_results[1]
    assert "code" in dependency_results[1]["error"]
    

def test_batch_maven_versions_check_empty_dependencies() -> None:
    """Test the batch_maven_versions_check tool with an empty dependencies array."""
    result = batch_maven_versions_check(dependencies=[])
    
    # Verify error response
    assert result["status"] == "error"
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.EMPTY_DEPENDENCIES
    assert "message" in result["error"]


def test_batch_maven_versions_check_missing_required_fields() -> None:
    """Test the batch_maven_versions_check tool with dependencies missing required fields."""
    dependencies = [
        {
            "dependency": "org.apache.commons:commons-lang3"
            # Missing version
        },
        {
            # Missing dependency
            "version": "1.0.0"
        }
    ]
    
    result = batch_maven_versions_check(dependencies=dependencies)
    
    # Verify overall result - should be error (all failed)
    assert result["status"] == "error"
    assert "result" in result
    assert "dependencies" in result["result"]
    assert "summary" in result["result"]
    
    # Verify summary
    summary = result["result"]["summary"]
    assert summary["total"] == 2
    assert summary["success"] == 0
    assert summary["failed"] == 2
    
    # Verify each dependency result
    dependency_results = result["result"]["dependencies"]
    assert len(dependency_results) == 2
    
    # First dependency (should fail due to missing version)
    assert dependency_results[0]["dependency"] == "org.apache.commons:commons-lang3"
    assert dependency_results[0]["status"] == "error"
    assert "error" in dependency_results[0]
    assert dependency_results[0]["error"]["code"] == ErrorCode.MISSING_PARAMETER
    
    # Second dependency (should fail due to missing dependency)
    assert dependency_results[1]["status"] == "error"
    assert "error" in dependency_results[1]
    assert dependency_results[1]["error"]["code"] == ErrorCode.MISSING_PARAMETER


def test_batch_maven_versions_check_invalid_input() -> None:
    """Test the batch_maven_versions_check tool with an invalid input type for dependencies."""
    # Test with non-array dependencies
    result = batch_maven_versions_check(dependencies="not-an-array")
    
    # Verify error response
    assert result["status"] == "error"
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.INVALID_INPUT_FORMAT
    assert "message" in result["error"]


def test_batch_maven_versions_check_different_version_formats() -> None:
    """Test the batch_maven_versions_check tool with different version formats."""
    dependencies = [
        {
            "dependency": "org.apache.commons:commons-lang3",
            "version": "3.12.0"  # Standard semver
        },
        {
            "dependency": "org.json:json",
            "version": "20231013"  # Calendar version
        }
    ]
    
    result = batch_maven_versions_check(dependencies=dependencies)
    
    # Verify overall result
    assert result["status"] == "success"
    assert "result" in result
    assert "dependencies" in result["result"]
    
    # Verify each dependency result
    dependency_results = result["result"]["dependencies"]
    assert len(dependency_results) == 2
    
    # First dependency (standard semver)
    assert dependency_results[0]["dependency"] == "org.apache.commons:commons-lang3"
    assert dependency_results[0]["status"] == "success"
    
    # Second dependency (calendar version)
    assert dependency_results[1]["dependency"] == "org.json:json"
    assert dependency_results[1]["status"] == "success"


def test_batch_maven_versions_check_with_packaging_and_classifier() -> None:
    """Test the batch_maven_versions_check tool with packaging and classifier options."""
    dependencies = [
        {
            "dependency": "org.apache.commons:commons-lang3",
            "version": "3.12.0",
            "packaging": "jar"
        },
        {
            "dependency": "org.springframework.boot:spring-boot-dependencies",
            "version": "3.1.0",
            "packaging": "pom"  # Explicit packaging
        }
    ]
    
    result = batch_maven_versions_check(dependencies=dependencies)
    
    # Verify overall result
    assert result["status"] == "success"
    assert "result" in result
    assert "dependencies" in result["result"]
    
    # Verify each dependency result
    dependency_results = result["result"]["dependencies"]
    assert len(dependency_results) == 2
    
    # All dependencies should have succeeded
    assert dependency_results[0]["status"] == "success"
    assert dependency_results[1]["status"] == "success"