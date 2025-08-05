#!/usr/bin/env python3
"""
Example usage of the Serena LSP Error Analysis Tool

This script demonstrates how to use the SerenaLSPAnalyzer programmatically
and provides examples of different analysis scenarios.
"""

import os
import sys
import json

# Add src to path for imports (same as main script)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def example_basic_analysis():
    """Example: Basic repository analysis"""
    print("🔍 Example 1: Basic Repository Analysis")
    print("=" * 50)
    
    # This would work if dependencies are installed
    try:
        from serena_analysis import SerenaLSPAnalyzer
        
        with SerenaLSPAnalyzer(verbose=True) as analyzer:
            # Analyze current directory
            result = analyzer.analyze_repository(".", output_format="text")
            print("Analysis completed!")
            print(result[:500] + "..." if len(result) > 500 else result)
            
    except ImportError as e:
        print(f"⚠️  Dependencies not installed: {e}")
        print("📋 This example shows the intended usage pattern")
        print("🔧 Install dependencies with: pip install -e .")

def example_json_output():
    """Example: JSON output for programmatic processing"""
    print("\n📊 Example 2: JSON Output for Programmatic Processing")
    print("=" * 50)
    
    try:
        from serena_analysis import SerenaLSPAnalyzer
        
        with SerenaLSPAnalyzer(verbose=False, max_workers=2) as analyzer:
            # Get JSON results
            result = analyzer.analyze_repository(
                ".",
                severity_filter="ERROR",
                output_format="json"
            )
            
            # Process results programmatically
            if isinstance(result, dict):
                print(f"📈 Total files analyzed: {result.get('total_files', 0)}")
                print(f"🔍 Total diagnostics found: {result.get('total_diagnostics', 0)}")
                print(f"⚡ Analysis time: {result.get('performance_stats', {}).get('analysis_time', 0):.2f}s")
                
                # Show severity breakdown
                severity_counts = result.get('diagnostics_by_severity', {})
                for severity, count in severity_counts.items():
                    print(f"   {severity}: {count}")
            
    except ImportError as e:
        print(f"⚠️  Dependencies not installed: {e}")
        print("📋 Example JSON output structure:")
        example_json = {
            "total_files": 150,
            "processed_files": 148,
            "failed_files": 2,
            "total_diagnostics": 42,
            "diagnostics_by_severity": {
                "ERROR": 25,
                "WARNING": 15,
                "INFO": 2
            },
            "performance_stats": {
                "analysis_time": 45.2,
                "total_time": 52.1
            }
        }
        print(json.dumps(example_json, indent=2))

def example_remote_repository():
    """Example: Analyzing a remote repository"""
    print("\n🌐 Example 3: Remote Repository Analysis")
    print("=" * 50)
    
    try:
        from serena_analysis import SerenaLSPAnalyzer
        
        # Example with a small public repository
        repo_url = "https://github.com/octocat/Hello-World.git"
        
        with SerenaLSPAnalyzer(verbose=True, timeout=300) as analyzer:
            result = analyzer.analyze_repository(
                repo_url,
                language_override="python",
                severity_filter="ERROR"
            )
            print(f"Remote analysis completed for {repo_url}")
            
    except ImportError as e:
        print(f"⚠️  Dependencies not installed: {e}")
        print("📋 Command line equivalent:")
        print("./serena_analysis.py https://github.com/user/repo.git --severity ERROR --verbose")

def example_command_line_usage():
    """Show command line usage examples"""
    print("\n💻 Command Line Usage Examples")
    print("=" * 50)
    
    examples = [
        ("Basic analysis", "./serena_analysis.py ."),
        ("Error filtering", "./serena_analysis.py . --severity ERROR"),
        ("Verbose mode", "./serena_analysis.py . --verbose"),
        ("Custom settings", "./serena_analysis.py . --timeout 900 --max-workers 8"),
        ("JSON output", "./serena_analysis.py . --output json"),
        ("Remote repo", "./serena_analysis.py https://github.com/user/repo.git"),
        ("Language override", "./serena_analysis.py . --language python --verbose"),
        ("Large repo optimization", "./serena_analysis.py . --timeout 1200 --max-workers 2 --severity ERROR")
    ]
    
    for description, command in examples:
        print(f"📋 {description}:")
        print(f"   {command}")
        print()

def main():
    """Run all examples"""
    print("🚀 Serena LSP Error Analysis Tool - Usage Examples")
    print("=" * 60)
    
    example_basic_analysis()
    example_json_output()
    example_remote_repository()
    example_command_line_usage()
    
    print("✨ Key Features:")
    print("   🔍 Comprehensive analysis of entire codebases")
    print("   📡 Real LSP integration using Serena and SolidLSP")
    print("   ⚡ High-performance parallel processing")
    print("   🎯 Flexible filtering and output formats")
    print("   📈 Advanced analytics and progress tracking")
    print("   🌍 Support for local and remote repositories")
    
    print("\n📖 For more information, see README_serena_analysis.md")
    print("🔧 Install dependencies: pip install -e .")
    print("❓ Get help: ./serena_analysis.py --help")

if __name__ == "__main__":
    main()
