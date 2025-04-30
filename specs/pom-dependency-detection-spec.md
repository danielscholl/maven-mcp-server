# Feature Specification: POM Dependency Auto-Detection

> Enhance the Maven Check MCP server to automatically detect and properly handle POM dependencies based on artifact naming patterns.

## Implementation Details
- Automatically identify artifacts that are likely to be POM dependencies based on naming conventions
- Implement direct repository access as a fallback when the Maven Central search API fails
- Add special handling for commonly used libraries with unique patterns

### Auto-Detection Features
- **Naming Pattern Detection**:
  - Automatically detect artifact IDs ending with "-dependencies" or "-bom" and use "pom" packaging
  - This removes the need for users to manually specify packaging="pom" for these artifacts
  - Apply this detection consistently across all tools (get_latest, check_exists, find_by_component)

- **Direct Repository Access**:
  - Add direct Maven repository access capability (`check_direct_repository_access()`)
  - Use direct access as a fallback when search API returns no results
  - Access Maven metadata XML directly to extract version information when available

- **Special Case Handling**:
  - Add specialized handling for Spring Boot dependencies artifacts
  - Implement fallback patterns for commonly used libraries that don't follow standard indexing patterns
  - Support library-specific quirks in version resolution

### Testing Requirements
- Run tests with `uv run pytest`
- No mocking of Maven API calls — tests must hit the real Maven Central API
- Add test coverage for:
  - Automatic POM detection for "-bom" and "-dependencies" artifacts
  - Direct repository access fallback mechanism
  - Special case handling for Spring Boot and similar libraries
  - Integration tests for end-to-end verification

## Tools Affected
All three existing tools are affected by these enhancements:
1. `get_maven_latest_version`
2. `check_maven_version_exists` 
3. `find_maven_latest_component_version`

No API signature changes are needed, as these enhancements are internal implementation details that improve user experience.

## Relevant Files
- src/maven_mcp_server/shared/utils.py (add check_direct_repository_access)
- src/maven_mcp_server/tools/version_exist.py
- src/maven_mcp_server/tools/check_version.py
- src/maven_mcp_server/tools/latest_by_semver.py
- src/maven_mcp_server/tests/tools/test_pom_dependencies.py (new)
- src/maven_mcp_server/tests/tools/test_direct_access.py (new)
- src/maven_mcp_server/tests/tools/test_pom_integration.py (new)

## Validation (Close the Loop)
> Be sure to test this capability with uv run pytest.

- `uv run pytest src/maven_mcp_server/tests/tools/test_pom_dependencies.py`
- `uv run pytest src/maven_mcp_server/tests/tools/test_direct_access.py`
- `uv run pytest src/maven_mcp_server/tests/tools/test_pom_integration.py`
- Manual testing with common Maven dependencies to verify real-world behavior