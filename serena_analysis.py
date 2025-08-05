#!/usr/bin/env python3
"""
Serena LSP Error Analysis Tool - Full Codebase Comprehensive Analysis

This tool analyzes ENTIRE repositories using Serena and SolidLSP to extract ALL LSP errors
and diagnostics from every source file in the codebase. It supports both local repositories 
and remote Git repositories via URL.

Features:
- Analyzes ALL source files without any limitations
- Real LSP integration using Serena Project and SolidLanguageServer
- Multi-language support with automatic detection
- Comprehensive error handling for large-scale analysis
- Progress tracking and performance optimization
- Exact output format: ERRORS: ['count'] followed by numbered error list

Usage:
    python serena_analysis.py <repo_url_or_path> [options]

Example:
    python serena_analysis.py https://github.com/user/repo.git
    python serena_analysis.py /path/to/local/repo --severity ERROR
    python serena_analysis.py . --verbose --timeout 600
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse

# Serena and SolidLSP imports
try:
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_types import Diagnostic, DiagnosticsSeverity
    from solidlsp.settings import SolidLSPSettings
    from solidlsp.ls import SolidLanguageServer
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Please ensure Serena and SolidLSP are properly installed.")
    print("Try: pip install -e . && pip install all required dependencies")
    sys.exit(1)


class SerenaAnalyzer:
    """
    Comprehensive LSP analyzer for entire codebases using Serena and SolidLSP.
    
    This class provides full codebase analysis capabilities without any file count
    limitations, using real LSP integration for accurate error detection.
    """
    
    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4):
        """
        Initialize the comprehensive analyzer.
        
        Args:
            verbose: Enable verbose logging and progress tracking
            timeout: Timeout for language server operations (increased default for large codebases)
            max_workers: Maximum number of concurrent workers for file processing
        """
        self.verbose = verbose
        self.timeout = timeout
        self.max_workers = max_workers
        self.temp_dir: Optional[str] = None
        self.project: Optional[Project] = None
        self.language_server: Optional[SolidLanguageServer] = None
        
        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.analysis_start_time = None
        self.lock = threading.Lock()
        
        # Set up comprehensive logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        if verbose:
            self.logger.info("🚀 Initializing Comprehensive Serena LSP Analyzer")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
        
        # Performance tracking
        self.performance_stats = {
            'clone_time': 0,
            'setup_time': 0,
            'lsp_start_time': 0,
            'analysis_time': 0,
            'total_time': 0
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources including language server and temporary directories."""
        try:
            if self.language_server and self.language_server.is_running():
                self.logger.info("Stopping language server...")
                self.language_server.stop()
                
            if self.temp_dir and os.path.exists(self.temp_dir):
                self.logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith('.git')
    
    def clone_repository(self, repo_url: str) -> str:
        """
        Clone a Git repository to a temporary directory.
        
        Args:
            repo_url: The Git repository URL
            
        Returns:
            Path to the cloned repository
            
        Raises:
            RuntimeError: If cloning fails
        """
        self.logger.info(f"Cloning repository: {repo_url}")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="serena_analysis_")
        repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            # Clone the repository
            cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")
                
            self.logger.info(f"Repository cloned to: {clone_path}")
            return clone_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git clone timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    def detect_language(self, repo_path: str) -> Language:
        """
        Detect the primary programming language of the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Detected Language enum value
        """
        self.logger.info("Detecting repository language...")
        
        # Language detection based on file extensions and common files
        # Using only languages available in the SolidLSP Language enum
        language_indicators = {
            Language.PYTHON: ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            Language.TYPESCRIPT: ['.ts', '.tsx', '.js', '.jsx', 'tsconfig.json', 'package.json', 'yarn.lock'],
            Language.JAVA: ['.java', 'pom.xml', 'build.gradle'],
            Language.CSHARP: ['.cs', '.csproj', '.sln'],
            Language.CPP: ['.cpp', '.cc', '.cxx', '.h', '.hpp', 'CMakeLists.txt'],
            Language.RUST: ['.rs', 'Cargo.toml'],
            Language.GO: ['.go', 'go.mod'],
            Language.PHP: ['.php', 'composer.json'],
            Language.RUBY: ['.rb', 'Gemfile'],
            Language.KOTLIN: ['.kt', '.kts'],
            Language.DART: ['.dart', 'pubspec.yaml'],
            Language.CLOJURE: ['.clj', '.cljs', '.cljc', 'project.clj'],
            Language.ELIXIR: ['.ex', '.exs', 'mix.exs'],
            Language.TERRAFORM: ['.tf', '.tfvars'],
        }
        
        file_counts = {lang: 0 for lang in language_indicators.keys()}
        
        # Walk through the repository and count file types
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
            
            for file in files:
                file_lower = file.lower()
                for lang, indicators in language_indicators.items():
                    if any(file_lower.endswith(ext) or file_lower == indicator 
                          for ext in indicators for indicator in [ext] if ext.startswith('.')):
                        file_counts[lang] += 1
                    elif any(file_lower == indicator 
                            for indicator in indicators if not indicator.startswith('.')):
                        file_counts[lang] += 5  # Weight config files higher
        
        # Find the language with the most files
        detected_lang = max(file_counts, key=file_counts.get)
        
        if file_counts[detected_lang] == 0:
            self.logger.warning("Could not detect language, defaulting to Python")
            detected_lang = Language.PYTHON
        
        self.logger.info(f"Detected language: {detected_lang.value}")
        return detected_lang
    
    def setup_project(self, repo_path: str, language: Optional[Language] = None) -> Project:
        """
        Set up a Serena project for the repository.
        
        Args:
            repo_path: Path to the repository
            language: Optional language override
            
        Returns:
            Configured Project instance
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path is not a directory: {repo_path}")
        
        # Detect language if not provided
        if language is None:
            language = self.detect_language(repo_path)
        
        self.logger.info(f"Setting up project for {repo_path} with language {language.value}")
        
        # Create project configuration
        project_config = ProjectConfig(
            project_name=os.path.basename(repo_path),
            language=language,
            ignored_paths=[
                '.git/**',
                '**/__pycache__/**',
                '**/node_modules/**',
                '**/target/**',
                '**/build/**',
                '**/.venv/**',
                '**/venv/**',
            ],
            ignore_all_files_in_gitignore=True
        )
        
        # Create and return project
        self.project = Project(repo_path, project_config)
        return self.project
    
    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """
        Start the language server for the project.
        
        Args:
            project: The Serena project
            
        Returns:
            Started SolidLanguageServer instance
        """
        self.logger.info("Starting language server...")
        
        try:
            # Create language server
            self.language_server = project.create_language_server(
                log_level=logging.DEBUG if self.verbose else logging.WARNING,
                ls_timeout=self.timeout
            )
            
            # Start the server
            self.language_server.start()
            
            if not self.language_server.is_running():
                raise RuntimeError("Language server failed to start")
            
            self.logger.info("Language server started successfully")
            return self.language_server
            
        except Exception as e:
            raise RuntimeError(f"Failed to start language server: {e}")
    
    def collect_diagnostics(self, project: Project, language_server: SolidLanguageServer, 
                          severity_filter: Optional[DiagnosticsSeverity] = None) -> List[Diagnostic]:
        """
        Collect diagnostics from ALL source files in the project with comprehensive analysis.
        
        This method processes every single source file without any limitations,
        using real LSP integration and parallel processing for efficiency.
        
        Args:
            project: The Serena project
            language_server: The language server instance
            severity_filter: Optional severity level filter
            
        Returns:
            List of ALL collected diagnostics from the entire codebase
        """
        self.analysis_start_time = time.time()
        self.logger.info("🔍 Starting comprehensive LSP analysis of ENTIRE codebase...")
        
        # Get ALL source files - no limitations
        try:
            source_files = project.gather_source_files()
            self.total_files = len(source_files)
            self.logger.info(f"📊 Found {self.total_files} source files to analyze")
            
            if self.total_files == 0:
                self.logger.warning("⚠️  No source files found in the project")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Failed to gather source files: {e}")
            return []
        
        # Initialize progress tracking
        all_diagnostics = []
        self.processed_files = 0
        self.failed_files = 0
        
        # Progress reporting setup
        progress_interval = max(1, self.total_files // 20)  # Report every 5%
        last_progress_report = 0
        
        self.logger.info(f"🚀 Processing ALL {self.total_files} files with {self.max_workers} workers...")
        
        # Process files with controlled concurrency for LSP stability
        def analyze_single_file(file_path: str) -> Tuple[str, List[Diagnostic], Optional[str]]:
            """Analyze a single file and return results."""
            try:
                # Get diagnostics for this file using real LSP
                diagnostics = language_server.request_text_document_diagnostics(file_path)
                
                # Filter by severity if specified
                if severity_filter is not None:
                    diagnostics = [d for d in diagnostics if d.get('severity') == severity_filter.value]
                
                return file_path, diagnostics, None
                
            except Exception as e:
                return file_path, [], str(e)
        
        # Use ThreadPoolExecutor for controlled parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {
                executor.submit(analyze_single_file, file_path): file_path 
                for file_path in source_files
            }
            
            # Process completed futures as they finish
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                
                try:
                    analyzed_file, diagnostics, error = future.result()
                    
                    with self.lock:
                        if error is None:
                            all_diagnostics.extend(diagnostics)
                            self.processed_files += 1
                            
                            if self.verbose and len(diagnostics) > 0:
                                self.logger.debug(f"✅ Found {len(diagnostics)} diagnostics in {os.path.basename(analyzed_file)}")
                        else:
                            self.failed_files += 1
                            self.logger.warning(f"⚠️  Failed to analyze {os.path.basename(analyzed_file)}: {error}")
                        
                        # Progress reporting
                        current_progress = self.processed_files + self.failed_files
                        if current_progress - last_progress_report >= progress_interval:
                            percentage = (current_progress / self.total_files) * 100
                            elapsed = time.time() - self.analysis_start_time
                            rate = current_progress / elapsed if elapsed > 0 else 0
                            eta = (self.total_files - current_progress) / rate if rate > 0 else 0
                            
                            self.logger.info(f"📈 Progress: {current_progress}/{self.total_files} ({percentage:.1f}%) "
                                           f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s")
                            last_progress_report = current_progress
                            
                except Exception as e:
                    with self.lock:
                        self.failed_files += 1
                        self.logger.error(f"❌ Unexpected error processing {os.path.basename(file_path)}: {e}")
        
        # Final statistics
        analysis_time = time.time() - self.analysis_start_time
        self.performance_stats['analysis_time'] = analysis_time
        self.total_diagnostics = len(all_diagnostics)
        
        self.logger.info("=" * 80)
        self.logger.info("📋 COMPREHENSIVE ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {self.processed_files}")
        self.logger.info(f"❌ Files failed: {self.failed_files}")
        self.logger.info(f"📊 Total files analyzed: {self.processed_files + self.failed_files}/{self.total_files}")
        self.logger.info(f"🔍 Total LSP diagnostics found: {self.total_diagnostics}")
        self.logger.info(f"⏱️  Analysis time: {analysis_time:.2f} seconds")
        self.logger.info(f"🚀 Processing rate: {(self.processed_files + self.failed_files) / analysis_time:.2f} files/sec")
        
        if self.failed_files > 0:
            failure_rate = (self.failed_files / self.total_files) * 100
            self.logger.warning(f"⚠️  Failure rate: {failure_rate:.1f}% ({self.failed_files}/{self.total_files} files)")
        
        self.logger.info("=" * 80)
        
        return all_diagnostics
    
    def format_diagnostic_output(self, diagnostics: List[Diagnostic]) -> str:
        """
        Format diagnostics in the requested output format.
        
        Args:
            diagnostics: List of diagnostics to format
            
        Returns:
            Formatted output string
        """
        if not diagnostics:
            return "ERRORS: ['0']\nNo errors found."
        
        # Count total errors
        error_count = len(diagnostics)
        
        # Start with the header
        output_lines = [f"ERRORS: ['{error_count}']"]
        
        # Format each diagnostic
        for i, diagnostic in enumerate(diagnostics, 1):
            # Extract location information
            range_info = diagnostic.get('range', {})
            start_pos = range_info.get('start', {})
            line = start_pos.get('line', 0) + 1  # LSP uses 0-based line numbers
            character = start_pos.get('character', 0) + 1  # LSP uses 0-based character numbers
            
            # Extract file path from URI
            uri = diagnostic.get('uri', '')
            if uri.startswith('file://'):
                file_path = uri[7:]  # Remove 'file://' prefix
                file_name = os.path.basename(file_path)
            else:
                file_name = 'unknown'
            
            # Get diagnostic details
            message = diagnostic.get('message', 'No message')
            severity = diagnostic.get('severity', DiagnosticsSeverity.ERROR.value)
            code = diagnostic.get('code', 'unknown')
            source = diagnostic.get('source', 'unknown')
            
            # Map severity to readable format
            severity_map = {
                DiagnosticsSeverity.ERROR.value: 'ERROR',
                DiagnosticsSeverity.WARNING.value: 'WARNING',
                DiagnosticsSeverity.INFORMATION.value: 'INFO',
                DiagnosticsSeverity.HINT.value: 'HINT'
            }
            severity_str = severity_map.get(severity, 'UNKNOWN')
            
            # Format the diagnostic line
            location = f"line {line}, col {character}"
            error_reason = message.replace('\n', ' ').strip()
            other_types = f"severity: {severity_str}, code: {code}, source: {source}"
            
            diagnostic_line = f"{i}. '{location}' '{file_name}' '{error_reason}' '{other_types}'"
            output_lines.append(diagnostic_line)
        
        return '\n'.join(output_lines)
    
    def analyze_repository(self, repo_url_or_path: str, 
                          severity_filter: Optional[str] = None,
                          language_override: Optional[str] = None) -> str:
        """
        Main comprehensive analysis function that orchestrates the entire process.
        
        This method performs full codebase analysis without any limitations,
        processing every single source file using real LSP integration.
        
        Args:
            repo_url_or_path: Repository URL or local path
            severity_filter: Optional severity filter ('ERROR', 'WARNING', 'INFO', 'HINT')
            language_override: Optional language override
            
        Returns:
            Formatted analysis results with complete error listing
        """
        total_start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting COMPREHENSIVE LSP Error Analysis")
            self.logger.info("=" * 80)
            self.logger.info(f"📁 Target: {repo_url_or_path}")
            self.logger.info(f"🔍 Severity filter: {severity_filter or 'ALL'}")
            self.logger.info(f"🌐 Language override: {language_override or 'AUTO-DETECT'}")
            self.logger.info("=" * 80)
            
            # Step 1: Repository handling
            clone_start = time.time()
            if self.is_git_url(repo_url_or_path):
                self.logger.info("📥 Cloning remote repository...")
                repo_path = self.clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
                if not os.path.exists(repo_path):
                    raise FileNotFoundError(f"Local path does not exist: {repo_path}")
                self.logger.info(f"📂 Using local repository: {repo_path}")
            
            self.performance_stats['clone_time'] = time.time() - clone_start
            
            # Step 2: Parse configuration
            language = None
            if language_override:
                try:
                    language = Language(language_override.lower())
                    self.logger.info(f"🎯 Language override: {language.value}")
                except ValueError:
                    self.logger.warning(f"⚠️  Invalid language '{language_override}', will auto-detect")
            
            severity = None
            if severity_filter:
                severity_map = {
                    'ERROR': DiagnosticsSeverity.ERROR,
                    'WARNING': DiagnosticsSeverity.WARNING,
                    'INFO': DiagnosticsSeverity.INFORMATION,
                    'HINT': DiagnosticsSeverity.HINT
                }
                severity = severity_map.get(severity_filter.upper())
                if severity is None:
                    self.logger.warning(f"⚠️  Invalid severity '{severity_filter}', showing all diagnostics")
                else:
                    self.logger.info(f"🔍 Filtering by severity: {severity_filter.upper()}")
            
            # Step 3: Project setup
            setup_start = time.time()
            self.logger.info("⚙️  Setting up Serena project...")
            project = self.setup_project(repo_path, language)
            self.performance_stats['setup_time'] = time.time() - setup_start
            
            # Step 4: Language server initialization
            lsp_start = time.time()
            self.logger.info("🔧 Starting SolidLSP language server...")
            language_server = self.start_language_server(project)
            
            # Give the language server time to fully initialize for large codebases
            initialization_time = 5 if self.total_files > 100 else 2
            self.logger.info(f"⏳ Allowing {initialization_time}s for LSP initialization...")
            time.sleep(initialization_time)
            
            self.performance_stats['lsp_start_time'] = time.time() - lsp_start
            
            # Step 5: Comprehensive diagnostic collection
            self.logger.info("🔍 Beginning comprehensive LSP diagnostic collection...")
            diagnostics = self.collect_diagnostics(project, language_server, severity)
            
            # Step 6: Format results
            self.logger.info("📋 Formatting comprehensive results...")
            result = self.format_diagnostic_output(diagnostics)
            
            # Final performance summary
            total_time = time.time() - total_start_time
            self.performance_stats['total_time'] = total_time
            
            self.logger.info("🎉 COMPREHENSIVE ANALYSIS COMPLETED SUCCESSFULLY!")
            self.logger.info("=" * 80)
            self.logger.info("⏱️  PERFORMANCE SUMMARY:")
            self.logger.info(f"   📥 Repository setup: {self.performance_stats['clone_time']:.2f}s")
            self.logger.info(f"   ⚙️  Project configuration: {self.performance_stats['setup_time']:.2f}s")
            self.logger.info(f"   🔧 LSP server startup: {self.performance_stats['lsp_start_time']:.2f}s")
            self.logger.info(f"   🔍 Diagnostic analysis: {self.performance_stats['analysis_time']:.2f}s")
            self.logger.info(f"   🎯 Total execution time: {total_time:.2f}s")
            
            if self.total_files > 0:
                self.logger.info(f"   📊 Average time per file: {self.performance_stats['analysis_time'] / self.total_files:.3f}s")
            
            self.logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ COMPREHENSIVE ANALYSIS FAILED: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            return f"ERRORS: ['0']\nComprehensive analysis failed: {e}"


def main():
    """Main entry point for comprehensive LSP error analysis."""
    parser = argparse.ArgumentParser(
        description="Comprehensive LSP Error Analysis Tool - Analyzes ENTIRE codebases using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 COMPREHENSIVE ANALYSIS EXAMPLES:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR --verbose
  %(prog)s . --timeout 600 --max-workers 8 --language python
  %(prog)s https://github.com/Zeeeepa/graph-sitter --verbose

📊 OUTPUT FORMAT:
  ERRORS: ['count']
  1. 'location' 'file' 'error reason' 'other types'
  2. 'location' 'file' 'error reason' 'other types'
  ...

⚡ PERFORMANCE TIPS:
  - Use --max-workers to control parallel processing
  - Increase --timeout for very large repositories
  - Use --severity ERROR to focus on critical issues
  - Enable --verbose for detailed progress tracking
        """
    )
    
    parser.add_argument(
        'repository',
        help='Repository URL or local path to analyze (analyzes ALL source files)'
    )
    
    parser.add_argument(
        '--severity',
        choices=['ERROR', 'WARNING', 'INFO', 'HINT'],
        help='Filter diagnostics by severity level (default: show all diagnostics)'
    )
    
    parser.add_argument(
        '--language',
        help='Override automatic language detection (e.g., python, javascript, java, typescript)'
    )
    
    parser.add_argument(
        '--timeout',
        type=float,
        default=600,
        help='Timeout for LSP operations in seconds (default: 600 for large codebases)'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Maximum number of parallel workers for file processing (default: 4)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging with progress tracking and performance metrics'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.max_workers < 1:
        print("❌ Error: --max-workers must be at least 1")
        sys.exit(1)
    
    if args.timeout < 60:
        print("⚠️  Warning: Timeout less than 60 seconds may cause issues with large repositories")
    
    print("🚀 COMPREHENSIVE LSP ERROR ANALYSIS TOOL")
    print("=" * 80)
    print("📋 Configuration:")
    print(f"   📁 Repository: {args.repository}")
    print(f"   🔍 Severity filter: {args.severity or 'ALL'}")
    print(f"   🌐 Language: {args.language or 'AUTO-DETECT'}")
    print(f"   ⏱️  Timeout: {args.timeout}s")
    print(f"   👥 Max workers: {args.max_workers}")
    print(f"   📊 Verbose: {args.verbose}")
    print("=" * 80)
    
    # Run the comprehensive analysis
    try:
        with SerenaAnalyzer(
            verbose=args.verbose, 
            timeout=args.timeout,
            max_workers=args.max_workers
        ) as analyzer:
            result = analyzer.analyze_repository(
                args.repository,
                severity_filter=args.severity,
                language_override=args.language
            )
            
            # Output the results
            print("\n" + "=" * 80)
            print("📋 COMPREHENSIVE ANALYSIS RESULTS")
            print("=" * 80)
            print(result)
            print("=" * 80)
            
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
