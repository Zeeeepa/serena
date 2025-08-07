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
    
    if not requirements_file.exists():
        print("Error: requirements.txt not found!")
        return False
    
    try:
        print("Installing Serena dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_file),
            "--target", str(current_dir / "server" / "lib"),
            "--upgrade"
        ])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
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

