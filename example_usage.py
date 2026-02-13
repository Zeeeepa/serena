#!/usr/bin/env python3
"""
Example usage of Serena LSP Error Analyzer

This script demonstrates various ways to use the analyzer programmatically
and shows how to integrate it into other tools or workflows.
"""

import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from serena_analyzer import SerenaAnalyzer, AnalysisResult

def example_basic_analysis():
    """Basic analysis example"""
    print("📝 Example 1: Basic Analysis")
    print("-" * 40)
    
    analyzer = SerenaAnalyzer(verbose=False)
    
    try:
        # Analyze current directory
        result = analyzer.analyze(".")
        
        print(f"✅ Analysis completed:")
        print(f"   Total errors: {result.total_errors}")
        print(f"   Critical: {result.critical_count}")
        print(f"   Major: {result.major_count}")
        print(f"   Minor: {result.minor_count}")
        print(f"   Languages: {', '.join(result.languages_analyzed)}")
        print(f"   Analysis time: {result.analysis_time:.2f}s")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None
    finally:
        analyzer.cleanup()

def example_github_analysis():
    """GitHub repository analysis example"""
    print("\n📝 Example 2: GitHub Repository Analysis")
    print("-" * 40)
    
    # Example with a small public repository
    github_url = "https://github.com/octocat/Hello-World"
    
    analyzer = SerenaAnalyzer(verbose=True)
    
    try:
        print(f"🔍 Analyzing GitHub repository: {github_url}")
        result = analyzer.analyze(github_url)
        
        # Format and display results
        formatted_output = analyzer.format_output(result)
        print(f"\n📋 Analysis Results:")
        print(formatted_output)
        
        return result
        
    except Exception as e:
        print(f"❌ GitHub analysis failed: {e}")
        return None
    finally:
        analyzer.cleanup()

