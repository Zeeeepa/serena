#!/usr/bin/env python3
"""
Serena MCP Server Entry Point for DXT Extension
"""

import sys
import os
import argparse
from pathlib import Path

# Add the bundled serena package to Python path
current_dir = Path(__file__).parent
serena_lib_path = current_dir / "lib"
if serena_lib_path.exists():
    sys.path.insert(0, str(serena_lib_path))

try:
    from serena.mcp import SerenaMCPFactorySingleProcess
    from serena.util.logging import MemoryLogHandler
    from serena.constants import DEFAULT_CONTEXT, DEFAULT_MODES
    import logging as std_logging
    
    # Import core Serena components to verify they're available
    from serena.agent import SerenaAgent
    from serena.project import Project
    from serena.tools.tools_base import ToolRegistry
    
except ImportError as e:
    print(f"Error importing Serena modules: {e}", file=sys.stderr)
    print("Make sure Serena is properly installed or bundled with this extension.", file=sys.stderr)
    print("Try running the setup.py script to install dependencies.", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Serena MCP Server")
    parser.add_argument("--project", type=str, help="Project directory path")
    parser.add_argument("--context", type=str, default=DEFAULT_CONTEXT, help="Context configuration")
    parser.add_argument("--modes", type=str, nargs="*", default=DEFAULT_MODES, help="Agent modes")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level")
    parser.add_argument("--tool-timeout", type=float, help="Tool execution timeout")
    parser.add_argument("--enable-web-dashboard", action="store_true", help="Enable web dashboard")
    parser.add_argument("--enable-gui-log-window", action="store_true", help="Enable GUI log window")
    parser.add_argument("--trace-lsp-communication", action="store_true", help="Trace LSP communication")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = getattr(std_logging, args.log_level.upper())
    std_logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )
    
    logger = std_logging.getLogger(__name__)
    logger.info("Starting Serena MCP Server")
    
    try:
        # Initialize memory log handler
        memory_log_handler = MemoryLogHandler()
        
        # Create MCP factory
        factory = SerenaMCPFactorySingleProcess(
            context=args.context,
            project=args.project,
            memory_log_handler=memory_log_handler
        )
        
        # Create MCP server
        server = factory.create_mcp_server(
            modes=args.modes,
            enable_web_dashboard=args.enable_web_dashboard,
            enable_gui_log_window=args.enable_gui_log_window,
            log_level=args.log_level,
            trace_lsp_communication=args.trace_lsp_communication,
            tool_timeout=args.tool_timeout,
        )
        
        logger.info("MCP server created successfully")
        
        # Run the server with stdio transport (required for DXT)
        server.run(transport="stdio")
        
    except Exception as e:
        logger.error(f"Failed to start Serena MCP Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
