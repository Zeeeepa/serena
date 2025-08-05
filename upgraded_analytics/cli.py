#!/usr/bin/env python3
"""
Command-line interface for repository analytics.

Usage:
    python cli.py --repo owner/repo
    python cli.py --repo https://github.com/owner/repo
    python cli.py --repo owner/repo --no-runtime-errors
    python cli.py --repo owner/repo --max-files 100
"""

import argparse
import asyncio
import json
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import RepositoryAnalysisRequest
from src.analyzer import RepositoryAnalyzer


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def print_analysis_summary(result):
    """Print a human-readable summary of the analysis results."""
    print("\n" + "="*80)
    print(f"REPOSITORY ANALYSIS RESULTS")
    print("="*80)
    print(f"Repository: {result.repo_url}")
    print(f"Description: {result.description}")
    print(f"Analysis Duration: {result.analysis_duration_seconds:.2f} seconds")
    print(f"Languages Detected: {', '.join(result.languages_detected)}")
    
    print("\n📊 BASIC METRICS")
    print("-" * 40)
    print(f"Files: {result.num_files:,}")
    print(f"Functions: {result.num_functions:,}")
    print(f"Classes: {result.num_classes:,}")
    
    print("\n📏 LINE METRICS")
    print("-" * 40)
    print(f"Lines of Code (LOC): {result.line_metrics.loc:,}")
    print(f"Logical Lines (LLOC): {result.line_metrics.lloc:,}")
    print(f"Source Lines (SLOC): {result.line_metrics.sloc:,}")
    print(f"Comment Lines: {result.line_metrics.comments:,}")
    print(f"Comment Density: {result.line_metrics.comment_density:.1f}%")
    
    print("\n🔄 COMPLEXITY METRICS")
    print("-" * 40)
    print(f"Average Cyclomatic Complexity: {result.complexity_metrics.average_cyclomatic_complexity:.2f}")
    print(f"Complexity Rank: {result.complexity_metrics.complexity_rank}")
    print(f"Functions Analyzed: {result.complexity_metrics.functions_analyzed:,}")
    
    print("\n📐 HALSTEAD METRICS")
    print("-" * 40)
    print(f"Total Volume: {result.halstead_metrics.total_volume:,}")
    print(f"Average Volume: {result.halstead_metrics.average_volume:,}")
    print(f"Functions Analyzed: {result.halstead_metrics.functions_analyzed:,}")
    
    print("\n🔧 MAINTAINABILITY")
    print("-" * 40)
    print(f"Average Index: {result.maintainability_metrics.average_index}")
    print(f"Maintainability Rank: {result.maintainability_metrics.maintainability_rank}")
    print(f"Functions Analyzed: {result.maintainability_metrics.functions_analyzed:,}")
    
    print("\n🏗️ INHERITANCE")
    print("-" * 40)
    print(f"Average Depth: {result.inheritance_metrics.average_depth:.2f}")
    print(f"Classes Analyzed: {result.inheritance_metrics.classes_analyzed:,}")
    
    # Runtime errors summary
    if result.runtime_error_summary.total_files_analyzed > 0:
        print("\n🚨 RUNTIME ERRORS (SolidLSP)")
        print("-" * 40)
        print(f"Files Analyzed: {result.runtime_error_summary.total_files_analyzed:,}")
        print(f"Files with Errors: {result.runtime_error_summary.files_with_errors:,}")
        print(f"Total Issues: {result.runtime_error_summary.total_errors:,}")
        print(f"  • Errors: {result.runtime_error_summary.errors:,}")
        print(f"  • Warnings: {result.runtime_error_summary.warnings:,}")
        print(f"  • Information: {result.runtime_error_summary.information:,}")
        print(f"  • Hints: {result.runtime_error_summary.hints:,}")
        
        if result.runtime_error_summary.language_summaries:
            print("\n📋 ERRORS BY LANGUAGE")
            print("-" * 40)
            for lang, summary in result.runtime_error_summary.language_summaries.items():
                print(f"{lang.upper()}: {summary.total_errors} issues in {summary.files_with_errors}/{summary.total_files} files")
        
        # Show top files with most errors
        if result.runtime_error_summary.file_summaries:
            top_files = sorted(
                result.runtime_error_summary.file_summaries,
                key=lambda x: x.total_errors,
                reverse=True
            )[:5]
            
            if top_files and top_files[0].total_errors > 0:
                print("\n🔥 TOP FILES WITH ISSUES")
                print("-" * 40)
                for file_summary in top_files:
                    if file_summary.total_errors > 0:
                        print(f"{file_summary.file_path}: {file_summary.total_errors} issues")
    
    # Git activity
    if result.monthly_commits:
        total_commits = sum(result.monthly_commits.values())
        print(f"\n📈 GIT ACTIVITY (Last 12 months)")
        print("-" * 40)
        print(f"Total Commits: {total_commits:,}")
        
        # Show recent months with commits
        recent_months = list(result.monthly_commits.items())[-6:]
        for month, count in recent_months:
            if count > 0:
                print(f"{month}: {count} commits")
    
    # Analysis errors
    if result.analysis_errors:
        print(f"\n⚠️ ANALYSIS WARNINGS ({len(result.analysis_errors)})")
        print("-" * 40)
        for error in result.analysis_errors[:5]:  # Show first 5 errors
            print(f"• {error['component']}: {error['message']}")
        if len(result.analysis_errors) > 5:
            print(f"... and {len(result.analysis_errors) - 5} more")
    
    print("\n" + "="*80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze repositories for code quality metrics and runtime errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --repo Zeeeepa/graph-sitter
  python cli.py --repo https://github.com/microsoft/vscode
  python cli.py --repo owner/repo --no-runtime-errors
  python cli.py --repo owner/repo --max-files 100 --output results.json
        """
    )
    
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository to analyze (format: owner/repo or full GitHub URL)"
    )
    
    parser.add_argument(
        "--no-runtime-errors",
        action="store_true",
        help="Skip runtime error analysis (faster but less comprehensive)"
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum number of files to analyze for runtime errors"
    )
    
    parser.add_argument(
        "--languages",
        nargs="+",
        help="Specific languages to analyze (e.g., python typescript java)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for JSON results (default: print to stdout)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary, not full JSON output"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Create analysis request
    request = RepositoryAnalysisRequest(
        repo_url=args.repo,
        include_runtime_errors=not args.no_runtime_errors,
        languages=args.languages,
        max_files=args.max_files
    )
    
    # Run analysis
    try:
        print(f"🔍 Analyzing repository: {args.repo}")
        if not args.no_runtime_errors:
            print("📋 Including runtime error analysis using SolidLSP")
        
        analyzer = RepositoryAnalyzer()
        result = analyzer.analyze_repository(request)
        
        # Output results
        if args.summary_only:
            print_analysis_summary(result)
        else:
            result_json = result.model_dump_json(indent=2)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(result_json)
                print(f"✅ Results saved to {args.output}")
                print_analysis_summary(result)
            else:
                print(result_json)
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

