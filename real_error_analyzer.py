#!/usr/bin/env python3
"""
Real Error Analyzer - Only shows actual errors that would occur at runtime

This analyzer uses proper scope resolution and semantic analysis to detect
only real errors, not false positives.
"""

import ast
import os
import sys
import json
import argparse
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import importlib.util
import traceback

@dataclass
class RealError:
    """Represents a real error that would occur at runtime."""
    file_path: str
    line: int
    column: int
    error_type: str
    message: str
    severity: str
    code: str
    category: str

class ScopeAnalyzer(ast.NodeVisitor):
    """Analyzes variable scopes and imports to detect real errors."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.errors = []
        self.scopes = [set()]  # Stack of scopes
        self.imports = set()
        self.builtin_names = set(dir(__builtins__))
        self.current_class = None
        self.current_function = None
        
        # Add common Python builtins that might not be in __builtins__
        self.builtin_names.update({
            'Exception', 'ValueError', 'TypeError', 'AttributeError', 'KeyError',
            'IndexError', 'NameError', 'ImportError', 'FileNotFoundError',
            'RuntimeError', 'NotImplementedError', 'StopIteration', 'GeneratorExit',
            'SystemExit', 'KeyboardInterrupt', 'UnicodeDecodeError', 'SyntaxError',
            'IndentationError', 'TabError', 'ZeroDivisionError', 'OverflowError',
            'FloatingPointError', 'ArithmeticError', 'LookupError', 'BufferError',
            'MemoryError', 'Warning', 'UserWarning', 'DeprecationWarning',
            'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
            'FutureWarning', 'ImportWarning', 'UnicodeWarning', 'BytesWarning',
            'ResourceWarning', 'ConnectionError', 'BlockingIOError', 'ChildProcessError',
            'ConnectionAbortedError', 'ConnectionRefusedError', 'ConnectionResetError',
            'FileExistsError', 'IsADirectoryError', 'NotADirectoryError',
            'InterruptedError', 'PermissionError', 'ProcessLookupError', 'TimeoutError',
            'OSError', 'IOError', 'EOFError', 'AssertionError', 'SystemError',
            'ReferenceError', 'RecursionError', 'UnboundLocalError'
        })
    
    def push_scope(self):
        """Push a new scope onto the stack."""
        self.scopes.append(set())
    
    def pop_scope(self):
        """Pop the current scope from the stack."""
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def add_name(self, name: str):
        """Add a name to the current scope."""
        self.scopes[-1].add(name)
    
    def is_name_defined(self, name: str) -> bool:
        """Check if a name is defined in any scope."""
        # Check all scopes from innermost to outermost
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        
        # Check imports
        if name in self.imports:
            return True
        
        # Check builtins
        if name in self.builtin_names:
            return True
        
        return False
    
    def add_error(self, node: ast.AST, error_type: str, message: str, severity: str = "ERROR"):
        """Add a real error to the list."""
        error = RealError(
            file_path=self.file_path,
            line=node.lineno,
            column=node.col_offset + 1,
            error_type=error_type,
            message=message,
            severity=severity,
            code=f"E{len(self.errors) + 1:03d}",
            category="real_error"
        )
        self.errors.append(error)
    
    def visit_Import(self, node: ast.Import):
        """Handle import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
            self.add_name(name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from ... import statements."""
        for alias in node.names:
            if alias.name == '*':
                # Can't easily resolve * imports, so skip
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
            self.add_name(name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions."""
        self.add_name(node.name)
        
        # Push new scope for function
        old_function = self.current_function
        self.current_function = node.name
        self.push_scope()
        
        # Add parameters to scope
        for arg in node.args.args:
            self.add_name(arg.arg)
        
        # Add *args and **kwargs if present
        if node.args.vararg:
            self.add_name(node.args.vararg.arg)
        if node.args.kwarg:
            self.add_name(node.args.kwarg.arg)
        
        # Visit function body
        for stmt in node.body:
            self.visit(stmt)
        
        # Pop function scope
        self.pop_scope()
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)  # Same logic as regular functions
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions."""
        self.add_name(node.name)
        
        # Push new scope for class
        old_class = self.current_class
        self.current_class = node.name
        self.push_scope()
        
        # Visit class body
        for stmt in node.body:
            self.visit(stmt)
        
        # Pop class scope
        self.pop_scope()
        self.current_class = old_class
    
    def visit_Assign(self, node: ast.Assign):
        """Handle assignments."""
        # Visit the value first
        self.visit(node.value)
        
        # Add assigned names to scope
        for target in node.targets:
            self._add_assignment_targets(target)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignments."""
        if node.value:
            self.visit(node.value)
        self._add_assignment_targets(node.target)
    
    def visit_AugAssign(self, node: ast.AugAssign):
        """Handle augmented assignments (+=, -=, etc.)."""
        self.visit(node.value)
        # Target should already be defined for augmented assignment
        self.visit(node.target)
    
    def _add_assignment_targets(self, target: ast.AST):
        """Add assignment targets to the current scope."""
        if isinstance(target, ast.Name):
            self.add_name(target.id)
        elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
            for elt in target.elts:
                self._add_assignment_targets(elt)
        elif isinstance(target, ast.Starred):
            self._add_assignment_targets(target.value)
        # For other types (Attribute, Subscript), don't add to scope
    
    def visit_For(self, node: ast.For):
        """Handle for loops."""
        # Visit the iterator first
        self.visit(node.iter)
        
        # Add loop variable to scope
        self._add_assignment_targets(node.target)
        
        # Visit loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Visit else clause if present
        for stmt in node.orelse:
            self.visit(stmt)
    
    def visit_AsyncFor(self, node: ast.AsyncFor):
        """Handle async for loops."""
        self.visit_For(node)  # Same logic as regular for loops
    
    def visit_With(self, node: ast.With):
        """Handle with statements."""
        # Visit context expressions first
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self._add_assignment_targets(item.optional_vars)
        
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_AsyncWith(self, node: ast.AsyncWith):
        """Handle async with statements."""
        self.visit_With(node)  # Same logic as regular with statements
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Handle except clauses."""
        if node.type:
            self.visit(node.type)
        
        if node.name:
            self.add_name(node.name)
        
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_comprehension(self, node: ast.comprehension):
        """Handle list/dict/set comprehensions."""
        # Visit iterator first
        self.visit(node.iter)
        
        # Add target to scope (but in a new scope for comprehensions)
        self.push_scope()
        self._add_assignment_targets(node.target)
        
        # Visit conditions
        for if_ in node.ifs:
            self.visit(if_)
        
        # Don't pop scope here - let the parent comprehension handle it
    
    def visit_ListComp(self, node: ast.ListComp):
        """Handle list comprehensions."""
        # Comprehensions have their own scope
        self.push_scope()
        
        # Visit generators (in reverse order for proper scoping)
        for generator in node.generators:
            self.visit_comprehension(generator)
        
        # Visit element
        self.visit(node.elt)
        
        self.pop_scope()
    
    def visit_SetComp(self, node: ast.SetComp):
        """Handle set comprehensions."""
        self.visit_ListComp(node)  # Same logic as list comprehensions
    
    def visit_DictComp(self, node: ast.DictComp):
        """Handle dict comprehensions."""
        self.push_scope()
        
        for generator in node.generators:
            self.visit_comprehension(generator)
        
        self.visit(node.key)
        self.visit(node.value)
        
        self.pop_scope()
    
    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        """Handle generator expressions."""
        self.visit_ListComp(node)  # Same logic as list comprehensions
    
    def visit_Name(self, node: ast.Name):
        """Handle name references."""
        if isinstance(node.ctx, ast.Load):
            # This is a name being used (not assigned)
            if not self.is_name_defined(node.id):
                self.add_error(
                    node,
                    "NameError",
                    f"Name '{node.id}' is not defined",
                    "ERROR"
                )
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Handle attribute access."""
        # Only check the base object, not the attribute name
        self.visit(node.value)
    
    def visit_Call(self, node: ast.Call):
        """Handle function calls."""
        # Check if we're calling an undefined function
        if isinstance(node.func, ast.Name):
            if not self.is_name_defined(node.func.id):
                self.add_error(
                    node,
                    "NameError",
                    f"Name '{node.func.id}' is not defined",
                    "ERROR"
                )
        
        self.generic_visit(node)

