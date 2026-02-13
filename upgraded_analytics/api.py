#!/usr/bin/env python3
"""
Main API script for repository analytics.

This script can be run in two modes:
1. CLI mode: python api.py --repo owner/repo
2. Server mode: python api.py --server [--host 127.0.0.1] [--port 8000]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def run_cli_analysis(args):
    """Run CLI analysis mode."""
    from src.models import RepositoryAnalysisRequest
    from src.analyzer import RepositoryAnalyzer
    import json
    import logging
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Create analysis request
    request = RepositoryAnalysisRequest(
        repo_url=args.repo,
        include_runtime_errors=not args.no_runtime_errors,
        languages=getattr(args, 'languages', None),
        max_files=getattr(args, 'max_files', None)
    )
    
    # Run analysis
    try:
        print(f"🔍 Analyzing repository: {args.repo}")
        if not args.no_runtime_errors:
            print("📋 Including runtime error analysis using SolidLSP")
        
        analyzer = RepositoryAnalyzer()
        result = analyzer.analyze_repository(request)
        
        # Print summary
        print("\n" + "="*80)
        print(f"ANALYSIS COMPLETE")
        print("="*80)
        print(f"Repository: {result.repo_url}")
        print(f"Files: {result.num_files:,}")
        print(f"Functions: {result.num_functions:,}")
        print(f"Classes: {result.num_classes:,}")
        print(f"Runtime Errors Found: {result.runtime_error_summary.total_errors:,}")
        print(f"Analysis Duration: {result.analysis_duration_seconds:.2f} seconds")
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result.model_dump_json(indent=2))
            print(f"✅ Full results saved to {args.output}")
        else:
            print("\n📄 Full JSON results:")
            print(result.model_dump_json(indent=2))
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_server_mode(args):
    """Run FastAPI server mode."""
    import uvicorn
    from src.api import app
    
    print(f"🚀 Starting Repository Analytics API server")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📖 API documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health check: http://{args.host}:{args.port}/health")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Repository Analytics with SolidLSP Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CLI Analysis Mode
  python api.py --repo Zeeeepa/graph-sitter
  python api.py --repo owner/repo --no-runtime-errors --output results.json
  
  # Server Mode  
  python api.py --server
  python api.py --server --host 0.0.0.0 --port 8080
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--repo",
        help="Repository to analyze (CLI mode) - format: owner/repo or full GitHub URL"
    )
    mode_group.add_argument(
        "--server",
        action="store_true",
        help="Run in server mode (starts FastAPI server)"
    )
    
    # CLI mode options
    parser.add_argument(
        "--no-runtime-errors",
        action="store_true",
        help="Skip runtime error analysis (CLI mode only)"
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum number of files to analyze for runtime errors (CLI mode only)"
    )
    
    parser.add_argument(
        "--languages",
        nargs="+",
        help="Specific languages to analyze (CLI mode only)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for JSON results (CLI mode only)"
    )
    
    # Server mode options
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (server mode only)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (server mode only)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (server mode only)"
    )
    
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level (server mode only)"
    )
    
    # Common options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Route to appropriate mode
    if args.repo:
        run_cli_analysis(args)
    elif args.server:
        run_server_mode(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

