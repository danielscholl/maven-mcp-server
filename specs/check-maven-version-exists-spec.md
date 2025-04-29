# Feature Specification: Check Maven Version Exists

> Verify if a specific version of a Maven dependency exists in the Maven Central repository.

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- Implement direct version existence checking against Maven Central
- Ensure robust error handling for all possible failure scenarios
- Make sure this functionality works end to end as an MCP tool in the server.py file

### Tool Details
- Implement in `src/maven_mcp_server/tools/version_exist.py`
- **check_maven_version_exists()**
  - Validate the dependency format (must be groupId:artifactId)
  - Validate the version string format
  - Query Maven Central API to check if the specific version exists
  - Properly handle package types and classifiers in the query
  - Return a boolean indicating existence (true/false)
- Optimize API calls for direct version checking when possible

### Input Rules
- `dependency` **MUST** match `groupId:artifactId` (no embedded version)
- `version` is required and must be a valid version string
- `packaging` is optional, defaults to "jar"
- `classifier` is optional, can be null or a valid classifier string

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Existing versions (return true)
  - Non-existing versions (return false)
  - Different packaging types
  - Dependencies with classifiers
  - Input validation errors
  - API response errors
- Tests must verify correctness across normal and boundary cases

## Tool to Expose

```text
check_maven_version_exists(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: str | None = None
) -> bool
```

### Response Format
- Return format matches the defined success/error dictionary structure:
  ```python
  # Success response
  {
    "tool_name": "check_maven_version_exists",
    "status": "success",
    "result": {
        "exists": bool
    }
  }
  
  # Error response
  {
    "tool_name": "check_maven_version_exists",
    "status": "error",
    "error": {
        "code": str,  # One of the ErrorCode enum values
        "message": str  # Human-readable error message
    }
  }
  ```

### Error Codes

| Code | Meaning |
|------|---------|
| INVALID_INPUT_FORMAT | Malformed dependency or version string |
| MISSING_PARAMETER    | Required parameter missing |
| DEPENDENCY_NOT_FOUND | No versions found for the dependency |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/version_exist.py
- src/maven_mcp_server/tests/tools/test_version_exist.py
- src/maven_mcp_server/tests/shared/test_utils.py

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_version_exist.py`
- Manual testing with actual Maven dependencies to verify real-world behavior