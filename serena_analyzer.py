#!/usr/bin/env python3
"""
Serena LSP Error Analyzer

A comprehensive script that retrieves ALL LSP errors from any codebase using Serena's solidlsp integration.
Supports both GitHub repositories and local codebases, with automatic language detection and 
multi-language server support.

Usage:
    python serena_analyzer.py <github_repo_url_or_local_path>
    
Examples:
    python serena_analyzer.py https://github.com/user/repo
    python serena_analyzer.py /path/to/local/project
    python serena_analyzer.py .

Output Format:
    ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
    1 ⚠️- project/src/file.py / Function - 'function_name' [error details]
    2 ⚠️- project/src/file.py / Class - 'class_name' [error details]
    ...
"""

import argparse
import asyncio
import logging
import os
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# Add Serena to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from serena.project import Project
    from serena.config.serena_config import ProjectConfig
    from solidlsp import SolidLanguageServer
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.ls_types import Diagnostic, DiagnosticsSeverity
    from solidlsp.settings import SolidLSPSettings
except ImportError as e:
    print(f"❌ Error importing Serena modules: {e}")
    print("Make sure you're running this script from the Serena root directory")
    sys.exit(1)


@dataclass
class ErrorInfo:
    """Structured error information"""
    file_path: str
    line: int
    column: int
    severity: str  # Critical, Major, Minor
    message: str
    code: Optional[str]
    source: Optional[str]
    symbol_context: Optional[str] = None  # Function/Class context


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    total_errors: int
    critical_count: int
    major_count: int
    minor_count: int
    errors: List[ErrorInfo]
    analysis_time: float
    languages_analyzed: List[str]
    files_processed: int


