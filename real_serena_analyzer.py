#!/usr/bin/env python3
"""
REAL Serena LSP Error Analysis Tool - Using Actual Serena Libraries

This tool uses the ACTUAL Serena and SolidLSP libraries to analyze repositories
and extract all LSP errors and diagnostics from the codebase.
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
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import urlparse

# ACTUAL Serena and SolidLSP imports - verified from source
try:
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
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
    from solidlsp.lsp_protocol_handler.lsp_types import ErrorCodes
except ImportError as e:
    print(f"Error: Failed to import required Serena/SolidLSP modules: {e}")
    print("Please ensure Serena and SolidLSP are properly installed.")
    print("Try: pip install -e . from the serena repository root")
    sys.exit(1)


@dataclass
class RealDiagnostic:
    """Real diagnostic using actual Serena/SolidLSP types."""
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

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class RealSerenaLSPAnalyzer:
    """
    Real LSP analyzer using actual Serena and SolidLSP libraries.
    """

    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4):
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

        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

        if verbose:
            self.logger.info("🚀 Initializing REAL Serena LSP Analyzer")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.language_server:
                try:
                    if hasattr(self.language_server, 'is_running') and self.language_server.is_running():
                        self.logger.info("🛑 Stopping language server...")
                        self.language_server.stop()
                        self.logger.info("✅ Language server stopped")
                except Exception as e:
                    self.logger.warning(f"⚠️  Error stopping language server: {e}")
                finally:
                    self.language_server = None

            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    self.logger.info(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"⚠️  Error cleaning up: {e}")

        except Exception as e:
            self.logger.error(f"❌ Critical error during cleanup: {e}")

    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith(".git")

    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        self.logger.info(f"📥 Cloning repository: {repo_url}")

        self.temp_dir = tempfile.mkdtemp(prefix="real_serena_analysis_")
        repo_name = os.path.basename(repo_url.rstrip("/").replace(".git", ""))
        clone_path = os.path.join(self.temp_dir, repo_name)

        try:
            cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)

            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")

            self.logger.info(f"✅ Repository cloned to: {clone_path}")
            return clone_path

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git clone timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")

    def detect_language(self, repo_path: str) -> Language:
        """Detect the primary programming language using actual Language enum."""
        self.logger.info("🔍 Detecting repository language...")

        # Use actual Language enum values from the real library
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

        # Walk through the repository and count file types
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "target", "build", "dist", "vendor"
            ]]

            for file in files:
                file_lower = file.lower()
                for lang, indicators in language_indicators.items():
                    if any(file_lower.endswith(ext) for ext in indicators if ext.startswith(".")):
                        file_counts[lang] += 1
                    elif any(file_lower == indicator for indicator in indicators if not indicator.startswith(".")):
                        file_counts[lang] += 5  # Weight config files higher

        # Find the language with the most files
        detected_lang = max(file_counts, key=file_counts.get)

        if file_counts[detected_lang] == 0:
            self.logger.warning("Could not detect language, defaulting to Python")
            detected_lang = Language.PYTHON

        self.logger.info(f"✅ Detected language: {detected_lang.value}")
        return detected_lang

    def setup_project(self, repo_path: str, language: Optional[Language] = None) -> Project:
        """Set up a Serena project using actual ProjectConfig."""
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path is not a directory: {repo_path}")

        # Detect language if not provided
        if language is None:
            language = self.detect_language(repo_path)

        self.logger.info(f"⚙️  Setting up project for {repo_path} with language {language.value}")

        # Create project configuration using actual ProjectConfig
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

        # Create and return project using actual Project class
        self.project = Project(repo_path, project_config)
        return self.project

    def start_language_server(self, project: Project) -> SolidLanguageServer:
        """Start the language server using actual Serena project method."""
        self.logger.info("🔧 Starting REAL Serena language server...")

        try:
            # Use the actual create_language_server method from Project
            self.language_server = project.create_language_server(
                log_level=logging.DEBUG if self.verbose else logging.WARNING,
                ls_timeout=self.timeout,
                trace_lsp_communication=self.verbose,
            )

            if not self.language_server:
                raise RuntimeError("Failed to create language server instance")

            self.logger.info("📡 Starting language server process...")
            
            # Start the server using actual method
            self.language_server.start()

            # Wait for server to be ready
            initialization_time = 5 if self.total_files > 100 else 2
            self.logger.info(f"⏳ Allowing {initialization_time}s for LSP initialization...")
            time.sleep(initialization_time)

            # Verify server is running
            if hasattr(self.language_server, 'is_running') and not self.language_server.is_running():
                raise RuntimeError("Language server failed to start")

            self.logger.info("🎉 REAL Serena language server successfully started!")
            return self.language_server

        except Exception as e:
            self.logger.error(f"❌ Failed to start language server: {e}")
            raise RuntimeError(f"Failed to start language server: {e}")

    def collect_diagnostics(self, project: Project, language_server: SolidLanguageServer) -> List[RealDiagnostic]:
        """Collect diagnostics using actual Serena methods."""
        self.analysis_start_time = time.time()
        self.logger.info("🔍 Starting REAL Serena LSP analysis...")

        # Get ALL source files using actual gather_source_files method
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

        self.logger.info(f"🚀 Processing {self.total_files} files with REAL Serena LSP...")

        def analyze_single_file(file_path: str) -> Tuple[str, List[RealDiagnostic], Optional[str]]:
            """Analyze a single file using REAL Serena LSP methods."""
            try:
                # Use actual request_text_document_diagnostics method
                lsp_diagnostics = language_server.request_text_document_diagnostics(file_path)

                enhanced_diagnostics = []
                for diag in lsp_diagnostics:
                    # Extract diagnostic information using actual LSP response structure
                    range_info = diag.get("range", {})
                    start_pos = range_info.get("start", {})
                    line = start_pos.get("line", 0) + 1  # LSP uses 0-based line numbers
                    column = start_pos.get("character", 0) + 1  # LSP uses 0-based character numbers

                    # Map severity using actual DiagnosticsSeverity enum
                    severity_map = {
                        DiagnosticsSeverity.ERROR: "ERROR",
                        DiagnosticsSeverity.WARNING: "WARNING", 
                        DiagnosticsSeverity.INFORMATION: "INFO",
                        DiagnosticsSeverity.HINT: "HINT",
                    }

                    severity_value = diag.get("severity", DiagnosticsSeverity.ERROR)
                    severity = severity_map.get(severity_value, "UNKNOWN")

                    # Extract error code if available
                    diagnostic_code = diag.get("code")
                    error_code = None
                    if diagnostic_code and isinstance(diagnostic_code, int):
                        try:
                            error_code = ErrorCodes(diagnostic_code)
                        except ValueError:
                            pass

                    # Create enhanced diagnostic using actual data
                    enhanced_diag = RealDiagnostic(
                        file_path=file_path,
                        line=line,
                        column=column,
                        severity=severity,
                        message=diag.get("message", "No message"),
                        code=str(diag.get("code", "")),
                        source=diag.get("source", "lsp"),
                        category="real_lsp_diagnostic",
                        tags=["real_serena_lsp_analysis"],
                        error_code=error_code,
                    )
                    enhanced_diagnostics.append(enhanced_diag)

                if self.verbose and len(enhanced_diagnostics) > 0:
                    self.logger.debug(f"✅ Found {len(enhanced_diagnostics)} diagnostics in {os.path.basename(file_path)}")

                return file_path, enhanced_diagnostics, None

            except Exception as e:
                self.logger.warning(f"⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
                return file_path, [], str(e)

        # Process files with controlled parallelism
        batch_size = min(20, max(1, self.total_files // 5))
        file_batches = [source_files[i:i + batch_size] for i in range(0, len(source_files), batch_size)]

        self.logger.info(f"📦 Processing {len(file_batches)} batches of ~{batch_size} files each")

        for batch_idx, file_batch in enumerate(file_batches):
            self.logger.info(f"📦 Processing batch {batch_idx + 1}/{len(file_batches)} ({len(file_batch)} files)")

            with ThreadPoolExecutor(max_workers=min(2, self.max_workers)) as executor:
                future_to_file = {executor.submit(analyze_single_file, file_path): file_path for file_path in file_batch}

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
                                if self.verbose:
                                    self.logger.warning(f"⚠️  Failed: {os.path.basename(analyzed_file)}: {error}")

                    except Exception as e:
                        with self.lock:
                            self.failed_files += 1
                            self.logger.error(f"❌ Error processing {os.path.basename(file_path)}: {e}")

            # Brief pause between batches
            if batch_idx < len(file_batches) - 1:
                time.sleep(0.5)

        # Final statistics
        analysis_time = time.time() - self.analysis_start_time
        self.total_diagnostics = len(all_diagnostics)

        # Categorize diagnostics by severity
        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "HINT": 0, "UNKNOWN": 0}
        for diag in all_diagnostics:
            severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1

        self.logger.info("=" * 80)
        self.logger.info("📋 REAL SERENA LSP ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {self.processed_files}")
        self.logger.info(f"❌ Files failed: {self.failed_files}")
        self.logger.info(f"📊 Total files analyzed: {self.processed_files + self.failed_files}/{self.total_files}")
        self.logger.info(f"🔍 Total REAL LSP diagnostics found: {self.total_diagnostics}")
        self.logger.info("📋 Diagnostics by severity:")
        for severity, count in severity_counts.items():
            if count > 0:
                self.logger.info(f"   {severity}: {count}")
        self.logger.info(f"⏱️  Analysis time: {analysis_time:.2f} seconds")
        self.logger.info("=" * 80)

        return all_diagnostics

    def format_diagnostic_output(self, diagnostics: List[RealDiagnostic]) -> str:
        """Format diagnostics in the requested output format."""
        if not diagnostics:
            return "ERRORS: ['0']\nNo errors found."

        # Sort diagnostics by severity (ERROR first), then by file, then by line
        severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3, "UNKNOWN": 4}

        diagnostics.sort(key=lambda d: (
            severity_priority.get(d.severity, 5),
            d.file_path.lower(),
            d.line,
        ))

        # Generate output
        error_count = len(diagnostics)
        output_lines = [f"ERRORS: ['{error_count}']"]

        # Add each formatted diagnostic
        for i, diag in enumerate(diagnostics, 1):
            file_name = os.path.basename(diag.file_path)
            location = f"line {diag.line}, col {diag.column}"

            # Clean and truncate message
            clean_message = diag.message.replace("\n", " ").replace("\r", " ")
            clean_message = " ".join(clean_message.split())

            if len(clean_message) > 200:
                clean_message = clean_message[:197] + "..."

            # Enhanced metadata formatting
            metadata_parts = [f"severity: {diag.severity}"]

            if diag.code and diag.code != "":
                metadata_parts.append(f"code: {diag.code}")

            if diag.source and diag.source != "lsp":
                metadata_parts.append(f"source: {diag.source}")

            if diag.error_code:
                metadata_parts.append(f"lsp_error: {diag.error_code.name}")

            if diag.category and diag.category != "real_lsp_diagnostic":
                metadata_parts.append(f"category: {diag.category}")

            other_types = ", ".join(metadata_parts)

            diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
            output_lines.append(diagnostic_line)

        return "\n".join(output_lines)

    def analyze_repository(self, repo_url_or_path: str, language_override: Optional[str] = None) -> str:
        """Main analysis function using REAL Serena and SolidLSP."""
        total_start_time = time.time()

        try:
            self.logger.info("🚀 Starting REAL SERENA LSP Error Analysis")
            self.logger.info("=" * 80)
            self.logger.info(f"📁 Target: {repo_url_or_path}")
            self.logger.info(f"🌐 Language override: {language_override or 'AUTO-DETECT'}")
            self.logger.info("=" * 80)

            # Step 1: Repository handling
            if self.is_git_url(repo_url_or_path):
                self.logger.info("📥 Cloning remote repository...")
                repo_path = self.clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
                if not os.path.exists(repo_path):
                    raise FileNotFoundError(f"Local path does not exist: {repo_path}")
                self.logger.info(f"📂 Using local repository: {repo_path}")

            # Step 2: Parse language configuration
            language = None
            if language_override:
                try:
                    language = Language(language_override.lower())
                    self.logger.info(f"🎯 Language override: {language.value}")
                except ValueError:
                    self.logger.warning(f"⚠️  Invalid language '{language_override}', will auto-detect")

            # Step 3: Project setup using REAL Serena
            self.logger.info("⚙️  Setting up REAL Serena project...")
            project = self.setup_project(repo_path, language)

            # Step 4: Language server initialization using REAL SolidLSP
            self.logger.info("🔧 Starting REAL SolidLSP language server...")
            language_server = self.start_language_server(project)

            # Step 5: Comprehensive diagnostic collection using REAL methods
            self.logger.info("🔍 Beginning REAL Serena LSP diagnostic collection...")
            diagnostics = self.collect_diagnostics(project, language_server)

            # Step 6: Format results
            self.logger.info("📋 Formatting REAL results...")
            result = self.format_diagnostic_output(diagnostics)

            # Final performance summary
            total_time = time.time() - total_start_time
            self.logger.info("🎉 REAL SERENA LSP ANALYSIS COMPLETED!")
            self.logger.info(f"🎯 Total execution time: {total_time:.2f}s")

            return result

        except Exception as e:
            self.logger.error(f"❌ REAL SERENA LSP ANALYSIS FAILED: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            return f"ERRORS: ['0']\nReal Serena LSP analysis failed: {e}"


def main():
    """Main entry point for REAL Serena LSP error analysis."""
    parser = argparse.ArgumentParser(
        description="🚀 REAL SERENA LSP ERROR ANALYSIS TOOL - Using Actual Serena/SolidLSP Libraries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("repository", help="Repository URL or local path to analyze")
    parser.add_argument("--language", help="Override language detection (e.g., python, typescript, java)")
    parser.add_argument("--timeout", type=float, default=600, help="Timeout for operations (default: 600)")
    parser.add_argument("--max-workers", type=int, default=2, help="Max parallel workers (default: 2)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    print("🚀 REAL SERENA LSP ERROR ANALYSIS TOOL")
    print("📋 Using ACTUAL Serena and SolidLSP Libraries")
    print("=" * 80)
    print(f"📁 Repository: {args.repository}")
    print(f"🌐 Language: {args.language or 'AUTO-DETECT'}")
    print(f"⏱️  Timeout: {args.timeout}s")
    print(f"👥 Max workers: {args.max_workers}")
    print(f"📋 Verbose: {args.verbose}")
    print("=" * 80)

    try:
        with RealSerenaLSPAnalyzer(
            verbose=args.verbose, 
            timeout=args.timeout, 
            max_workers=args.max_workers
        ) as analyzer:
            result = analyzer.analyze_repository(
                args.repository,
                language_override=args.language,
            )

            print("\n" + "=" * 80)
            print("📋 REAL SERENA LSP ANALYSIS RESULTS")
            print("=" * 80)
            print(result)
            print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
