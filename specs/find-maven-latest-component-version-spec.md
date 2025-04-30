# Feature Specification: Find Maven Latest Component Version

> Extend the Maven Check MCP server to provide fine-grained version resolution based on semantic versioning components. Support both standard semver versions and non-semver formats like calendar versions (20231013).

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- Implement proper semantic versioning component-based resolution
- Support both standard semver formats (MAJOR.MINOR.PATCH) and non-semver formats (e.g., calendar dates 20231013)
- Ensure robust error handling for all possible failure scenarios
- Make sure this functionality works end to end as an MCP tool in the server.py file

### Tool Details
- Implement in `src/maven_mcp_server/tools/latest_by_semver.py`
- **find_maven_latest_component_version()**
  - Parse and validate the input version string 
    - Standard semver format (MAJOR.MINOR.PATCH)
    - Calendar versions (e.g., 20231013)
    - Simple numeric versions (e.g., 5, 10)
    - Partial semver versions (e.g., 1.0)
  - Validate the target_component parameter (must be "major", "minor", or "patch")
  - Fetch all available versions for the dependency
  - Based on `target_component`, calculate and return the latest:
    - **major** → highest available major version across all versions
    - **minor** → highest minor version within the given major version
    - **patch** → highest patch version within the given major.minor version
  - Must ignore pre-release versions unless explicitly specified
  - Handle packaging types and classifiers correctly
- Automatically detect POM dependencies (artifacts with -bom or -dependencies suffix)
- Provide direct repository access fallback for dependencies not properly indexed by Maven search API
- Special handling for specific library patterns like Spring Boot dependencies
- Graceful fallback when versions don't follow semver format

### Input Rules
- `dependency` **MUST** match `groupId:artifactId` (no embedded version)
- `version` can be provided in various formats:
  - Standard semantic version (`MAJOR.MINOR.PATCH`) - preferred
  - Calendar format (e.g., `20231013`)
  - Simple numeric format (e.g., `5`)
  - Partial semver format (e.g., `1.0`)
- `target_component` must be one of: `major`, `minor`, or `patch`
- `packaging` is optional, defaults to "jar" (automatically uses "pom" for dependencies with -bom or -dependencies suffix)
- `classifier` is optional, can be null or a valid classifier string

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Major version latest detection
  - Minor version latest detection
  - Patch version latest detection
  - Different packaging types
  - Dependencies with classifiers
  - Various version formats (standard semver, calendar format, etc.)
  - Input validation errors
  - API response errors
  - Graceful handling of non-semver versions
- Tests must verify correctness across normal and boundary cases

## Tool to Expose

```text
find_maven_latest_component_version(
    dependency: str,
    version: str,
    target_component: str,  # One of "major", "minor", "patch"
    packaging: str = "jar",
    classifier: str | None = None
) -> str
```

### Response Format
- Return format matches the defined success/error dictionary structure:
  ```python
  # Success response
  {
    "tool_name": "find_maven_latest_component_version",
    "status": "success",
    "result": {
        "latest_version": str
    }
  }
  
  # Error response
  {
    "tool_name": "find_maven_latest_component_version",
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
| INVALID_TARGET_COMPONENT | Invalid target_component value |
| MISSING_PARAMETER    | Required parameter missing |
| DEPENDENCY_NOT_FOUND | No versions found for the dependency |
| VERSION_NOT_FOUND    | Version not found though dependency exists |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/latest_by_semver.py
- src/maven_mcp_server/tests/tools/test_latest_by_semver.py
- src/maven_mcp_server/tests/shared/test_utils.py

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_latest_by_semver.py`
- Manual testing with actual Maven dependencies to verify real-world behavior