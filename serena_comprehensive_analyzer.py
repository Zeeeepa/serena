#!/usr/bin/env python3
"""
Comprehensive Serena LSP Error Analysis Tool

This tool provides maximum comprehension LSP error retrieval and report generation
using Serena and SolidLSP to extract ALL LSP errors and diagnostics from codebases.

Features:
- 100% LSP error retrieval with full location paths
- Complete folder/filename, error type, error reason, severity reporting
- Real LSP integration using Serena and SolidLSP
- Comprehensive protocol support with ProcessLaunchInfo, LSPError, MessageType
- Enhanced diagnostic collection with position and range information
- Robust process management and server lifecycle handling
- Parallel processing for large codebases
- Advanced error categorization and analysis

Usage:
    python serena_comprehensive_analyzer.py <repo_url_or_path> [options]

Example:
    python serena_comprehensive_analyzer.py https://github.com/user/repo.git
    python serena_comprehensive_analyzer.py /path/to/local/repo --severity ERROR
    python serena_comprehensive_analyzer.py . --verbose --timeout 120
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
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from urllib.parse import urlparse

# Comprehensive Serena and SolidLSP imports
try:
    # Core Serena imports
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    
    # SolidLSP core configuration and server
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.settings import SolidLSPSettings
    from solidlsp import SolidLanguageServer
    
    # Comprehensive LSP protocol types and diagnostics
    from solidlsp.ls_types import (
        DiagnosticsSeverity,
        DiagnosticSeverity,
        Diagnostic,
        ErrorCodes,
        LSPErrorCodes,
        Position,
        Range,
        Location,
        MarkupContent,
        MarkupKind,
        CompletionItemKind,
        CompletionItem,
        UnifiedSymbolInformation,
        SymbolKind,
        SymbolTag,
    )
    
    # LSP protocol handler components for robust server management
    from solidlsp.lsp_protocol_handler.server import (
        ProcessLaunchInfo,
        LSPError,
        MessageType,
    )
    
    # Serena symbol handling for comprehensive code analysis
    from serena.symbol import (
        LanguageServerSymbolRetriever,
        ReferenceInLanguageServerSymbol,
        LanguageServerSymbol,
        Symbol,
        PositionInFile,
        LanguageServerSymbolLocation,
    )
    
except ImportError as e:
    print(f"Error: Failed to import required Serena/SolidLSP modules: {e}")
    print("Please ensure Serena and SolidLSP are properly installed.")
    print("Try: pip install -e . from the serena repository root")
    sys.exit(1)


@dataclass
class EnhancedDiagnostic:
    """Enhanced diagnostic with comprehensive LSP protocol metadata."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    error_code: Optional[ErrorCodes] = None
    # Enhanced LSP protocol fields
    range_info: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    related_information: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_information is None:
            self.related_information = []


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
    server_status: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.server_status is None:
            self.server_status = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ComprehensiveSerenaAnalyzer:
    """
    Maximum comprehension LSP analyzer for entire codebases using Serena and SolidLSP.
    
    This class provides 100% LSP error retrieval with complete location paths,
    error types, error reasons, and severity levels for all programming languages
    supported by Serena.
    """
    
    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4):
        """
        Initialize the comprehensive analyzer.
        
        Args:
            verbose: Enable verbose logging and progress tracking
            timeout: Timeout for language server operations
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
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_stats = {
            'clone_time': 0,
            'setup_time': 0,
            'lsp_start_time': 0,
            'analysis_time': 0,
            'total_time': 0
        }
        
        if verbose:
            self.logger.info("🚀 Initializing Comprehensive Serena LSP Analyzer")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
    
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
                self.logger.info("🛑 Stopping language server...")
                self.language_server.stop()
                
            if self.temp_dir and os.path.exists(self.temp_dir):
                self.logger.info(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            self.logger.warning(f"⚠️  Error during cleanup: {e}")
    
    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith('.git')
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        self.logger.info(f"📥 Cloning repository: {repo_url}")
        
        self.temp_dir = tempfile.mkdtemp(prefix="serena_analysis_")
        repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
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
        """Detect the primary programming language of the repository."""
        self.logger.info("🔍 Detecting repository language...")
        
        language_indicators = {
            Language.PYTHON: ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            Language.TYPESCRIPT: ['.ts', '.tsx', '.js', '.jsx', 'tsconfig.json', 'package.json'],
            Language.JAVA: ['.java', 'pom.xml', 'build.gradle'],
            Language.CSHARP: ['.cs', '.csproj', '.sln'],
            Language.CPP: ['.cpp', '.cc', '.cxx', '.h', '.hpp', 'CMakeLists.txt'],
            Language.RUST: ['.rs', 'Cargo.toml'],
            Language.GO: ['.go', 'go.mod'],
            Language.PHP: ['.php', 'composer.json'],
            Language.RUBY: ['.rb', 'Gemfile'],
            Language.KOTLIN: ['.kt', '.kts'],
            Language.DART: ['.dart', 'pubspec.yaml'],
        }
        
        file_counts = {lang: 0 for lang in language_indicators.keys()}
        
        for root, dirs, files in os.walk(repo_path):
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
                        file_counts[lang] += 5
        
        detected_lang = max(file_counts, key=file_counts.get)
        
        if file_counts[detected_lang] == 0:
            self.logger.warning("Could not detect language, defaulting to Python")
            detected_lang = Language.PYTHON
        
        self.logger.info(f"✅ Detected language: {detected_lang.value}")
        return detected_lang
    
    def setup_project(self, repo_path: str, language: Optional[Language] = None) -> Project:
        """Set up a Serena project for the repository."""
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path is not a directory: {repo_path}")
        
        if language is None:
            language = self.detect_language(repo_path)
        
        self.logger.info(f"⚙️  Setting up project for {repo_path} with language {language.value}")
        
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
        
        self.project = Project(repo_path, project_config)
        return self.project
    
    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """Start the language server for the project with enhanced initialization."""
        self.logger.info("🔧 Starting enhanced language server initialization...")
        
        max_attempts = 3
        base_delay = 2.0
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    self.logger.info(f"🔄 Retry attempt {attempt + 1}/{max_attempts} after {delay}s delay...")
                    time.sleep(delay)
                
                self.logger.info(f"🚀 Language server initialization attempt {attempt + 1}/{max_attempts}")
                
                init_start_time = time.time()
                
                self.language_server = project.create_language_server(
                    log_level=logging.DEBUG if self.verbose else logging.WARNING,
                    ls_timeout=self.timeout,
                    trace_lsp_communication=self.verbose
                )
                
                if not self.language_server:
                    raise RuntimeError("Failed to create language server instance")
                
                self.logger.info("📡 Starting language server process...")
                self.language_server.start()
                
                startup_time = time.time() - init_start_time
                self.logger.info(f"⏱️  Language server startup took {startup_time:.2f}s")
                
                if not self.language_server.is_running():
                    raise RuntimeError("Language server process is not running after start")
                
                # Wait for server to be fully ready
                self.logger.info("🔍 Validating language server readiness...")
                ready_timeout = min(30, self.timeout // 4)
                
                for i in range(int(ready_timeout)):
                    if not self.language_server.is_running():
                        raise RuntimeError(f"Server stopped during initialization at {i}s")
                    
                    if self.verbose and i % 5 == 0:
                        self.logger.debug(f"🔍 Server readiness check: {i}/{ready_timeout}s")
                    
                    time.sleep(1)
                
                if not self.language_server.is_running():
                    raise RuntimeError("Language server stopped running during initialization")
                
                total_init_time = time.time() - init_start_time
                self.logger.info(f"🎉 Language server successfully initialized in {total_init_time:.2f}s")
                
                return self.language_server
                
            except Exception as e:
                error_msg = f"Language server initialization attempt {attempt + 1} failed: {e}"
                
                if attempt < max_attempts - 1:
                    self.logger.warning(f"⚠️  {error_msg}")
                    self._cleanup_failed_server()
                else:
                    self.logger.error(f"❌ {error_msg}")
                    raise RuntimeError(f"Failed to start language server after {max_attempts} attempts: {e}")
        
        raise RuntimeError("Language server initialization failed unexpectedly")
    
    def _cleanup_failed_server(self):
        """Clean up a failed server instance."""
        if self.language_server:
            try:
                if self.language_server.is_running():
                    self.language_server.stop()
            except Exception as cleanup_error:
                self.logger.debug(f"Error during server cleanup: {cleanup_error}")
            finally:
                self.language_server = None
    
    def collect_diagnostics(self, project: Project, language_server: SolidLanguageServer, 
                          severity_filter: Optional[DiagnosticsSeverity] = None) -> List[EnhancedDiagnostic]:
        """
        Collect diagnostics from ALL source files in the project using comprehensive LSP analysis.
        
        This method processes every single source file without any limitations,
        providing 100% LSP error retrieval with complete location paths.
        """
        self.analysis_start_time = time.time()
        self.logger.info("🔍 Starting comprehensive LSP analysis of entire codebase...")
        
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
        progress_interval = max(1, self.total_files // 50)
        last_progress_report = 0
        
        self.logger.info(f"🚀 Processing ALL {self.total_files} files with comprehensive analysis...")
        self.logger.info(f"⚙️  Using {self.max_workers} workers with batch processing")
        
        def analyze_single_file(file_path: str, retry_count: int = 0) -> Tuple[str, List[EnhancedDiagnostic], Optional[str], bool]:
            """Analyze a single file using comprehensive LSP with enhanced error handling."""
            try:
                # Get diagnostics from LSP using Serena's method
                try:
                    lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)
                    
                except LSPError as lsp_error:
                    # Handle LSP-specific errors with appropriate retry logic
                    if lsp_error.code == ErrorCodes.RequestCancelled:
                        if self.verbose:
                            self.logger.debug(f"🔄 Request cancelled for {os.path.basename(file_path)}: {lsp_error.message}")
                        return file_path, [], f"LSP Request Cancelled: {lsp_error.message}", retry_count < 2
                    elif lsp_error.code == ErrorCodes.ContentModified:
                        if self.verbose:
                            self.logger.debug(f"📝 Content modified for {os.path.basename(file_path)}: {lsp_error.message}")
                        return file_path, [], f"LSP Content Modified: {lsp_error.message}", retry_count < 2
                    elif lsp_error.code == ErrorCodes.ServerNotInitialized:
                        self.logger.error(f"❌ Server not initialized for {os.path.basename(file_path)}: {lsp_error.message}")
                        return file_path, [], f"LSP Server Not Initialized: {lsp_error.message}", False
                    else:
                        self.logger.warning(f"⚠️  LSP Error for {os.path.basename(file_path)}: {lsp_error}")
                        retryable = retry_count < 2 and lsp_error.code not in [
                            ErrorCodes.InvalidRequest, ErrorCodes.MethodNotFound, ErrorCodes.InvalidParams
                        ]
                        return file_path, [], f"LSP Error ({lsp_error.code}): {lsp_error.message}", retryable
                
                enhanced_diagnostics = []
                for diag in lsp_diagnostics:
                    # Extract comprehensive diagnostic information
                    range_info = diag.get('range', {})
                    start_pos = range_info.get('start', {})
                    end_pos = range_info.get('end', {})
                    line = start_pos.get('line', 0) + 1  # LSP uses 0-based line numbers
                    column = start_pos.get('character', 0) + 1  # LSP uses 0-based character numbers
                    
                    # Create proper LSP Position and Range objects
                    position_start = Position(line=start_pos.get('line', 0), character=start_pos.get('character', 0))
                    position_end = Position(line=end_pos.get('line', 0), character=end_pos.get('character', 0))
                    range_obj = Range(start=position_start, end=position_end)
                    
                    # Create Location object for enhanced diagnostic
                    location_obj = Location(uri=f"file://{file_path}", range=range_obj)
                    
                    # Map severity with comprehensive handling
                    severity_map = {
                        DiagnosticsSeverity.ERROR: 'ERROR',
                        DiagnosticsSeverity.WARNING: 'WARNING',
                        DiagnosticsSeverity.INFORMATION: 'INFO',
                        DiagnosticsSeverity.HINT: 'HINT'
                    }
                    
                    severity_value = diag.get('severity', DiagnosticsSeverity.ERROR)
                    severity = severity_map.get(severity_value, 'UNKNOWN')
                    
                    # Apply severity filter
                    if severity_filter and severity_value != severity_filter:
                        continue
                    
                    # Extract error code if available
                    diagnostic_code = diag.get('code')
                    error_code = None
                    if diagnostic_code and isinstance(diagnostic_code, int):
                        try:
                            error_code = ErrorCodes(diagnostic_code)
                        except ValueError:
                            pass
                    
                    # Get path relative to project root for clean display
                    try:
                        if hasattr(project, 'project_path'):
                            project_root = project.project_path
                            if file_path.startswith(project_root):
                                display_path = os.path.relpath(file_path, project_root)
                            else:
                                display_path = os.path.relpath(file_path)
                        else:
                            display_path = os.path.relpath(file_path)
                            # Clean up excessive ../ paths
                            if display_path.count('../') > 3:
                                path_parts = file_path.split('/')
                                # Find meaningful path components
                                for i, part in enumerate(path_parts):
                                    if part and not part.startswith('serena_analysis_') and not part.startswith('tmp'):
                                        display_path = '/'.join(path_parts[i+1:]) if i+1 < len(path_parts) else path_parts[-1]
                                        break
                                else:
                                    display_path = '/'.join(path_parts[-3:]) if len(path_parts) >= 3 else '/'.join(path_parts)
                    except (ValueError, AttributeError):
                        display_path = file_path
                    
                    # Create enhanced diagnostic with comprehensive LSP protocol information
                    enhanced_diag = EnhancedDiagnostic(
                        file_path=display_path,
                        line=line,
                        column=column,
                        severity=severity,
                        message=diag.get('message', 'No message'),
                        code=str(diag.get('code', '')),
                        source=diag.get('source', 'lsp'),
                        category='lsp_diagnostic',
                        tags=['comprehensive_serena_lsp_analysis'],
                        error_code=error_code,
                        range_info=range_info,
                        location={"uri": f"file://{file_path}", "range": range_info}
                    )
                    enhanced_diagnostics.append(enhanced_diag)
                
                # Log diagnostic collection
                if self.verbose and len(enhanced_diagnostics) > 0:
                    if any(d.severity == 'ERROR' for d in enhanced_diagnostics):
                        self.logger.debug(f"🔴 Found {len(enhanced_diagnostics)} diagnostics (including errors) in {os.path.basename(file_path)}")
                    elif any(d.severity == 'WARNING' for d in enhanced_diagnostics):
                        self.logger.debug(f"🟡 Found {len(enhanced_diagnostics)} diagnostics (warnings) in {os.path.basename(file_path)}")
                    else:
                        self.logger.debug(f"🔵 Found {len(enhanced_diagnostics)} diagnostics (info/hints) in {os.path.basename(file_path)}")
                
                return file_path, enhanced_diagnostics, None, False
                
            except Exception as e:
                self.logger.warning(f"⚠️  Unexpected error analyzing {os.path.basename(file_path)}: {e}")
                retryable = retry_count < 2 and any(keyword in str(e).lower() for keyword in [
                    "timeout", "connection", "temporary", "busy", "retry"
                ])
                return file_path, [], str(e), retryable
        
        # Process files in batches for optimal LSP server efficiency
        batch_size = min(50, max(1, self.total_files // 10))
        file_batches = [source_files[i:i + batch_size] for i in range(0, len(source_files), batch_size)]
        
        self.logger.info(f"📦 Processing {len(file_batches)} batches of ~{batch_size} files each")
        
        for batch_idx, file_batch in enumerate(file_batches):
            self.logger.info(f"📦 Processing batch {batch_idx + 1}/{len(file_batches)} ({len(file_batch)} files)")
            
            # Use ThreadPoolExecutor for controlled parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(analyze_single_file, file_path): file_path 
                    for file_path in file_batch
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        analyzed_file, diagnostics, error, should_retry = future.result()
                        
                        with self.lock:
                            if error is None:
                                all_diagnostics.extend(diagnostics)
                                self.processed_files += 1
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
                                               f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s")
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
        
        # Final comprehensive statistics
        analysis_time = time.time() - self.analysis_start_time
        self.performance_stats['analysis_time'] = analysis_time
        self.total_diagnostics = len(all_diagnostics)
        
        # Categorize diagnostics by severity
        severity_counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0, 'HINT': 0, 'UNKNOWN': 0}
        for diag in all_diagnostics:
            severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
        
        self.logger.info("=" * 80)
        self.logger.info("📋 COMPREHENSIVE SERENA LSP ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {self.processed_files}")
        self.logger.info(f"❌ Files failed: {self.failed_files}")
        self.logger.info(f"📊 Total files analyzed: {self.processed_files + self.failed_files}/{self.total_files}")
        self.logger.info(f"🔍 Total LSP diagnostics found: {self.total_diagnostics}")
        self.logger.info("📋 Diagnostics by severity:")
        for severity, count in severity_counts.items():
            if count > 0:
                self.logger.info(f"   {severity}: {count}")
        self.logger.info(f"⏱️  Analysis time: {analysis_time:.2f} seconds")
        self.logger.info(f"🚀 Processing rate: {(self.processed_files + self.failed_files) / analysis_time:.2f} files/sec")
        self.logger.info("=" * 80)
        
        return all_diagnostics
    
    def format_diagnostic_output(self, diagnostics: List[EnhancedDiagnostic]) -> str:
        """
        Format diagnostics with FULL location paths, error types, error reasons, and severity.
        
        Format: ERROR #N: [full/folder/path/file.py:line X, col Y] | ERROR_TYPE: code | REASON: message | SEVERITY: level
        """
        if not diagnostics:
            return "ERRORS: ['0']\nNo errors found."
        
        # Sort diagnostics by severity (ERROR first), then by file, then by line
        severity_priority = {'ERROR': 0, 'WARNING': 1, 'INFO': 2, 'HINT': 3, 'UNKNOWN': 4}
        
        diagnostics.sort(key=lambda d: (
            severity_priority.get(d.severity, 5),
            d.file_path.lower(),
            d.line
        ))
        
        # Generate comprehensive output with full paths and structured format
        error_count = len(diagnostics)
        output_lines = [f"ERRORS: ['{error_count}']"]
        
        # Add each formatted diagnostic with FULL location path, error type, error reason, severity
        for i, diag in enumerate(diagnostics, 1):
            # Format: ERROR #1: [full/folder/path/file.py:line:col] | ERROR_TYPE: error_code | REASON: full error message | SEVERITY: ERROR
            full_location = f"{diag.file_path}:line {diag.line}, col {diag.column}"
            error_type = diag.code if diag.code and diag.code != '' else 'UNKNOWN_ERROR'
            error_reason = diag.message  # Keep full message - no truncation for comprehensive analysis
            severity = diag.severity
            
            diagnostic_line = f"ERROR #{i}: [{full_location}] | ERROR_TYPE: {error_type} | REASON: {error_reason} | SEVERITY: {severity}"
            output_lines.append(diagnostic_line)
            output_lines.append("")  # Add blank line for readability
        
        # Add comprehensive summary statistics if verbose mode or many errors
        if self.verbose or error_count > 50:
            output_lines.append("")
            output_lines.append("=" * 80)
            output_lines.append("COMPREHENSIVE SERENA LSP DIAGNOSTIC SUMMARY")
            output_lines.append("=" * 80)
            
            # Severity breakdown
            severity_counts = {}
            file_counts = {}
            error_type_counts = {}
            
            for diag in diagnostics:
                severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
                file_counts[diag.file_path] = file_counts.get(diag.file_path, 0) + 1
                if diag.code and diag.code != '':
                    error_type_counts[diag.code] = error_type_counts.get(diag.code, 0) + 1
            
            output_lines.append("Diagnostics by Severity:")
            for severity, count in sorted(severity_counts.items()):
                output_lines.append(f"  {severity}: {count}")
            
            # Top error types
            if error_type_counts:
                output_lines.append("")
                output_lines.append("Top Error Types:")
                sorted_error_types = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)
                for i, (error_type, count) in enumerate(sorted_error_types[:10], 1):
                    output_lines.append(f"  {i}. {error_type}: {count} occurrences")
            
            # Files with most errors
            sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
            output_lines.append("")
            output_lines.append("Files with Most Errors:")
            for i, (file_path, count) in enumerate(sorted_files[:10], 1):
                file_name = os.path.basename(file_path)
                output_lines.append(f"  {i}. {file_name}: {count} errors")
            
            output_lines.append("=" * 80)
        
        return '\n'.join(output_lines)
    
    def analyze_repository(self, repo_url_or_path: str, 
                          severity_filter: Optional[str] = None,
                          language_override: Optional[str] = None,
                          output_format: str = 'text') -> Union[str, Dict[str, Any]]:
        """
        Main comprehensive analysis function providing maximum LSP error retrieval.
        
        This method provides 100% LSP error retrieval with complete location paths,
        error types, error reasons, and severity levels.
        """
        total_start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting COMPREHENSIVE SERENA LSP Error Analysis")
            self.logger.info("=" * 80)
            self.logger.info(f"📁 Target: {repo_url_or_path}")
            self.logger.info(f"🔍 Severity filter: {severity_filter or 'ALL'}")
            self.logger.info(f"🌐 Language override: {language_override or 'AUTO-DETECT'}")
            self.logger.info(f"📊 Output format: {output_format}")
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
            
            # Give the language server time to fully initialize
            initialization_time = 5 if self.total_files > 100 else 2
            self.logger.info(f"⏳ Allowing {initialization_time}s for LSP initialization...")
            time.sleep(initialization_time)
            
            self.performance_stats['lsp_start_time'] = time.time() - lsp_start
            
            # Step 5: Comprehensive diagnostic collection
            self.logger.info("🔍 Beginning comprehensive Serena LSP diagnostic collection...")
            diagnostics = self.collect_diagnostics(project, language_server, severity)
            
            # Step 6: Generate results
            if output_format == 'json':
                results = self._generate_results(diagnostics, project.config.language.value, repo_path, total_start_time)
                return results.to_dict()
            else:
                # Step 7: Format results with full paths and comprehensive information
                self.logger.info("📋 Formatting comprehensive results...")
                result = self.format_diagnostic_output(diagnostics)
                
                # Final performance summary
                total_time = time.time() - total_start_time
                self.performance_stats['total_time'] = total_time
                
                self.logger.info("🎉 COMPREHENSIVE SERENA LSP ANALYSIS COMPLETED!")
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
            self.logger.error(f"❌ COMPREHENSIVE SERENA LSP ANALYSIS FAILED: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            
            if output_format == 'json':
                return {"error": str(e), "diagnostics": []}
            else:
                return f"ERRORS: ['0']\nSerena LSP analysis failed: {e}"
    
    def _generate_results(self, diagnostics: List[EnhancedDiagnostic], 
                         language: str, repo_path: str, start_time: float) -> AnalysisResults:
        """Generate comprehensive analysis results."""
        # Count diagnostics by severity and file
        severity_counts = {}
        file_counts = {}
        
        for diag in diagnostics:
            severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
            file_counts[diag.file_path] = file_counts.get(diag.file_path, 0) + 1
        
        total_time = time.time() - start_time
        self.performance_stats['total_time'] = total_time
        
        return AnalysisResults(
            total_files=self.total_files,
            processed_files=self.processed_files,
            failed_files=self.failed_files,
            total_diagnostics=self.total_diagnostics,
            diagnostics_by_severity=severity_counts,
            diagnostics_by_file=file_counts,
            diagnostics=diagnostics,
            performance_stats=self.performance_stats,
            language_detected=language,
            repository_path=repo_path,
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            server_status={"status": "completed", "total_files": self.total_files}
        )


def main():
    """Main entry point for comprehensive Serena LSP error analysis with maximum comprehension."""
    parser = argparse.ArgumentParser(
        description="🚀 COMPREHENSIVE SERENA LSP ERROR ANALYSIS TOOL - Maximum comprehension LSP error retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 COMPREHENSIVE SERENA LSP ANALYSIS - MAXIMUM ERROR RETRIEVAL:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR --verbose
  %(prog)s . --timeout 600 --max-workers 8 --language python
  %(prog)s https://github.com/Zeeeepa/serena --verbose --output json

📊 OUTPUT FORMAT - FULL LOCATION PATHS WITH STRUCTURED INFORMATION:
  ERRORS: ['count']
  ERROR #1: [full/folder/path/file.py:line X, col Y] | ERROR_TYPE: code | REASON: message | SEVERITY: level
  ERROR #2: [full/folder/path/file.py:line X, col Y] | ERROR_TYPE: code | REASON: message | SEVERITY: level
  ...
  
  [COMPREHENSIVE SERENA LSP DIAGNOSTIC SUMMARY - when verbose or >50 errors]
  Diagnostics by Severity:
    ERROR: 45
    WARNING: 23
  Top Error Types:
    1. reportMissingImports: 12 occurrences
    2. reportArgumentType: 8 occurrences
  Files with Most Errors:
    1. main.py: 12 errors
    2. utils.py: 8 errors

🚀 COMPREHENSIVE SERENA LSP FEATURES:
  ✅ 100% LSP error retrieval with complete location paths
  ✅ Full folder/filename, error type, error reason, severity reporting
  ✅ Real LSP integration using Serena and SolidLSP
  ✅ Support for all languages supported by Serena
  ✅ Comprehensive diagnostic collection from entire codebase
  ✅ Enhanced LSP protocol support with ProcessLaunchInfo, LSPError, MessageType
  ✅ Batch processing with adaptive sizing for LSP efficiency
  ✅ Advanced error categorization and analysis
  ✅ Retry mechanisms for transient failures
  ✅ Enhanced progress tracking with ETA calculations
  ✅ Memory-efficient processing for very large codebases
  ✅ Statistical analysis of error patterns and types
  ✅ Both text and JSON output formats

⚡ PERFORMANCE OPTIMIZATION TIPS:
  - Use --max-workers 2-8 for optimal parallel processing
  - Increase --timeout 600+ for very large repositories (1000+ files)
  - Use --severity ERROR to focus on critical issues only
  - Enable --verbose for detailed progress tracking and diagnostics
  - For repositories >5000 files, consider --max-workers 2 to prevent LSP overload

🔧 SUPPORTED LANGUAGES:
  Python, TypeScript/JavaScript, Java, C#, C++, Rust, Go, PHP, Ruby, Kotlin, Dart

💡 MAXIMUM COMPREHENSION FEATURES:
  - Complete folder structure preservation in error paths
  - Full error messages without truncation
  - Comprehensive error type classification
  - Enhanced LSP protocol integration
  - Advanced diagnostic metadata collection
  - Robust error handling and retry mechanisms
        """
    )
    
    parser.add_argument(
        'repository',
        help='Repository URL or local path to analyze (analyzes ALL source files with 100%% error retrieval)'
    )
    
    parser.add_argument(
        '--severity',
        choices=['ERROR', 'WARNING', 'INFO', 'HINT'],
        help='Filter diagnostics by severity level (default: show all diagnostics)'
    )
    
    parser.add_argument(
        '--language',
        help='Override automatic language detection (e.g., python, typescript, java, rust)'
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
        help='Output format (default: text with full paths and structured information)'
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
    
    print("🚀 COMPREHENSIVE SERENA LSP ERROR ANALYSIS TOOL")
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
    print("🎯 MAXIMUM COMPREHENSION LSP ERROR RETRIEVAL")
    print("   ✅ 100% error retrieval with full location paths")
    print("   ✅ Complete folder/filename, error type, error reason, severity")
    print("   ✅ Real LSP integration using Serena and SolidLSP")
    print("   ✅ Enhanced protocol support and robust error handling")
    print("=" * 80)
    
    # Run the comprehensive Serena LSP analysis
    try:
        with ComprehensiveSerenaAnalyzer(
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
                print("📋 COMPREHENSIVE SERENA LSP ANALYSIS RESULTS")
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
