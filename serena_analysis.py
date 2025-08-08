#!/usr/bin/env python3
"""
Production-Ready Serena Analysis Tool

This is the main analysis interface that provides comprehensive LSP-based
codebase analysis using the Serena bridge components. It offers a clean,
high-level API for analyzing entire codebases with multiple output formats
and comprehensive error handling.

Usage:
    python serena_analysis.py <repo_url_or_path> [options]

Example:
    python serena_analysis.py https://github.com/user/repo.git
    python serena_analysis.py /path/to/local/repo --severity ERROR --verbose
    python serena_analysis.py . --timeout 600 --max-workers 8 --output json
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional

# Import the comprehensive bridge components
try:
    from serena_bridge import *
    from serena_bridge_part2 import SerenaComprehensiveAnalyzer
except ImportError as e:
    print(f"❌ Critical Error: Failed to import Serena bridge components: {e}")
    print("Please ensure serena_bridge.py and serena_bridge_part2.py are in the same directory.")
    sys.exit(1)


class SerenaAnalysisInterface:
    """
    High-level interface for Serena codebase analysis.
    
    This class provides a clean, user-friendly API for performing
    comprehensive LSP-based analysis of codebases using the Serena bridge.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the analysis interface.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.logger = self._setup_logging(verbose)
        
        if verbose:
            self.logger.info("🚀 Initializing Serena Analysis Interface")
    
    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Set up comprehensive logging."""
        logger = logging.getLogger("serena_analysis")
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            
            if verbose:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                logger.setLevel(logging.DEBUG)
            else:
                formatter = logging.Formatter(
                    "%(levelname)s - %(message)s"
                )
                logger.setLevel(logging.INFO)
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def analyze_codebase(
        self,
        repo_url_or_path: str,
        severity_filter: Optional[str] = None,
        language_override: Optional[str] = None,
        timeout: float = 600,
        max_workers: int = 4,
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            repo_url_or_path: Repository URL or local path
            severity_filter: Optional severity filter ('ERROR', 'WARNING', 'INFO', 'HINT')
            language_override: Optional language override
            timeout: Timeout for LSP operations in seconds
            max_workers: Maximum number of parallel workers
            output_format: Output format ('text' or 'json')
            
        Returns:
            Analysis results with metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info("🔍 Starting comprehensive Serena codebase analysis...")
            
            # Validate inputs
            self._validate_inputs(
                repo_url_or_path, severity_filter, language_override, 
                timeout, max_workers, output_format
            )
            
            # Perform analysis using the comprehensive analyzer
            with SerenaComprehensiveAnalyzer(
                verbose=self.verbose,
                timeout=timeout,
                max_workers=max_workers
            ) as analyzer:
                
                result = analyzer.analyze_repository(
                    repo_url_or_path=repo_url_or_path,
                    severity_filter=severity_filter,
                    language_override=language_override,
                    output_format=output_format
                )
                
                analysis_time = time.time() - start_time
                
                # Wrap result with metadata
                return {
                    "success": True,
                    "analysis_time": analysis_time,
                    "result": result,
                    "metadata": {
                        "repo_url_or_path": repo_url_or_path,
                        "severity_filter": severity_filter,
                        "language_override": language_override,
                        "timeout": timeout,
                        "max_workers": max_workers,
                        "output_format": output_format,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                
        except Exception as e:
            analysis_time = time.time() - start_time
            error_msg = f"Analysis failed: {e}"
            
            self.logger.error(f"❌ {error_msg}")
            
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": str(e),
                "analysis_time": analysis_time,
                "result": None,
                "metadata": {
                    "repo_url_or_path": repo_url_or_path,
                    "severity_filter": severity_filter,
                    "language_override": language_override,
                    "timeout": timeout,
                    "max_workers": max_workers,
                    "output_format": output_format,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
    
    def _validate_inputs(
        self,
        repo_url_or_path: str,
        severity_filter: Optional[str],
        language_override: Optional[str],
        timeout: float,
        max_workers: int,
        output_format: str
    ) -> None:
        """Validate input parameters."""
        
        # Validate repo path/URL
        if not repo_url_or_path or not repo_url_or_path.strip():
            raise ValueError("Repository URL or path cannot be empty")
        
        # Validate severity filter
        if severity_filter:
            valid_severities = ["ERROR", "WARNING", "INFO", "HINT"]
            if severity_filter.upper() not in valid_severities:
                raise ValueError(f"Invalid severity filter: {severity_filter}. Must be one of: {valid_severities}")
        
        # Validate language override
        if language_override:
            try:
                Language(language_override.lower())
            except ValueError:
                available_languages = [lang.value for lang in Language]
                raise ValueError(f"Invalid language: {language_override}. Available: {available_languages}")
        
        # Validate timeout
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if timeout < 60:
            self.logger.warning("⚠️  Timeout less than 60 seconds may cause issues with large repositories")
        
        # Validate max_workers
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        
        if max_workers > 16:
            self.logger.warning("⚠️  Using more than 16 workers may overwhelm the LSP server")
        
        # Validate output format
        if output_format not in ["text", "json"]:
            raise ValueError("output_format must be 'text' or 'json'")
    
    def quick_analysis(
        self,
        repo_url_or_path: str,
        errors_only: bool = True
    ) -> Dict[str, Any]:
        """
        Perform a quick analysis focusing on errors only.
        
        Args:
            repo_url_or_path: Repository URL or local path
            errors_only: If True, only show ERROR severity diagnostics
            
        Returns:
            Quick analysis results
        """
        return self.analyze_codebase(
            repo_url_or_path=repo_url_or_path,
            severity_filter="ERROR" if errors_only else None,
            timeout=300,  # 5 minutes
            max_workers=2,  # Conservative for quick analysis
            output_format="json"
        )
    
    def detailed_analysis(
        self,
        repo_url_or_path: str,
        language_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a detailed analysis with all diagnostics.
        
        Args:
            repo_url_or_path: Repository URL or local path
            language_override: Optional language override
            
        Returns:
            Detailed analysis results
        """
        return self.analyze_codebase(
            repo_url_or_path=repo_url_or_path,
            language_override=language_override,
            timeout=900,  # 15 minutes
            max_workers=4,
            output_format="json"
        )


