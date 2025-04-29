# Feature Specification: Get Maven Latest Version

> Core functionality to retrieve the latest version of a Maven dependency from the Maven Central repository.

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- Implement proper semantic versioning comparison for accurate version detection
- Ensure robust error handling for all possible failure scenarios
- Make sure this functionality works end to end as an MCP tool in the server.py file

### Tool Details
- Implement in `src/maven_mcp_server/tools/check_version.py`
- **get_maven_latest_version()**
  - Validate the dependency format (must be groupId:artifactId)
  - Query Maven Central API to retrieve all versions
  - Apply semantic versioning comparison to determine the actual latest version
  - Sort and filter results properly (ignoring snapshots unless specifically requested)
  - Return the latest version as a string
- Handle packaging types and classifiers correctly

### Input Rules
- `dependency` **MUST** match `groupId:artifactId` (no embedded version)
- `packaging` is optional, defaults to "jar"
- `classifier` is optional, can be null or a valid classifier string

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Valid dependencies with various versions
  - Dependencies with different packaging types
  - Dependencies with classifiers
  - Input validation errors
  - API response errors
- Tests must verify correctness across normal and boundary cases

## Tool to Expose

```text
get_maven_latest_version(
    dependency: str, 
    packaging: str = "jar", 
    classifier: str | None = None
) -> str
```

### Response Format
- Return format matches the defined success/error dictionary structure:
  ```python
  # Success response
  {
    "tool_name": "get_maven_latest_version",
    "status": "success",
    "result": {
        "latest_version": str
    }
  }
  
  # Error response
  {
    "tool_name": "get_maven_latest_version",
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
| INVALID_INPUT_FORMAT | Malformed dependency string |
| MISSING_PARAMETER    | Required parameter missing |
| DEPENDENCY_NOT_FOUND | No versions found for the dependency |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/check_version.py
- src/maven_mcp_server/tests/tools/test_check_version.py
- src/maven_mcp_server/tests/shared/test_utils.py

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_check_version.py`
- Manual testing with actual Maven dependencies to verify real-world behavior