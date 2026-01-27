#!/usr/bin/env python3
"""
Test script for Serena LSP Error Analyzer

This script creates a test project with intentional errors and validates
that the analyzer can detect and report them correctly.
"""

import os
import tempfile
import shutil
from pathlib import Path

def create_test_project():
    """Create a test project with intentional errors"""
    test_dir = tempfile.mkdtemp(prefix="serena_test_")
    
    # Create Python file with errors
    python_file = Path(test_dir) / "test_errors.py"
    python_file.write_text('''
# Test Python file with intentional errors
import os
import sys

def function_with_issues():
    # Undefined variable (Critical error)
    result = undefined_variable + 5
    
    # Unused variable (Major warning)
    unused_var = "this is not used"
    
    # Type error (Critical error)
    number = "string" + 42
    
    return result

class TestClass:
    def __init__(self):
        self.value = None
    
    def method_with_issues(self):
        # Potential None access (Major warning)
        return self.value.upper()

# Missing main guard (Minor info)
function_with_issues()
''')
    
    # Create TypeScript file with errors
    ts_file = Path(test_dir) / "test_errors.ts"
    ts_file.write_text('''
// Test TypeScript file with intentional errors

function testFunction(): string {
    // Undefined variable (Critical error)
    console.log(undefinedVar);
    
    // Unreachable code (Major warning)
    return "hello";
    console.log("This will never execute");
}

// Unused function (Minor info)
function unusedFunction(): void {
    return;
}

// Missing return type (Major warning)
function noReturnType() {
    return 42;
}

testFunction();
''')
    
    # Create project configuration
    serena_dir = Path(test_dir) / ".serena"
    serena_dir.mkdir()
    
    project_yml = serena_dir / "project.yml"
    project_yml.write_text('''
project_name: test_project
language: python
ignored_paths: []
excluded_tools: []
included_optional_tools: []
read_only: false
ignore_all_files_in_gitignore: true
initial_prompt: ""
encoding: utf-8
''')
    
    return test_dir

def main():
    """Test the Serena analyzer"""
    print("🧪 Testing Serena LSP Error Analyzer")
    print("=" * 50)
    
    # Create test project
    test_dir = create_test_project()
    print(f"📁 Created test project: {test_dir}")
    
    try:
        # Import and run the analyzer
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        
        from serena_analyzer import SerenaAnalyzer
        
        # Create analyzer instance
        analyzer = SerenaAnalyzer(verbose=True)
        
        # Run analysis
        print("\n🔍 Running analysis...")
        result = analyzer.analyze(test_dir)
        
        # Display results
        print(f"\n📊 Test Results:")
        print(f"   Total errors: {result.total_errors}")
        print(f"   Critical: {result.critical_count}")
        print(f"   Major: {result.major_count}")
        print(f"   Minor: {result.minor_count}")
        print(f"   Languages: {result.languages_analyzed}")
        print(f"   Files processed: {result.files_processed}")
        print(f"   Analysis time: {result.analysis_time:.2f}s")
        
        # Format and display output
        output = analyzer.format_output(result)
        print(f"\n📋 Formatted Output:")
        print(output)
        
        # Validate results
        if result.total_errors > 0:
            print(f"\n✅ Test PASSED: Found {result.total_errors} errors as expected")
        else:
            print(f"\n❌ Test FAILED: No errors found, expected some errors")
        
        # Cleanup
        analyzer.cleanup()
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
            print(f"\n🧹 Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    main()

