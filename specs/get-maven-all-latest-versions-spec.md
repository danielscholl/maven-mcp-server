# Feature Specification: Get Maven All Latest Versions

> Extend the Maven Check MCP server to provide the latest versions for all semantic versioning components (major, minor, patch) in a single call. Support both standard semver versions and non-semver formats like calendar versions (20231013).

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- Return the latest version for each semantic versioning component (major, minor, patch) for a given dependency
- Support both standard semver formats (MAJOR.MINOR.PATCH) and non-semver formats (e.g., calendar dates 20231013)
- Ensure robust error handling for all possible failure scenarios
- Make sure this functionality works end to end as an MCP tool in the server.py file

### Tool Details
- Implement in `src/maven_mcp_server/tools/all_latest_versions.py`
- **get_maven_all_latest_versions()**
  - Parse and validate the input version string
    - Standard semver format (MAJOR.MINOR.PATCH)
    - Calendar versions (e.g., 20231013)
    - Simple numeric versions (e.g., 5, 10)
    - Partial semver versions (e.g., 1.0)
  - Fetch all available versions for the dependency
  - Calculate and return the latest versions for all components:
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
- `packaging` is optional, defaults to "jar" (automatically uses "pom" for dependencies with -bom or -dependencies suffix)
- `classifier` is optional, can be null or a valid classifier string

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Verification of all three component versions returned
  - Different packaging types
  - Dependencies with classifiers
  - Various version formats (standard semver, calendar format, etc.)
  - Input validation errors
  - API response errors
  - Graceful handling of non-semver versions
- Tests must verify correctness across normal and boundary cases

## Tool to Expose

```text
get_maven_all_latest_versions(
    dependency: str,
    version: str,
    packaging: str = "jar",
    classifier: str | None = None
) -> dict
```

### Response Format
- Return format matches the defined success/error dictionary structure:
  ```python
  # Success response
  {
    "tool_name": "get_maven_all_latest_versions",
    "status": "success",
    "result": {
        "latest_major_version": str,
        "latest_minor_version": str,
        "latest_patch_version": str
    }
  }
  
  # Error response
  {
    "tool_name": "get_maven_all_latest_versions",
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
| VERSION_NOT_FOUND    | Version not found though dependency exists |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/all_latest_versions.py
- src/maven_mcp_server/tests/tools/test_all_latest_versions.py
- src/maven_mcp_server/tests/shared/test_utils.py

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_all_latest_versions.py`
- Manual testing with actual Maven dependencies to verify real-world behavior