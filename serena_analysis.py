#!/usr/bin/env python3
"""
Serena LSP Error Analysis Tool

This tool analyzes repositories using Serena and SolidLSP to extract all LSP errors
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
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Serena and SolidLSP imports
try:
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.ls_types import Diagnostic, DiagnosticsSeverity
    from solidlsp.settings import SolidLSPSettings
    from solidlsp import SolidLanguageServer
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Please ensure Serena and SolidLSP are properly installed.")
    sys.exit(1)


class SerenaAnalyzer:
    """Main class for analyzing repositories with Serena and SolidLSP."""
    
    def __init__(self, verbose: bool = False, timeout: float = 300):
        """
        Initialize the analyzer.
        
        Args:
            verbose: Enable verbose logging
            timeout: Timeout for language server operations
        """
        self.verbose = verbose
        self.timeout = timeout
        self.temp_dir: Optional[str] = None
        self.project: Optional[Project] = None
        self.language_server: Optional[SolidLanguageServer] = None
        
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
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
        language_indicators = {
            Language.PYTHON: ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            Language.JAVASCRIPT: ['.js', '.jsx', 'package.json', 'yarn.lock'],
            Language.TYPESCRIPT: ['.ts', '.tsx', 'tsconfig.json'],
            Language.JAVA: ['.java', 'pom.xml', 'build.gradle'],
            Language.CSHARP: ['.cs', '.csproj', '.sln'],
            Language.CPP: ['.cpp', '.cc', '.cxx', '.h', '.hpp', 'CMakeLists.txt'],
            Language.RUST: ['.rs', 'Cargo.toml'],
            Language.GO: ['.go', 'go.mod'],
            Language.PHP: ['.php', 'composer.json'],
            Language.RUBY: ['.rb', 'Gemfile'],
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
            name=os.path.basename(repo_path),
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
        Collect diagnostics from all source files in the project.
        
        Args:
            project: The Serena project
            language_server: The language server instance
            severity_filter: Optional severity level filter
            
        Returns:
            List of collected diagnostics
        """
        self.logger.info("Collecting diagnostics from source files...")
        
        # Get all source files
        try:
            source_files = project.gather_source_files()
            self.logger.info(f"Found {len(source_files)} source files to analyze")
        except Exception as e:
            self.logger.error(f"Failed to gather source files: {e}")
            return []
        
        all_diagnostics = []
        processed_files = 0
        failed_files = 0
        
        for file_path in source_files:
            try:
                self.logger.debug(f"Analyzing file: {file_path}")
                
                # Get diagnostics for this file
                diagnostics = language_server.request_text_document_diagnostics(file_path)
                
                # Filter by severity if specified
                if severity_filter is not None:
                    diagnostics = [d for d in diagnostics if d.get('severity') == severity_filter.value]
                
                all_diagnostics.extend(diagnostics)
                processed_files += 1
                
                if self.verbose and len(diagnostics) > 0:
                    self.logger.debug(f"Found {len(diagnostics)} diagnostics in {file_path}")
                
            except Exception as e:
                failed_files += 1
                self.logger.warning(f"Failed to analyze {file_path}: {e}")
                continue
        
        self.logger.info(f"Analysis complete: {processed_files} files processed, {failed_files} files failed")
        self.logger.info(f"Total diagnostics collected: {len(all_diagnostics)}")
        
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
        Main analysis function that orchestrates the entire process.
        
        Args:
            repo_url_or_path: Repository URL or local path
            severity_filter: Optional severity filter ('ERROR', 'WARNING', 'INFO', 'HINT')
            language_override: Optional language override
            
        Returns:
            Formatted analysis results
        """
        try:
            # Determine if we need to clone or use local path
            if self.is_git_url(repo_url_or_path):
                repo_path = self.clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
                if not os.path.exists(repo_path):
                    raise FileNotFoundError(f"Local path does not exist: {repo_path}")
            
            # Parse language override
            language = None
            if language_override:
                try:
                    language = Language(language_override.lower())
                except ValueError:
                    self.logger.warning(f"Invalid language '{language_override}', will auto-detect")
            
            # Parse severity filter
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
                    self.logger.warning(f"Invalid severity '{severity_filter}', showing all diagnostics")
            
            # Set up project
            project = self.setup_project(repo_path, language)
            
            # Start language server
            language_server = self.start_language_server(project)
            
            # Give the language server a moment to initialize
            time.sleep(2)
            
            # Collect diagnostics
            diagnostics = self.collect_diagnostics(project, language_server, severity)
            
            # Format and return results
            return self.format_diagnostic_output(diagnostics)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return f"ERRORS: ['0']\nAnalysis failed: {e}"


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze repositories for LSP errors using Serena and SolidLSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/user/repo.git
  %(prog)s /path/to/local/repo --severity ERROR
  %(prog)s . --verbose --timeout 120 --language python
        """
    )
    
    parser.add_argument(
        'repository',
        help='Repository URL or local path to analyze'
    )
    
    parser.add_argument(
        '--severity',
        choices=['ERROR', 'WARNING', 'INFO', 'HINT'],
        help='Filter diagnostics by severity level (default: show all)'
    )
    
    parser.add_argument(
        '--language',
        help='Override language detection (e.g., python, javascript, java)'
    )
    
    parser.add_argument(
        '--timeout',
        type=float,
        default=300,
        help='Timeout for operations in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Run the analysis
    with SerenaAnalyzer(verbose=args.verbose, timeout=args.timeout) as analyzer:
        result = analyzer.analyze_repository(
            args.repository,
            severity_filter=args.severity,
            language_override=args.language
        )
        print(result)


if __name__ == '__main__':
    main()

