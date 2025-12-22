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

def find_project_root():
    """
    Find the project root directory by looking for common project indicators.
    Falls back to current working directory if no indicators found.
    """
    current = Path.cwd()
    
    # Common project root indicators
    project_indicators = [
        '.git',           # Git repository
        '.gitignore',     # Git ignore file
        'package.json',   # Node.js project
        'requirements.txt', # Python project
        'pyproject.toml', # Modern Python project
        'Cargo.toml',     # Rust project
        'pom.xml',        # Maven project
        'build.gradle',   # Gradle project
        'Makefile',       # Make-based project
        'README.md',      # Project documentation
        'README.rst',     # Python project documentation
        'setup.py',       # Python setup
        'composer.json',  # PHP project
        'go.mod',         # Go project
    ]
    
    # Start from current directory and walk up
    for path in [current] + list(current.parents):
        # Check if any project indicators exist in this directory
        for indicator in project_indicators:
            if (path / indicator).exists():
                return path
    
    # If no indicators found, use current working directory
    return current

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
        # Find the project root (look for common project indicators)
        project_root = find_project_root()
        
        # Create Workspace folder in project root
        workspace_dir = project_root / "Workspace"
        workspace_dir.mkdir(exist_ok=True)
        
        os.environ["SERENA_PROJECT_DIR"] = str(workspace_dir)
        
        # Create a sample file to show the workspace is working
        readme_file = workspace_dir / "README.md"
        if not readme_file.exists():
            readme_file.write_text("""# Serena Workspace

This is your project's Workspace directory. You can:

1. Use `list_dir` with "." to see files in this workspace
2. Use `list_dir` with ".." to see the project root
3. Create files with `create_text_file`
4. Read files with `read_file`
5. Navigate between workspace and project files

## Directory Structure

```
Project Root/
├── Workspace/          ← You are here (Serena's working directory)
│   ├── README.md       ← This file
│   └── (your files)    ← Files you create will appear here
├── src/                ← Your project source code
├── docs/               ← Project documentation
└── ...                 ← Other project files
```

## Getting Started

Try these commands:
- `list_dir` with path "." to see this workspace
- `list_dir` with path ".." to see the project root
- `create_text_file` to create a new file here
- `read_file` with path "README.md" to read this file
- `find_file` to search for files in the project

## Working with Project Files

- Use relative paths like "../src/main.py" to access project files
- Use absolute paths for system files
- The workspace keeps your Serena work organized and separate
""")
    
    try:
        # Import the main function from serena_mcp
        from serena_mcp import main
        main()
    except Exception as e:
        print(f"Error starting Serena MCP server: {e}", file=sys.stderr)
        sys.exit(1)
