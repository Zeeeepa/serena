#!/usr/bin/env python3
"""
Serena LSP Error Analysis Tool - Enhanced Version

This tool provides comprehensive LSP error analysis using Serena and SolidLSP
with improved error handling, performance optimization, and detailed reporting.

Usage:
    python serena_analysis.py <repo_url_or_path> [options]

Examples:
    python serena_analysis.py https://github.com/user/repo.git
    python serena_analysis.py /path/to/local/repo --severity ERROR
    python serena_analysis.py . --verbose --timeout 120 --max-workers 8
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple, Union
from urllib.parse import urlparse

# Enhanced imports with fallback handling
try:
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.ls_types import (
        DiagnosticsSeverity, ErrorCodes, LSPErrorCodes, DiagnosticSeverity,
        Diagnostic, Position, Range, MarkupContent, Location, MarkupKind,
        CompletionItemKind, CompletionItem, UnifiedSymbolInformation,
        SymbolKind, SymbolTag
    )
    from solidlsp.settings import SolidLSPSettings
    from solidlsp import SolidLanguageServer
    from serena.symbol import (
        LanguageServerSymbolRetriever, ReferenceInLanguageServerSymbol,
        LanguageServerSymbol, Symbol, PositionInFile, LanguageServerSymbolLocation
    )
    from solidlsp.lsp_protocol_handler.server import (
        ProcessLaunchInfo, LSPError, MessageType
    )
    SERENA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Serena/SolidLSP not fully available: {e}")
    print("📦 Falling back to mock analysis mode")
    SERENA_AVAILABLE = False
    
    # Mock classes for fallback
    class Language:
        PYTHON = "python"
        TYPESCRIPT = "typescript"
        JAVASCRIPT = "javascript"
        JAVA = "java"
        CSHARP = "csharp"
        CPP = "cpp"
        RUST = "rust"
        GO = "go"
        PHP = "php"
        RUBY = "ruby"
        KOTLIN = "kotlin"
        DART = "dart"
        CLOJURE = "clojure"
        ELIXIR = "elixir"
        TERRAFORM = "terraform"
    
    class DiagnosticsSeverity:
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4


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
    tags: List[str] = None
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class MockLSPAnalyzer:
    """Mock LSP analyzer for when Serena is not available."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        # Common error patterns by language
        self.error_patterns = {
            'python': [
                (r'print\s*\([^)]*\)', 'Print statement found - potential debug code', 'WARNING'),
                (r'TODO|FIXME|XXX', 'TODO/FIXME comment found', 'INFO'),
                (r'except\s*:', 'Bare except clause - should specify exception type', 'WARNING'),
                (r'import\s+\*', 'Wildcard import - not recommended', 'WARNING'),
                (r'eval\s*\(', 'Use of eval() - potential security risk', 'ERROR'),
                (r'exec\s*\(', 'Use of exec() - potential security risk', 'ERROR'),
            ],
            'typescript': [
                (r'console\.log\s*\(', 'Console.log found - potential debug code', 'WARNING'),
                (r'any\s*[;\]\}]', 'Use of any type - consider more specific typing', 'HINT'),
                (r'@ts-ignore', '@ts-ignore comment - consider fixing the underlying issue', 'WARNING'),
            ],
            'javascript': [
                (r'console\.log\s*\(', 'Console.log found - potential debug code', 'WARNING'),
                (r'debugger;', 'Debugger statement found', 'WARNING'),
                (r'==\s*(?!==)', 'Use === instead of == for strict equality', 'WARNING'),
                (r'var\s+', 'Use let or const instead of var', 'HINT'),
            ]
        }
    
    def analyze_file(self, file_path: str, language: str) -> List[EnhancedDiagnostic]:
        """Analyze a single file using pattern matching."""
        import re
        
        if language not in self.error_patterns:
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            self.logger.warning(f"Could not read file {file_path}: {e}")
            return []
        
        diagnostics = []
        lines = content.split('\n')
        
        for pattern, message, severity in self.error_patterns[language]:
            for line_num, line in enumerate(lines):
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    diagnostic = EnhancedDiagnostic(
                        file_path=file_path,
                        line=line_num + 1,
                        column=match.start() + 1,
                        severity=severity,
                        message=message,
                        code=f"mock_{pattern[:20]}",
                        source="mock_analyzer",
                        category="code_quality",
                        tags=["mock_analysis"]
                    )
                    diagnostics.append(diagnostic)
        
        return diagnostics