class SerenaAnalyzer:
    """Comprehensive LSP error analyzer using Serena's solidlsp integration"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.setup_logging()
        self.temp_dir: Optional[str] = None
        self.project: Optional[Project] = None
        self.language_servers: Dict[Language, SolidLanguageServer] = {}
        self.errors: List[ErrorInfo] = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Reduce noise from solidlsp
        logging.getLogger('solidlsp').setLevel(logging.WARNING)
        
    def is_github_url(self, path: str) -> bool:
        """Check if the path is a GitHub URL"""
        try:
            parsed = urlparse(path)
            return parsed.netloc.lower() in ['github.com', 'www.github.com']
        except:
            return False
    
    def clone_github_repo(self, github_url: str) -> str:
        """Clone GitHub repository to temporary directory"""
        import subprocess
        
        self.temp_dir = tempfile.mkdtemp(prefix="serena_analyzer_")
        self.logger.info(f"🔄 Cloning {github_url} to {self.temp_dir}")
        
        try:
            # Extract repo name for directory
            repo_name = github_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            clone_path = os.path.join(self.temp_dir, repo_name)
            
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', github_url, clone_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            self.logger.info(f"✅ Successfully cloned to {clone_path}")
            return clone_path
            
        except subprocess.TimeoutExpired:
            raise Exception("Git clone timed out after 5 minutes")
        except FileNotFoundError:
            raise Exception("Git command not found. Please install git.")
        except Exception as e:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {e}")
    
    def initialize_project(self, project_path: str) -> Project:
        """Initialize Serena project with automatic language detection"""
        self.logger.info(f"🔍 Initializing Serena project at {project_path}")
        
        try:
            # Load or create project configuration
            project = Project.load(project_path, autogenerate=True)
            self.logger.info(f"✅ Project initialized: {project.project_name}")
            self.logger.info(f"📝 Detected language: {project.language.value}")
            
            return project
            
        except Exception as e:
            raise Exception(f"Failed to initialize project: {e}")
    
    def get_supported_languages(self, project: Project) -> List[Language]:
        """Get all supported languages found in the project"""
        languages = set()
        
        # Always include the primary detected language
        languages.add(project.language)
        
        # Scan for additional languages based on file extensions
        try:
            source_files = project.gather_source_files()
            
            language_patterns = {
                Language.PYTHON: ['.py', '.pyi'],
                Language.TYPESCRIPT: ['.ts', '.tsx', '.js', '.jsx'],
                Language.JAVA: ['.java'],
                Language.CSHARP: ['.cs'],
                Language.RUST: ['.rs'],
                Language.GO: ['.go'],
                Language.RUBY: ['.rb'],
                Language.CPP: ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
                Language.PHP: ['.php'],
                Language.DART: ['.dart'],
                Language.KOTLIN: ['.kt', '.kts'],
                Language.CLOJURE: ['.clj', '.cljs', '.cljc'],
                Language.ELIXIR: ['.ex', '.exs'],
                Language.TERRAFORM: ['.tf', '.tfvars']
            }
            
            for file_path in source_files:
                file_ext = Path(file_path).suffix.lower()
                for lang, extensions in language_patterns.items():
                    if file_ext in extensions:
                        languages.add(lang)
                        break
            
            self.logger.info(f"🌐 Detected languages: {[lang.value for lang in languages]}")
            return list(languages)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error detecting additional languages: {e}")
            return [project.language]
    
    def create_language_server(self, language: Language, project_root: str) -> SolidLanguageServer:
        """Create and initialize a language server for the given language"""
        self.logger.info(f"🚀 Creating {language.value} language server")
        
        try:
            # Create language server configuration
            ls_config = LanguageServerConfig(
                code_language=language,
                ignored_paths=self.project._ignored_patterns if self.project else [],
                trace_lsp_communication=self.verbose
            )
            
            # Create logger with appropriate level
            ls_logger = LanguageServerLogger(
                log_level=logging.DEBUG if self.verbose else logging.WARNING
            )
            
            # Create language server
            ls = SolidLanguageServer.create(
                ls_config,
                ls_logger,
                project_root,
                timeout=60.0,  # 1 minute timeout
                solidlsp_settings=SolidLSPSettings()
            )
            
            return ls
            
        except Exception as e:
            raise Exception(f"Failed to create {language.value} language server: {e}")
    
    def start_language_servers(self, languages: List[Language], project_root: str) -> Dict[Language, SolidLanguageServer]:
        """Start all required language servers"""
        servers = {}
        
        for language in languages:
            try:
                self.logger.info(f"🔧 Starting {language.value} language server...")
                
                ls = self.create_language_server(language, project_root)
                ls.start()
                
                if ls.is_running():
                    servers[language] = ls
                    self.logger.info(f"✅ {language.value} language server started successfully")
                else:
                    self.logger.warning(f"⚠️ Failed to start {language.value} language server")
                    
            except Exception as e:
                self.logger.error(f"❌ Error starting {language.value} language server: {e}")
                continue
        
        self.logger.info(f"🎯 Successfully started {len(servers)}/{len(languages)} language servers")
        return servers
    
    def get_file_language(self, file_path: str) -> Optional[Language]:
        """Determine the language of a file based on its extension"""
        ext = Path(file_path).suffix.lower()
        
        extension_map = {
            '.py': Language.PYTHON, '.pyi': Language.PYTHON,
            '.ts': Language.TYPESCRIPT, '.tsx': Language.TYPESCRIPT,
            '.js': Language.TYPESCRIPT, '.jsx': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.rs': Language.RUST,
            '.go': Language.GO,
            '.rb': Language.RUBY,
            '.cpp': Language.CPP, '.cc': Language.CPP, '.cxx': Language.CPP,
            '.c': Language.CPP, '.h': Language.CPP, '.hpp': Language.CPP,
            '.php': Language.PHP,
            '.dart': Language.DART,
            '.kt': Language.KOTLIN, '.kts': Language.KOTLIN,
            '.clj': Language.CLOJURE, '.cljs': Language.CLOJURE, '.cljc': Language.CLOJURE,
            '.ex': Language.ELIXIR, '.exs': Language.ELIXIR,
            '.tf': Language.TERRAFORM, '.tfvars': Language.TERRAFORM
        }
        
        return extension_map.get(ext)
    
    def get_symbol_context(self, file_path: str, line: int, language_server: SolidLanguageServer) -> Optional[str]:
        """Get symbol context (function/class name) for an error location"""
        try:
            # Get document symbols for the file
            symbols = language_server.get_document_symbols(file_path)
            
            # Find the symbol that contains this line
            for symbol in symbols:
                symbol_range = symbol.get('range', {})
                start_line = symbol_range.get('start', {}).get('line', 0)
                end_line = symbol_range.get('end', {}).get('line', 0)
                
                if start_line <= line <= end_line:
                    symbol_name = symbol.get('name', 'unknown')
                    symbol_kind = symbol.get('kind', 0)
                    
                    # Map LSP symbol kinds to readable names
                    kind_map = {
                        1: 'File', 2: 'Module', 3: 'Namespace', 4: 'Package',
                        5: 'Class', 6: 'Method', 7: 'Property', 8: 'Field',
                        9: 'Constructor', 10: 'Enum', 11: 'Interface', 12: 'Function',
                        13: 'Variable', 14: 'Constant', 15: 'String', 16: 'Number',
                        17: 'Boolean', 18: 'Array', 19: 'Object', 20: 'Key',
                        21: 'Null', 22: 'EnumMember', 23: 'Struct', 24: 'Event',
                        25: 'Operator', 26: 'TypeParameter'
                    }
                    
                    kind_name = kind_map.get(symbol_kind, 'Symbol')
                    return f"{kind_name} - '{symbol_name}'"
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not get symbol context for {file_path}:{line}: {e}")
            return None
    
    def collect_file_diagnostics(self, file_path: str, language_server: SolidLanguageServer, language: Language) -> List[ErrorInfo]:
        """Collect diagnostics for a single file"""
        errors = []
        
        try:
            # Request diagnostics for the file
            diagnostics = language_server.request_text_document_diagnostics(file_path)
            
            for diagnostic in diagnostics:
                # Map LSP severity to our classification
                severity_map = {
                    DiagnosticsSeverity.ERROR: "Critical",
                    DiagnosticsSeverity.WARNING: "Major", 
                    DiagnosticsSeverity.INFORMATION: "Minor",
                    DiagnosticsSeverity.HINT: "Minor"
                }
                
                lsp_severity = diagnostic.get('severity', DiagnosticsSeverity.ERROR)
                severity = severity_map.get(lsp_severity, "Critical")
                
                # Extract location information
                range_info = diagnostic.get('range', {})
                start_pos = range_info.get('start', {})
                line = start_pos.get('line', 0) + 1  # Convert to 1-based
                column = start_pos.get('character', 0)
                
                # Get symbol context
                symbol_context = self.get_symbol_context(file_path, line - 1, language_server)
                
                error = ErrorInfo(
                    file_path=file_path,
                    line=line,
                    column=column,
                    severity=severity,
                    message=diagnostic.get('message', 'No message'),
                    code=diagnostic.get('code'),
                    source=diagnostic.get('source', language.value),
                    symbol_context=symbol_context
                )
                
                errors.append(error)
                
        except Exception as e:
            self.logger.debug(f"Error collecting diagnostics for {file_path}: {e}")
        
        return errors
    
    def collect_all_diagnostics(self) -> List[ErrorInfo]:
        """Collect diagnostics from all language servers for all files"""
        all_errors = []
        
        if not self.project or not self.language_servers:
            return all_errors
        
        try:
            # Get all source files
            source_files = self.project.gather_source_files()
            self.logger.info(f"📄 Found {len(source_files)} source files to analyze")
            
            # Group files by language for efficient processing
            files_by_language = {}
            for file_path in source_files:
                file_language = self.get_file_language(file_path)
                if file_language and file_language in self.language_servers:
                    if file_language not in files_by_language:
                        files_by_language[file_language] = []
                    files_by_language[file_language].append(file_path)
            
            # Process files for each language server
            with ThreadPoolExecutor(max_workers=len(self.language_servers)) as executor:
                future_to_info = {}
                
                for language, files in files_by_language.items():
                    language_server = self.language_servers[language]
                    
                    self.logger.info(f"🔍 Analyzing {len(files)} {language.value} files...")
                    
                    # Submit file processing tasks
                    for file_path in files:
                        future = executor.submit(
                            self.collect_file_diagnostics,
                            file_path,
                            language_server,
                            language
                        )
                        future_to_info[future] = (file_path, language.value)
                
                # Collect results
                processed_files = 0
                for future in as_completed(future_to_info):
                    file_path, language_name = future_to_info[future]
                    try:
                        file_errors = future.result(timeout=30)  # 30 second timeout per file
                        all_errors.extend(file_errors)
                        processed_files += 1
                        
                        if processed_files % 50 == 0:  # Progress update every 50 files
                            self.logger.info(f"📊 Processed {processed_files}/{len(future_to_info)} files...")
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error processing {file_path}: {e}")
                        continue
            
            self.logger.info(f"✅ Analysis complete: {len(all_errors)} errors found in {processed_files} files")
            return all_errors
            
        except Exception as e:
            self.logger.error(f"❌ Error during diagnostic collection: {e}")
            return all_errors
    
    def format_output(self, result: AnalysisResult) -> str:
        """Format the analysis result according to the specified format"""
        output_lines = []
        
        # Header with summary
        header = f"ERRORS: {result.total_errors} [⚠️ Critical: {result.critical_count}] [👉 Major: {result.major_count}] [🔍 Minor: {result.minor_count}]"
        output_lines.append(header)
        
        # Sort errors by severity (Critical first, then Major, then Minor)
        severity_order = {"Critical": 0, "Major": 1, "Minor": 2}
        sorted_errors = sorted(result.errors, key=lambda x: (severity_order[x.severity], x.file_path, x.line))
        
        # Format each error
        for i, error in enumerate(sorted_errors, 1):
            # Choose emoji based on severity
            emoji = {"Critical": "⚠️", "Major": "👉", "Minor": "🔍"}[error.severity]
            
            # Format symbol context
            context = error.symbol_context or "Unknown"
            
            # Format the error line
            error_line = f"{i} {emoji}- {error.file_path} / {context} [{error.message}]"
            
            # Add source and code if available
            if error.source and error.code:
                error_line += f" ({error.source}:{error.code})"
            elif error.source:
                error_line += f" ({error.source})"
            
            output_lines.append(error_line)
        
        return "\n".join(output_lines)
    
    def analyze(self, path: str) -> AnalysisResult:
        """Main analysis function"""
        start_time = time.time()
        
        try:
            # Determine if it's a GitHub URL or local path
            if self.is_github_url(path):
                project_path = self.clone_github_repo(path)
            else:
                project_path = os.path.abspath(path)
                if not os.path.exists(project_path):
                    raise Exception(f"Path does not exist: {project_path}")
            
            # Initialize Serena project
            self.project = self.initialize_project(project_path)
            
            # Detect supported languages
            languages = self.get_supported_languages(self.project)
            
            # Start language servers
            self.language_servers = self.start_language_servers(languages, project_path)
            
            if not self.language_servers:
                raise Exception("No language servers could be started")
            
            # Collect all diagnostics
            all_errors = self.collect_all_diagnostics()
            
            # Calculate statistics
            critical_count = sum(1 for e in all_errors if e.severity == "Critical")
            major_count = sum(1 for e in all_errors if e.severity == "Major")
            minor_count = sum(1 for e in all_errors if e.severity == "Minor")
            
            analysis_time = time.time() - start_time
            
            return AnalysisResult(
                total_errors=len(all_errors),
                critical_count=critical_count,
                major_count=major_count,
                minor_count=minor_count,
                errors=all_errors,
                analysis_time=analysis_time,
                languages_analyzed=[lang.value for lang in self.language_servers.keys()],
                files_processed=len(self.project.gather_source_files()) if self.project else 0
            )
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            if self.verbose:
                self.logger.error(traceback.format_exc())
            raise
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop all language servers
            for language, server in self.language_servers.items():
                try:
                    if server.is_running():
                        self.logger.info(f"🔄 Stopping {language.value} language server...")
                        server.stop()
                except Exception as e:
                    self.logger.warning(f"⚠️ Error stopping {language.value} server: {e}")
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                self.logger.info(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error during cleanup: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Serena LSP Error Analyzer - Retrieve ALL LSP errors from any codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/user/repo
  %(prog)s /path/to/local/project  
  %(prog)s .
  
Output format:
  ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
  1 ⚠️- project/src/file.py / Function - 'function_name' [error details]
  2 👉- project/src/file.py / Class - 'class_name' [error details]
  ...
        """
    )
    
    parser.add_argument(
        "path",
        help="GitHub repository URL or local project path"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = SerenaAnalyzer(verbose=args.verbose)
    
    try:
        print("🚀 Serena LSP Error Analyzer")
        print("=" * 50)
        print(f"📂 Target: {args.path}")
        print()
        
        # Run analysis
        result = analyzer.analyze(args.path)
        
        # Format output
        output = analyzer.format_output(result)
        
        # Print summary
        print(f"✅ Analysis completed in {result.analysis_time:.2f} seconds")
        print(f"📊 Languages analyzed: {', '.join(result.languages_analyzed)}")
        print(f"📄 Files processed: {result.files_processed}")
        print()
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"💾 Results saved to: {args.output}")
        else:
            print(output)
            
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    main()

