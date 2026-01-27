#!/usr/bin/env python3
"""
Test script for serena_analysis.py

This script demonstrates the functionality of the Serena LSP Error Analysis Tool
with various test cases and examples.
"""

import os
import tempfile
import subprocess
import sys
from pathlib import Path


def create_test_python_project():
    """Create a temporary Python project with intentional errors for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_python_project_")
    
    # Create main.py with errors
    main_py_content = '''#!/usr/bin/env python3
"""Test Python file with intentional errors."""

import os
import sys
import unused_module  # This will be flagged as unused

def main():
    # Undefined variable error
    print(undefined_variable)
    
    # Missing return statement
    def helper_function():
        x = 5
        # Missing return
    
    # Unused variable
    unused_var = "this is not used"
    
    # Type error (if using type checker)
    result = "string" + 5
    
    return result

if __name__ == "__main__":
    main()
'''
    
    # Create utils.py with more errors
    utils_py_content = '''"""Utility functions with errors."""

def calculate_something(a, b):
    # Division by zero potential
    return a / b

def unused_function():
    """This function is never called."""
    pass

# Syntax error in comment - missing closing quote
def broken_function():
    return "missing quote
'''
    
    # Create requirements.txt
    requirements_content = '''requests==2.28.0
numpy==1.21.0
pandas==1.3.0
'''
    
    # Write files
    with open(os.path.join(temp_dir, "main.py"), "w") as f:
        f.write(main_py_content)
    
    with open(os.path.join(temp_dir, "utils.py"), "w") as f:
        f.write(utils_py_content)
    
    with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
        f.write(requirements_content)
    
    return temp_dir


def create_test_javascript_project():
    """Create a temporary JavaScript project with intentional errors for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_js_project_")
    
    # Create main.js with errors
    main_js_content = '''// Test JavaScript file with intentional errors

const fs = require('fs');
const path = require('path');
const unusedModule = require('unused-module'); // Unused import

function main() {
    // Undefined variable
    console.log(undefinedVariable);
    
    // Missing semicolon
    let x = 5
    let y = 10;
    
    // Unreachable code
    return x + y;
    console.log("This will never execute");
}

// Function with no return statement when expected
function calculateSomething(a, b) {
    let result = a + b;
    // Missing return statement
}

// Unused variable
const unusedVar = "this is not used";

main();
'''
    
    # Create package.json
    package_json_content = '''{
  "name": "test-project",
  "version": "1.0.0",
  "description": "Test project for serena analysis",
  "main": "main.js",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "eslint": "^8.0.0"
  }
}
'''
    
    # Write files
    with open(os.path.join(temp_dir, "main.js"), "w") as f:
        f.write(main_js_content)
    
    with open(os.path.join(temp_dir, "package.json"), "w") as f:
        f.write(package_json_content)
    
    return temp_dir


def run_analysis_test(project_path, test_name, expected_errors=None):
    """Run the analysis tool on a test project and display results."""
    print(f"\n{'='*60}")
    print(f"Running test: {test_name}")
    print(f"Project path: {project_path}")
    print(f"{'='*60}")
    
    try:
        # Run the analysis tool
        cmd = [sys.executable, "serena_analysis.py", project_path, "--verbose"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        # Basic validation
        if "ERRORS:" in result.stdout:
            print("✅ Analysis completed successfully")
        else:
            print("❌ Analysis may have failed - no error count found")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


def test_command_line_options():
    """Test various command line options."""
    print(f"\n{'='*60}")
    print("Testing command line options")
    print(f"{'='*60}")
    
    # Test help option
    try:
        result = subprocess.run([sys.executable, "serena_analysis.py", "--help"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and "usage:" in result.stdout.lower():
            print("✅ Help option works correctly")
        else:
            print("❌ Help option failed")
    except Exception as e:
        print(f"❌ Help test failed: {e}")
    
    # Test invalid arguments
    try:
        result = subprocess.run([sys.executable, "serena_analysis.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("✅ Correctly rejects missing repository argument")
        else:
            print("❌ Should reject missing repository argument")
    except Exception as e:
        print(f"❌ Invalid argument test failed: {e}")


def main():
    """Main test function."""
    print("Serena LSP Error Analysis Tool - Test Suite")
    print("=" * 60)
    
    # Check if the analysis tool exists
    if not os.path.exists("serena_analysis.py"):
        print("❌ serena_analysis.py not found in current directory")
        sys.exit(1)
    
    # Test command line options
    test_command_line_options()
    
    # Create and test Python project
    python_project = None
    js_project = None
    
    try:
        print("\n📁 Creating test Python project...")
        python_project = create_test_python_project()
        success = run_analysis_test(python_project, "Python Project Analysis")
        
        if success:
            print("✅ Python project test completed")
        else:
            print("❌ Python project test failed")
        
        print("\n📁 Creating test JavaScript project...")
        js_project = create_test_javascript_project()
        success = run_analysis_test(js_project, "JavaScript Project Analysis")
        
        if success:
            print("✅ JavaScript project test completed")
        else:
            print("❌ JavaScript project test failed")
        
        # Test with severity filter
        if python_project:
            print("\n🔍 Testing severity filtering...")
            cmd = [sys.executable, "serena_analysis.py", python_project, "--severity", "ERROR"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print("Severity filter test output:")
            print(result.stdout)
        
        # Test current directory (if it's a valid project)
        if os.path.exists("pyproject.toml") or os.path.exists("setup.py") or os.path.exists("requirements.txt"):
            print("\n📂 Testing current directory analysis...")
            cmd = [sys.executable, "serena_analysis.py", ".", "--timeout", "60"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            print("Current directory test output:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
    finally:
        # Cleanup
        if python_project and os.path.exists(python_project):
            import shutil
            shutil.rmtree(python_project, ignore_errors=True)
            print(f"🧹 Cleaned up Python test project: {python_project}")
        
        if js_project and os.path.exists(js_project):
            import shutil
            shutil.rmtree(js_project, ignore_errors=True)
            print(f"🧹 Cleaned up JavaScript test project: {js_project}")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

