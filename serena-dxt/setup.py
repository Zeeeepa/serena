#!/usr/bin/env python3
"""
Setup script for Serena DXT Extension
This script helps install the required dependencies for the Serena MCP server.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python dependencies."""
    current_dir = Path(__file__).parent
    requirements_file = current_dir / "requirements.txt"
    lib_dir = current_dir / "server" / "lib"
    
    if not requirements_file.exists():
        print("Error: requirements.txt not found!")
        return False
    
    # Create lib directory if it doesn't exist
    lib_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("Installing Serena dependencies...")
        print(f"Target directory: {lib_dir}")
        
        # Install dependencies with more specific options
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_file),
            "--target", str(lib_dir),
            "--upgrade",
            "--no-deps",  # Install without dependencies first
            "--force-reinstall"
        ])
        
        # Then install with dependencies to ensure everything is included
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_file),
            "--target", str(lib_dir),
            "--upgrade"
        ])
        
        print("Dependencies installed successfully!")
        
        # Verify critical dependencies
        critical_deps = ["mcp", "fastmcp", "docstring_parser", "pydantic", "pyyaml"]
        missing_deps = []
        
        for dep in critical_deps:
            dep_path = lib_dir / dep
            if not dep_path.exists():
                # Check for alternative naming patterns
                alt_patterns = [f"{dep.replace('-', '_')}", f"{dep.replace('_', '-')}"]
                found = False
                for pattern in alt_patterns:
                    if (lib_dir / pattern).exists():
                        found = True
                        break
                if not found:
                    missing_deps.append(dep)
        
        if missing_deps:
            print(f"Warning: Some critical dependencies may be missing: {missing_deps}")
            print("The extension may not work correctly.")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("You may need to install dependencies manually:")
        print(f"pip install -r {requirements_file} --target {lib_dir}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major != 3 or version.minor < 11 or version.minor >= 12:
        print(f"Warning: Serena requires Python 3.11.x, but you have {version.major}.{version.minor}.{version.micro}")
        print("The extension may not work correctly.")
        return False
    return True

def main():
    print("Serena DXT Extension Setup")
    print("=" * 30)
    
    if not check_python_version():
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if install_dependencies():
        print("\nSetup completed successfully!")
        print("You can now use the Serena DXT extension.")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
