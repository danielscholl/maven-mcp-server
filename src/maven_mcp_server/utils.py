from typing import Dict, Any
import requests

def get_latest_version(group_id: str, artifact_id: str) -> Dict[str, Any]:
    """
    Get the latest version of a Maven artifact from Maven Central.
    
    Args:
        group_id: The group ID of the artifact
        artifact_id: The artifact ID
        
    Returns:
        Dict containing the latest version or error information
    """
    try:
        # For BOM artifacts, we need to check both jar and pom packaging
        if artifact_id.endswith("-bom"):
            # First try with pom packaging
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}+AND+p:pom&rows=1&wt=json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["response"]["numFound"] > 0:
                latest_version = data["response"]["docs"][0]["latestVersion"]
                return {
                    "status": "success",
                    "result": {
                        "latest_version": latest_version
                    }
                }
            
            # If no pom found, try with jar packaging
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}+AND+p:jar&rows=1&wt=json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["response"]["numFound"] > 0:
                latest_version = data["response"]["docs"][0]["latestVersion"]
                return {
                    "status": "success",
                    "result": {
                        "latest_version": latest_version
                    }
                }
            
            return {
                "status": "error",
                "error": {
                    "message": f"Artifact {group_id}:{artifact_id} not found in Maven Central"
                }
            }
        
        # For regular artifacts, just check jar packaging
        url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}+AND+p:jar&rows=1&wt=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["response"]["numFound"] > 0:
            latest_version = data["response"]["docs"][0]["latestVersion"]
            return {
                "status": "success",
                "result": {
                    "latest_version": latest_version
                }
            }
        
        return {
            "status": "error",
            "error": {
                "message": f"Artifact {group_id}:{artifact_id} not found in Maven Central"
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": {
                "message": f"Error querying Maven Central: {str(e)}"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        } 