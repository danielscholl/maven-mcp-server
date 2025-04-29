# Maven Check MCP Server

A lightweight MCP server that lets Large Language Models query Maven Central for artifact versions. This server allows Claude and other LLMs to find the latest version of a Maven dependency and check if a specific version exists.

## Features

- Find the latest version of any Maven dependency (library)
- Check if a specific version of a dependency exists
- Support for packaging types (jar, war, pom, etc.)
- Support for classifiers
- Proper semantic versioning comparisons
- Connection via Model Context Protocol (MCP)

## Installation

```bash
# Clone the repository
git clone https://github.com/danielscholl/maven-mcp-server.git
cd maven-mcp-server

# Install dependencies and the package
uv sync && uv pip install -e .
```

## MCP Server Configuration

To use this MCP server with your projects, add the following to your `.mcp.json`:

```json
{
  "mcpServers": {
    "maven-check": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "maven-check"],
      "env": {}
    }
  }
}
```

[![Install with UVX in VS Code](https://img.shields.io/badge/VS_Code-UVX-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode:mcp/install?%7B%22name%22%3A%22maven-check%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22git%2Bhttps%3A%2F%2Fgithub.com%2Fdanielscholl%2Fmaven-mcp-server%40main%22%2C%22maven-check%22%5D%2C%22env%22%3A%7B%7D%7D)

## Usage

Start the server:

```bash
uv run maven-check
```

For debug logging:

```bash
uv run maven-check --debug
```

## Tools

This MCP server provides two tools:

### 1. get_maven_latest_version

Gets the latest version of a Maven dependency.

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `packaging` (optional): The packaging type, defaults to 'jar'
- `classifier` (optional): The classifier, if any

**Example:**
```json
{
  "dependency": "org.apache.commons:commons-lang3"
}
```

**Returns:** The latest version as a string (e.g., "3.14.0")

### 2. check_maven_version_exists

Checks if a specific version of a Maven dependency exists.

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `version` (required): The version to check
- `packaging` (optional): The packaging type, defaults to 'jar'
- `classifier` (optional): The classifier, if any

**Example:**
```json
{
  "dependency": "org.apache.commons:commons-lang3",
  "version": "3.14.0"
}
```

**Returns:** A boolean indicating whether the version exists ("true" or "false")

## How It Works

The server works by:

1. Querying the Maven Central Repository Search API
2. Parsing and validating dependency formats
3. For latest version queries:
   - Fetches all versions of the artifact
   - Sorts them using proper semantic versioning rules
   - Returns the most recent version
4. For version existence checks:
   - Directly queries Maven Central for the specific version
   - Returns whether it exists

## Development

### Testing

Run all tests:
```bash
uv run pytest
```

Run specific test:
```bash
uv run pytest src/maven_mcp_server/tests/tools/test_version_exist.py
```

## Using with Claude

Once the server is set up and Claude Code is connected, you can use the tools like this:

1. **Get the latest version of a Maven dependency**:
   ```
   What is the latest version of org.springframework:spring-framework-bom 
   ```

2. **Check if a specific version exists**:
   ```
   Does version 3.14.0 of org.apache.commons:commons-lang3 exist?
   ```