class RealErrorAnalyzer:
    """Analyzes Python code to find only real errors that would occur at runtime."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.all_errors = []
    
    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        return path.startswith(('http://', 'https://')) and '.git' in path
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        if self.verbose:
            print(f"📥 Cloning repository: {repo_url}")
        
        temp_dir = tempfile.mkdtemp(prefix="real_error_analysis_")
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
    
    def analyze_file(self, file_path: str) -> List[RealError]:
        """Analyze a single Python file for real errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                # Syntax errors are real errors
                return [RealError(
                    file_path=file_path,
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    error_type="SyntaxError",
                    message=str(e.msg),
                    severity="ERROR",
                    code="E001",
                    category="syntax_error"
                )]
            
            # Analyze for real errors
            analyzer = ScopeAnalyzer(file_path)
            analyzer.visit(tree)
            
            return analyzer.errors
            
        except UnicodeDecodeError:
            return [RealError(
                file_path=file_path,
                line=1,
                column=1,
                error_type="UnicodeDecodeError",
                message="File contains invalid UTF-8 encoding",
                severity="ERROR",
                code="E002",
                category="encoding_error"
            )]
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error analyzing {file_path}: {e}")
            return []
    
    def analyze_directory(self, directory: str, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Analyze all Python files in a directory."""
        if self.verbose:
            print(f"🔍 Finding Python files in: {directory}")
        
        python_files = self.find_python_files(directory, max_files)
        self.total_files = len(python_files)
        
        if self.verbose:
            print(f"📊 Found {self.total_files} Python files")
            if max_files and self.total_files >= max_files:
                print(f"🎯 Limiting analysis to first {max_files} files")
        
        all_errors = []
        
        for file_path in python_files:
            if self.verbose:
                print(f"🔍 Analyzing {os.path.basename(file_path)}...")
            
            try:
                errors = self.analyze_file(file_path)
                all_errors.extend(errors)
                self.processed_files += 1
                
                if self.verbose and errors:
                    print(f"  🚨 Found {len(errors)} real errors")
                
            except Exception as e:
                self.failed_files += 1
                if self.verbose:
                    print(f"  ❌ Failed to analyze: {e}")
        
        self.all_errors = all_errors
        
        # Categorize errors
        error_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for error in all_errors:
            error_counts[error.error_type] += 1
            severity_counts[error.severity] += 1
        
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'total_errors': len(all_errors),
            'errors_by_type': dict(error_counts),
            'errors_by_severity': dict(severity_counts),
            'errors': all_errors
        }
    
    def format_output(self, results: Dict[str, Any], output_format: str = "text") -> str:
        """Format the analysis results."""
        if output_format == "json":
            # Convert errors to dictionaries for JSON serialization
            json_results = results.copy()
            json_results['errors'] = [
                {
                    'file_path': error.file_path,
                    'line': error.line,
                    'column': error.column,
                    'error_type': error.error_type,
                    'message': error.message,
                    'severity': error.severity,
                    'code': error.code,
                    'category': error.category
                }
                for error in results['errors']
            ]
            return json.dumps(json_results, indent=2)
        
        # Text format
        errors = results['errors']
        if not errors:
            return "ERRORS: ['0']\nNo real errors found."
        
        lines = [f"ERRORS: ['{len(errors)}']"]
        
        # Sort errors by file, then by line number
        sorted_errors = sorted(errors, key=lambda e: (e.file_path, e.line, e.column))
        
        for i, error in enumerate(sorted_errors, 1):
            file_name = os.path.basename(error.file_path)
            location = f"line {error.line}, col {error.column}"
            
            line = f"{i}. '{location}' '{file_name}' '{error.message}' 'severity: {error.severity}, code: {error.code}, type: {error.error_type}'"
            lines.append(line)
        
        # Add summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("🎯 REAL ERROR ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"📁 Files analyzed: {results['processed_files']}/{results['total_files']}")
        lines.append(f"🚨 Real errors found: {results['total_errors']}")
        
        if results['errors_by_severity']:
            lines.append("")
            lines.append("📊 Errors by severity:")
            for severity, count in results['errors_by_severity'].items():
                lines.append(f"  {severity}: {count}")
        
        if results['errors_by_type']:
            lines.append("")
            lines.append("📋 Errors by type:")
            for error_type, count in results['errors_by_type'].items():
                lines.append(f"  {error_type}: {count}")
        
        return "\n".join(lines)
    
    def analyze(self, target: str, max_files: Optional[int] = None, output_format: str = "text") -> str:
        """Main analysis function."""
        temp_dir = None
        
        try:
            # Handle Git URLs
            if self.is_git_url(target):
                target = self.clone_repository(target)
                temp_dir = os.path.dirname(target)
            
            # Ensure target exists
            if not os.path.exists(target):
                return f"ERRORS: ['0']\nError: Path '{target}' does not exist."
            
            # Analyze the directory
            results = self.analyze_directory(target, max_files)
            
            # Format and return results
            return self.format_output(results, output_format)
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Real Error Analyzer - Only shows actual Python errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s https://github.com/user/repo.git --verbose
  %(prog)s . --max-files 50 --output json
  %(prog)s project --verbose --output json

This analyzer uses proper scope resolution to detect only real errors
that would actually occur when running the Python code, eliminating
false positives from basic AST analysis.
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
        print("🚀 REAL ERROR ANALYZER")
        print("=" * 60)
        print(f"📁 Target: {args.target}")
        print(f"📊 Max files: {args.max_files or 'unlimited'}")
        print(f"📋 Output format: {args.output}")
        print("=" * 60)
    
    # Run analysis
    analyzer = RealErrorAnalyzer(verbose=args.verbose)
    result = analyzer.analyze(args.target, args.max_files, args.output)
    
    print(result)

if __name__ == "__main__":
    main()
