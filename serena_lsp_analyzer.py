#!/usr/bin/env python3
"""
Serena LSP Error Analysis Tool - Real Implementation

This tool provides comprehensive LSP error analysis using the actual Serena codebase.
It analyzes Python codebases using real LSP servers and provides detailed error reporting.

Usage:
    python serena_lsp_analyzer.py <repo_path> [options]

Example:
    python serena_lsp_analyzer.py . --verbose --symbols
    python serena_lsp_analyzer.py /path/to/repo --severity ERROR
"""

import argparse
import json
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add src directory to Python path for direct imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Core Serena imports
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project

    # SolidLSP imports
    from solidlsp.ls_config import Language
    from solidlsp import SolidLanguageServer
    from solidlsp.ls_types import DiagnosticsSeverity, SymbolKind

    SERENA_AVAILABLE = True
    print("✅ Serena and SolidLSP modules loaded successfully")

except ImportError as e:
    print(f"❌ Failed to import Serena/SolidLSP modules: {e}")
    print("Please ensure you're running from the serena repository root directory.")
    sys.exit(1)


@dataclass
class ErrorInfo:
    """Standardized error information."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.severity} {self.file_path}:{self.line}:{self.column} - {self.message}"


@dataclass
class SymbolInfo:
    """Symbol information from LSP."""
    name: str
    kind: int
    location: Dict[str, Any]
    container_name: Optional[str] = None
    detail: Optional[str] = None


@dataclass
class AnalysisResults:
    """Analysis results."""
    total_files: int
    processed_files: int
    failed_files: int
    total_diagnostics: int
    diagnostics: List[ErrorInfo]
    symbols: List[SymbolInfo]
    performance_stats: Dict[str, float]
    language_detected: str
    repository_path: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SerenaLSPAnalyzer:
    """Real Serena LSP analyzer implementation."""

    def __init__(self, verbose: bool = False, enable_symbols: bool = False, timeout: float = 300):
        self.verbose = verbose
        self.enable_symbols = enable_symbols
        self.timeout = timeout
        self.project: Optional[Project] = None
        self.language_server: Optional[SolidLanguageServer] = None
        
        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.total_symbols = 0
        
        # Results storage
        self.diagnostics: List[ErrorInfo] = []
        self.symbols: List[SymbolInfo] = []
        
        # Performance tracking
        self.performance_stats = {
            "setup_time": 0,
            "lsp_start_time": 0,
            "analysis_time": 0,
            "symbol_analysis_time": 0,
            "total_time": 0,
        }

        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        if self.language_server:
            try:
                self.language_server.stop()
                self.logger.info("✅ Language server stopped")
            except Exception as e:
                self.logger.warning(f"⚠️  Error stopping language server: {e}")
            finally:
                self.language_server = None

    def detect_language(self, repo_path: str) -> Language:
        """Detect the primary programming language."""
        self.logger.info("🔍 Detecting repository language...")
        
        # Count Python files
        python_files = 0
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "target", "build", "dist", "vendor"
            ]]
            
            for file in files:
                if file.endswith('.py'):
                    python_files += 1

        if python_files > 0:
            self.logger.info(f"✅ Detected Python ({python_files} .py files)")
            return Language.PYTHON
        else:
            self.logger.warning("No Python files found, defaulting to Python")
            return Language.PYTHON

    def setup_project(self, repo_path: str) -> Project:
        """Set up Serena project."""
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        language = self.detect_language(repo_path)
        self.logger.info(f"⚙️  Setting up project for {repo_path}")

        project_config = ProjectConfig(
            project_name=os.path.basename(os.path.abspath(repo_path)),
            language=language,
            ignored_paths=[
                ".git/**",
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/target/**",
                "**/build/**",
                "**/.venv/**",
                "**/venv/**",
                "**/dist/**",
            ],
            ignore_all_files_in_gitignore=True,
        )

        self.project = Project(repo_path, project_config)
        return self.project

    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """Start the language server."""
        self.logger.info("🔧 Starting language server...")
        
        try:
            self.language_server = project.create_language_server(
                log_level=logging.DEBUG if self.verbose else logging.WARNING,
                ls_timeout=self.timeout,
            )
            
            if not self.language_server:
                raise RuntimeError("Failed to create language server")

            self.language_server.start()
            
            # Wait for server to be ready
            time.sleep(2)
            
            if not self.language_server.is_running():
                raise RuntimeError("Language server failed to start")

            self.logger.info("✅ Language server started successfully")
            return self.language_server

        except Exception as e:
            self.logger.error(f"❌ Failed to start language server: {e}")
            raise

    def collect_diagnostics(self, project: Project, language_server: SolidLanguageServer) -> List[ErrorInfo]:
        """Collect diagnostics from all source files."""
        self.logger.info("🔍 Collecting diagnostics from all source files...")
        
        try:
            source_files = project.gather_source_files()
            self.total_files = len(source_files)
            self.logger.info(f"📊 Found {self.total_files} source files")

            if self.total_files == 0:
                self.logger.warning("⚠️  No source files found")
                return []

        except Exception as e:
            self.logger.error(f"❌ Failed to gather source files: {e}")
            return []

        all_diagnostics = []
        
        def analyze_file(file_path: str) -> List[ErrorInfo]:
            """Analyze a single file."""
            try:
                # Get diagnostics from LSP server
                lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)
                
                file_diagnostics = []
                for diag in lsp_diagnostics:
                    # Extract diagnostic information
                    range_info = diag.get("range", {})
                    start_pos = range_info.get("start", {})
                    line = start_pos.get("line", 0) + 1  # Convert to 1-based
                    column = start_pos.get("character", 0) + 1

                    # Map severity
                    severity_map = {
                        DiagnosticsSeverity.ERROR: "ERROR",
                        DiagnosticsSeverity.WARNING: "WARNING",
                        DiagnosticsSeverity.INFORMATION: "INFO",
                        DiagnosticsSeverity.HINT: "HINT",
                    }
                    
                    severity_value = diag.get("severity", DiagnosticsSeverity.ERROR)
                    severity = severity_map.get(severity_value, "UNKNOWN")

                    error_info = ErrorInfo(
                        file_path=file_path,
                        line=line,
                        column=column,
                        severity=severity,
                        message=diag.get("message", "No message"),
                        code=str(diag.get("code", "")),
                        source=diag.get("source", "lsp")
                    )
                    file_diagnostics.append(error_info)

                return file_diagnostics

            except Exception as e:
                self.logger.debug(f"Error analyzing {file_path}: {e}")
                return []

        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(analyze_file, file_path): file_path 
                             for file_path in source_files}

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    diagnostics = future.result()
                    all_diagnostics.extend(diagnostics)
                    self.processed_files += 1
                    
                    if self.verbose and diagnostics:
                        self.logger.debug(f"Found {len(diagnostics)} diagnostics in {os.path.basename(file_path)}")
                        
                except Exception as e:
                    self.failed_files += 1
                    self.logger.warning(f"⚠️  Failed to analyze {os.path.basename(file_path)}: {e}")

        self.total_diagnostics = len(all_diagnostics)
        self.diagnostics = all_diagnostics
        
        self.logger.info(f"✅ Analysis complete: {self.total_diagnostics} diagnostics from {self.processed_files} files")
        return all_diagnostics

    def collect_symbols(self, project: Project, language_server: SolidLanguageServer) -> List[SymbolInfo]:
        """Collect symbols if enabled."""
        if not self.enable_symbols:
            return []
            
        self.logger.info("🔍 Collecting symbols...")
        
        try:
            source_files = project.gather_source_files()
            all_symbols = []
            
            # Limit to first 20 files for performance
            for file_path in source_files[:20]:
                try:
                    symbols_response = language_server.request_text_document_symbols(file_path)
                    
                    for symbol_data in symbols_response:
                        symbol_info = SymbolInfo(
                            name=symbol_data.get("name", "unknown"),
                            kind=symbol_data.get("kind", SymbolKind.Variable),
                            location=symbol_data.get("location", {}),
                            container_name=symbol_data.get("containerName"),
                            detail=symbol_data.get("detail")
                        )
                        all_symbols.append(symbol_info)
                        
                except Exception as e:
                    self.logger.debug(f"Error getting symbols from {file_path}: {e}")
                    continue
            
            self.total_symbols = len(all_symbols)
            self.symbols = all_symbols
            self.logger.info(f"✅ Found {self.total_symbols} symbols")
            return all_symbols
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting symbols: {e}")
            return []

    def format_output(self, diagnostics: List[ErrorInfo]) -> str:
        """Format diagnostics for output."""
        if not diagnostics:
            return "ERRORS: 0\nNo errors found."

        # Sort by severity and file
        severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3}
        diagnostics.sort(key=lambda d: (
            severity_priority.get(d.severity, 4),
            d.file_path,
            d.line
        ))

        error_count = len(diagnostics)
        critical_count = len([d for d in diagnostics if d.severity == "ERROR"])
        warning_count = len([d for d in diagnostics if d.severity == "WARNING"])
        
        output_lines = [f"ERRORS: {error_count} [⚠️ Critical: {critical_count}] [👉 Major: {warning_count}]"]

        for i, diag in enumerate(diagnostics, 1):
            severity_icon = "⚠️" if diag.severity == "ERROR" else "👉" if diag.severity == "WARNING" else "🔍"
            
            # Clean message
            clean_message = diag.message.replace("\n", " ").strip()
            if len(clean_message) > 150:
                clean_message = clean_message[:147] + "..."

            # Format metadata
            metadata = [f"severity: {diag.severity}"]
            if diag.code:
                metadata.append(f"code: {diag.code}")
            if diag.source and diag.source != "lsp":
                metadata.append(f"source: {diag.source}")

            metadata_str = ", ".join(metadata)
            
            line = f"{i} {severity_icon}- {diag.file_path} / line {diag.line}, col {diag.column} - '{clean_message}' [{metadata_str}]"
            output_lines.append(line)

        return "\n".join(output_lines)

    def analyze_repository(self, repo_path: str, severity_filter: Optional[str] = None) -> str:
        """Main analysis function."""
        total_start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting Serena LSP Error Analysis")
            self.logger.info("=" * 60)
            self.logger.info(f"📁 Target: {repo_path}")
            self.logger.info(f"🔍 Severity filter: {severity_filter or 'ALL'}")
            self.logger.info(f"🔍 Symbol analysis: {'ENABLED' if self.enable_symbols else 'DISABLED'}")
            self.logger.info("=" * 60)

            # Step 1: Project setup
            setup_start = time.time()
            project = self.setup_project(repo_path)
            self.performance_stats["setup_time"] = time.time() - setup_start

            # Step 2: Language server startup
            lsp_start = time.time()
            language_server = self.start_language_server(project)
            self.performance_stats["lsp_start_time"] = time.time() - lsp_start

            # Step 3: Diagnostic collection
            analysis_start = time.time()
            diagnostics = self.collect_diagnostics(project, language_server)
            self.performance_stats["analysis_time"] = time.time() - analysis_start

            # Step 4: Symbol collection (if enabled)
            if self.enable_symbols:
                symbol_start = time.time()
                symbols = self.collect_symbols(project, language_server)
                self.performance_stats["symbol_analysis_time"] = time.time() - symbol_start

            # Step 5: Format results
            result = self.format_output(diagnostics)

            # Performance summary
            total_time = time.time() - total_start_time
            self.performance_stats["total_time"] = total_time

            self.logger.info("🎉 Analysis completed!")
            self.logger.info("=" * 60)
            self.logger.info(f"⏱️  Setup: {self.performance_stats['setup_time']:.2f}s")
            self.logger.info(f"🔧 LSP startup: {self.performance_stats['lsp_start_time']:.2f}s")
            self.logger.info(f"🔍 Analysis: {self.performance_stats['analysis_time']:.2f}s")
            if self.enable_symbols:
                self.logger.info(f"📊 Symbols: {self.performance_stats['symbol_analysis_time']:.2f}s ({self.total_symbols} found)")
            self.logger.info(f"🎯 Total: {total_time:.2f}s")
            self.logger.info("=" * 60)

            return result

        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            return f"ERRORS: 0\nAnalysis failed: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Serena LSP Error Analysis Tool - Real Implementation"
    )
    
    parser.add_argument("repository", help="Repository path to analyze")
    parser.add_argument("--severity", choices=["ERROR", "WARNING", "INFO", "HINT"], 
                       help="Filter diagnostics by severity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--symbols", action="store_true", help="Enable symbol analysis")
    parser.add_argument("--timeout", type=float, default=300, help="LSP timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()

    print("🚀 SERENA LSP ERROR ANALYSIS TOOL")
    print("=" * 60)

    try:
        with SerenaLSPAnalyzer(
            verbose=args.verbose,
            enable_symbols=args.symbols,
            timeout=args.timeout
        ) as analyzer:
            result = analyzer.analyze_repository(args.repository, args.severity)
            
            if args.json:
                # Create analysis results object
                analysis_results = AnalysisResults(
                    total_files=analyzer.total_files,
                    processed_files=analyzer.processed_files,
                    failed_files=analyzer.failed_files,
                    total_diagnostics=analyzer.total_diagnostics,
                    diagnostics=analyzer.diagnostics,
                    symbols=analyzer.symbols,
                    performance_stats=analyzer.performance_stats,
                    language_detected="Python",
                    repository_path=args.repository
                )
                print(json.dumps(analysis_results.to_dict(), indent=2, default=str))
            else:
                print("\n" + "=" * 60)
                print("📋 ANALYSIS RESULTS")
                print("=" * 60)
                print(result)
                print("=" * 60)

    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

