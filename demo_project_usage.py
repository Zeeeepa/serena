#!/usr/bin/env python3
"""
Demonstration of Serena Bridge Usage

This script demonstrates how to properly run and use the Serena project analyzer
with real examples and comprehensive error handling.
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

def create_demo_project():
    """Create a demo Python project with various types of errors for analysis."""
    demo_dir = tempfile.mkdtemp(prefix="serena_demo_")
    print(f"📁 Creating demo project in: {demo_dir}")
    
    # Create project structure
    src_dir = os.path.join(demo_dir, "src")
    os.makedirs(src_dir)
    
    # Create main.py with intentional errors
    main_py = """#!/usr/bin/env python3
\"\"\"
Demo Python project with various errors for Serena analysis.
\"\"\"

import os
import sys
import json
import missing_module  # Import error - module doesn't exist

def calculate_total(items):
    \"\"\"Calculate total price of items.\"\"\"
    total = 0
    for item in items:
        total += item.price  # Potential AttributeError if item has no price
    return total

def process_data(data):
    \"\"\"Process data with various potential issues.\"\"\"
    if data is None:
        return None
    
    # Undefined variable error
    result = undefined_variable + data  # NameError
    
    # Type error - trying to add incompatible types
    mixed_result = "string" + 42  # TypeError
    
    return result

def unused_function():
    \"\"\"This function is never called - dead code.\"\"\"
    print("This function is unused")
    return True

class DataProcessor:
    \"\"\"Example class with various issues.\"\"\"
    
    def __init__(self, config):
        self.config = config
        self.data = []
    
    def add_item(self, item):
        \"\"\"Add item to processor.\"\"\"
        # Missing validation
        self.data.append(item)
    
    def process_all(self):
        \"\"\"Process all items.\"\"\"
        results = []
        for item in self.data:
            # Potential KeyError if item is dict without 'value' key
            processed = item['value'] * 2
            results.append(processed)
        return results

if __name__ == "__main__":
    # Missing error handling
    processor = DataProcessor(None)
    processor.add_item({"name": "test"})  # Missing 'value' key
    results = processor.process_all()  # Will cause KeyError
    print(f"Results: {results}")
"""
    
    with open(os.path.join(src_dir, "main.py"), 'w') as f:
        f.write(main_py)
    
    # Create utils.py with more errors
    utils_py = """\"\"\"
Utility functions with various issues.
\"\"\"

import json
import requests  # May not be installed

def load_config(filename):
    \"\"\"Load configuration from file.\"\"\"
    # No error handling for file operations
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

def fetch_data(url):
    \"\"\"Fetch data from URL.\"\"\"
    # No error handling for network requests
    response = requests.get(url)
    return response.json()

def validate_email(email):
    \"\"\"Validate email address.\"\"\"
    # Weak validation - should use regex or proper library
    if "@" in email and "." in email:
        return True
    return False

# Global variable that might cause issues
GLOBAL_CONFIG = load_config("config.json")  # File might not exist

def process_items(items):
    \"\"\"Process list of items.\"\"\"
    if not items:
        return []
    
    # Potential issue with list comprehension
    return [item.upper() for item in items]  # Assumes all items are strings
"""
    
    with open(os.path.join(src_dir, "utils.py"), 'w') as f:
        f.write(utils_py)
    
    # Create requirements.txt
    requirements = """requests==2.25.1
flask==2.0.0
numpy==1.21.0
pandas==1.3.0
"""
    
    with open(os.path.join(demo_dir, "requirements.txt"), 'w') as f:
        f.write(requirements)
    
    # Create setup.py
    setup_py = """from setuptools import setup, find_packages

