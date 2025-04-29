"""
Main entry point for the Maven Check MCP server.
This module defines the main function that is called when the server is run.
"""

import argparse
import sys
import logging

from maven_mcp_server.server import serve


def main() -> None:
    """
    Parse command line arguments and start the Maven Check MCP server.
    This function is the entry point for the maven-check command.
    """
    parser = argparse.ArgumentParser(
        description="Maven Check MCP Server - A lightweight MCP server that lets Large Language Models query Maven Central for artifact versions"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Start the server
        serve()
    except KeyboardInterrupt:
        print("\nServer shutdown requested.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()