class EnhancedSerenaAnalyzer:
    """Enhanced comprehensive LSP analyzer with improved error handling and performance."""
    
    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4):
        """Initialize the enhanced analyzer."""
        self.verbose = verbose
        self.timeout = timeout
        self.max_workers = max_workers
        self.temp_dir: Optional[str] = None
        self.project: Optional[Any] = None
        self.language_server: Optional[Any] = None
        
        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.analysis_start_time = None
        self.lock = threading.Lock()
        
        # Set up logging
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
        
        # Initialize mock analyzer as fallback
        self.mock_analyzer = MockLSPAnalyzer(verbose)
        
        if verbose:
            self.logger.info("🚀 Enhanced Serena LSP Analyzer initialized")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
            self.logger.info(f"📦 Serena available: {SERENA_AVAILABLE}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if SERENA_AVAILABLE and self.language_server:
                if hasattr(self.language_server, 'is_running') and self.language_server.is_running():
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
    
    def detect_language(self, repo_path: str) -> str:
        """Detect the primary programming language of the repository."""
        self.logger.info("🔍 Detecting repository language...")
        
        # Language detection based on file extensions
        language_indicators = {
            'python': ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            'typescript': ['.ts', '.tsx', 'tsconfig.json'],
            'javascript': ['.js', '.jsx', 'package.json', 'yarn.lock'],
            'java': ['.java', 'pom.xml', 'build.gradle'],
            'csharp': ['.cs', '.csproj', '.sln'],
            'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp', 'CMakeLists.txt'],
            'rust': ['.rs', 'Cargo.toml'],
            'go': ['.go', 'go.mod'],
            'php': ['.php', 'composer.json'],
            'ruby': ['.rb', 'Gemfile'],
        }
        
        file_counts = {lang: 0 for lang in language_indicators.keys()}
        
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
        
        detected_lang = max(file_counts, key=file_counts.get)
        
        if file_counts[detected_lang] == 0:
            self.logger.warning("Could not detect language, defaulting to Python")
            detected_lang = 'python'
        
        self.logger.info(f"✅ Detected language: {detected_lang}")
        return detected_lang
    
    def get_source_files(self, repo_path: str, language: str) -> List[str]:
        """Get all source files for the detected language."""
        extensions_map = {
            'python': ['.py'],
            'typescript': ['.ts', '.tsx'],
            'javascript': ['.js', '.jsx'],
            'java': ['.java'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
            'rust': ['.rs'],
            'go': ['.go'],
            'php': ['.php'],
            'ruby': ['.rb'],
        }
        
        extensions = extensions_map.get(language, ['.py'])
        source_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'target', 'build', 'dist', 'vendor', '.git'
            ]]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    source_files.append(os.path.join(root, file))
        
        return source_files
    
    def setup_serena_project(self, repo_path: str, language: str) -> Any:
        """Set up a Serena project if available."""
        if not SERENA_AVAILABLE:
            return None
        
        try:
            # Map string language to Language enum
            language_map = {
                'python': Language.PYTHON,
                'typescript': Language.TYPESCRIPT,
                'javascript': Language.TYPESCRIPT,  # Use TS server for JS
                'java': Language.JAVA,
                'csharp': Language.CSHARP,
                'cpp': Language.CPP,
                'rust': Language.RUST,
                'go': Language.GO,
                'php': Language.PHP,
                'ruby': Language.RUBY,
            }
            
            lang_enum = language_map.get(language, Language.PYTHON)
            
            # Create project configuration
            project_config = ProjectConfig(
                project_name=os.path.basename(repo_path),
                language=lang_enum,
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
            
        except Exception as e:
            self.logger.warning(f"Failed to setup Serena project: {e}")
            return None
    
    def start_language_server(self, project: Any) -> Any:
        """Start the language server if Serena is available."""
        if not SERENA_AVAILABLE or not project:
            return None
        
        try:
            self.language_server = project.create_language_server(
                log_level=logging.DEBUG if self.verbose else logging.WARNING,
                ls_timeout=self.timeout
            )
            
            self.language_server.start()
            
            if not self.language_server.is_running():
                raise RuntimeError("Language server failed to start")
            
            self.logger.info("✅ Language server started successfully")
            return self.language_server
            
        except Exception as e:
            self.logger.warning(f"Failed to start language server: {e}")
            return None
    
    def collect_lsp_diagnostics(self, source_files: List[str], language_server: Any, 
                               severity_filter: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """Collect diagnostics using real LSP if available."""
        if not language_server:
            return []
        
        diagnostics = []
        
        def analyze_file_lsp(file_path: str) -> List[EnhancedDiagnostic]:
            """Analyze a single file using LSP."""
            try:
                # Get diagnostics from LSP
                lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)
                
                file_diagnostics = []
                for diag in lsp_diagnostics:
                    # Extract diagnostic information
                    range_info = diag.get('range', {})
                    start_pos = range_info.get('start', {})
                    line = start_pos.get('line', 0) + 1
                    column = start_pos.get('character', 0) + 1
                    
                    severity_map = {
                        DiagnosticsSeverity.ERROR.value: 'ERROR',
                        DiagnosticsSeverity.WARNING.value: 'WARNING',
                        DiagnosticsSeverity.INFORMATION.value: 'INFO',
                        DiagnosticsSeverity.HINT.value: 'HINT'
                    }
                    
                    severity = severity_map.get(diag.get('severity'), 'UNKNOWN')
                    
                    # Apply severity filter
                    if severity_filter and severity != severity_filter:
                        continue
                    
                    enhanced_diag = EnhancedDiagnostic(
                        file_path=file_path,
                        line=line,
                        column=column,
                        severity=severity,
                        message=diag.get('message', 'No message'),
                        code=str(diag.get('code', '')),
                        source=diag.get('source', 'lsp'),
                        category='lsp_diagnostic',
                        tags=['lsp_analysis']
                    )
                    file_diagnostics.append(enhanced_diag)
                
                return file_diagnostics
                
            except Exception as e:
                self.logger.warning(f"LSP analysis failed for {file_path}: {e}")
                return []
        
        # Process files with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(analyze_file_lsp, file_path): file_path 
                for file_path in source_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_diagnostics = future.result()
                    diagnostics.extend(file_diagnostics)
                    
                    with self.lock:
                        self.processed_files += 1
                        if self.verbose and len(file_diagnostics) > 0:
                            self.logger.debug(f"✅ LSP found {len(file_diagnostics)} diagnostics in {os.path.basename(file_path)}")
                            
                except Exception as e:
                    with self.lock:
                        self.failed_files += 1
                        self.logger.warning(f"Failed to process {file_path}: {e}")
        
        return diagnostics
    
    def collect_mock_diagnostics(self, source_files: List[str], language: str,
                                severity_filter: Optional[str] = None) -> List[EnhancedDiagnostic]:
        """Collect diagnostics using mock analyzer."""
        diagnostics = []
        
        def analyze_file_mock(file_path: str) -> List[EnhancedDiagnostic]:
            """Analyze a single file using mock analyzer."""
            try:
                file_diagnostics = self.mock_analyzer.analyze_file(file_path, language)
                
                # Apply severity filter
                if severity_filter:
                    file_diagnostics = [d for d in file_diagnostics if d.severity == severity_filter]
                
                return file_diagnostics
                
            except Exception as e:
                self.logger.warning(f"Mock analysis failed for {file_path}: {e}")
                return []
        
        # Process files with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(analyze_file_mock, file_path): file_path 
                for file_path in source_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_diagnostics = future.result()
                    diagnostics.extend(file_diagnostics)
                    
                    with self.lock:
                        self.processed_files += 1
                        if self.verbose and len(file_diagnostics) > 0:
                            self.logger.debug(f"✅ Mock found {len(file_diagnostics)} diagnostics in {os.path.basename(file_path)}")
                            
                except Exception as e:
                    with self.lock:
                        self.failed_files += 1
                        self.logger.warning(f"Failed to process {file_path}: {e}")
        
        return diagnostics
    
    def analyze_repository(self, repo_url_or_path: str, 
                          severity_filter: Optional[str] = None,
                          language_override: Optional[str] = None,
                          output_format: str = 'text') -> Union[str, Dict[str, Any]]:
        """Main comprehensive analysis function."""
        total_start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting Enhanced LSP Error Analysis")
            self.logger.info("=" * 80)
            self.logger.info(f"📁 Target: {repo_url_or_path}")
            self.logger.info(f"🔍 Severity filter: {severity_filter or 'ALL'}")
            self.logger.info(f"🌐 Language override: {language_override or 'AUTO-DETECT'}")
            self.logger.info(f"📦 Serena available: {SERENA_AVAILABLE}")
            self.logger.info("=" * 80)
            
            # Step 1: Repository handling
            clone_start = time.time()
            if self.is_git_url(repo_url_or_path):
                repo_path = self.clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
                if not os.path.exists(repo_path):
                    raise FileNotFoundError(f"Local path does not exist: {repo_path}")
            
            self.performance_stats['clone_time'] = time.time() - clone_start
            
            # Step 2: Language detection
            language = language_override or self.detect_language(repo_path)
            
            # Step 3: Get source files
            source_files = self.get_source_files(repo_path, language)
            self.total_files = len(source_files)
            
            if self.total_files == 0:
                self.logger.warning("⚠️  No source files found")
                return self._format_empty_result(output_format)
            
            self.logger.info(f"📊 Found {self.total_files} source files to analyze")
            
            # Step 4: Analysis setup
            setup_start = time.time()
            project = self.setup_serena_project(repo_path, language) if SERENA_AVAILABLE else None
            language_server = self.start_language_server(project) if project else None
            self.performance_stats['setup_time'] = time.time() - setup_start
            
            # Step 5: Diagnostic collection
            self.analysis_start_time = time.time()
            self.processed_files = 0
            self.failed_files = 0
            
            if language_server:
                self.logger.info("🔍 Using real LSP analysis...")
                diagnostics = self.collect_lsp_diagnostics(source_files, language_server, severity_filter)
            else:
                self.logger.info("🔍 Using mock pattern analysis...")
                diagnostics = self.collect_mock_diagnostics(source_files, language, severity_filter)
            
            self.performance_stats['analysis_time'] = time.time() - self.analysis_start_time
            self.total_diagnostics = len(diagnostics)
            
            # Step 6: Generate results
            results = self._generate_results(
                diagnostics, language, repo_path, total_start_time
            )
            
            # Step 7: Format output
            if output_format == 'json':
                return results.to_dict()
            else:
                return self._format_text_output(results)
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            
            if output_format == 'json':
                return {"error": str(e), "diagnostics": []}
            else:
                return f"ERRORS: ['0']\nAnalysis failed: {e}"
    
    def _generate_results(self, diagnostics: List[EnhancedDiagnostic], 
                         language: str, repo_path: str, start_time: float) -> AnalysisResults:
        """Generate comprehensive analysis results."""
        # Count diagnostics by severity
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
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _format_empty_result(self, output_format: str) -> Union[str, Dict[str, Any]]:
        """Format empty result."""
        if output_format == 'json':
            return {"total_diagnostics": 0, "diagnostics": [], "message": "No source files found"}
        else:
            return "ERRORS: ['0']\nNo source files found."
    
    def _format_text_output(self, results: AnalysisResults) -> str:
        """Format results as text output."""
        if not results.diagnostics:
            return "ERRORS: ['0']\nNo errors found."
        
        # Start with header
        output_lines = [f"ERRORS: ['{results.total_diagnostics}']"]
        
        # Add summary
        output_lines.append(f"\n📊 ANALYSIS SUMMARY:")
        output_lines.append(f"   Total files: {results.total_files}")
        output_lines.append(f"   Processed: {results.processed_files}")
        output_lines.append(f"   Failed: {results.failed_files}")
        output_lines.append(f"   Language: {results.language_detected}")
        output_lines.append(f"   Analysis time: {results.performance_stats['analysis_time']:.2f}s")
        
        # Add severity breakdown
        if results.diagnostics_by_severity:
            output_lines.append(f"\n🔍 BY SEVERITY:")
            for severity, count in sorted(results.diagnostics_by_severity.items()):
                output_lines.append(f"   {severity}: {count}")
        
        # Add detailed diagnostics
        output_lines.append(f"\n📋 DETAILED DIAGNOSTICS:")
        
        for i, diag in enumerate(results.diagnostics, 1):
            file_name = os.path.basename(diag.file_path)
            location = f"line {diag.line}, col {diag.column}"
            error_reason = diag.message.replace('\n', ' ').strip()
            other_types = f"severity: {diag.severity}, code: {diag.code}, source: {diag.source}"
            
            diagnostic_line = f"{i}. '{location}' '{file_name}' '{error_reason}' '{other_types}'"
            output_lines.append(diagnostic_line)
        
        return '\n'.join(output_lines)


def main():
    """Main entry point for enhanced LSP error analysis."""
    parser = argparse.ArgumentParser(
        description="Enhanced LSP Error Analysis Tool - Comprehensive codebase analysis using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 ENHANCED ANALYSIS EXAMPLES:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR --verbose
  %(prog)s . --timeout 600 --max-workers 8 --language python
  %(prog)s https://github.com/Zeeeepa/graph-sitter --output json

📊 OUTPUT FORMATS:
  text: Human-readable format with summary and detailed diagnostics
  json: Machine-readable JSON format with complete metadata

⚡ PERFORMANCE TIPS:
  • Use --max-workers to control parallel processing
  • Increase --timeout for very large repositories  
  • Use --severity ERROR to focus on critical issues
  • Enable --verbose for detailed progress tracking
  • Use --output json for programmatic processing
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
    
    print("🚀 ENHANCED LSP ERROR ANALYSIS TOOL")
    print("=" * 80)
    print("📋 Configuration:")
    print(f"   📁 Repository: {args.repository}")
    print(f"   🔍 Severity filter: {args.severity or 'ALL'}")
    print(f"   🌐 Language: {args.language or 'AUTO-DETECT'}")
    print(f"   ⏱️  Timeout: {args.timeout}s")
    print(f"   👥 Max workers: {args.max_workers}")
    print(f"   📊 Output format: {args.output}")
    print(f"   📋 Verbose: {args.verbose}")
    print(f"   📦 Serena available: {SERENA_AVAILABLE}")
    print("=" * 80)
    
    # Run the enhanced analysis
    try:
        with EnhancedSerenaAnalyzer(
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
                print("📋 ENHANCED ANALYSIS RESULTS")
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