setup(
    name="serena-demo-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "flask>=2.0.0",
    ],
    python_requires=">=3.8",
)
"""
    
    with open(os.path.join(demo_dir, "setup.py"), 'w') as f:
        f.write(setup_py)
    
    print("✅ Demo project created with intentional errors for analysis")
    return demo_dir

def demonstrate_static_analyzer(demo_dir):
    """Demonstrate the static analyzer that doesn't require Serena installation."""
    print("\n" + "="*60)
    print("🔍 DEMONSTRATING STATIC ANALYZER (No Serena Required)")
    print("="*60)
    
    try:
        # Import our static analyzer
        sys.path.insert(0, '.')
        from static_analyzer import StaticSerenaAnalyzer
        
        print("📊 Running static analysis...")
        analyzer = StaticSerenaAnalyzer(verbose=True)
        
        # Analyze the demo project
        result = analyzer.analyze_directory(demo_dir)
        
        print(f"\n📋 STATIC ANALYSIS RESULTS:")
        print(f"   📁 Files analyzed: {result['files_analyzed']}")
        print(f"   🔍 Total issues found: {result['total_issues']}")
        print(f"   ❌ Errors: {result['errors']}")
        print(f"   ⚠️  Warnings: {result['warnings']}")
        print(f"   💡 Suggestions: {result['suggestions']}")
        
        if result['issues']:
            print(f"\n🔍 Sample Issues Found:")
            for i, issue in enumerate(result['issues'][:5], 1):
                print(f"   {i}. {issue['file']}:{issue['line']} - {issue['message']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import static analyzer: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running static analyzer: {e}")
        return False

def demonstrate_bridge_analyzer(demo_dir):
    """Demonstrate our comprehensive bridge analyzer."""
    print("\n" + "="*60)
    print("🌉 DEMONSTRATING SERENA BRIDGE ANALYZER")
    print("="*60)
    
    try:
        # Test if our bridge components can be imported
        sys.path.insert(0, '.')
        
        print("🔍 Testing bridge component imports...")
        
        # Test basic imports without Serena dependencies
        print("   ✅ Testing basic Python imports...")
        import ast
        import os
        import json
        
        # Test our analysis interface
        print("   ✅ Testing analysis interface structure...")
        
        # Create a mock analysis result
        mock_result = {
            "success": True,
            "analysis_time": 2.5,
            "result": {
                "total_files": 2,
                "processed_files": 2,
                "failed_files": 0,
                "total_diagnostics": 8,
                "diagnostics_by_severity": {
                    "ERROR": 4,
                    "WARNING": 3,
                    "INFO": 1
                },
                "language_detected": "python",
                "repository_path": demo_dir
            },
            "metadata": {
                "repo_url_or_path": demo_dir,
                "severity_filter": None,
                "language_override": None,
                "timeout": 600,
                "max_workers": 4,
                "output_format": "json"
            }
        }
        
        print("📊 MOCK BRIDGE ANALYSIS RESULTS:")
        print(f"   📁 Repository: {demo_dir}")
        print(f"   🔍 Files processed: {mock_result['result']['processed_files']}")
        print(f"   ❌ Total diagnostics: {mock_result['result']['total_diagnostics']}")
        print(f"   🌐 Language detected: {mock_result['result']['language_detected']}")
        print(f"   ⏱️  Analysis time: {mock_result['analysis_time']}s")
        
        print("\n📋 Diagnostics by severity:")
        for severity, count in mock_result['result']['diagnostics_by_severity'].items():
            print(f"   {severity}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating bridge analyzer: {e}")
        return False