def main():
    """Main entry point for the Serena analysis tool."""
    parser = argparse.ArgumentParser(
        description="🚀 Production-Ready Serena LSP Analysis Tool - Comprehensive codebase analysis using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 COMPREHENSIVE SERENA ANALYSIS EXAMPLES:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR --verbose
  %(prog)s . --timeout 600 --max-workers 8 --language python
  %(prog)s https://github.com/Zeeeepa/serena --verbose --output json

📊 OUTPUT FORMATS:
  text: Human-readable format with error listing
  json: Structured JSON with complete metadata

🚀 SERENA BRIDGE FEATURES:
  ✅ 100% API compatibility with actual Serena implementation
  ✅ Comprehensive LSP server lifecycle management
  ✅ Advanced diagnostic collection and parsing
  ✅ Robust error handling and recovery
  ✅ Performance optimized batch processing
  ✅ Complete language detection and project setup
  ✅ Production-ready resource management

⚡ PERFORMANCE OPTIMIZATION TIPS:
  - Use --max-workers 2-8 for optimal parallel processing
  - Increase --timeout 600+ for very large repositories (1000+ files)
  - Use --severity ERROR to focus on critical issues only
  - Enable --verbose for detailed progress tracking and diagnostics

🔧 SUPPORTED LANGUAGES:
  Python, TypeScript/JavaScript, Java, C#, C++, Rust, Go, PHP, Ruby, Kotlin, Dart
        """,
    )

    parser.add_argument(
        "repository",
        help="Repository URL or local path to analyze (analyzes ALL source files)",
    )

    parser.add_argument(
        "--severity",
        choices=["ERROR", "WARNING", "INFO", "HINT"],
        help="Filter diagnostics by severity level (default: show all diagnostics)",
    )

    parser.add_argument(
        "--language",
        help="Override automatic language detection (e.g., python, typescript, java, rust)",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=600,
        help="Timeout for LSP operations in seconds (default: 600 for large codebases)",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers for file processing (default: 4)",
    )

    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging with progress tracking and performance metrics",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Perform quick analysis (errors only, reduced timeout)",
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Perform detailed analysis (all diagnostics, extended timeout)",
    )

    args = parser.parse_args()

    # Validate conflicting options
    if args.quick and args.detailed:
        print("❌ Error: --quick and --detailed options are mutually exclusive")
        sys.exit(1)

    print("🚀 PRODUCTION-READY SERENA LSP ANALYSIS TOOL")
    print("=" * 80)
    print("📋 Configuration:")
    print(f"   📁 Repository: {args.repository}")
    print(f"   🔍 Severity filter: {args.severity or 'ALL'}")
    print(f"   🌐 Language: {args.language or 'AUTO-DETECT'}")
    print(f"   ⏱️  Timeout: {args.timeout}s")
    print(f"   👥 Max workers: {args.max_workers}")
    print(f"   📊 Output format: {args.output}")
    print(f"   📋 Verbose: {args.verbose}")
    
    if args.quick:
        print(f"   ⚡ Mode: Quick analysis (errors only)")
    elif args.detailed:
        print(f"   🔍 Mode: Detailed analysis (all diagnostics)")
    else:
        print(f"   🎯 Mode: Standard analysis")
    
    print("=" * 80)

    # Create analysis interface
    try:
        interface = SerenaAnalysisInterface(verbose=args.verbose)
        
        # Perform analysis based on mode
        if args.quick:
            result = interface.quick_analysis(args.repository)
        elif args.detailed:
            result = interface.detailed_analysis(
                args.repository, 
                language_override=args.language
            )
        else:
            result = interface.analyze_codebase(
                repo_url_or_path=args.repository,
                severity_filter=args.severity,
                language_override=args.language,
                timeout=args.timeout,
                max_workers=args.max_workers,
                output_format=args.output
            )
        
        # Output results
        if not result["success"]:
            print(f"\n❌ Analysis failed: {result['error']}")
            sys.exit(1)
        
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE SERENA ANALYSIS RESULTS")
        print("=" * 80)
        
        if args.output == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result["result"])
        
        print("=" * 80)
        print(f"⏱️  Total analysis time: {result['analysis_time']:.2f} seconds")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
