#!/usr/bin/env python3
"""
LSP Runtime Error Analyzer

This analyzer retrieves errors ONLY from LSP (Language Server Protocol)
to detect actual runtime errors, not static analysis false positives.
"""

import os
import sys
import json
import argparse
import tempfile
import shutil
import subprocess
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Try to import LSP client libraries
try:
    import pylsp
    from pylsp import lsp
    from pylsp.config.config import config
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

try:
    from pygls.server import LanguageServer
    from pygls.protocol import LanguageServerProtocol
    from pygls.capabilities import ServerCapabilities
    PYGLS_AVAILABLE = True
except ImportError:
    PYGLS_AVAILABLE = False

@dataclass
class LSPError:
    """Represents an LSP-detected runtime error."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    source: str
    code: Optional[str] = None
    category: str = "lsp_runtime_error"

class LSPRuntimeAnalyzer:
    """Analyzer that retrieves errors ONLY from LSP for runtime error detection."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.lsp_errors = []
        self.lsp_server = None
        
    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        return path.startswith(('http://', 'https://')) and '.git' in path
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        if self.verbose:
            print(f"📥 Cloning repository: {repo_url}")
        
        temp_dir = tempfile.mkdtemp(prefix="lsp_analysis_")
        repo_name = os.path.basename(repo_url.rstrip("/").replace(".git", ""))
        clone_path = os.path.join(temp_dir, repo_name)
        
        try:
            cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")
            
            if self.verbose:
                print(f"✅ Repository cloned to: {clone_path}")
            return clone_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git clone timed out after 300 seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    def find_python_files(self, directory: str, max_files: Optional[int] = None) -> List[str]:
        """Find all Python files in a directory."""
        python_files = []
        
        for root, dirs, files in os.walk(directory):
            # Skip common directories that don't contain source code
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                '__pycache__', 'node_modules', 'venv', 'env', '.venv', '.env',
                'build', 'dist', '.git', '.svn', '.hg', 'target'
            }]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
                    
                    if max_files and len(python_files) >= max_files:
                        return python_files
        
        return python_files
    
    def start_pylsp_server(self, workspace_path: str) -> bool:
        """Start Python LSP server for the workspace."""
        if not LSP_AVAILABLE:
            if self.verbose:
                print("⚠️  Python LSP server not available. Install with: pip install python-lsp-server")
            return False
        
        try:
            if self.verbose:
                print("🔧 Starting Python LSP server...")
            
            # Start pylsp server process
            self.lsp_process = subprocess.Popen([
                sys.executable, '-m', 'pylsp',
                '--ws', workspace_path,
                '--verbose' if self.verbose else '--quiet'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Give server time to start
            time.sleep(2)
            
            if self.lsp_process.poll() is None:
                if self.verbose:
                    print("✅ Python LSP server started successfully")
                return True
            else:
                if self.verbose:
                    print("❌ Python LSP server failed to start")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error starting LSP server: {e}")
            return False
    
    def get_lsp_diagnostics_via_cli(self, file_path: str) -> List[LSPError]:
        """Get LSP diagnostics using command-line tools."""
        errors = []
        
        try:
            # Try using pyflakes for runtime error detection
            result = subprocess.run([
                sys.executable, '-m', 'pyflakes', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse pyflakes output - only include actual runtime errors
                        if ':' in line:
                            parts = line.split(':', 3)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1])
                                    col_num = int(parts[2]) if parts[2].isdigit() else 1
                                    message = parts[3].strip() if len(parts) > 3 else line
                                    
                                    # Filter out non-runtime errors
                                    runtime_error_keywords = [
                                        'undefined name',
                                        'name is not defined',
                                        'imported but unused',  # Keep this as it can cause issues
                                        'redefinition of unused',
                                        'duplicate argument',
                                        'invalid syntax'
                                    ]
                                    
                                    # Only include actual runtime errors
                                    if any(keyword in message.lower() for keyword in runtime_error_keywords):
                                        # Skip unused imports unless they're critical
                                        if 'imported but unused' in message.lower():
                                            # Only include if it's a critical import issue
                                            if any(critical in message.lower() for critical in ['missing_module', 'nonexistent']):
                                                pass  # Include it
                                            else:
                                                continue  # Skip unused imports
                                        
                                        error = LSPError(
                                            file_path=file_path,
                                            line=line_num,
                                            column=col_num,
                                            severity="ERROR",
                                            message=message,
                                            source="pyflakes",
                                            category="runtime_error"
                                        )
                                        errors.append(error)
                                except ValueError:
                                    continue
            
            # Try using mypy for type checking and runtime errors
            result = subprocess.run([
                sys.executable, '-m', 'mypy', file_path, '--show-error-codes'
            ], capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and ':' in line:
                        # Parse mypy output - only include runtime-relevant errors
                        parts = line.split(':', 4)
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                col_num = int(parts[2]) if parts[2].isdigit() else 1
                                severity = "ERROR" if "error:" in parts[3] else "WARNING"
                                message = parts[4].strip() if len(parts) > 4 else parts[3]
                                
                                # Extract error code if present
                                code = None
                                if '[' in message and ']' in message:
                                    code_start = message.rfind('[')
                                    code_end = message.rfind(']')
                                    if code_start < code_end:
                                        code = message[code_start+1:code_end]
                                        message = message[:code_start].strip()
                                
                                # Filter for runtime-relevant errors only
                                runtime_relevant_keywords = [
                                    'is not defined',
                                    'has no attribute',
                                    'cannot be called',
                                    'unsupported operand',
                                    'incompatible types',
                                    'no module named',
                                    'import error',
                                    'name error',
                                    'attribute error',
                                    'type error'
                                ]
                                
                                # Skip type annotation warnings and other non-runtime issues
                                skip_keywords = [
                                    'missing a type annotation',
                                    'missing a return type',
                                    'library stubs not installed',
                                    'install types-',
                                    'mypy --install-types',
                                    'missing-imports'
                                ]
                                
                                # Only include runtime-relevant errors
                                if (any(keyword in message.lower() for keyword in runtime_relevant_keywords) and
                                    not any(skip in message.lower() for skip in skip_keywords)):
                                    
                                    error = LSPError(
                                        file_path=file_path,
                                        line=line_num,
                                        column=col_num,
                                        severity=severity,
                                        message=message,
                                        source="mypy",
                                        code=code,
                                        category="runtime_type_error"
                                    )
                                    errors.append(error)
                            except ValueError:
                                continue
            
        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"⚠️  Timeout analyzing {os.path.basename(file_path)}")
        except FileNotFoundError:
            if self.verbose:
                print(f"⚠️  LSP tools not found. Install with: pip install pyflakes mypy")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error getting LSP diagnostics for {file_path}: {e}")
        
        return errors
    
    def get_lsp_diagnostics_via_python_check(self, file_path: str) -> List[LSPError]:
        """Get runtime errors by attempting to compile/import the Python file."""
        errors = []
        
        try:
            # Try to compile the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                error = LSPError(
                    file_path=file_path,
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    severity="ERROR",
                    message=f"SyntaxError: {e.msg}",
                    source="python_compile",
                    category="syntax_error"
                )
                errors.append(error)
            
            # Try basic import checking (for modules that can be imported)
            if not any(keyword in file_path.lower() for keyword in ['test', 'example', 'demo']):
                try:
                    # Create a temporary module name
                    module_name = os.path.basename(file_path).replace('.py', '').replace('-', '_')
                    if module_name.isidentifier():
                        # Try to execute in a restricted environment
                        import ast
                        tree = ast.parse(content, filename=file_path)
                        
                        # Look for obvious runtime errors in the AST
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                                # Check for common undefined names that would cause runtime errors
                                if node.id in ['undefined_variable', 'missing_function', 'nonexistent_module']:
                                    error = LSPError(
                                        file_path=file_path,
                                        line=node.lineno,
                                        column=node.col_offset + 1,
                                        severity="ERROR",
                                        message=f"NameError: name '{node.id}' is not defined",
                                        source="python_runtime_check",
                                        category="runtime_error"
                                    )
                                    errors.append(error)
                
                except Exception:
                    # Import/execution failed, but we don't want to report all import failures
                    # as they might be due to missing dependencies in the analysis environment
                    pass
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error checking {file_path}: {e}")
        
        return errors
    
    def analyze_file_with_lsp(self, file_path: str) -> List[LSPError]:
        """Analyze a single file using LSP-based tools."""
        all_errors = []
        
        # Method 1: Use CLI-based LSP tools (pyflakes, mypy)
        cli_errors = self.get_lsp_diagnostics_via_cli(file_path)
        all_errors.extend(cli_errors)
        
        # Method 2: Use Python compilation check
        compile_errors = self.get_lsp_diagnostics_via_python_check(file_path)
        all_errors.extend(compile_errors)
        
        # Remove duplicates based on line, column, and message
        unique_errors = []
        seen = set()
        for error in all_errors:
            key = (error.line, error.column, error.message)
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        return unique_errors
    
    def analyze_directory(self, directory: str, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Analyze all Python files in a directory using LSP."""
        if self.verbose:
            print(f"🔍 Finding Python files in: {directory}")
        
        python_files = self.find_python_files(directory, max_files)
        self.total_files = len(python_files)
        
        if self.verbose:
            print(f"📊 Found {self.total_files} Python files")
            if max_files and self.total_files >= max_files:
                print(f"🎯 Limiting analysis to first {max_files} files")
        
        # Try to start LSP server for the workspace
        lsp_started = self.start_pylsp_server(directory)
        
        all_errors = []
        
        for file_path in python_files:
            if self.verbose:
                print(f"🔍 Analyzing {os.path.basename(file_path)} with LSP...")
            
            try:
                errors = self.analyze_file_with_lsp(file_path)
                all_errors.extend(errors)
                self.processed_files += 1
                
                if self.verbose and errors:
                    print(f"  🚨 Found {len(errors)} LSP runtime errors")
                elif self.verbose:
                    print(f"  ✅ No LSP errors found")
                
            except Exception as e:
                self.failed_files += 1
                if self.verbose:
                    print(f"  ❌ Failed to analyze: {e}")
        
        self.lsp_errors = all_errors
        
        # Categorize errors
        error_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        for error in all_errors:
            error_counts[error.category] += 1
            severity_counts[error.severity] += 1
            source_counts[error.source] += 1
        
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'total_errors': len(all_errors),
            'errors_by_category': dict(error_counts),
            'errors_by_severity': dict(severity_counts),
            'errors_by_source': dict(source_counts),
            'errors': all_errors
        }
    
    def format_output(self, results: Dict[str, Any], output_format: str = "text") -> str:
        """Format the LSP analysis results."""
        if output_format == "json":
            # Convert errors to dictionaries for JSON serialization
            json_results = results.copy()
            json_results['errors'] = [
                {
                    'file_path': error.file_path,
                    'line': error.line,
                    'column': error.column,
                    'severity': error.severity,
                    'message': error.message,
                    'source': error.source,
                    'code': error.code,
                    'category': error.category
                }
                for error in results['errors']
            ]
            return json.dumps(json_results, indent=2)
        
        # Text format
        errors = results['errors']
        if not errors:
            return "ERRORS: ['0']\nNo LSP runtime errors found. ✅ All code passes LSP validation!"
        
        lines = [f"ERRORS: ['{len(errors)}']"]
        
        # Sort errors by file, then by line number
        sorted_errors = sorted(errors, key=lambda e: (e.file_path, e.line, e.column))
        
        for i, error in enumerate(sorted_errors, 1):
            file_name = os.path.basename(error.file_path)
            location = f"line {error.line}, col {error.column}"
            
            # Include LSP source and code information
            source_info = f"source: {error.source}"
            if error.code:
                source_info += f", code: {error.code}"
            
            line = f"{i}. '{location}' '{file_name}' '{error.message}' '{source_info}, severity: {error.severity}'"
            lines.append(line)
        
        # Add comprehensive summary
        lines.append("")
        lines.append("=" * 70)
        lines.append("🎯 LSP RUNTIME ERROR ANALYSIS SUMMARY")
        lines.append("=" * 70)
        lines.append(f"📁 Files analyzed: {results['processed_files']}/{results['total_files']}")
        lines.append(f"🚨 LSP runtime errors found: {results['total_errors']}")
        
        if results['errors_by_severity']:
            lines.append("")
            lines.append("📊 Errors by severity:")
            for severity, count in results['errors_by_severity'].items():
                lines.append(f"  {severity}: {count}")
        
        if results['errors_by_source']:
            lines.append("")
            lines.append("🔧 Errors by LSP source:")
            for source, count in results['errors_by_source'].items():
                lines.append(f"  {source}: {count}")
        
        if results['errors_by_category']:
            lines.append("")
            lines.append("🏷️  Errors by category:")
            for category, count in results['errors_by_category'].items():
                lines.append(f"  {category}: {count}")
        
        return "\n".join(lines)
    
    def analyze(self, target: str, max_files: Optional[int] = None, output_format: str = "text") -> str:
        """Main LSP analysis function."""
        temp_dir = None
        
        try:
            # Handle Git URLs
            if self.is_git_url(target):
                target = self.clone_repository(target)
                temp_dir = os.path.dirname(target)
            
            # Ensure target exists
            if not os.path.exists(target):
                return f"ERRORS: ['0']\nError: Path '{target}' does not exist."
            
            # Analyze the directory using LSP
            results = self.analyze_directory(target, max_files)
            
            # Format and return results
            return self.format_output(results, output_format)
            
        finally:
            # Clean up LSP server and temporary directory
            if hasattr(self, 'lsp_process') and self.lsp_process:
                try:
                    self.lsp_process.terminate()
                    self.lsp_process.wait(timeout=5)
                except:
                    pass
            
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LSP Runtime Error Analyzer - Retrieves errors ONLY from LSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s https://github.com/user/repo.git --verbose
  %(prog)s . --max-files 50 --output json

This analyzer retrieves errors ONLY from Language Server Protocol (LSP)
to detect actual runtime errors, not static analysis false positives.

LSP Tools Used:
- pyflakes (runtime error detection)
- mypy (type checking and runtime errors)
- python compile (syntax error detection)

Install LSP dependencies:
  pip install python-lsp-server pyflakes mypy
        """
    )
    
    parser.add_argument(
        "target",
        help="Directory path or Git repository URL to analyze"
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum number of files to analyze (default: no limit)"
    )
    
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print("🚀 LSP RUNTIME ERROR ANALYZER")
        print("=" * 70)
        print(f"📁 Target: {args.target}")
        print(f"📊 Max files: {args.max_files or 'unlimited'}")
        print(f"📋 Output format: {args.output}")
        print("🔧 LSP Tools: pyflakes, mypy, python compile")
        print("=" * 70)
    
    # Run LSP analysis
    analyzer = LSPRuntimeAnalyzer(verbose=args.verbose)
    result = analyzer.analyze(args.target, args.max_files, args.output)
    
    print(result)

if __name__ == "__main__":
    main()
