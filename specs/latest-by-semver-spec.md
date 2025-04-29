# Feature Update Specification: Latest Version By SemVer

> Extend the Maven Check MCP server to provide fine-grained version resolution based on semantic versioning components.

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- After you implement, update the README.md with the new tool's functionality
- Make sure this functionality works end to end. This functionality will be exposed as an MCP tool in the server.py file.

### New Tool Details
- Create a new tool latest_by_semver in `src/maven_mcp_server_tools/tools/latest_by_semver.py`
- **find_maven_latest_component_version()**
  - Parse and validate the input version string
  - Fetch all available versions for the dependency
  - Based on `target_component`, calculate and return the latest:
    - **major** → highest available major version
    - **minor** → highest minor version within the given major
    - **patch** → highest patch version within the given major.minor
  - Must ignore pre-release versions (unless explicitly specified later)
- Return the latest version of dependency based on target component.

### Input Rules
- `dependency` **MUST** match `groupId:artifactId`
- `version` **MUST** be a valid semantic version (`MAJOR.MINOR.PATCH`)
- `target_component` must be one of: `major`, `minor`, or `patch`
- Reject unknown `target_component` values with proper error handling

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - major version latest detection
  - minor version latest detection
  - patch version latest detection
  - input validation errors
- Tests must verify correctness across normal and boundary cases

## Tools to Expose

```text
find_maven_latest_component_version(
    dependency: str,
    version: str,
    target_component: str  # One of "major", "minor", "patch"
) -> str
```

### Response Format
- Return format matches the existing success/error dictionary structure:
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
        "code": str,
        "message": str
    }
  }
  ```



## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/latest_by_semver.py
- src/maven_mcp_server/tests/tools/latest_by_semver.py
- src/maven_mcp_server/tests/shared/test_utils.py

## Validation (Close the Loop)
> Be sure to test this new capability with uv run pytest.

- `uv run pytest src/just_prompt/tests/molecules/test_business_analyst_prompt.py`
- `uv run just-prompt --help` to validate the tool works as expected.