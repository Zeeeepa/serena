#!/usr/bin/env python3
"""
Comprehensive Serena LSP Error Analysis Tool

This unified analyzer combines all Serena capabilities into a single comprehensive tool
that provides complete codebase analysis with ALL LSP server errors, symbol overviews,
and advanced code intelligence features.

Features:
- Complete LSP error reporting from all language servers
- Comprehensive symbol analysis and mapping
- Advanced code intelligence and refactoring capabilities
- Real-time analysis with background processing
- Detailed JSON reporting with full metrics
- Runtime error collection and analysis
- All Serena features in one unified interface

Usage:
    python serena_analyzer.py <repo_url_or_path> [options]

Example:
    python serena_analyzer.py https://github.com/user/repo.git
    python serena_analyzer.py /path/to/local/repo --severity ERROR --symbols
    python serena_analyzer.py . --verbose --timeout 120 --completion-analysis
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
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from urllib.parse import urlparse
from pathlib import Path
from enum import IntEnum, Enum

# Enhanced Serena and SolidLSP imports with comprehensive protocol support
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

    SERENA_AVAILABLE = True

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
    range_info: Optional[Dict[str, Any]] = None  # LSP Range object
    location: Optional[Dict[str, Any]] = None  # LSP Location object
    related_information: List[Dict[str, Any]] = None
    markup_content: Optional[Dict[str, Any]] = None  # MarkupContent for rich descriptions
    symbol_kind: Optional[int] = None  # Associated symbol kind if applicable
    completion_items: List[Dict[str, Any]] = None  # Related completion suggestions

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_information is None:
            self.related_information = []
        if self.completion_items is None:
            self.completion_items = []


@dataclass
class EnhancedSymbolInfo:
    """Enhanced symbol information with comprehensive metadata."""
    name: str
    kind: int  # SymbolKind
    location: Dict[str, Any]  # Location with URI and Range
    container_name: Optional[str] = None
    detail: Optional[str] = None
    documentation: Optional[Dict[str, Any]] = None  # MarkupContent
    tags: List[int] = None  # SymbolTag list
    references: List[Dict[str, Any]] = None  # Reference locations

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.references is None:
            self.references = []


@dataclass
class RuntimeError:
    """Runtime error information captured during execution."""
    file_path: str
    line: int
    column: int
    error_type: str
    error_message: str
    stack_trace: str
    execution_time: float
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class LSPServerInfo:
    """Information about the LSP server process."""
    process_info: Optional[ProcessLaunchInfo] = None
    server_status: str = "not_started"
    initialization_time: float = 0.0
    last_error: Optional[LSPError] = None
    message_count: int = 0
    error_count: int = 0


@dataclass
class AnalysisResults:
    """Comprehensive analysis results with enhanced LSP protocol support."""
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
    # Enhanced analysis results
    symbols: List[EnhancedSymbolInfo] = None
    runtime_errors: List[RuntimeError] = None
    symbol_references: Dict[str, List[Dict[str, Any]]] = None
    markup_content_analysis: List[Dict[str, Any]] = None
    lsp_error_counts: Dict[str, int] = None
    server_status: Dict[str, Any] = None

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []
        if self.runtime_errors is None:
            self.runtime_errors = []
        if self.symbol_references is None:
            self.symbol_references = {}
        if self.markup_content_analysis is None:
            self.markup_content_analysis = []
        if self.lsp_error_counts is None:
            self.lsp_error_counts = {}
        if self.server_status is None:
            self.server_status = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class RuntimeContext:
    """Runtime context information for errors that occur during execution."""
    exception_type: str
    stack_trace: List[str] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    
    def __str__(self) -> str:
        return f"RuntimeContext({self.exception_type}, {len(self.stack_trace)} frames)"


class RuntimeErrorCollector:
    """
    Collects runtime errors during code execution using various Python hooks
    and integrates with Serena's error analysis capabilities.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.runtime_errors: List[RuntimeError] = []
        self.error_handlers: List[Callable[[RuntimeError], None]] = []
        self._lock = threading.RLock()
        self._original_excepthook: Optional[Callable] = None
        self._active = False
        
        # Error collection settings
        self.max_errors = 1000
        self.max_stack_depth = 50
        self.collect_variables = True
        self.variable_max_length = 200
        
    def start_collection(self) -> None:
        """Start collecting runtime errors."""
        if self._active:
            return
            
        try:
            self._original_excepthook = sys.excepthook
            sys.excepthook = self._handle_exception
            self._active = True
            
        except Exception as e:
            print(f"Failed to start runtime error collection: {e}")
    
    def stop_collection(self) -> None:
        """Stop collecting runtime errors."""
        if not self._active:
            return
            
        try:
            if self._original_excepthook:
                sys.excepthook = self._original_excepthook
            self._active = False
            
        except Exception as e:
            print(f"Failed to stop runtime error collection: {e}")
    
    def _handle_exception(self, exc_type: type, exc_value: BaseException, exc_traceback) -> None:
        """Handle main thread exceptions."""
        try:
            self._collect_error(exc_type, exc_value, exc_traceback)
        except Exception as e:
            print(f"Error in exception handler: {e}")
        
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _collect_error(self, exc_type: type, exc_value: BaseException, exc_traceback) -> None:
        """Collect error information from exception."""
        try:
            if exc_traceback is None:
                return
                
            import traceback
            tb_list = traceback.extract_tb(exc_traceback)
            if not tb_list:
                return
            
            # Find the most relevant frame
            target_frame = None
            for frame in tb_list:
                if self._is_repo_file(frame.filename):
                    target_frame = frame
                    break
            
            if not target_frame:
                target_frame = tb_list[-1]
            
            # Create runtime error
            runtime_error = RuntimeError(
                file_path=str(Path(target_frame.filename).relative_to(self.repo_path)) if self._is_repo_file(target_frame.filename) else target_frame.filename,
                line=target_frame.lineno or 1,
                column=0,
                error_type=exc_type.__name__,
                error_message=str(exc_value),
                stack_trace='\n'.join(traceback.format_tb(exc_traceback, limit=self.max_stack_depth)),
                execution_time=time.time(),
                context={
                    'exception_type': exc_type.__name__,
                    'thread_id': threading.get_ident(),
                    'process_id': os.getpid()
                }
            )
            
            with self._lock:
                self.runtime_errors.append(runtime_error)
                if len(self.runtime_errors) > self.max_errors:
                    self.runtime_errors = self.runtime_errors[-self.max_errors:]
            
            for handler in self.error_handlers:
                try:
                    handler(runtime_error)
                except Exception as e:
                    print(f"Error in error handler: {e}")
                    
        except Exception as e:
            print(f"Failed to collect error: {e}")
    
    def _is_repo_file(self, file_path: str) -> bool:
        """Check if file is within the repository."""
        try:
            Path(file_path).relative_to(self.repo_path)
            return True
        except ValueError:
            return False
    
    def get_runtime_errors(self) -> List[RuntimeError]:
        """Get all collected runtime errors."""
        with self._lock:
            return self.runtime_errors.copy()
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.runtime_errors.clear()