def example_custom_processing():
    """Example of custom error processing"""
    print("\n📝 Example 3: Custom Error Processing")
    print("-" * 40)
    
    analyzer = SerenaAnalyzer(verbose=False)
    
    try:
        result = analyzer.analyze(".")
        
        if result.total_errors == 0:
            print("✅ No errors found!")
            return
        
        # Group errors by file
        errors_by_file = {}
        for error in result.errors:
            if error.file_path not in errors_by_file:
                errors_by_file[error.file_path] = []
            errors_by_file[error.file_path].append(error)
        
        print(f"📊 Error Distribution:")
        for file_path, file_errors in errors_by_file.items():
            critical = sum(1 for e in file_errors if e.severity == "Critical")
            major = sum(1 for e in file_errors if e.severity == "Major")
            minor = sum(1 for e in file_errors if e.severity == "Minor")
            
            print(f"   📄 {file_path}: {len(file_errors)} total")
            print(f"      ⚠️ Critical: {critical}, 👉 Major: {major}, 🔍 Minor: {minor}")
        
        # Find most problematic files
        print(f"\n🔥 Most Problematic Files:")
        sorted_files = sorted(
            errors_by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for file_path, file_errors in sorted_files[:5]:
            print(f"   {len(file_errors):2d} errors: {file_path}")
        
        # Show error types
        print(f"\n📈 Error Types:")
        error_sources = {}
        for error in result.errors:
            source = error.source or "unknown"
            if source not in error_sources:
                error_sources[source] = 0
            error_sources[source] += 1
        
        for source, count in sorted(error_sources.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source}: {count} errors")
        
    except Exception as e:
        print(f"❌ Custom processing failed: {e}")
    finally:
        analyzer.cleanup()

def example_ci_integration():
    """Example of CI/CD integration"""
    print("\n📝 Example 4: CI/CD Integration")
    print("-" * 40)
    
    analyzer = SerenaAnalyzer(verbose=False)
    
    try:
        result = analyzer.analyze(".")
        
        # Define quality gates
        MAX_CRITICAL_ERRORS = 0
        MAX_MAJOR_ERRORS = 10
        MAX_TOTAL_ERRORS = 50
        
        print(f"🎯 Quality Gates:")
        print(f"   Max Critical Errors: {MAX_CRITICAL_ERRORS}")
        print(f"   Max Major Errors: {MAX_MAJOR_ERRORS}")
        print(f"   Max Total Errors: {MAX_TOTAL_ERRORS}")
        
        print(f"\n📊 Current Status:")
        print(f"   Critical Errors: {result.critical_count}")
        print(f"   Major Errors: {result.major_count}")
        print(f"   Total Errors: {result.total_errors}")
        
        # Check quality gates
        failed_gates = []
        
        if result.critical_count > MAX_CRITICAL_ERRORS:
            failed_gates.append(f"Critical errors: {result.critical_count} > {MAX_CRITICAL_ERRORS}")
        
        if result.major_count > MAX_MAJOR_ERRORS:
            failed_gates.append(f"Major errors: {result.major_count} > {MAX_MAJOR_ERRORS}")
        
        if result.total_errors > MAX_TOTAL_ERRORS:
            failed_gates.append(f"Total errors: {result.total_errors} > {MAX_TOTAL_ERRORS}")
        
        if failed_gates:
            print(f"\n❌ Quality Gates FAILED:")
            for gate in failed_gates:
                print(f"   • {gate}")
            
            # In CI, you would exit with non-zero code
            # sys.exit(1)
        else:
            print(f"\n✅ All Quality Gates PASSED!")
        
        # Generate CI report
        ci_report = {
            "status": "PASSED" if not failed_gates else "FAILED",
            "total_errors": result.total_errors,
            "critical_errors": result.critical_count,
            "major_errors": result.major_count,
            "minor_errors": result.minor_count,
            "languages_analyzed": result.languages_analyzed,
            "files_processed": result.files_processed,
            "analysis_time": result.analysis_time,
            "failed_gates": failed_gates
        }
        
        print(f"\n📋 CI Report:")
        import json
        print(json.dumps(ci_report, indent=2))
        
    except Exception as e:
        print(f"❌ CI integration example failed: {e}")
    finally:
        analyzer.cleanup()

def example_error_filtering():
    """Example of error filtering and categorization"""
    print("\n📝 Example 5: Error Filtering and Categorization")
    print("-" * 40)
    
    analyzer = SerenaAnalyzer(verbose=False)
    
    try:
        result = analyzer.analyze(".")
        
        if result.total_errors == 0:
            print("✅ No errors to filter!")
            return
        
        # Filter by severity
        critical_errors = [e for e in result.errors if e.severity == "Critical"]
        major_errors = [e for e in result.errors if e.severity == "Major"]
        minor_errors = [e for e in result.errors if e.severity == "Minor"]
        
        print(f"🔍 Filtering Results:")
        print(f"   Critical errors: {len(critical_errors)}")
        print(f"   Major errors: {len(major_errors)}")
        print(f"   Minor errors: {len(minor_errors)}")
        
        # Filter by file type
        python_errors = [e for e in result.errors if e.file_path.endswith('.py')]
        ts_errors = [e for e in result.errors if e.file_path.endswith(('.ts', '.js'))]
        
        print(f"\n📄 By File Type:")
        print(f"   Python errors: {len(python_errors)}")
        print(f"   TypeScript/JavaScript errors: {len(ts_errors)}")
        
        # Filter by error source
        if result.errors:
            print(f"\n🔧 By Error Source:")
            sources = set(e.source for e in result.errors if e.source)
            for source in sorted(sources):
                source_errors = [e for e in result.errors if e.source == source]
                print(f"   {source}: {len(source_errors)} errors")
        
        # Show sample of each category
        print(f"\n📋 Sample Critical Errors:")
        for error in critical_errors[:3]:
            context = error.symbol_context or "Unknown"
            print(f"   • {error.file_path}:{error.line} - {context}")
            print(f"     {error.message}")
        
    except Exception as e:
        print(f"❌ Error filtering example failed: {e}")
    finally:
        analyzer.cleanup()

def main():
    """Run all examples"""
    print("🚀 Serena LSP Error Analyzer - Usage Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_analysis()
    
    # Uncomment to test GitHub analysis (requires network)
    # example_github_analysis()
    
    example_custom_processing()
    example_ci_integration()
    example_error_filtering()
    
    print(f"\n✅ All examples completed!")
    print(f"\n💡 Integration Tips:")
    print(f"   • Use verbose=False for production to reduce noise")
    print(f"   • Implement timeout handling for large repositories")
    print(f"   • Cache results for repeated analysis")
    print(f"   • Filter errors based on your quality standards")
    print(f"   • Integrate with CI/CD for automated quality gates")

if __name__ == "__main__":
    main()