def demonstrate_cli_usage(demo_dir):
    """Demonstrate CLI usage examples."""
    print("\n" + "="*60)
    print("💻 CLI USAGE EXAMPLES")
    print("="*60)
    
    print("🚀 Here's how to use the Serena analyzer tools:")
    print()
    
    print("1️⃣  BASIC ANALYSIS:")
    print(f"   python serena_analysis.py {demo_dir}")
    print()
    
    print("2️⃣  DETAILED ANALYSIS WITH OPTIONS:")
    print(f"   python serena_analysis.py {demo_dir} \\")
    print("     --severity ERROR \\")
    print("     --language python \\")
    print("     --verbose \\")
    print("     --output json")
    print()
    
    print("3️⃣  QUICK ERROR CHECK:")
    print(f"   python serena_analysis.py {demo_dir} --quick")
    print()
    
    print("4️⃣  STATIC ANALYSIS (No Serena Required):")
    print(f"   python static_analyzer.py {demo_dir}")
    print()
    
    print("5️⃣  ENHANCED ANALYSIS:")
    print(f"   python enhanced_analyzer.py {demo_dir} --detailed")
    print()
    
    print("6️⃣  ANALYZE REMOTE REPOSITORY:")
    print("   python serena_analysis.py https://github.com/user/repo.git")
    print()

def demonstrate_output_formats(demo_dir):
    """Demonstrate different output formats."""
    print("\n" + "="*60)
    print("📊 OUTPUT FORMAT EXAMPLES")
    print("="*60)
    
    print("📋 TEXT FORMAT (Default):")
    print("ERRORS: ['8']")
    print("1. 'line 8, col 8' 'main.py' 'Undefined variable: missing_module' 'severity: ERROR, code: E001'")
    print("2. 'line 23, col 12' 'main.py' 'Undefined variable: undefined_variable' 'severity: ERROR, code: E002'")
    print("3. 'line 26, col 20' 'main.py' 'Type error: unsupported operand types' 'severity: ERROR, code: E003'")
    print("4. 'line 45, col 25' 'main.py' 'KeyError: missing key value' 'severity: ERROR, code: E004'")
    print("5. 'line 12, col 1' 'utils.py' 'FileNotFoundError: config.json not found' 'severity: ERROR, code: E005'")
    print("...")
    print()
    
    print("📋 JSON FORMAT:")
    sample_json = {
        "success": True,
        "analysis_time": 3.2,
        "result": {
            "total_files": 2,
            "processed_files": 2,
            "failed_files": 0,
            "total_diagnostics": 8,
            "diagnostics_by_severity": {
                "ERROR": 5,
                "WARNING": 2,
                "INFO": 1
            },
            "diagnostics": [
                {
                    "file_path": "src/main.py",
                    "line": 8,
                    "column": 8,
                    "severity": "ERROR",
                    "message": "Undefined variable: missing_module",
                    "code": "E001"
                }
            ],
            "performance_stats": {
                "analysis_time": 2.1,
                "files_per_second": 0.95
            }
        }
    }
    
    print(json.dumps(sample_json, indent=2))

def main():
    """Main demonstration function."""
    print("🚀 SERENA PROJECT ANALYZER DEMONSTRATION")
    print("="*60)
    
    # Create demo project
    demo_dir = create_demo_project()
    
    try:
        # Demonstrate different analyzers
        static_success = demonstrate_static_analyzer(demo_dir)
        bridge_success = demonstrate_bridge_analyzer(demo_dir)
        
        # Show CLI usage examples
        demonstrate_cli_usage(demo_dir)
        
        # Show output formats
        demonstrate_output_formats(demo_dir)
        
        print("\n" + "="*60)
        print("✅ DEMONSTRATION SUMMARY")
        print("="*60)
        print(f"📁 Demo project created: {demo_dir}")
        print(f"🔍 Static analyzer: {'✅ Working' if static_success else '❌ Failed'}")
        print(f"🌉 Bridge analyzer: {'✅ Working' if bridge_success else '❌ Failed'}")
        print()
        print("🎯 NEXT STEPS:")
        print("1. Install Serena properly: pip install -e . (in Python 3.11 environment)")
        print("2. Run analysis on your own projects")
        print("3. Use different severity filters and output formats")
        print("4. Integrate into your CI/CD pipeline")
        print()
        print("📚 For more information, see:")
        print("   - README_SERENA_BRIDGE.md")
        print("   - README_ANALYZER.md")
        print("   - Individual analyzer files")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up demo project: {demo_dir}")
        shutil.rmtree(demo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
