"""
SolidLSP integration for runtime error detection.
"""

import logging
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from serena.project import Project
from serena.config.serena_config import ProjectConfig
from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language
from solidlsp.ls_types import Diagnostic, DiagnosticsSeverity
from solidlsp.settings import SolidLSPSettings

from .models import (
    RuntimeError, FileErrorSummary, LanguageErrorSummary, 
    RuntimeErrorSummary, DiagnosticSeverity, Position, Range
)
from .language_detection import detect_repository_languages

logger = logging.getLogger(__name__)


@dataclass
class LanguageServerContext:
    """Context for a language server instance."""
    language: Language
    server: SolidLanguageServer
    project: Project
    file_extensions: Set[str]


class SolidLSPAnalyzer:
    """Analyzer that uses SolidLSP to detect runtime errors in repositories."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the SolidLSP analyzer.
        
        Args:
            temp_dir: Temporary directory for SolidLSP resources
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="solidlsp_")
        self.language_servers: Dict[Language, LanguageServerContext] = {}
        self.supported_languages = {
            Language.PYTHON: {'.py'},
            Language.TYPESCRIPT: {'.ts', '.tsx', '.js', '.jsx'},
            Language.JAVA: {'.java'},
            Language.CSHARP: {'.cs'},
            Language.GO: {'.go'},
            Language.RUST: {'.rs'},
            Language.PHP: {'.php'},
            Language.CLOJURE: {'.clj', '.cljs', '.cljc'},
            Language.ELIXIR: {'.ex', '.exs'},
        }
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def cleanup(self):
        """Clean up language servers and temporary resources."""
        for context in self.language_servers.values():
            try:
                if context.server.server_started:
                    context.server.stop()
            except Exception as e:
                logger.warning(f"Error stopping language server for {context.language}: {e}")
        
        self.language_servers.clear()
        
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory {self.temp_dir}: {e}")
    
    def _get_file_extension(self, file_path: str) -> str:
        """Get the file extension from a file path."""
        return Path(file_path).suffix.lower()
    
    def _get_language_for_file(self, file_path: str) -> Optional[Language]:
        """Determine the programming language for a file based on its extension."""
        ext = self._get_file_extension(file_path)
        for language, extensions in self.supported_languages.items():
            if ext in extensions:
                return language
        return None
    
    def _initialize_language_server(self, language: Language, repo_path: str) -> Optional[LanguageServerContext]:
        """Initialize a language server for the given language and repository."""
        try:
            logger.info(f"Initializing language server for {language.value}")
            
            # Create project configuration
            project_config = ProjectConfig.autogenerate(
                project_root=repo_path,
                project_language=language,
                save_to_disk=False
            )
            
            # Create project instance
            project = Project(
                project_root=repo_path,
                project_config=project_config
            )
            
            # Create language server
            solidlsp_settings = SolidLSPSettings(solidlsp_dir=self.temp_dir)
            language_server = project.create_language_server(
                log_level=logging.WARNING,  # Reduce noise
                ls_timeout=30.0,
                trace_lsp_communication=False
            )
            
            # Start the language server
            language_server.start()
            
            context = LanguageServerContext(
                language=language,
                server=language_server,
                project=project,
                file_extensions=self.supported_languages[language]
            )
            
            self.language_servers[language] = context
            logger.info(f"Successfully initialized language server for {language.value}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to initialize language server for {language.value}: {e}")
            return None
    
    def _convert_diagnostic_to_runtime_error(self, diagnostic: Diagnostic, file_path: str, file_content: Optional[str] = None) -> RuntimeError:
        """Convert a SolidLSP diagnostic to our RuntimeError model."""
        # Convert severity
        severity_map = {
            DiagnosticsSeverity.ERROR: DiagnosticSeverity.ERROR,
            DiagnosticsSeverity.WARNING: DiagnosticSeverity.WARNING,
            DiagnosticsSeverity.INFORMATION: DiagnosticSeverity.INFORMATION,
            DiagnosticsSeverity.HINT: DiagnosticSeverity.HINT,
        }
        
        severity = severity_map.get(diagnostic.get('severity'), DiagnosticSeverity.ERROR)
        
        # Extract range information
        range_data = diagnostic['range']
        start_pos = Position(
            line=range_data['start']['line'],
            character=range_data['start']['character']
        )
        end_pos = Position(
            line=range_data['end']['line'],
            character=range_data['end']['character']
        )
        error_range = Range(start=start_pos, end=end_pos)
        
        # Get line content if available
        line_content = None
        if file_content:
            try:
                lines = file_content.split('\n')
                if 0 <= start_pos.line < len(lines):
                    line_content = lines[start_pos.line].strip()
            except Exception:
                pass
        
        return RuntimeError(
            file_path=file_path,
            severity=severity,
            message=diagnostic['message'],
            code=diagnostic.get('code'),
            source=diagnostic.get('source'),
            range=error_range,
            line_content=line_content
        )
    
    def analyze_file(self, file_path: str, repo_path: str) -> List[RuntimeError]:
        """Analyze a single file for runtime errors."""
        language = self._get_language_for_file(file_path)
        if not language:
            return []
        
        # Get or initialize language server
        context = self.language_servers.get(language)
        if not context:
            context = self._initialize_language_server(language, repo_path)
            if not context:
                return []
        
        try:
            # Get relative path from repo root
            relative_path = os.path.relpath(file_path, repo_path)
            
            # Request diagnostics
            diagnostics = context.server.request_text_document_diagnostics(relative_path)
            
            # Read file content for line context
            file_content = None
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read file content for {file_path}: {e}")
            
            # Convert diagnostics to runtime errors
            runtime_errors = []
            for diagnostic in diagnostics:
                try:
                    error = self._convert_diagnostic_to_runtime_error(diagnostic, relative_path, file_content)
                    runtime_errors.append(error)
                except Exception as e:
                    logger.warning(f"Error converting diagnostic for {file_path}: {e}")
            
            return runtime_errors
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def analyze_repository(self, repo_path: str, max_files: Optional[int] = None) -> RuntimeErrorSummary:
        """Analyze an entire repository for runtime errors."""
        logger.info(f"Starting SolidLSP analysis of repository: {repo_path}")
        
        # Detect languages in the repository
        detected_languages = detect_repository_languages(repo_path)
        logger.info(f"Detected languages: {list(detected_languages.keys())}")
        
        # Find all relevant files
        all_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'target', 'build', 'dist'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self._get_language_for_file(file_path):
                    all_files.append(file_path)
        
        # Limit files if specified
        if max_files and len(all_files) > max_files:
            all_files = all_files[:max_files]
            logger.info(f"Limited analysis to {max_files} files")
        
        logger.info(f"Analyzing {len(all_files)} files")
        
        # Analyze files
        file_summaries = []
        language_summaries = {}
        total_errors = 0
        files_with_errors = 0
        
        for file_path in all_files:
            try:
                runtime_errors = self.analyze_file(file_path, repo_path)
                
                if runtime_errors:
                    files_with_errors += 1
                    total_errors += len(runtime_errors)
                
                # Create file summary
                file_summary = FileErrorSummary(
                    file_path=os.path.relpath(file_path, repo_path),
                    total_errors=len(runtime_errors),
                    runtime_errors=runtime_errors
                )
                
                # Count by severity
                for error in runtime_errors:
                    if error.severity == DiagnosticSeverity.ERROR:
                        file_summary.errors += 1
                    elif error.severity == DiagnosticSeverity.WARNING:
                        file_summary.warnings += 1
                    elif error.severity == DiagnosticSeverity.INFORMATION:
                        file_summary.information += 1
                    elif error.severity == DiagnosticSeverity.HINT:
                        file_summary.hints += 1
                
                file_summaries.append(file_summary)
                
                # Update language summaries
                language = self._get_language_for_file(file_path)
                if language:
                    lang_name = language.value
                    if lang_name not in language_summaries:
                        language_summaries[lang_name] = LanguageErrorSummary(language=lang_name)
                    
                    lang_summary = language_summaries[lang_name]
                    lang_summary.total_files += 1
                    if runtime_errors:
                        lang_summary.files_with_errors += 1
                        lang_summary.total_errors += len(runtime_errors)
                        lang_summary.errors += file_summary.errors
                        lang_summary.warnings += file_summary.warnings
                        lang_summary.information += file_summary.information
                        lang_summary.hints += file_summary.hints
                
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
        
        # Create summary
        summary = RuntimeErrorSummary(
            total_files_analyzed=len(all_files),
            files_with_errors=files_with_errors,
            total_errors=total_errors,
            languages_analyzed=list(language_summaries.keys()),
            language_summaries=language_summaries,
            file_summaries=file_summaries
        )
        
        # Count total errors by severity
        for file_summary in file_summaries:
            summary.errors += file_summary.errors
            summary.warnings += file_summary.warnings
            summary.information += file_summary.information
            summary.hints += file_summary.hints
        
        logger.info(f"SolidLSP analysis complete. Found {total_errors} total errors in {files_with_errors} files")
        return summary

