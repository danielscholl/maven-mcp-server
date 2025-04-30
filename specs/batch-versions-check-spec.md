# Feature Specification: Maven Batch Versions Check

> Extend the Maven Check MCP server to provide the ability to check latest versions for multiple dependencies in a single request, improving efficiency when working with POM files containing multiple dependencies.

## Implementation Details
- Be sure to validate this functionality with uv run pytest
- Create a new tool that accepts a list of dependency specifications
- Return the latest versions for each dependency in a single consolidated response
- Support both standard semver formats (MAJOR.MINOR.PATCH) and non-semver formats
- Ensure robust error handling for all possible failure scenarios
- Make sure this functionality works end to end as an MCP tool in the server.py file

### Tool Details
- Implement in `src/maven_mcp_server/tools/batch_versions.py`
- **batch_maven_versions_check()**
  - Accept an array of dependency objects, each containing:
    - dependency (required): in 'groupId:artifactId' format
    - version (required): current version string
    - packaging (optional): defaults to "jar"
    - classifier (optional): can be null or a valid classifier string
  - **IMPORTANT: Reuse existing code by directly calling `get_maven_all_latest_versions`**:
    - Do not duplicate any version checking or repository access logic
    - Simply loop through each dependency and call the existing function
    - This ensures consistency between single and batch calls and avoids code duplication
  - For each dependency in the input array:
    - Validate input parameters
    - Process using the existing get_maven_all_latest_versions function
    - Collect results, including any errors per dependency
  - Return a consolidated result object with status per dependency
  - Handle errors gracefully, allowing partial success (some dependencies succeeded, others failed)
  - Maintain full compatibility with the existing single-dependency API

### Input Rules
- `dependencies` **MUST** be an array of objects, each containing:
  - `dependency`: **MUST** match `groupId:artifactId` (no embedded version)
  - `version`: The current version string in any supported format
  - `packaging`: Optional, defaults to "jar" (auto-detects BOM dependencies)
  - `classifier`: Optional, can be null or a valid classifier string
- All validation rules from the single-dependency tools apply to each entry

### Example Input
```json
{
  "dependencies": [
    {
      "dependency": "org.apache.commons:commons-lang3",
      "version": "3.12.0"
    },
    {
      "dependency": "org.springframework.boot:spring-boot-dependencies", 
      "version": "3.1.0"
    },
    {
      "dependency": "org.json:json",
      "version": "20231013"
    }
  ]
}
```

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Multiple dependencies in a single request
  - Mix of successful and failed dependency lookups
  - Different version formats in the same request
  - Various error conditions (malformed inputs, API failures)
  - Edge cases (empty array, single item, large number of dependencies)
- Verify performance characteristics with multiple dependencies
- Tests must verify correctness across normal and boundary cases

## Tool to Expose

```text
batch_maven_versions_check(
    dependencies: list[dict]
) -> dict
```

### Response Format
- Return format matches the defined success/error dictionary structure:
  ```python
  # Success response
  {
    "tool_name": "batch_maven_versions_check",
    "status": "success",
    "result": {
      "dependencies": [
        {
          "dependency": "org.apache.commons:commons-lang3",
          "status": "success",
          "result": {
            "latest_major_version": "3.14.0",
            "latest_minor_version": "3.12.0",
            "latest_patch_version": "3.12.0"
          }
        },
        {
          "dependency": "org.springframework.boot:spring-boot-dependencies",
          "status": "success",
          "result": {
            "latest_major_version": "3.2.0",
            "latest_minor_version": "3.1.5",
            "latest_patch_version": "3.1.0"
          }
        },
        {
          "dependency": "org.json:json",
          "status": "success",
          "result": {
            "latest_major_version": "20240303",
            "latest_minor_version": "20240303",
            "latest_patch_version": "20240303"
          }
        }
      ],
      "summary": {
        "total": 3,
        "success": 3,
        "failed": 0
      }
    }
  }
  
  # Partial success/error response
  {
    "tool_name": "batch_maven_versions_check",
    "status": "partial_success",
    "result": {
      "dependencies": [
        {
          "dependency": "org.apache.commons:commons-lang3",
          "status": "success",
          "result": {
            "latest_major_version": "3.14.0",
            "latest_minor_version": "3.12.0",
            "latest_patch_version": "3.12.0"
          }
        },
        {
          "dependency": "invalid:dependency-format",
          "status": "error",
          "error": {
            "code": "INVALID_INPUT_FORMAT",
            "message": "Invalid dependency format: 'invalid:dependency-format'"
          }
        }
      ],
      "summary": {
        "total": 2,
        "success": 1,
        "failed": 1
      }
    }
  }
  
  # Overall error response (for issues affecting the entire batch)
  {
    "tool_name": "batch_maven_versions_check",
    "status": "error",
    "error": {
      "code": "INVALID_INPUT_FORMAT",
      "message": "Invalid input: 'dependencies' must be an array"
    }
  }
  ```

### Error Codes
Include all existing error codes plus:

| Code | Meaning |
|------|---------|
| INVALID_INPUT_FORMAT | Malformed dependency array or dependency object |
| MISSING_PARAMETER    | Required parameter missing |
| EMPTY_DEPENDENCIES   | Empty dependencies array provided |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Relevant Files
- src/maven_mcp_server/server.py
- src/maven_mcp_server/shared/utils.py
- src/maven_mcp_server/shared/data_types.py
- src/maven_mcp_server/tools/batch_versions.py
- src/maven_mcp_server/tools/all_latest_versions.py
- src/maven_mcp_server/tests/tools/test_batch_versions.py

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_batch_versions.py`
- Manual testing with actual Maven dependencies to verify real-world behavior
- Benchmark tests to verify performance with various batch sizes