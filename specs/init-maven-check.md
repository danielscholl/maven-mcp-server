# Specification for Maven Check

> A lightweight MCP server that lets Large Language Models query Maven Central for artifact versions.

## Implementation details

### Development Environment
- Python ≥ 3.12 with uv as the package manager
- Document all functions and classes with clear docstrings
- First, READ ai_docs/* to understand provider requirements and examples

### MCP Server Framework
- Use the standard `mcp-server` package for MCP protocol compatibility
- The server will handle stdin/stdout communication with the client
- Responses must follow the MCP protocol with a proper `content` array format

### Testing Requirements
- Run tests with `uv run pytest`
- Don't mock API calls - use actual Maven Central API in tests
- Tests should be case-insensitive for input matching
- Test both success and error paths

### API Integration
- Query the public Maven Central Search API (`https://search.maven.org/solrsearch/select`)
- Use the "core=gav" parameter for better version search
- Request multiple rows (at least 20) to get all versions for proper comparison
- Implement proper semantic versioning comparison for latest version detection
- Error handling is mandatory - every failure should return a well-formed MCP error object with a code and human-readable message
- Special handling for BOM artifacts
- Automatic detection of POM dependencies (artifacts with -bom or -dependencies suffix)
- Provide direct repository access fallback for dependencies not properly indexed by Maven search API
- Special handling for specific library patterns like Spring Boot dependencies

## Tools to Expose

> Here's the tools we want to expose:

```text
get_maven_latest_version(dependency: str, packaging: str = "jar", classifier: str | None = None) -> str
check_maven_version_exists(dependency: str, version: str, packaging: str = "jar", classifier: str | None = None) -> bool
```

### Input Rules
- `dependency` **MUST** match `groupId:artifactId` (no embedded version)
- `version` is required only for **check_maven_version_exists**

### Response Format
- Each tool returns a dictionary with status, result/error information:
  ```python
  # Success response
  {
    "tool_name": str,  # The name of the tool that was called
    "status": "success",
    "result": {
        # Tool-specific result data
        # For check_maven_version_exists: {"exists": bool}
        # For get_maven_latest_version: {"latest_version": str}
    }
  }
  
  # Error response
  {
    "tool_name": str,  # The name of the tool that was called
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
| VERSION_NOT_FOUND    | Version not found though dependency exists |
| MAVEN_API_ERROR      | Upstream Maven Central error (non‑200, network failure) |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Codebase Structure

- src/
    - maven_mcp_server/
        - __init__.py
        - main.py
        - server.py
            - serve_async() -> none
            - list_tools() -> List[Tool]
            - call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]
        - tools/
            - __init__.py
            - version_exist.py
              - def check_maven_version_exists
            - check_version.py
              - def get_maven_latest_version
        - shared/
            - __init__.py
            - utils.py
            - data_types.py
        - tests/
            - __init__.py
            - tools/
                - __init__.py
                - test_version_exist.py
                - test_check_version.py
            - shared/
                - __init__.py
                - test_utils.py

## Validation and Testing

1. **Unit Tests**: Run `uv run pytest <path_to_test>` for individual test files
2. **Full Test Suite**: Run `uv run pytest` to validate all tests are passing
3. **MCP Server Test**: Test the server with:
   - `uv run maven-check` - should start the server and wait for MCP input
   - `uv run maven-check --debug` - starts the server with debug logging
   - Test with the Claude CLI: `claude --mcp-debug` to verify connection
4. **Integration Test**: Use the .mcp.json configuration to connect the server to Claude

### Required .mcp.json Configuration

```json
{
  "mcpServers": {
    "maven-check": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "maven-check"
      ],
      "env": {}
    }
  }
}
```