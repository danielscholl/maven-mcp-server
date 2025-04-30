"""
Module containing the batch_maven_versions_check tool.
This tool allows checking latest versions for multiple dependencies in a single request.
"""

import logging
from typing import Dict, Any, List, Optional

from maven_mcp_server.shared.data_types import MavenError, ErrorCode, create_success_response, create_error_response, create_partial_success_response
from maven_mcp_server.tools.all_latest_versions import get_maven_all_latest_versions

logger = logging.getLogger("maven-check")

def batch_maven_versions_check(dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find the latest versions for multiple Maven dependencies in a single batch call.
    
    Args:
        dependencies: A list of dependency objects, each containing:
            - dependency (required): The dependency in the format 'groupId:artifactId'
            - version (required): The version string (in any supported format)
            - packaging (optional): The packaging type, defaults to 'jar'
            - classifier (optional): The classifier, if any
            
    Returns:
        A dictionary with the tool response containing results for each dependency and a summary.
    """
    tool_name = "batch_maven_versions_check"
    logger.info(f"{tool_name} called with {len(dependencies)} dependencies")
    
    # Input validation
    if not isinstance(dependencies, list):
        logger.error("Invalid input: 'dependencies' must be an array")
        return create_error_response(
            tool_name, 
            MavenError(ErrorCode.INVALID_INPUT_FORMAT, "Invalid input: 'dependencies' must be an array")
        )
    
    if not dependencies:
        logger.error("Empty dependencies array provided")
        return create_error_response(
            tool_name, 
            MavenError(ErrorCode.EMPTY_DEPENDENCIES, "Empty dependencies array provided")
        )
    
    results = []
    success_count = 0
    error_count = 0
    
    # Process each dependency individually
    for dependency_obj in dependencies:
        try:
            # Check for required fields
            if not isinstance(dependency_obj, dict):
                error_count += 1
                results.append({
                    "dependency": str(dependency_obj),
                    "status": "error",
                    "error": {
                        "code": ErrorCode.INVALID_INPUT_FORMAT,
                        "message": "Dependency must be an object"
                    }
                })
                continue
                
            # Extract parameters from dependency object
            dependency = dependency_obj.get("dependency")
            version = dependency_obj.get("version")
            
            if not dependency:
                error_count += 1
                results.append({
                    "dependency": str(dependency_obj),
                    "status": "error",
                    "error": {
                        "code": ErrorCode.MISSING_PARAMETER,
                        "message": "Required parameter 'dependency' is missing"
                    }
                })
                continue
                
            if not version:
                error_count += 1
                results.append({
                    "dependency": dependency,
                    "status": "error",
                    "error": {
                        "code": ErrorCode.MISSING_PARAMETER,
                        "message": "Required parameter 'version' is missing"
                    }
                })
                continue
            
            # Optional parameters
            packaging = dependency_obj.get("packaging", "jar")
            classifier = dependency_obj.get("classifier", None)
            
            # Directly use the existing function - leverage code reuse
            logger.info(f"Processing dependency: {dependency}, version: {version}, "
                       f"packaging: {packaging}, classifier: {classifier}")
            
            result = get_maven_all_latest_versions(
                dependency=dependency,
                version=version,
                packaging=packaging,
                classifier=classifier
            )
            
            # Process the result
            if result.get("status") == "success":
                success_count += 1
                results.append({
                    "dependency": dependency,
                    "status": "success",
                    "result": result.get("result", {})
                })
            else:
                error_count += 1
                results.append({
                    "dependency": dependency,
                    "status": "error",
                    "error": result.get("error", {
                        "code": ErrorCode.INTERNAL_SERVER_ERROR,
                        "message": "Unknown error processing dependency"
                    })
                })
                
        except Exception as e:
            logger.error(f"Error processing dependency {dependency_obj}: {str(e)}")
            error_count += 1
            results.append({
                "dependency": dependency_obj.get("dependency", str(dependency_obj)),
                "status": "error",
                "error": {
                    "code": ErrorCode.INTERNAL_SERVER_ERROR,
                    "message": f"Exception: {str(e)}"
                }
            })
    
    # Build the result object
    total_count = len(dependencies)
    logger.info(f"Batch processing complete. Total: {total_count}, "
               f"Success: {success_count}, Failed: {error_count}")
    
    result = {
        "dependencies": results,
        "summary": {
            "total": total_count,
            "success": success_count,
            "failed": error_count
        }
    }
    
    # Determine overall status and create appropriate response
    if error_count == 0:
        return create_success_response(tool_name, result)
    elif success_count > 0:
        return create_partial_success_response(tool_name, result)
    else:
        # If all dependencies failed, we'll still return a structured response with the details
        # rather than a simple error message
        return {
            "tool_name": tool_name,
            "status": "error",
            "result": result
        }