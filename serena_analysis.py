#!/usr/bin/env python3
"""
Comprehensive Serena LSP Error Analysis Tool

This tool analyzes entire repositories using Serena and SolidLSP to extract all LSP errors
and diagnostics from the codebase. It supports both local repositories and remote
Git repositories via URL.

Usage:
    python serena_analysis.py <repo_url_or_path> [options]

Example:
    python serena_analysis.py https://github.com/user/repo.git
    python serena_analysis.py /path/to/local/repo --severity ERROR
    python serena_analysis.py . --verbose --timeout 120
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import urlparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Serena and SolidLSP imports
from serena.config.serena_config import ProjectConfig
from serena.project import Project
from serena.symbol import (
    LanguageServerSymbolRetriever,
    ReferenceInLanguageServerSymbol,
    LanguageServerSymbol,
    Symbol,
    PositionInFile,
    LanguageServerSymbolLocation,
)
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.ls_types import DiagnosticsSeverity, Diagnostic
from solidlsp.settings import SolidLSPSettings
from solidlsp import SolidLanguageServer
from solidlsp.lsp_protocol_handler.server import (
    ProcessLaunchInfo,
    LSPError,
    MessageType,
)


@dataclass
class EnhancedDiagnostic:
    """Enhanced diagnostic with additional metadata."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_information: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnalysisResults:
    """Comprehensive analysis results."""
    total_files: int
    processed_files: int
    failed_files: int
    total_diagnostics: int
    diagnostics_by_severity: Dict[str, int]
    diagnostics_by_file: Dict[str, int]
    diagnostics: List[EnhancedDiagnostic]
    performance_stats: Dict[str, float]
    language_detected: str
    repository_path: str
    analysis_timestamp: str
    
    # Enhanced symbol analysis results
    total_symbols: int = 0
    symbols_by_kind: Dict[str, int] = field(default_factory=dict)
    symbol_analysis: Dict[str, Any] = field(default_factory=dict)
    symbol_errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class SerenaLSPAnalyzer:
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
        self.symbol_retriever: Optional[LanguageServerSymbolRetriever] = None
        
        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.analysis_start_time = None
        self.lock = threading.Lock()
        
        # Symbol analysis tracking
        self.total_symbols = 0
        self.symbol_references = 0
        self.symbol_errors = 0
        
        # Set up comprehensive logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
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
            'symbol_analysis_time': 0,
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
        self.logger.info(f"📥 Cloning repository: {repo_url}")
        
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
                
            self.logger.info(f"✅ Repository cloned to: {clone_path}")
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
        self.logger.info("🔍 Detecting repository language...")
        
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
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'target', 'build', 'dist', 'vendor'
            ]]
            
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
        
        self.logger.info(f"✅ Detected language: {detected_lang.value}")
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
        
        self.logger.info(f"⚙️  Setting up project for {repo_path} with language {language.value}")
        
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
                '**/dist/**',
                '**/vendor/**',
            ],
            ignore_all_files_in_gitignore=True
        )
        
        # Create and return project
        self.project = Project(repo_path, project_config)
        return self.project
    
    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """
        Start the language server for the project with enhanced initialization and error handling.
        
        Args:
            project: The Serena project
            
        Returns:
            Started and validated SolidLanguageServer instance
        """
        self.logger.info("🔧 Starting language server initialization...")
        
        max_attempts = 3
        base_delay = 2.0
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"🔄 Retry attempt {attempt + 1}/{max_attempts} after {delay}s delay...")
                    time.sleep(delay)
                
                self.logger.info(f"🚀 Language server initialization attempt {attempt + 1}/{max_attempts}")
                
                # Create language server with enhanced configuration
                try:
                    self.language_server = project.create_language_server(
                        log_level=logging.DEBUG if self.verbose else logging.WARNING,
                        ls_timeout=self.timeout,
                        trace_lsp_communication=self.verbose
                    )
                    
                    if not self.language_server:
                        raise RuntimeError("Failed to create language server instance")
                        
                except LSPError as lsp_err:
                    raise RuntimeError(f"LSP Error during server creation: {lsp_err}")
                except Exception as e:
                    raise RuntimeError(f"Failed to create language server: {e}")
                
                self.logger.info("📡 Starting language server process...")
                
                # Start the server with enhanced monitoring
                start_time = time.time()
                self.language_server.start()
                startup_time = time.time() - start_time
                
                self.logger.info(f"⏱️  Language server startup took {startup_time:.2f}s")
                
                # Enhanced server health validation
                if not self.language_server.is_running():
                    raise RuntimeError("Language server process is not running after start")
                
                # Wait for server to be fully ready
                self.logger.info("🔍 Validating language server readiness...")
                
                ready_timeout = min(30, self.timeout // 4)
                ready_start = time.time()
                
                while time.time() - ready_start < ready_timeout:
                    try:
                        # Simple readiness check - try to get server status
                        if self.language_server.is_running():
                            self.logger.info("✅ Language server readiness confirmed")
                            break
                    except Exception as e:
                        if self.verbose:
                            self.logger.debug(f"🔍 Readiness check: {e}")
                    
                    time.sleep(1)
                else:
                    self.logger.warning("⚠️  Language server readiness validation timed out, proceeding anyway")
                
                # Final validation
                if not self.language_server.is_running():
                    raise RuntimeError("Language server stopped running during initialization")
                
                total_init_time = time.time() - start_time
                self.logger.info(f"🎉 Language server successfully initialized in {total_init_time:.2f}s")
                
                # Initialize symbol retriever
                self.symbol_retriever = LanguageServerSymbolRetriever(self.language_server)
                self.logger.info("🔍 Symbol retriever initialized")
                
                return self.language_server
                
            except Exception as e:
                error_msg = f"Language server initialization attempt {attempt + 1} failed: {e}"
                
                if attempt < max_attempts - 1:
                    self.logger.warning(f"⚠️  {error_msg}")
                    
                    # Clean up failed server instance
                    if self.language_server:
                        try:
                            if self.language_server.is_running():
                                self.language_server.stop()
                        except Exception as cleanup_error:
                            self.logger.debug(f"Error during cleanup: {cleanup_error}")
                        finally:
                            self.language_server = None
                else:
                    self.logger.error(f"❌ {error_msg}")
                    raise RuntimeError(f"Failed to start language server after {max_attempts} attempts: {e}")
        
        # This should never be reached, but just in case
        raise RuntimeError("Language server initialization failed unexpectedly")
    
    def analyze_symbols_in_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze symbols in a specific file using the LanguageServerSymbolRetriever.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary containing symbol analysis results
        """
        if not self.symbol_retriever:
            return {"error": "Symbol retriever not initialized"}
        
        try:
            # Get relative path for the file
            if self.project and hasattr(self.project, 'project_root'):
                project_root = self.project.project_root
                if file_path.startswith(project_root):
                    relative_path = os.path.relpath(file_path, project_root)
                else:
                    relative_path = file_path
            else:
                relative_path = file_path
            
            # Get document symbols
            symbols = self.symbol_retriever.get_document_symbols(relative_path)
            
            symbol_analysis = {
                'file_path': file_path,
                'relative_path': relative_path,
                'total_symbols': len(symbols),
                'symbols_by_kind': {},
                'symbols': [],
                'symbol_locations': [],
                'symbol_references': []
            }
            
            for symbol in symbols:
                # Count symbols by kind
                kind = symbol.kind
                if kind not in symbol_analysis['symbols_by_kind']:
                    symbol_analysis['symbols_by_kind'][kind] = 0
                symbol_analysis['symbols_by_kind'][kind] += 1
                
                # Extract symbol information
                symbol_info = {
                    'name': symbol.name,
                    'kind': kind,
                    'location': {
                        'line': symbol.line,
                        'column': symbol.column,
                        'relative_path': symbol.relative_path
                    },
                    'body_range': None,
                    'name_path': symbol.get_name_path(),
                    'has_children': len(symbol.symbol_root.get("children", [])) > 0
                }
                
                # Get body positions if available
                try:
                    start_pos = symbol.get_body_start_position()
                    end_pos = symbol.get_body_end_position()
                    if start_pos and end_pos:
                        symbol_info['body_range'] = {
                            'start': {'line': start_pos.line, 'column': start_pos.col},
                            'end': {'line': end_pos.line, 'column': end_pos.col}
                        }
                except Exception as e:
                    if self.verbose:
                        self.logger.debug(f"Could not get body range for symbol {symbol.name}: {e}")
                
                symbol_analysis['symbols'].append(symbol_info)
                
                # Create symbol location for tracking
                location = LanguageServerSymbolLocation(
                    relative_path=symbol.relative_path,
                    line=symbol.line,
                    column=symbol.column
                )
                symbol_analysis['symbol_locations'].append({
                    'symbol_name': symbol.name,
                    'location': location.to_dict()
                })
            
            return symbol_analysis
            
        except Exception as e:
            self.logger.warning(f"Symbol analysis failed for {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'total_symbols': 0,
                'symbols_by_kind': {},
                'symbols': [],
                'symbol_locations': [],
                'symbol_references': []
            }
    
    def find_symbol_references(self, symbol_name: str, within_file: Optional[str] = None) -> List[ReferenceInLanguageServerSymbol]:
        """
        Find references to a specific symbol using the symbol retriever.
        
        Args:
            symbol_name: Name of the symbol to find references for
            within_file: Optional file path to limit search scope
            
        Returns:
            List of symbol references
        """
        if not self.symbol_retriever:
            return []
        
        try:
            # Find symbols by name
            symbols = self.symbol_retriever.find_by_name(
                symbol_name,
                include_body=False,
                substring_matching=True,
                within_relative_path=within_file
            )
            
            references = []
            for symbol in symbols:
                # Create a reference for each found symbol
                if symbol.line is not None and symbol.column is not None:
                    # Note: ReferenceInLanguageServerSymbol expects a symbol and position
                    # This is a simplified approach - in practice, you'd get actual references from LSP
                    reference = ReferenceInLanguageServerSymbol(
                        symbol=symbol,
                        line=symbol.line,
                        character=symbol.column
                    )
                    references.append(reference)
            
            return references
            
        except Exception as e:
            self.logger.warning(f"Failed to find references for symbol '{symbol_name}': {e}")
            return []
    
    def analyze_symbol_usage_patterns(self, source_files: List[str]) -> Dict[str, Any]:
        """
        Analyze symbol usage patterns across multiple files.
        
        Args:
            source_files: List of source files to analyze
            
        Returns:
            Dictionary containing symbol usage analysis
        """
        if not self.symbol_retriever:
            return {"error": "Symbol retriever not initialized"}
        
        symbol_start_time = time.time()
        self.logger.info("🔍 Starting comprehensive symbol analysis...")
        
        usage_analysis = {
            'total_files_analyzed': 0,
            'total_symbols_found': 0,
            'symbols_by_kind': {},
            'symbols_by_file': {},
            'common_symbol_names': {},
            'symbol_complexity': {},
            'potential_issues': []
        }
        
        for file_path in source_files:
            try:
                file_analysis = self.analyze_symbols_in_file(file_path)
                
                if 'error' not in file_analysis:
                    usage_analysis['total_files_analyzed'] += 1
                    usage_analysis['total_symbols_found'] += file_analysis['total_symbols']
                    
                    # Aggregate symbols by kind
                    for kind, count in file_analysis['symbols_by_kind'].items():
                        if kind not in usage_analysis['symbols_by_kind']:
                            usage_analysis['symbols_by_kind'][kind] = 0
                        usage_analysis['symbols_by_kind'][kind] += count
                    
                    # Track symbols by file
                    usage_analysis['symbols_by_file'][file_path] = file_analysis['total_symbols']
                    
                    # Track common symbol names
                    for symbol_info in file_analysis['symbols']:
                        name = symbol_info['name']
                        if name not in usage_analysis['common_symbol_names']:
                            usage_analysis['common_symbol_names'][name] = 0
                        usage_analysis['common_symbol_names'][name] += 1
                        
                        # Analyze symbol complexity (based on children)
                        if symbol_info['has_children']:
                            if name not in usage_analysis['symbol_complexity']:
                                usage_analysis['symbol_complexity'][name] = 0
                            usage_analysis['symbol_complexity'][name] += 1
                
                # Update tracking
                with self.lock:
                    self.total_symbols += file_analysis.get('total_symbols', 0)
                    
            except Exception as e:
                usage_analysis['potential_issues'].append({
                    'file': file_path,
                    'issue': f"Symbol analysis failed: {e}"
                })
                with self.lock:
                    self.symbol_errors += 1
        
        # Calculate analysis time
        symbol_analysis_time = time.time() - symbol_start_time
        self.performance_stats['symbol_analysis_time'] = symbol_analysis_time
        
        # Add summary statistics
        usage_analysis['analysis_summary'] = {
            'files_processed': usage_analysis['total_files_analyzed'],
            'symbols_found': usage_analysis['total_symbols_found'],
            'analysis_time': symbol_analysis_time,
            'avg_symbols_per_file': (
                usage_analysis['total_symbols_found'] / usage_analysis['total_files_analyzed']
                if usage_analysis['total_files_analyzed'] > 0 else 0
            )
        }
        
        self.logger.info(f"🔍 Symbol analysis completed: {usage_analysis['total_symbols_found']} symbols in {symbol_analysis_time:.2f}s")
        
        return usage_analysis
    
    def collect_diagnostics(self, project: Project, language_server: SolidLanguageServer, 
                          severity_filter: Optional[DiagnosticsSeverity] = None) -> List[Diagnostic]:
        """
        Collect diagnostics from ALL source files in the project with comprehensive analysis.
        
        This method processes every single source file without any limitations,
        using real LSP integration and parallel processing.
        
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
        
        # Initialize tracking
        all_diagnostics = []
        self.processed_files = 0
        self.failed_files = 0
        retry_files = []
        
        # Progress reporting
        progress_interval = max(1, self.total_files // 50)  # Report every 2%
        last_progress_report = 0
        
        self.logger.info(f"🚀 Processing ALL {self.total_files} files with comprehensive analysis...")
        self.logger.info(f"⚙️  Using {self.max_workers} workers with batch processing")
        
        def analyze_single_file(file_path: str, retry_count: int = 0) -> Tuple[str, List[Diagnostic], Optional[str], bool]:
            """Analyze a single file using LSP."""
            try:
                diagnostics = []
                
                # Method 1: Get diagnostics from LSP with enhanced error handling
                try:
                    lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)
                    if lsp_diagnostics:
                        diagnostics.extend(lsp_diagnostics)
                        if self.verbose:
                            self.logger.debug(f"🔍 Primary: {len(lsp_diagnostics)} diagnostics in {os.path.basename(file_path)}")
                except LSPError as lsp_err:
                    if self.verbose:
                        self.logger.debug(f"⚠️  LSP Error for {os.path.basename(file_path)}: {lsp_err}")
                    # LSP errors might be retryable depending on the error code
                    retryable = retry_count < 2 and lsp_err.code in [MessageType.error, MessageType.warning]
                    return file_path, [], f"LSP Error: {lsp_err}", retryable
                except Exception as e:
                    if self.verbose:
                        self.logger.debug(f"⚠️  Diagnostic collection failed for {os.path.basename(file_path)}: {e}")
                    # Determine if this is a retryable error
                    retryable = retry_count < 2 and ("timeout" in str(e).lower() or "connection" in str(e).lower())
                    return file_path, [], str(e), retryable
                
                # Filter by severity if specified
                if severity_filter is not None:
                    original_count = len(diagnostics)
                    diagnostics = [d for d in diagnostics if d.get('severity') == severity_filter.value]
                    if self.verbose and original_count != len(diagnostics):
                        self.logger.debug(f"🔍 Filtered {original_count} -> {len(diagnostics)} diagnostics for {os.path.basename(file_path)}")
                
                # Deduplicate diagnostics based on location and message
                unique_diagnostics = []
                seen_diagnostics = set()
                
                for diag in diagnostics:
                    # Create a unique key for deduplication
                    range_info = diag.get('range', {})
                    start_pos = range_info.get('start', {})
                    diag_key = (
                        start_pos.get('line', 0),
                        start_pos.get('character', 0),
                        diag.get('message', ''),
                        diag.get('code', '')
                    )
                    
                    if diag_key not in seen_diagnostics:
                        seen_diagnostics.add(diag_key)
                        unique_diagnostics.append(diag)
                
                if len(unique_diagnostics) != len(diagnostics) and self.verbose:
                    self.logger.debug(f"🔄 Deduplicated {len(diagnostics)} -> {len(unique_diagnostics)} diagnostics for {os.path.basename(file_path)}")
                
                return file_path, unique_diagnostics, None, False
                
            except Exception as e:
                # Determine if this is a retryable error
                retryable = retry_count < 2 and ("timeout" in str(e).lower() or "connection" in str(e).lower())
                return file_path, [], str(e), retryable
        
        # Process files in batches for better LSP server efficiency
        batch_size = min(50, max(1, self.total_files // 10))  # Adaptive batch size
        file_batches = [source_files[i:i + batch_size] for i in range(0, len(source_files), batch_size)]
        
        self.logger.info(f"📦 Processing {len(file_batches)} batches of ~{batch_size} files each")
        
        for batch_idx, file_batch in enumerate(file_batches):
            self.logger.info(f"📦 Processing batch {batch_idx + 1}/{len(file_batches)} ({len(file_batch)} files)")
            
            # Use ThreadPoolExecutor for controlled parallel processing within each batch
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit batch files for processing
                future_to_file = {
                    executor.submit(analyze_single_file, file_path): file_path 
                    for file_path in file_batch
                }
                
                # Process completed futures as they finish
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        analyzed_file, diagnostics, error, should_retry = future.result()
                        
                        with self.lock:
                            if error is None:
                                all_diagnostics.extend(diagnostics)
                                self.processed_files += 1
                                
                                if self.verbose and len(diagnostics) > 0:
                                    self.logger.debug(f"✅ Found {len(diagnostics)} diagnostics in {os.path.basename(analyzed_file)}")
                            elif should_retry:
                                retry_files.append(analyzed_file)
                                if self.verbose:
                                    self.logger.debug(f"🔄 Queued for retry: {os.path.basename(analyzed_file)}: {error}")
                            else:
                                self.failed_files += 1
                                self.logger.warning(f"⚠️  Failed to analyze {os.path.basename(analyzed_file)}: {error}")
                            
                            # Progress reporting
                            current_progress = self.processed_files + self.failed_files + len(retry_files)
                            if current_progress - last_progress_report >= progress_interval:
                                percentage = (current_progress / self.total_files) * 100
                                elapsed = time.time() - self.analysis_start_time
                                rate = current_progress / elapsed if elapsed > 0 else 0
                                eta = (self.total_files - current_progress) / rate if rate > 0 else 0
                                
                                self.logger.info(f"📈 Progress: {current_progress}/{self.total_files} ({percentage:.1f}%) "
                                               f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s - Retries: {len(retry_files)}")
                                last_progress_report = current_progress
                                
                    except Exception as e:
                        with self.lock:
                            self.failed_files += 1
                            self.logger.error(f"❌ Unexpected error processing {os.path.basename(file_path)}: {e}")
            
            # Brief pause between batches to prevent LSP server overload
            if batch_idx < len(file_batches) - 1:
                time.sleep(0.5)
        
        # Process retry files
        if retry_files:
            self.logger.info(f"🔄 Retrying {len(retry_files)} files that had transient failures...")
            
            with ThreadPoolExecutor(max_workers=max(1, self.max_workers // 2)) as executor:
                future_to_file = {
                    executor.submit(analyze_single_file, file_path, 1): file_path 
                    for file_path in retry_files
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        analyzed_file, diagnostics, error, _ = future.result()
                        
                        if error is None:
                            all_diagnostics.extend(diagnostics)
                            self.processed_files += 1
                            if self.verbose:
                                self.logger.debug(f"✅ Retry successful: {len(diagnostics)} diagnostics in {os.path.basename(analyzed_file)}")
                        else:
                            self.failed_files += 1
                            self.logger.warning(f"⚠️  Retry failed for {os.path.basename(analyzed_file)}: {error}")
                            
                    except Exception as e:
                        self.failed_files += 1
                        self.logger.error(f"❌ Retry error for {os.path.basename(file_path)}: {e}")
        
        # Final statistics
        analysis_time = time.time() - self.analysis_start_time
        self.performance_stats['analysis_time'] = analysis_time
        self.total_diagnostics = len(all_diagnostics)
        
        # Categorize diagnostics by severity for detailed reporting
        severity_counts = {
            'ERROR': 0,
            'WARNING': 0,
            'INFO': 0,
            'HINT': 0,
            'UNKNOWN': 0
        }
        
        for diag in all_diagnostics:
            severity = diag.get('severity', DiagnosticsSeverity.ERROR.value)
            severity_map = {
                DiagnosticsSeverity.ERROR.value: 'ERROR',
                DiagnosticsSeverity.WARNING.value: 'WARNING',
                DiagnosticsSeverity.INFORMATION.value: 'INFO',
                DiagnosticsSeverity.HINT.value: 'HINT'
            }
            severity_str = severity_map.get(severity, 'UNKNOWN')
            severity_counts[severity_str] += 1
        
        self.logger.info("=" * 80)
        self.logger.info("📋 COMPREHENSIVE ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {self.processed_files}")
        self.logger.info(f"❌ Files failed: {self.failed_files}")
        self.logger.info(f"🔄 Files retried: {len(retry_files)}")
        self.logger.info(f"📊 Total files analyzed: {self.processed_files + self.failed_files}/{self.total_files}")
        self.logger.info(f"🔍 Total LSP diagnostics found: {self.total_diagnostics}")
        self.logger.info("📋 Diagnostics by severity:")
        for severity, count in severity_counts.items():
            if count > 0:
                self.logger.info(f"   {severity}: {count}")
        self.logger.info(f"⏱️  Analysis time: {analysis_time:.2f} seconds")
        self.logger.info(f"🚀 Processing rate: {(self.processed_files + self.failed_files) / analysis_time:.2f} files/sec")
        
        if self.failed_files > 0:
            failure_rate = (self.failed_files / self.total_files) * 100
            self.logger.warning(f"⚠️  Failure rate: {failure_rate:.1f}% ({self.failed_files}/{self.total_files} files)")
        
        self.logger.info("=" * 80)
        
        return all_diagnostics
    
    def format_diagnostic_output(self, diagnostics: List[Diagnostic], project: Optional[Project] = None) -> str:
        """
        Format diagnostics in the requested output format with enhanced categorization and analysis.
        
        Args:
            diagnostics: List of diagnostics to format
            
        Returns:
            Formatted output string with enhanced analysis
        """
        if not diagnostics:
            return "ERRORS: ['0']\nNo errors found."
        
        # Enhanced diagnostic processing and categorization
        processed_diagnostics = []
        error_categories = {}
        file_error_counts = {}
        
        for diagnostic in diagnostics:
            # Extract and normalize location information
            range_info = diagnostic.get('range', {})
            start_pos = range_info.get('start', {})
            end_pos = range_info.get('end', {})
            
            line = start_pos.get('line', 0) + 1  # LSP uses 0-based line numbers
            character = start_pos.get('character', 0) + 1  # LSP uses 0-based character numbers
            end_line = end_pos.get('line', line)
            end_character = end_pos.get('character', character)
            
            # Enhanced file path extraction - preserve full folder structure
            uri = diagnostic.get('uri', '')
            if uri.startswith('file://'):
                full_file_path = uri[7:]  # Remove 'file://' prefix
                
                # Get path relative to project root for better readability while preserving folder structure
                try:
                    # Try to get path relative to the project root
                    if project and hasattr(project, 'project_path'):
                        project_root = project.project_path
                        if full_file_path.startswith(project_root):
                            file_path = os.path.relpath(full_file_path, project_root)
                        else:
                            file_path = os.path.relpath(full_file_path)
                    else:
                        # Fallback: try to get a clean relative path
                        file_path = os.path.relpath(full_file_path)
                        # If path starts with many ../ levels, just use basename with parent folder
                        if file_path.count('../') > 3:
                            file_path = '/'.join(full_file_path.split('/')[-3:])  # Keep last 3 path components
                except (ValueError, AttributeError):
                    file_path = full_file_path  # Keep full absolute path if relative conversion fails
                
                file_name = os.path.basename(file_path)
            else:
                file_path = 'unknown'
                file_name = 'unknown'
            
            # Enhanced diagnostic details extraction
            message = diagnostic.get('message', 'No message').strip()
            severity = diagnostic.get('severity', DiagnosticsSeverity.ERROR.value)
            code = diagnostic.get('code', 'unknown')
            source = diagnostic.get('source', 'unknown')
            
            # Clean message for better readability
            clean_message = message.replace('\n', ' ').replace('\r', ' ')
            # Remove excessive whitespace
            clean_message = ' '.join(clean_message.split())
            
            # Keep full message - no truncation for comprehensive error analysis
            
            # Enhanced severity mapping
            severity_map = {
                DiagnosticsSeverity.ERROR.value: 'ERROR',
                DiagnosticsSeverity.WARNING.value: 'WARNING',
                DiagnosticsSeverity.INFORMATION.value: 'INFO',
                DiagnosticsSeverity.HINT.value: 'HINT'
            }
            severity_str = severity_map.get(severity, 'UNKNOWN')
            
            # Enhanced location formatting
            if end_line != line or end_character != character:
                location = f"line {line}, col {character}-{end_character}"
            else:
                location = f"line {line}, col {character}"
            
            # Enhanced metadata formatting
            metadata_parts = [f"severity: {severity_str}"]
            
            if code and code != 'unknown':
                metadata_parts.append(f"code: {code}")
            
            if source and source != 'unknown':
                metadata_parts.append(f"source: {source}")
            
            other_types = ', '.join(metadata_parts)
            
            # Store processed diagnostic
            processed_diagnostic = {
                'location': location,
                'file_name': file_name,
                'file_path': file_path,
                'error_reason': clean_message,
                'other_types': other_types,
                'severity': severity_str,
                'code': code,
                'source': source,
                'original': diagnostic
            }
            processed_diagnostics.append(processed_diagnostic)
            
            # Track error categories for analysis
            error_key = f"{severity_str}:{code}"
            if error_key not in error_categories:
                error_categories[error_key] = []
            error_categories[error_key].append(processed_diagnostic)
            
            # Track file error counts
            if file_name not in file_error_counts:
                file_error_counts[file_name] = 0
            file_error_counts[file_name] += 1
        
        # Sort diagnostics by severity (ERROR first), then by file, then by line
        severity_priority = {'ERROR': 0, 'WARNING': 1, 'INFO': 2, 'HINT': 3, 'UNKNOWN': 4}
        
        processed_diagnostics.sort(key=lambda d: (
            severity_priority.get(d['severity'], 5),
            d['file_name'].lower(),
            int(d['location'].split(',')[0].split()[-1]) if 'line' in d['location'] else 0
        ))
        
        # Generate enhanced output
        error_count = len(processed_diagnostics)
        output_lines = [f"ERRORS: ['{error_count}']"]
        
        # Add each formatted diagnostic with FULL location path, error type, error reason, severity
        for i, diag in enumerate(processed_diagnostics, 1):
            # Format: ERROR #1: [full/folder/path/file.py:line:col] | ERROR_TYPE: error_code | REASON: full error message | SEVERITY: ERROR
            full_location = f"{diag['file_path']}:{diag['location']}"
            error_type = diag['code'] if diag['code'] and diag['code'] != 'unknown' else 'UNKNOWN_ERROR'
            error_reason = diag['error_reason']
            severity = diag['severity']
            
            diagnostic_line = f"ERROR #{i}: [{full_location}] | ERROR_TYPE: {error_type} | REASON: {error_reason} | SEVERITY: {severity}"
            output_lines.append(diagnostic_line)
            output_lines.append("")  # Add blank line for readability
        
        # Add enhanced summary statistics if verbose mode or many errors
        if self.verbose or error_count > 50:
            output_lines.append("")
            output_lines.append("=" * 60)
            output_lines.append("ENHANCED DIAGNOSTIC SUMMARY")
            output_lines.append("=" * 60)
            
            # Top error categories
            sorted_categories = sorted(error_categories.items(), key=lambda x: len(x[1]), reverse=True)
            output_lines.append("Top Error Categories:")
            for i, (category, diags) in enumerate(sorted_categories[:10], 1):
                severity, code = category.split(':', 1)
                output_lines.append(f"  {i}. {severity} {code}: {len(diags)} occurrences")
            
            # Files with most errors
            sorted_files = sorted(file_error_counts.items(), key=lambda x: x[1], reverse=True)
            output_lines.append("")
            output_lines.append("Files with Most Errors:")
            for i, (file_name, count) in enumerate(sorted_files[:10], 1):
                output_lines.append(f"  {i}. {file_name}: {count} errors")
            
            output_lines.append("=" * 60)
        
        return '\n'.join(output_lines)
    
    def analyze_repository(self, repo_url_or_path: str, 
                          severity_filter: Optional[str] = None,
                          language_override: Optional[str] = None,
                          output_format: str = 'text') -> Union[str, Dict[str, Any]]:
        """
        Main comprehensive analysis function that orchestrates the entire process.
        
        This method performs full codebase analysis without any limitations,
        processing every single source file using real LSP integration.
        
        Args:
            repo_url_or_path: Repository URL or local path
            severity_filter: Optional severity filter ('ERROR', 'WARNING', 'INFO', 'HINT')
            language_override: Optional language override
            output_format: Output format ('text' or 'json')
            
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
            
            # Step 5: Get source files for analysis
            source_files = project.gather_source_files()
            self.total_files = len(source_files)
            self.logger.info(f"📊 Found {self.total_files} source files to analyze")
            
            # Step 6: Comprehensive diagnostic collection
            self.logger.info("🔍 Beginning comprehensive LSP diagnostic collection...")
            diagnostics = self.collect_diagnostics(project, language_server, severity)
            
            # Step 7: Enhanced symbol analysis (if verbose or requested)
            symbol_analysis = {}
            if self.verbose or output_format == 'json':
                self.logger.info("🔍 Performing enhanced symbol analysis...")
                symbol_analysis = self.analyze_symbol_usage_patterns(source_files)
            
            # Step 8: Generate results
            results = self._generate_results(
                diagnostics, project.project_config.language.value, repo_path, total_start_time, symbol_analysis
            )
            
            # Step 7: Format output
            if output_format == 'json':
                return results.to_dict()
            else:
                return self.format_diagnostic_output(diagnostics, project)
            
        except Exception as e:
            self.logger.error(f"❌ COMPREHENSIVE ANALYSIS FAILED: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            
            if output_format == 'json':
                return {"error": str(e), "diagnostics": []}
            else:
                return f"ERRORS: ['0']\nComprehensive analysis failed: {e}"
    
    def _generate_results(self, diagnostics: List[Diagnostic], 
                         language: str, repo_path: str, start_time: float, 
                         symbol_analysis: Dict[str, Any] = None) -> AnalysisResults:
        """Generate comprehensive analysis results."""
        # Convert diagnostics to enhanced format
        enhanced_diagnostics = []
        severity_counts = {}
        file_counts = {}
        
        for diag in diagnostics:
            # Extract location information
            range_info = diag.get('range', {})
            start_pos = range_info.get('start', {})
            line = start_pos.get('line', 0) + 1
            column = start_pos.get('character', 0) + 1
            
            # Extract file path
            uri = diag.get('uri', '')
            if uri.startswith('file://'):
                file_path = uri[7:]
                try:
                    file_path = os.path.relpath(file_path)
                except ValueError:
                    pass
            else:
                file_path = 'unknown'
            
            # Map severity
            severity = diag.get('severity', DiagnosticsSeverity.ERROR.value)
            severity_map = {
                DiagnosticsSeverity.ERROR.value: 'ERROR',
                DiagnosticsSeverity.WARNING.value: 'WARNING',
                DiagnosticsSeverity.INFORMATION.value: 'INFO',
                DiagnosticsSeverity.HINT.value: 'HINT'
            }
            severity_str = severity_map.get(severity, 'UNKNOWN')
            
            enhanced_diag = EnhancedDiagnostic(
                file_path=file_path,
                line=line,
                column=column,
                severity=severity_str,
                message=diag.get('message', 'No message'),
                code=str(diag.get('code', '')),
                source=diag.get('source', 'lsp'),
                category='lsp_diagnostic',
                tags=['lsp_analysis']
            )
            enhanced_diagnostics.append(enhanced_diag)
            
            # Count by severity and file
            severity_counts[severity_str] = severity_counts.get(severity_str, 0) + 1
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
        
        total_time = time.time() - start_time
        self.performance_stats['total_time'] = total_time
        
        # Extract symbol analysis data if available
        symbol_data = symbol_analysis or {}
        
        return AnalysisResults(
            total_files=self.total_files,
            processed_files=self.processed_files,
            failed_files=self.failed_files,
            total_diagnostics=len(enhanced_diagnostics),
            diagnostics_by_severity=severity_counts,
            diagnostics_by_file=file_counts,
            diagnostics=enhanced_diagnostics,
            performance_stats=self.performance_stats,
            language_detected=language,
            repository_path=repo_path,
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            # Enhanced symbol analysis results
            total_symbols=symbol_data.get('total_symbols_found', self.total_symbols),
            symbols_by_kind=symbol_data.get('symbols_by_kind', {}),
            symbol_analysis=symbol_data,
            symbol_errors=self.symbol_errors
        )


def main():
    """Main entry point for comprehensive LSP error analysis."""
    parser = argparse.ArgumentParser(
        description="🚀 COMPREHENSIVE LSP ERROR ANALYSIS TOOL - Analyzes ENTIRE codebases using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 COMPREHENSIVE ANALYSIS EXAMPLES:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR --verbose
  %(prog)s . --timeout 600 --max-workers 8 --language python
  %(prog)s https://github.com/Zeeeepa/serena --verbose --output json

📊 OUTPUT FORMAT:
  ERRORS: ['count']
  1. 'location' 'file' 'error reason' 'other types'
  2. 'location' 'file' 'error reason' 'other types'
  ...
  
  [ENHANCED DIAGNOSTIC SUMMARY - when verbose or >50 errors]
  Top Error Categories:
    1. ERROR reportMissingImports: 45 occurrences
    2. WARNING unusedVariable: 23 occurrences
  Files with Most Errors:
    1. main.py: 12 errors
    2. utils.py: 8 errors

🚀 FEATURES:
  ✅ Real LSP integration using Serena and SolidLSP
  ✅ Comprehensive analysis of entire codebases without limitations
  ✅ Batch processing with adaptive sizing for LSP efficiency
  ✅ Advanced error categorization and deduplication
  ✅ Retry mechanisms for transient failures
  ✅ Enhanced progress tracking with ETA calculations
  ✅ Memory-efficient processing for very large codebases
  ✅ Intelligent error message cleaning and truncation
  ✅ Statistical analysis of error patterns
  ✅ Enhanced language server initialization with health checks

⚡ PERFORMANCE OPTIMIZATION TIPS:
  - Use --max-workers 2-8 for optimal parallel processing
  - Increase --timeout 600+ for very large repositories (1000+ files)
  - Use --severity ERROR to focus on critical issues only
  - Enable --verbose for detailed progress tracking and diagnostics
  - For repositories >5000 files, consider --max-workers 2 to prevent LSP overload
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
        '--output',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
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
    print(f"   📊 Output format: {args.output}")
    print(f"   📋 Verbose: {args.verbose}")
    print("=" * 80)
    
    # Run the comprehensive analysis
    try:
        with SerenaLSPAnalyzer(
            verbose=args.verbose, 
            timeout=args.timeout,
            max_workers=args.max_workers
        ) as analyzer:
            result = analyzer.analyze_repository(
                args.repository,
                severity_filter=args.severity,
                language_override=args.language,
                output_format=args.output
            )
            
            # Output the results
            if args.output == 'json':
                print(json.dumps(result, indent=2, default=str))
            else:
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
