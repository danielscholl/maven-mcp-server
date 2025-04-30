# Maven Check MCP Server

A lightweight MCP server that lets Large Language Models query Maven Central for artifact versions. This server allows Claude and other LLMs to find the latest version of a Maven dependency and check if a specific version exists.

## Features

- Find the latest version of any Maven dependency (library)
- Check if a specific version of a dependency exists
- Support for packaging types (jar, war, pom, etc.)
- Automatic detection of POM dependencies (artifacts with -bom or -dependencies suffix)
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

This MCP server provides four tools:

### 1. get_maven_latest_version

Gets the latest version of a Maven dependency.

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `packaging` (optional): The packaging type, defaults to 'jar' (automatically uses 'pom' for dependencies with -bom or -dependencies suffix)
- `classifier` (optional): The classifier, if any

**Examples:**
```json
{
  "dependency": "org.apache.commons:commons-lang3"
}
```

```json
{
  "dependency": "org.springframework.boot:spring-boot-dependencies"
}
```

**Returns:** The latest version as a string (e.g., "3.14.0")

### 2. check_maven_version_exists

Checks if a specific version of a Maven dependency exists.

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `version` (required): The version to check
- `packaging` (optional): The packaging type, defaults to 'jar' (automatically uses 'pom' for dependencies with -bom or -dependencies suffix)
- `classifier` (optional): The classifier, if any

**Examples:**
```json
{
  "dependency": "org.apache.commons:commons-lang3",
  "version": "3.14.0"
}
```

```json
{
  "dependency": "org.springframework.boot:spring-boot-dependencies",
  "version": "3.2.0"
}
```

**Returns:** A boolean indicating whether the version exists ("true" or "false")

### 3. find_maven_latest_component_version

Gets the latest version of a Maven dependency based on semantic versioning component (major, minor, or patch).

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `version` (required): The version in semantic version format (MAJOR.MINOR.PATCH)
- `target_component` (required): The component to find the latest version for, one of: "major", "minor", "patch"
- `packaging` (optional): The packaging type, defaults to 'jar' (automatically uses 'pom' for dependencies with -bom or -dependencies suffix)
- `classifier` (optional): The classifier, if any

**Examples:**
```json
{
  "dependency": "org.apache.commons:commons-lang3",
  "version": "3.12.0",
  "target_component": "minor"
}
```

```json
{
  "dependency": "org.springframework.boot:spring-boot-dependencies",
  "version": "3.1.0",
  "target_component": "minor"
}
```

**Returns:** The latest version as a string (e.g., "3.14.0")

#### Behavior by Target Component

- **major**: Returns the highest available major version (across all versions)
- **minor**: Returns the highest minor version within the given major version
- **patch**: Returns the highest patch version within the given major.minor version

### 4. get_maven_all_latest_versions

Gets the latest versions for all semantic versioning components (major, minor, patch) in a single call.

**Parameters:**
- `dependency` (required): The dependency in the format 'groupId:artifactId'
- `version` (required): The version in semantic version format (MAJOR.MINOR.PATCH)
- `packaging` (optional): The packaging type, defaults to 'jar' (automatically uses 'pom' for dependencies with -bom or -dependencies suffix)
- `classifier` (optional): The classifier, if any

**Examples:**
```json
{
  "dependency": "org.apache.commons:commons-lang3",
  "version": "3.12.0"
}
```

```json
{
  "dependency": "org.springframework.boot:spring-boot-dependencies",
  "version": "3.1.0"
}
```

**Returns:** A JSON object containing the latest versions for each component:
```json
{
  "latest_major_version": "3.14.0",
  "latest_minor_version": "3.12.0",
  "latest_patch_version": "3.12.0"
}
```

## How It Works

The server works by:

1. Querying the Maven Central Repository Search API
2. Parsing and validating dependency formats
3. Automatically detecting POM dependencies:
   - Identifies artifacts with "-bom" or "-dependencies" suffix
   - Uses "pom" packaging type for these artifacts
4. For latest version queries:
   - Fetches all versions of the artifact
   - Sorts them using proper semantic versioning rules
   - Returns the most recent version
5. For version existence checks:
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

3. **Get latest patch version**:
   ```
   I'm using version 2.0.2 of org.springdoc:springdoc-openapi-starter-webmvc-ui what is the latest patch?
   ```
   
4. **Working with BOM and POM dependencies**:
   ```
   What is the latest version of org.springframework.boot:spring-boot-dependencies?
   ```
   The server automatically detects dependencies with "-dependencies" or "-bom" suffix and uses POM packaging type.

5. **Get all latest versions in one call**:
   ```
   I'm using version 3.1.0 of org.springframework.boot:spring-boot-dependencies, what versions could I upgrade to?
   ```
   This returns the latest major, minor, and patch versions in a single call, making it efficient for understanding upgrade options.