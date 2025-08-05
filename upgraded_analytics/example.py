#!/usr/bin/env python3
"""
Example usage of the Repository Analytics API.

This script demonstrates how to use the upgraded analytics system
both programmatically and via the CLI.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import RepositoryAnalysisRequest
from src.analyzer import RepositoryAnalyzer


def example_programmatic_usage():
    """Example of using the analyzer programmatically."""
    print("🔍 Example: Programmatic Repository Analysis")
    print("=" * 50)
    
    # Create analysis request
    request = RepositoryAnalysisRequest(
        repo_url="Zeeeepa/graph-sitter",
        include_runtime_errors=True,
        max_files=50  # Limit for faster demo
    )
    
    # Create analyzer and run analysis
    analyzer = RepositoryAnalyzer()
    
    try:
        print(f"Analyzing repository: {request.repo_url}")
        result = analyzer.analyze_repository(request)
        
        # Print summary
        print(f"\n✅ Analysis Complete!")
        print(f"Repository: {result.repo_url}")
        print(f"Description: {result.description}")
        print(f"Files: {result.num_files:,}")
        print(f"Functions: {result.num_functions:,}")
        print(f"Classes: {result.num_classes:,}")
        print(f"Languages: {', '.join(result.languages_detected)}")
        print(f"Runtime Errors: {result.runtime_error_summary.total_errors:,}")
        print(f"Analysis Duration: {result.analysis_duration_seconds:.2f}s")
        
        # Show complexity metrics
        print(f"\n📊 Code Quality Metrics:")
        print(f"Average Complexity: {result.complexity_metrics.average_cyclomatic_complexity:.2f} ({result.complexity_metrics.complexity_rank})")
        print(f"Maintainability Index: {result.maintainability_metrics.average_index} ({result.maintainability_metrics.maintainability_rank})")
        print(f"Comment Density: {result.line_metrics.comment_density:.1f}%")
        
        # Show runtime errors if any
        if result.runtime_error_summary.total_errors > 0:
            print(f"\n🚨 Runtime Issues Found:")
            print(f"Files with issues: {result.runtime_error_summary.files_with_errors}")
            print(f"Total issues: {result.runtime_error_summary.total_errors}")
            print(f"  • Errors: {result.runtime_error_summary.errors}")
            print(f"  • Warnings: {result.runtime_error_summary.warnings}")
            print(f"  • Info: {result.runtime_error_summary.information}")
            print(f"  • Hints: {result.runtime_error_summary.hints}")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


def example_cli_commands():
    """Show example CLI commands."""
    print("\n🖥️  Example CLI Commands")
    print("=" * 50)
    
    commands = [
        "# Basic analysis",
        "python api.py --repo Zeeeepa/graph-sitter",
        "",
        "# Skip runtime errors for faster analysis", 
        "python api.py --repo owner/repo --no-runtime-errors",
        "",
        "# Limit files and save to JSON",
        "python api.py --repo owner/repo --max-files 100 --output results.json",
        "",
        "# Analyze specific languages only",
        "python api.py --repo owner/repo --languages python typescript",
        "",
        "# Start API server",
        "python api.py --server --host 0.0.0.0 --port 8080",
        "",
        "# Verbose logging",
        "python api.py --repo owner/repo --verbose",
    ]
    
    for cmd in commands:
        print(cmd)


def example_api_usage():
    """Show example API usage."""
    print("\n🌐 Example API Usage")
    print("=" * 50)
    
    api_examples = [
        "# Start the server",
        "python api.py --server",
        "",
        "# Analyze repository via API",
        'curl -X POST "http://localhost:8000/analyze" \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"repo_url": "owner/repo", "include_runtime_errors": true}\'',
        "",
        "# Get supported languages",
        'curl "http://localhost:8000/languages"',
        "",
        "# Health check",
        'curl "http://localhost:8000/health"',
    ]
    
    for example in api_examples:
        print(example)


def main():
    """Main example function."""
    print("🚀 Repository Analytics with SolidLSP - Examples")
    print("=" * 60)
    
    # Show CLI examples
    example_cli_commands()
    
    # Show API examples  
    example_api_usage()
    
    # Ask if user wants to run programmatic example
    print("\n" + "=" * 60)
    response = input("Would you like to run a live analysis example? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        example_programmatic_usage()
    else:
        print("👋 Example complete! Use the CLI commands above to get started.")


if __name__ == "__main__":
    main()

