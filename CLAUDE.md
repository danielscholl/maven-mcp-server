# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Start server: `uv run maven-check` (with debug: `uv run maven-check --debug`)
- Run all tests: `uv run pytest`
- Run single test: `uv run pytest src/maven_mcp_server/tests/path/to/test_file.py::test_function_name`
- Dependencies: `uv pip install -e .` or `uv pip install -e ".[dev]"` (with dev dependencies)

## Code Style Guidelines
- Python 3.12+ with type hints throughout
- Follow PEP 8 conventions for formatting
- Snake_case for variables, functions, and modules
- Use docstrings for all functions, classes, and modules
- Import order: standard library, third-party, local modules
- Comprehensive error handling with specific error codes from ErrorCode enum
- Clean separation of concerns between modules (tools, shared, utils)
- Logging for all important operations (use the logger from the module)
- Tests should cover both success and error paths
- Descriptive variable names that indicate purpose and type