class SerenaLSPAnalyzer:
    """
    Comprehensive LSP analyzer for entire codebases using Serena and SolidLSP.
    
    This class provides full codebase analysis capabilities using real LSP integration
    for accurate error detection across all programming languages supported by Serena.
    """

    def __init__(
        self,
        verbose: bool = False,
        timeout: float = 600,
        max_workers: int = 4,
        enable_symbols: bool = False,
        enable_runtime_errors: bool = False,
    ):
        """
        Initialize the comprehensive analyzer with enhanced LSP protocol support.
        
        Args:
            verbose: Enable verbose logging and progress tracking
            timeout: Timeout for language server operations
            max_workers: Maximum number of concurrent workers for file processing
            enable_symbols: Enable comprehensive symbol analysis
            enable_runtime_errors: Enable runtime error collection during execution
        """
        self.verbose = verbose
        self.timeout = timeout
        self.max_workers = max_workers
        self.enable_symbols = enable_symbols
        self.enable_runtime_errors = enable_runtime_errors
        self.temp_dir: Optional[str] = None
        self.project: Optional[Project] = None
        self.language_server: Optional[SolidLanguageServer] = None
        self.server_info: LSPServerInfo = LSPServerInfo()
        self.runtime_collector: Optional[RuntimeErrorCollector] = None

        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.total_symbols = 0
        self.total_runtime_errors = 0
        self.analysis_start_time = None
        self.lock = threading.Lock()

        # Enhanced analysis collections
        self.collected_symbols: List[EnhancedSymbolInfo] = []
        self.collected_runtime_errors: List[RuntimeError] = []
        self.symbol_references: Dict[str, List[Dict[str, Any]]] = {}
        self.markup_content_items: List[Dict[str, Any]] = []

        # Set up comprehensive logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self.performance_stats = {
            "clone_time": 0,
            "setup_time": 0,
            "lsp_start_time": 0,
            "analysis_time": 0,
            "runtime_analysis_time": 0,
            "total_time": 0,
        }

        if verbose:
            self.logger.info("🚀 Initializing Enhanced Serena LSP Analyzer")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
            if enable_runtime_errors:
                self.logger.info("🔥 Runtime error collection enabled")
        
        # Initialize runtime error collection if enabled
        if enable_runtime_errors:
            self._initialize_runtime_collection()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()

    def cleanup(self):
        """Clean up resources including language server and temporary directories with enhanced error handling."""
        try:
            # Enhanced language server cleanup with LSPError handling
            if self.language_server:
                try:
                    if self.language_server.is_running():
                        self.logger.info("🛑 Stopping language server...")
                        self.server_info.server_status = "stopping"

                        # Attempt graceful shutdown
                        self.language_server.stop()

                        # Wait briefly for graceful shutdown
                        time.sleep(1)

                        if self.language_server.is_running():
                            self.logger.warning("⚠️  Language server did not stop gracefully")
                            self.server_info.server_status = "force_stopped"
                        else:
                            self.logger.info("✅ Language server stopped successfully")
                            self.server_info.server_status = "stopped"
                    else:
                        self.logger.debug("🔍 Language server was not running")
                        self.server_info.server_status = "not_running"

                except LSPError as lsp_error:
                    self.server_info.last_error = lsp_error
                    self.server_info.error_count += 1
                    self.logger.warning(f"⚠️  LSP Error during server shutdown: {lsp_error}")
                    self.server_info.server_status = "error_during_stop"

                except Exception as e:
                    # Convert to LSPError for consistent handling
                    lsp_error = LSPError(ErrorCodes.InternalError, f"Error stopping server: {str(e)}")
                    self.server_info.last_error = lsp_error
                    self.server_info.error_count += 1
                    self.logger.warning(f"⚠️  Error stopping language server: {e}")
                    self.server_info.server_status = "error_during_stop"

                finally:
                    self.language_server = None

            # Stop runtime error collection
            if self.runtime_collector:
                try:
                    self.runtime_collector.stop_collection()
                    self.logger.info("🔥 Runtime error collection stopped")
                except Exception as e:
                    self.logger.warning(f"⚠️  Error stopping runtime collection: {e}")

            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    self.logger.info(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                    self.logger.debug("✅ Temporary directory cleaned up successfully")
                except Exception as e:
                    self.logger.warning(f"⚠️  Error cleaning up temporary directory: {e}")

            # Log final server statistics
            if self.verbose and self.server_info.message_count > 0:
                self.logger.info("📊 Final LSP Server Statistics:")
                self.logger.info(f"   📨 Total messages: {self.server_info.message_count}")
                self.logger.info(f"   ❌ Total errors: {self.server_info.error_count}")
                self.logger.info(f"   ⏱️  Initialization time: {self.server_info.initialization_time:.2f}s")
                self.logger.info(f"   📊 Final status: {self.server_info.server_status}")

                if self.server_info.last_error:
                    self.logger.info(f"   🔴 Last error: {self.server_info.last_error}")

        except Exception as e:
            # Final fallback error handling
            self.logger.error(f"❌ Critical error during cleanup: {e}")
            self.server_info.server_status = "cleanup_failed"

    def _initialize_runtime_collection(self) -> None:
        """Initialize runtime error collection."""
        try:
            # We'll initialize this when we have a repo path
            self.logger.info("🔥 Runtime error collection will be initialized with repository")
        except Exception as e:
            self.logger.error(f"Failed to initialize runtime error collection: {e}")
            self.enable_runtime_errors = False

    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith(".git")

    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        self.logger.info(f"📥 Cloning repository: {repo_url}")

        self.temp_dir = tempfile.mkdtemp(prefix="serena_analysis_")
        repo_name = os.path.basename(repo_url.rstrip("/").replace(".git", ""))
        clone_path = os.path.join(self.temp_dir, repo_name)

        try:
            cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
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
            Language.PYTHON: [".py", "requirements.txt", "setup.py", "pyproject.toml"],
            Language.TYPESCRIPT: [".ts", ".tsx", ".js", ".jsx", "tsconfig.json", "package.json"],
            Language.JAVA: [".java", "pom.xml", "build.gradle"],
            Language.CSHARP: [".cs", ".csproj", ".sln"],
            Language.CPP: [".cpp", ".cc", ".cxx", ".h", ".hpp", "CMakeLists.txt"],
            Language.RUST: [".rs", "Cargo.toml"],
            Language.GO: [".go", "go.mod"],
            Language.PHP: [".php", "composer.json"],
            Language.RUBY: [".rb", "Gemfile"],
            Language.KOTLIN: [".kt", ".kts"],
            Language.DART: [".dart", "pubspec.yaml"],
        }

        file_counts = {lang: 0 for lang in language_indicators.keys()}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "target", "build", "dist", "vendor"
            ]]

            for file in files:
                file_lower = file.lower()
                for lang, indicators in language_indicators.items():
                    if any(file_lower.endswith(ext) or file_lower == indicator 
                          for ext in indicators for indicator in [ext] if ext.startswith(".")):
                        file_counts[lang] += 1
                    elif any(file_lower == indicator 
                            for indicator in indicators if not indicator.startswith(".")):
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
                ".git/**",
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/target/**",
                "**/build/**",
                "**/.venv/**",
                "**/venv/**",
                "**/dist/**",
                "**/vendor/**",
            ],
            ignore_all_files_in_gitignore=True,
        )

        self.project = Project(repo_path, project_config)
        return self.project

    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """Start the language server for the project with enhanced initialization using ProcessLaunchInfo and LSPError handling."""
        self.logger.info("🔧 Starting enhanced language server initialization...")
        self.server_info.server_status = "initializing"

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

                try:
                    self.language_server = project.create_language_server(
                        log_level=logging.DEBUG if self.verbose else logging.WARNING,
                        ls_timeout=self.timeout,
                        trace_lsp_communication=self.verbose,
                    )

                    if not self.language_server:
                        raise LSPError(ErrorCodes.InternalError, "Failed to create language server instance")

                    # Store process information if available
                    if hasattr(self.language_server, "process_info"):
                        self.server_info.process_info = self.language_server.process_info

                except Exception as e:
                    if not isinstance(e, LSPError):
                        lsp_error = LSPError(ErrorCodes.ServerNotInitialized, f"Server creation failed: {str(e)}")
                    else:
                        lsp_error = e
                    self.server_info.last_error = lsp_error
                    raise lsp_error

                self.logger.info("📡 Starting language server process...")

                try:
                    self.language_server.start()
                    self.server_info.server_status = "starting"

                except Exception as e:
                    lsp_error = LSPError(ErrorCodes.ServerNotInitialized, f"Server start failed: {str(e)}")
                    self.server_info.last_error = lsp_error
                    self.server_info.error_count += 1
                    raise lsp_error

                startup_time = time.time() - init_start_time
                self.server_info.initialization_time = startup_time

                self.logger.info(f"⏱️  Language server startup took {startup_time:.2f}s")

                # Enhanced server health validation with LSPError handling
                try:
                    if not self.language_server.is_running():
                        raise LSPError(ErrorCodes.ServerNotInitialized, "Language server process is not running after start")

                    self.server_info.server_status = "running"

                    # Wait for server to be fully ready with progress logging
                    self.logger.info("🔍 Validating language server readiness...")
                    ready_timeout = min(30, self.timeout // 4)

                    for i in range(int(ready_timeout)):
                        if not self.language_server.is_running():
                            raise LSPError(ErrorCodes.ServerNotInitialized, f"Server stopped during initialization at {i}s")

                        if self.verbose and i % 5 == 0:
                            self.logger.debug(f"🔍 Server readiness check: {i}/{ready_timeout}s")

                        time.sleep(1)

                    if not self.language_server.is_running():
                        raise LSPError(ErrorCodes.ServerNotInitialized, "Language server stopped running during initialization")

                    self.server_info.server_status = "ready"

                except LSPError as lsp_error:
                    self.server_info.last_error = lsp_error
                    self.server_info.error_count += 1
                    raise lsp_error

                total_init_time = time.time() - init_start_time
                self.server_info.initialization_time = total_init_time

                self.logger.info(f"🎉 Language server successfully initialized in {total_init_time:.2f}s")

                return self.language_server

            except LSPError as lsp_error:
                self.server_info.last_error = lsp_error
                self.server_info.error_count += 1
                error_msg = f"LSP Error (attempt {attempt + 1}): {lsp_error}"

                if attempt < max_attempts - 1:
                    self.logger.warning(f"⚠️  {error_msg}")
                    self._cleanup_failed_server()
                else:
                    self.logger.error(f"❌ {error_msg}")
                    self.server_info.server_status = "failed"
                    raise RuntimeError(f"Failed to start language server after {max_attempts} attempts: {lsp_error}")

            except Exception as e:
                lsp_error = LSPError(ErrorCodes.InternalError, f"Unexpected error: {str(e)}")
                self.server_info.last_error = lsp_error
                self.server_info.error_count += 1
                error_msg = f"Unexpected error (attempt {attempt + 1}): {e}"

                if attempt < max_attempts - 1:
                    self.logger.warning(f"⚠️  {error_msg}")
                    self._cleanup_failed_server()
                else:
                    self.logger.error(f"❌ {error_msg}")
                    self.server_info.server_status = "failed"
                    raise RuntimeError(f"Failed to start language server after {max_attempts} attempts: {e}")

        self.server_info.server_status = "failed"
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
                self.server_info.server_status = "stopped"

    def collect_diagnostics(
        self,
        project: Project,
        language_server: SolidLanguageServer,
        severity_filter: Optional[DiagnosticsSeverity] = None,
    ) -> List[EnhancedDiagnostic]:
        """Collect diagnostics from ALL source files in the project using Serena LSP integration."""
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

        self.logger.info(f"🚀 Processing ALL {self.total_files} files with Serena LSP analysis...")

        def analyze_single_file(file_path: str) -> Tuple[str, List[EnhancedDiagnostic], Optional[str]]:
            """Analyze a single file using Serena LSP with enhanced error handling."""
            try:
                # Increment message count for tracking
                self.server_info.message_count += 1

                # Get diagnostics from LSP using Serena's method with LSPError handling
                try:
                    lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)

                except LSPError as lsp_error:
                    self.server_info.error_count += 1
                    self.server_info.last_error = lsp_error

                    if lsp_error.code == ErrorCodes.RequestCancelled:
                        if self.verbose:
                            self.logger.debug(f"🔄 Request cancelled for {os.path.basename(file_path)}: {lsp_error.message}")
                        return file_path, [], f"LSP Request Cancelled: {lsp_error.message}"
                    elif lsp_error.code == ErrorCodes.ServerNotInitialized:
                        self.logger.error(f"❌ Server not initialized for {os.path.basename(file_path)}: {lsp_error.message}")
                        return file_path, [], f"LSP Server Not Initialized: {lsp_error.message}"
                    else:
                        self.logger.warning(f"⚠️  LSP Error for {os.path.basename(file_path)}: {lsp_error}")
                        return file_path, [], f"LSP Error ({lsp_error.code}): {lsp_error.message}"

                enhanced_diagnostics = []
                for diag in lsp_diagnostics:
                    # Extract diagnostic information using proper LSP types
                    range_info = diag.get("range", {})
                    start_pos = range_info.get("start", {})
                    line = start_pos.get("line", 0) + 1  # LSP uses 0-based line numbers
                    column = start_pos.get("character", 0) + 1  # LSP uses 0-based character numbers

                    # Create proper LSP Position and Range objects
                    position_start = Position(line=start_pos.get("line", 0), character=start_pos.get("character", 0))
                    position_end = Position(line=range_info.get("end", {}).get("line", 0), character=range_info.get("end", {}).get("character", 0))
                    range_obj = Range(start=position_start, end=position_end)

                    # Create Location object for enhanced diagnostic
                    location_obj = Location(uri=f"file://{file_path}", range=range_obj)

                    # Map severity with MessageType integration
                    severity_map = {
                        DiagnosticsSeverity.ERROR: "ERROR",
                        DiagnosticsSeverity.WARNING: "WARNING",
                        DiagnosticsSeverity.INFORMATION: "INFO",
                        DiagnosticsSeverity.HINT: "HINT",
                    }

                    severity_value = diag.get("severity", DiagnosticsSeverity.ERROR)
                    severity = severity_map.get(severity_value, "UNKNOWN")

                    # Apply severity filter
                    if severity_filter and severity_value != severity_filter:
                        continue

                    # Extract error code if available
                    diagnostic_code = diag.get("code")
                    error_code = None
                    if diagnostic_code and isinstance(diagnostic_code, int):
                        try:
                            error_code = ErrorCodes(diagnostic_code)
                        except ValueError:
                            pass

                    # Create enhanced diagnostic with LSP protocol information
                    enhanced_diag = EnhancedDiagnostic(
                        file_path=file_path,
                        line=line,
                        column=column,
                        severity=severity,
                        message=diag.get("message", "No message"),
                        code=str(diag.get("code", "")),
                        source=diag.get("source", "lsp"),
                        category="lsp_diagnostic",
                        tags=["serena_lsp_analysis"],
                        error_code=error_code,
                        range_info=range_info,
                        location={"uri": f"file://{file_path}", "range": range_info},
                    )
                    enhanced_diagnostics.append(enhanced_diag)

                return file_path, enhanced_diagnostics, None

            except Exception as e:
                self.server_info.error_count += 1
                self.logger.warning(f"⚠️  Unexpected error analyzing {os.path.basename(file_path)}: {e}")
                return file_path, [], str(e)

        # Process files with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(analyze_single_file, file_path): file_path for file_path in source_files}

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    analyzed_file, diagnostics, error = future.result()

                    with self.lock:
                        if error is None:
                            all_diagnostics.extend(diagnostics)
                            self.processed_files += 1
                        else:
                            self.failed_files += 1
                            self.logger.warning(f"⚠️  Failed to analyze {os.path.basename(analyzed_file)}: {error}")

                except Exception as e:
                    with self.lock:
                        self.failed_files += 1
                        self.logger.error(f"❌ Unexpected error processing {os.path.basename(file_path)}: {e}")

        # Final statistics
        analysis_time = time.time() - self.analysis_start_time
        self.performance_stats["analysis_time"] = analysis_time
        self.total_diagnostics = len(all_diagnostics)

        self.logger.info("=" * 80)
        self.logger.info("📋 COMPREHENSIVE SERENA LSP ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {self.processed_files}")
        self.logger.info(f"❌ Files failed: {self.failed_files}")
        self.logger.info(f"🔍 Total LSP diagnostics found: {self.total_diagnostics}")
        self.logger.info(f"⏱️  Analysis time: {analysis_time:.2f} seconds")
        self.logger.info("=" * 80)

        return all_diagnostics

    def format_diagnostic_output(self, diagnostics: List[EnhancedDiagnostic], include_runtime: bool = True) -> str:
        """Format diagnostics in the requested output format with enhanced categorization."""
        all_diagnostics = diagnostics.copy()
        
        # Add runtime errors if available and requested
        if include_runtime and self.runtime_collector:
            try:
                runtime_errors = self.runtime_collector.get_runtime_errors()
                for runtime_error in runtime_errors:
                    # Convert RuntimeError to EnhancedDiagnostic
                    enhanced_diag = EnhancedDiagnostic(
                        file_path=runtime_error.file_path,
                        line=runtime_error.line,
                        column=runtime_error.column,
                        severity="ERROR",
                        message=f"[RUNTIME] {runtime_error.error_type}: {runtime_error.error_message}",
                        code=runtime_error.error_type,
                        source="runtime",
                        category="runtime_error",
                        tags=["runtime_error", "execution_error"]
                    )
                    all_diagnostics.append(enhanced_diag)
            except Exception as e:
                self.logger.warning(f"⚠️  Error including runtime errors: {e}")
        
        if not all_diagnostics:
            return "ERRORS: ['0']\nNo errors found."

        # Sort diagnostics by severity (ERROR first), then by file, then by line
        severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3, "UNKNOWN": 4}

        all_diagnostics.sort(key=lambda d: (
            severity_priority.get(d.severity, 5),
            d.file_path.lower(),
            d.line,
        ))

        # Generate output with enhanced categorization
        error_count = len(all_diagnostics)
        critical_count = len([d for d in all_diagnostics if d.severity == "ERROR"])
        warning_count = len([d for d in all_diagnostics if d.severity == "WARNING"])
        runtime_count = len([d for d in all_diagnostics if d.source == "runtime"])
        
        output_lines = [f"ERRORS: {error_count} [⚠️ Critical: {critical_count}] [👉 Major: {warning_count}] [🔥 Runtime: {runtime_count}]"]

        # Add each formatted diagnostic
        for i, diag in enumerate(all_diagnostics, 1):
            file_name = os.path.basename(diag.file_path)
            location = f"line {diag.line}, col {diag.column}"

            # Clean and truncate message for better readability
            clean_message = diag.message.replace("\n", " ").replace("\r", " ")
            clean_message = " ".join(clean_message.split())

            if len(clean_message) > 200:
                clean_message = clean_message[:197] + "..."

            # Enhanced metadata formatting with LSP protocol information
            metadata_parts = [f"severity: {diag.severity}"]

            if diag.code and diag.code != "":
                metadata_parts.append(f"code: {diag.code}")

            if diag.source and diag.source != "lsp":
                metadata_parts.append(f"source: {diag.source}")

            # Add LSP error code information if available
            if diag.error_code:
                metadata_parts.append(f"lsp_error: {diag.error_code.name}")

            # Add category information
            if diag.category and diag.category != "lsp_diagnostic":
                metadata_parts.append(f"category: {diag.category}")

            other_types = ", ".join(metadata_parts)

            # Enhanced format matching the requested output
            severity_icon = "⚠️" if diag.severity == "ERROR" else "👉" if diag.severity == "WARNING" else "🔍"
            
            # Format: 1 ⚠️- projectname'/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]
            diagnostic_line = f"{i} {severity_icon}- {diag.file_path} / {location} - '{clean_message}' [{other_types}]"
            output_lines.append(diagnostic_line)

        return "\n".join(output_lines)

    def _collect_symbol_analysis(self, project: Project, language_server: SolidLanguageServer) -> None:
        """Collect comprehensive symbol analysis from the project."""
        try:
            symbol_start_time = time.time()
            self.logger.info("🔍 Starting comprehensive symbol analysis...")
            
            # Get all source files for symbol analysis
            source_files = project.gather_source_files()
            symbol_files_processed = 0
            
            for file_path in source_files[:50]:  # Limit to first 50 files for performance
                try:
                    # Get document symbols
                    symbols = self._get_document_symbols(language_server, file_path)
                    if symbols:
                        self.collected_symbols.extend(symbols)
                        symbol_files_processed += 1
                    
                    # Get symbol references for key symbols
                    if len(self.collected_symbols) > 0:
                        self._collect_symbol_references(language_server, file_path)
                    
                except Exception as e:
                    self.logger.debug(f"Error analyzing symbols in {file_path}: {e}")
                    continue
            
            symbol_time = time.time() - symbol_start_time
            self.performance_stats["symbol_analysis_time"] = symbol_time
            self.total_symbols = len(self.collected_symbols)
            
            self.logger.info(f"✅ Symbol analysis complete: {self.total_symbols} symbols from {symbol_files_processed} files in {symbol_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Error during symbol analysis: {e}")

    def _get_document_symbols(self, language_server: SolidLanguageServer, file_path: str) -> List[EnhancedSymbolInfo]:
        """Get document symbols from a file using LSP."""
        try:
            # Request document symbols from LSP server
            symbols_response = language_server.request_text_document_symbols(file_path)
            enhanced_symbols = []
            
            for symbol_data in symbols_response:
                try:
                    # Extract symbol information
                    symbol_name = symbol_data.get("name", "unknown")
                    symbol_kind = symbol_data.get("kind", SymbolKind.Variable)
                    
                    # Get location information
                    location_data = symbol_data.get("location", {})
                    if not location_data and "range" in symbol_data:
                        # Some servers return range directly
                        location_data = {
                            "uri": f"file://{file_path}",
                            "range": symbol_data["range"]
                        }
                    
                    # Create enhanced symbol info
                    enhanced_symbol = EnhancedSymbolInfo(
                        name=symbol_name,
                        kind=symbol_kind,
                        location=location_data,
                        container_name=symbol_data.get("containerName"),
                        detail=symbol_data.get("detail"),
                        documentation=self._extract_symbol_documentation(symbol_data),
                        tags=symbol_data.get("tags", [])
                    )
                    
                    enhanced_symbols.append(enhanced_symbol)
                    
                except Exception as e:
                    self.logger.debug(f"Error processing symbol {symbol_data}: {e}")
                    continue
            
            return enhanced_symbols
            
        except Exception as e:
            self.logger.debug(f"Error getting document symbols for {file_path}: {e}")
            return []

    def _collect_symbol_references(self, language_server: SolidLanguageServer, file_path: str) -> None:
        """Collect symbol references for important symbols."""
        try:
            # Get a few key symbols to analyze references for
            key_symbols = [s for s in self.collected_symbols[-10:] if s.kind in [
                SymbolKind.Function, SymbolKind.Class, SymbolKind.Method
            ]]
            
            for symbol in key_symbols:
                try:
                    # Extract position from symbol location
                    location = symbol.location
                    if "range" in location and "start" in location["range"]:
                        start_pos = location["range"]["start"]
                        line = start_pos.get("line", 0)
                        character = start_pos.get("character", 0)
                        
                        # Request references
                        references = language_server.request_references(file_path, line, character)
                        if references:
                            self.symbol_references[symbol.name] = references
                            
                except Exception as e:
                    self.logger.debug(f"Error getting references for symbol {symbol.name}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error collecting symbol references: {e}")

    def _extract_symbol_documentation(self, symbol_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract documentation from symbol data."""
        try:
            # Check for documentation in various formats
            if "documentation" in symbol_data:
                doc = symbol_data["documentation"]
                if isinstance(doc, str):
                    return {"kind": "plaintext", "value": doc}
                elif isinstance(doc, dict):
                    return doc
            
            # Check for detail field as fallback
            if "detail" in symbol_data and symbol_data["detail"]:
                return {"kind": "plaintext", "value": symbol_data["detail"]}
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting symbol documentation: {e}")
            return None

    def get_completion_analysis(self, language_server: SolidLanguageServer, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get completion analysis at a specific position."""
        try:
            completions = language_server.request_completion(file_path, line, character)
            enhanced_completions = []
            
            for completion in completions:
                enhanced_completion = {
                    "label": completion.get("label", ""),
                    "kind": completion.get("kind", CompletionItemKind.Text),
                    "detail": completion.get("detail", ""),
                    "documentation": completion.get("documentation", ""),
                    "insert_text": completion.get("insertText", completion.get("label", "")),
                    "sort_text": completion.get("sortText", ""),
                    "filter_text": completion.get("filterText", "")
                }
                enhanced_completions.append(enhanced_completion)
            
            return enhanced_completions
            
        except Exception as e:
            self.logger.debug(f"Error getting completions: {e}")
            return []

    def get_hover_analysis(self, language_server: SolidLanguageServer, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get hover information at a specific position."""
        try:
            hover_info = language_server.request_hover(file_path, line, character)
            if hover_info:
                return {
                    "contents": hover_info.get("contents", ""),
                    "range": hover_info.get("range", {}),
                    "markup_kind": hover_info.get("contents", {}).get("kind", "plaintext") if isinstance(hover_info.get("contents"), dict) else "plaintext"
                }
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting hover info: {e}")
            return None

    def get_signature_analysis(self, language_server: SolidLanguageServer, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get signature help at a specific position."""
        try:
            signature_help = language_server.request_signature_help(file_path, line, character)
            if signature_help:
                signatures = signature_help.get("signatures", [])
                active_signature = signature_help.get("activeSignature", 0)
                active_parameter = signature_help.get("activeParameter", 0)
                
                enhanced_signatures = []
                for sig in signatures:
                    enhanced_sig = {
                        "label": sig.get("label", ""),
                        "documentation": sig.get("documentation", ""),
                        "parameters": sig.get("parameters", []),
                        "active_parameter": active_parameter
                    }
                    enhanced_signatures.append(enhanced_sig)
                
                return {
                    "signatures": enhanced_signatures,
                    "active_signature": active_signature,
                    "active_parameter": active_parameter
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting signature help: {e}")
            return None

    def analyze_repository(
        self,
        repo_url_or_path: str,
        severity_filter: Optional[str] = None,
        language_override: Optional[str] = None,
        output_format: str = "text",
    ) -> Union[str, Dict[str, Any]]:
        """Main comprehensive analysis function using Serena and SolidLSP."""
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

            self.performance_stats["clone_time"] = time.time() - clone_start

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
                    "ERROR": DiagnosticsSeverity.ERROR,
                    "WARNING": DiagnosticsSeverity.WARNING,
                    "INFO": DiagnosticsSeverity.INFORMATION,
                    "HINT": DiagnosticsSeverity.HINT,
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
            
            # Initialize runtime error collection with actual repo path
            if self.enable_runtime_errors and not self.runtime_collector:
                try:
                    self.runtime_collector = RuntimeErrorCollector(repo_path)
                    self.runtime_collector.start_collection()
                    self.logger.info("🔥 Runtime error collection started")
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to start runtime error collection: {e}")
                    self.enable_runtime_errors = False
            
            self.performance_stats["setup_time"] = time.time() - setup_start

            # Step 4: Language server initialization
            lsp_start = time.time()
            self.logger.info("🔧 Starting SolidLSP language server...")
            language_server = self.start_language_server(project)

            # Give the language server time to fully initialize
            initialization_time = 5 if self.total_files > 100 else 2
            self.logger.info(f"⏳ Allowing {initialization_time}s for LSP initialization...")
            time.sleep(initialization_time)

            self.performance_stats["lsp_start_time"] = time.time() - lsp_start

            # Step 5: Comprehensive diagnostic collection
            self.logger.info("🔍 Beginning comprehensive Serena LSP diagnostic collection...")
            diagnostics = self.collect_diagnostics(project, language_server, severity)

            # Step 5.5: Symbol analysis if enabled
            if self.enable_symbols:
                self.logger.info("🔍 Performing comprehensive symbol analysis...")
                self._collect_symbol_analysis(project, language_server)

            # Step 6: Format results
            self.logger.info("📋 Formatting comprehensive results...")
            result = self.format_diagnostic_output(diagnostics)

            # Final performance summary
            total_time = time.time() - total_start_time
            self.performance_stats["total_time"] = total_time

            self.logger.info("🎉 COMPREHENSIVE SERENA LSP ANALYSIS COMPLETED!")
            self.logger.info("=" * 80)
            self.logger.info("⏱️  PERFORMANCE SUMMARY:")
            self.logger.info(f"   📥 Repository setup: {self.performance_stats['clone_time']:.2f}s")
            self.logger.info(f"   ⚙️  Project configuration: {self.performance_stats['setup_time']:.2f}s")
            self.logger.info(f"   🔧 LSP server startup: {self.performance_stats['lsp_start_time']:.2f}s")
            self.logger.info(f"   🔍 Diagnostic analysis: {self.performance_stats.get('analysis_time', 0):.2f}s")
            if self.enable_symbols:
                self.logger.info(f"   🔍 Symbol analysis: {self.performance_stats.get('symbol_analysis_time', 0):.2f}s")
                self.logger.info(f"   📊 Total symbols found: {self.total_symbols}")
            self.logger.info(f"   🎯 Total execution time: {total_time:.2f}s")
            self.logger.info("=" * 80)

            return result

        except Exception as e:
            self.logger.error(f"❌ COMPREHENSIVE SERENA LSP ANALYSIS FAILED: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")

            return f"ERRORS: ['0']\nSerena LSP analysis failed: {e}"


def main():
    """Main entry point for comprehensive Serena LSP error analysis."""
    parser = argparse.ArgumentParser(
        description="🚀 COMPREHENSIVE SERENA LSP ERROR ANALYSIS TOOL - Analyzes ENTIRE codebases using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("repository", help="Repository URL or local path to analyze (analyzes ALL source files)")
    parser.add_argument("--severity", choices=["ERROR", "WARNING", "INFO", "HINT"], help="Filter diagnostics by severity level")
    parser.add_argument("--language", help="Override automatic language detection")
    parser.add_argument("--timeout", type=float, default=600, help="Timeout for LSP operations in seconds")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of parallel workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--symbols", action="store_true", help="Enable comprehensive symbol analysis")
    parser.add_argument("--runtime-errors", action="store_true", help="Enable runtime error collection")

    args = parser.parse_args()

    print("🚀 COMPREHENSIVE SERENA LSP ERROR ANALYSIS TOOL")
    print("=" * 80)

    try:
        with SerenaLSPAnalyzer(
            verbose=args.verbose,
            timeout=args.timeout,
            max_workers=args.max_workers,
            enable_symbols=args.symbols,
            enable_runtime_errors=args.runtime_errors,
        ) as analyzer:
            result = analyzer.analyze_repository(
                args.repository,
                severity_filter=args.severity,
                language_override=args.language,
            )

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


# ============================================================================
# ENHANCED INTEGRATION CLASS
# ============================================================================

class EnhancedSerenaIntegration:
    """
    Enhanced integration class that provides unified access to all Serena capabilities
    including LSP diagnostics, runtime error collection, and comprehensive analysis.
    """
    
    def __init__(self, repo_path: str, enable_runtime_errors: bool = True):
        self.repo_path = repo_path
        self.analyzer = SerenaLSPAnalyzer(
            verbose=True,
            enable_runtime_errors=enable_runtime_errors
        )
        
    def get_all_errors(self) -> str:
        """Get all errors (static and runtime) in the enhanced format."""
        return self.analyzer.analyze_repository(self.repo_path)
    
    def get_runtime_errors(self) -> List[RuntimeError]:
        """Get only runtime errors."""
        if self.analyzer.runtime_collector:
            return self.analyzer.runtime_collector.get_runtime_errors()
        return []
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive analysis of the codebase."""
        result = self.analyzer.analyze_repository(self.repo_path)
        
        runtime_summary = {}
        if self.analyzer.runtime_collector:
            runtime_errors = self.analyzer.runtime_collector.get_runtime_errors()
            runtime_summary = {
                'total_runtime_errors': len(runtime_errors),
                'runtime_error_types': list(set(e.error_type for e in runtime_errors)),
                'files_with_runtime_errors': list(set(e.file_path for e in runtime_errors))
            }
        
        symbol_summary = {}
        if self.analyzer.enable_symbols:
            symbol_summary = {
                'total_symbols': len(self.analyzer.collected_symbols),
                'symbol_types': list(set(s.kind for s in self.analyzer.collected_symbols)),
                'files_with_symbols': list(set(s.location.get('uri', '').replace('file://', '') for s in self.analyzer.collected_symbols if s.location)),
                'symbol_references_count': len(self.analyzer.symbol_references)
            }
        
        return {
            'formatted_output': result,
            'runtime_summary': runtime_summary,
            'symbol_summary': symbol_summary,
            'performance_stats': self.analyzer.performance_stats
        }
    
    def get_symbol_analysis(self) -> Dict[str, Any]:
        """Get detailed symbol analysis results."""
        if not self.analyzer.enable_symbols:
            return {'error': 'Symbol analysis not enabled'}
        
        return {
            'total_symbols': len(self.analyzer.collected_symbols),
            'symbol_references': self.analyzer.symbol_references,
            'analysis_time': self.analyzer.performance_stats.get('symbol_analysis_time', 0)
        }
    
    def clear_runtime_errors(self) -> None:
        """Clear all runtime errors."""
        if self.analyzer.runtime_collector:
            self.analyzer.runtime_collector.clear_runtime_errors()
    
    def shutdown(self) -> None:
        """Shutdown the integration."""
        self.analyzer.cleanup()


def create_enhanced_serena_integration(repo_path: str, enable_runtime_errors: bool = True) -> EnhancedSerenaIntegration:
    """Create an enhanced Serena integration for a repository."""
    return EnhancedSerenaIntegration(repo_path, enable_runtime_errors)


def get_comprehensive_errors(repo_path: str, include_runtime: bool = True) -> str:
    """Get comprehensive error analysis for a repository."""
    with SerenaLSPAnalyzer(verbose=True, enable_runtime_errors=include_runtime) as analyzer:
        return analyzer.analyze_repository(repo_path)


if __name__ == "__main__":
    main()
