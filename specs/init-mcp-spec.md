# Specification for Hello World MCP Server

> A minimal MCP server implementation to serve as a learning example and sanity check.

## Implementation Details

### Development Environment
- Python ≥ 3.12 with uv as the package manager
- Document all functions and classes with clear docstrings
- Focus on simplicity and clarity for demonstration purposes

### MCP Server Framework
- Use the standard `mcp-server` package for MCP protocol compatibility
- The server will handle stdin/stdout communication with the client
- Responses must follow the MCP protocol with a proper `content` array format

### Testing Requirements
- Run tests with `uv run pytest`
- Tests should verify both success and error paths
- Keep tests simple but comprehensive

## Tools to Expose

```text
hello_world(name: str = "World") -> str
```

### Input Rules
- `name` is optional, defaults to "World"
- If provided, `name` should be a non-empty string

### Response Format
- The tool returns a dictionary with status, result/error information:
  ```python
  # Success response
  {
    "tool_name": "hello_world",
    "status": "success",
    "result": {
        "message": str  # "Hello, {name}!"
    }
  }
  
  # Error response
  {
    "tool_name": "hello_world",
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
| INVALID_INPUT_FORMAT | Empty or invalid name parameter |
| INTERNAL_SERVER_ERROR| Unhandled exception inside the server |

## Codebase Structure

- src/
    - hello_mcp_server/
        - __init__.py
        - main.py
        - server.py
            - serve_async() -> none
            - list_tools() -> List[Tool]
            - call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]
        - tools/
            - __init__.py
            - hello.py
              - def hello_world
        - shared/
            - __init__.py
            - utils.py
            - data_types.py
        - tests/
            - __init__.py
            - tools/
                - __init__.py
                - test_hello.py
            - shared/
                - __init__.py
                - test_utils.py

## Validation and Testing

1. **Unit Tests**: Run `uv run pytest <path_to_test>` for individual test files
2. **Full Test Suite**: Run `uv run pytest` to validate all tests are passing
3. **MCP Server Test**: Test the server with:
   - `uv run hello-world` - should start the server and wait for MCP input
   - `uv run hello-world --debug` - starts the server with debug logging
   - Test with the Claude CLI: `claude --mcp-debug` to verify connection
4. **Integration Test**: Use the .mcp.json configuration to connect the server to Claude

### Required .mcp.json Configuration

```json
{
  "mcpServers": {
    "hello-world": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "hello-world"
      ],
      "env": {}
    }
  }
}
```