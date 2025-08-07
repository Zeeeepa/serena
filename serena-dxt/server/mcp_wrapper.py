#!/usr/bin/env python3
"""
MCP Wrapper for Serena - Ensures proper MCP stdio mode
This wrapper ensures Serena runs in MCP mode without showing help
"""

import sys
import os
from pathlib import Path

# Add the bundled serena package to Python path
current_dir = Path(__file__).parent
serena_lib_path = current_dir / "lib"
if serena_lib_path.exists():
    sys.path.insert(0, str(serena_lib_path))

# Import and run the main server with forced MCP mode
if __name__ == "__main__":
    # Force MCP stdio mode by clearing argv and setting defaults
    original_argv = sys.argv.copy()
    sys.argv = [sys.argv[0]]  # Keep only script name
    
    # Set environment variables for configuration
    os.environ.setdefault("SERENA_LOG_LEVEL", "ERROR")
    os.environ.setdefault("SERENA_CONTEXT", "desktop-app")
    
    try:
        # Import the main function from serena_mcp
        from serena_mcp import main
        main()
    except Exception as e:
        print(f"Error starting Serena MCP server: {e}", file=sys.stderr)
        sys.exit(1)

