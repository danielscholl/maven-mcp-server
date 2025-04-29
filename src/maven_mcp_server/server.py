"""
MCP Server implementation for Maven Check using the standard mcp.server package.
This module defines the serve function that starts the MCP server.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from maven_mcp_server.tools.version_exist import get_maven_latest_version
from maven_mcp_server.tools.check_version import check_maven_version_exists
from maven_mcp_server.shared.data_types import ErrorCode, MavenError, create_error_response


async def serve_async() -> None:
    """
    Start the Maven Check MCP server.
    This function registers the MCP tools and starts the server.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("maven-check")
    
    # Create the MCP server
    server = Server("maven-check")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Register all available tools with the MCP server."""
        return [
            Tool(
                name="get_maven_latest_version",
                description="Get the latest version of a Maven dependency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dependency": {
                            "type": "string",
                            "description": "The dependency in the format 'groupId:artifactId'."
                        },
                        "packaging": {
                            "type": "string",
                            "description": "The packaging type, defaults to 'jar'.",
                            "default": "jar"
                        },
                        "classifier": {
                            "type": ["string", "null"],
                            "description": "The classifier, if any.",
                            "default": None
                        }
                    },
                    "required": ["dependency"]
                }
            ),
            Tool(
                name="check_maven_version_exists",
                description="Check if a specific version of a Maven dependency exists",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dependency": {
                            "type": "string",
                            "description": "The dependency in the format 'groupId:artifactId'."
                        },
                        "version": {
                            "type": "string",
                            "description": "The version to check."
                        },
                        "packaging": {
                            "type": "string",
                            "description": "The packaging type, defaults to 'jar'.",
                            "default": "jar"
                        },
                        "classifier": {
                            "type": ["string", "null"],
                            "description": "The classifier, if any.",
                            "default": None
                        }
                    },
                    "required": ["dependency", "version"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls from the MCP client."""
        logger.info(f"Tool call: {name}, arguments: {arguments}")
        
        try:
            if name == "get_maven_latest_version":
                result = get_maven_latest_version(**arguments)
                if result.get("status") == "success":
                    latest_version = result.get("result", {}).get("latest_version")
                    logger.info(f"Returning latest version: {latest_version}")
                    
                    # Format as expected by MCP server - return TextContent
                    return [TextContent(
                        type="text",
                        text=latest_version
                    )]
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Error in get_maven_latest_version: {error_msg}")
                    
                    # Return error as TextContent instead of raising exception
                    return [TextContent(
                        type="text",
                        text=f"Error: {error_msg}"
                    )]
                
            elif name == "check_maven_version_exists":
                result = check_maven_version_exists(**arguments)
                if result.get("status") == "success":
                    exists = result.get("result", {}).get("exists")
                    logger.info(f"Version exists: {exists}")
                    
                    # Format as expected by MCP server - return TextContent
                    return [TextContent(
                        type="text",
                        text="true" if exists else "false"
                    )]
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Error in check_maven_version_exists: {error_msg}")
                    
                    # Return error as TextContent instead of raising exception
                    return [TextContent(
                        type="text",
                        text=f"Error: {error_msg}"
                    )]
            else:
                logger.error(f"Unknown tool: {name}")
                # Return error as TextContent instead of raising exception
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]
                
        except Exception as e:
            logger.error(f"Error handling tool call: {name}, error: {e}")
            # Return exception as TextContent instead of re-raising
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    # Initialize and run the server
    try:
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise


def serve() -> None:
    """
    Synchronous wrapper for the async serve function.
    This is used as the entry point for the maven-check command.
    """
    asyncio.run(serve_async())