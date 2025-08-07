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
    
    # Set a default project directory if not specified
    if not os.environ.get("SERENA_PROJECT_DIR"):
        # Use /tmp as default project directory for MCPHub
        default_project = "/tmp/serena-workspace"
        os.makedirs(default_project, exist_ok=True)
        os.environ["SERENA_PROJECT_DIR"] = default_project
        
        # Create a sample file to show the workspace is working
        sample_file = Path(default_project) / "README.md"
        if not sample_file.exists():
            sample_file.write_text("""# Serena Workspace

This is your Serena workspace directory. You can:

1. Use `list_dir` with "." to see files in this directory
2. Create files with `create_text_file`
3. Read files with `read_file`
4. Navigate and edit your project files

To work with a different directory, use the full path or relative paths from here.

## Getting Started

Try these commands:
- `list_dir` with path "." to see this directory
- `create_text_file` to create a new file
- `read_file` with path "README.md" to read this file
""")
    
    try:
        # Import the main function from serena_mcp
        from serena_mcp import main
        main()
    except Exception as e:
        print(f"Error starting Serena MCP server: {e}", file=sys.stderr)
        sys.exit(1)
