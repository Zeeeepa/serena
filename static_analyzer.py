#!/usr/bin/env python3
"""
Static Python Code Analysis Tool
Analyzes Python code for common errors without requiring LSP
"""

import ast
import os
import sys
import tempfile
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import traceback

@dataclass
class StaticDiagnostic:
    """Static analysis diagnostic"""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: str = "static_analysis"

class PythonStaticAnalyzer(ast.NodeVisitor):
    """AST-based Python static analyzer"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.diagnostics = []
        self.imports = set()
        self.defined_names = set()
        self.used_names = set()
        
    def add_diagnostic(self, node, severity: str, message: str, code: str = None):
        """Add a diagnostic for a node"""
        diagnostic = StaticDiagnostic(
            file_path=self.file_path,
            line=getattr(node, 'lineno', 1),
            column=getattr(node, 'col_offset', 0) + 1,
            severity=severity,
            message=message,
            code=code,
            source="static_analysis"
        )
        self.diagnostics.append(diagnostic)
    
    def visit_Import(self, node):
        """Check import statements"""
        for alias in node.names:
            self.imports.add(alias.name)
            if alias.asname:
                self.defined_names.add(alias.asname)
            else:
                self.defined_names.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check from-import statements"""
        if node.module:
            self.imports.add(node.module)
        
        for alias in node.names:
            if alias.name == '*':
                self.add_diagnostic(node, "WARNING", "Wildcard import should be avoided", "W001")
            else:
                if alias.asname:
                    self.defined_names.add(alias.asname)
                else:
                    self.defined_names.add(alias.name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Check function definitions"""
        self.defined_names.add(node.name)
        
        # Check for functions with too many arguments
        if len(node.args.args) > 10:
            self.add_diagnostic(node, "WARNING", f"Function '{node.name}' has too many parameters ({len(node.args.args)})", "W002")
        
        # Check for missing docstring in public functions
        if not node.name.startswith('_') and not ast.get_docstring(node):
            self.add_diagnostic(node, "INFO", f"Public function '{node.name}' is missing a docstring", "I001")
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Check class definitions"""
        self.defined_names.add(node.name)
        
        # Check for missing docstring in public classes
        if not node.name.startswith('_') and not ast.get_docstring(node):
            self.add_diagnostic(node, "INFO", f"Public class '{node.name}' is missing a docstring", "I002")
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Check name usage"""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Check try-except blocks"""
        for handler in node.handlers:
            if handler.type is None:
                self.add_diagnostic(handler, "WARNING", "Bare except clause should be avoided", "W003")
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Check comparisons"""
        # Check for comparison with None using == instead of is
        for i, comparator in enumerate(node.comparators):
            if isinstance(comparator, ast.Constant) and comparator.value is None:
                op = node.ops[i]
                if isinstance(op, ast.Eq):
                    self.add_diagnostic(node, "WARNING", "Use 'is None' instead of '== None'", "W004")
                elif isinstance(op, ast.NotEq):
                    self.add_diagnostic(node, "WARNING", "Use 'is not None' instead of '!= None'", "W005")
        self.generic_visit(node)
    
    def finalize_analysis(self):
        """Finalize analysis and check for undefined names"""
        # Check for potentially undefined names (basic check)
        builtin_names = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'sum',
            'min', 'max', 'abs', 'round', 'open', 'type', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'delattr', 'callable', 'iter', 'next', 'all', 'any',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'ImportError', 'ModuleNotFoundError', 'FileNotFoundError', 'OSError', 'IOError',
            'True', 'False', 'None', '__name__', '__file__', '__doc__'
        }
        
        undefined_names = self.used_names - self.defined_names - builtin_names
        
        # Filter out common patterns that are likely defined elsewhere
        filtered_undefined = set()
        for name in undefined_names:
            # Skip names that are likely attributes or methods
            if '.' not in name and not name.startswith('__') and not name.endswith('__'):
                # Skip common patterns
                if name not in ['self', 'cls', 'args', 'kwargs', 'e', 'f', 'i', 'j', 'k', 'v', 'x', 'y', 'z']:
                    filtered_undefined.add(name)
        
        # Note: This is a very basic undefined name check and will have false positives
        # In a real LSP, this would be much more sophisticated

def analyze_python_file(file_path: str) -> List[StaticDiagnostic]:
    """Analyze a single Python file"""
    diagnostics = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            diagnostic = StaticDiagnostic(
                file_path=file_path,
                line=e.lineno or 1,
                column=(e.offset or 0) + 1,
                severity="ERROR",
                message=f"Syntax error: {e.msg}",
                code="E001",
                source="syntax_check"
            )
            diagnostics.append(diagnostic)
            return diagnostics
        
        # Run static analysis
        analyzer = PythonStaticAnalyzer(file_path)
        analyzer.visit(tree)
        analyzer.finalize_analysis()
        
        diagnostics.extend(analyzer.diagnostics)
        
    except Exception as e:
        diagnostic = StaticDiagnostic(
            file_path=file_path,
            line=1,
            column=1,
            severity="ERROR",
            message=f"Failed to analyze file: {str(e)}",
            code="E002",
            source="file_error"
        )
        diagnostics.append(diagnostic)
    
    return diagnostics

def clone_repository(repo_url: str) -> str:
    """Clone a Git repository to a temporary directory."""
    print(f"📥 Cloning repository: {repo_url}")
    
    temp_dir = tempfile.mkdtemp(prefix="static_analysis_")
    repo_name = os.path.basename(repo_url.rstrip("/").replace(".git", ""))
    clone_path = os.path.join(temp_dir, repo_name)
    
    try:
        cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        print(f"✅ Repository cloned to: {clone_path}")
        return clone_path
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 300 seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to clone repository: {e}")

def find_python_files(repo_path: str) -> List[str]:
    """Find all Python files in the repository"""
    python_files = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip common ignore directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
            "node_modules", "__pycache__", "target", "build", "dist", "vendor", ".venv", "venv"
        ]]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def format_results(diagnostics: List[StaticDiagnostic]) -> str:
    """Format diagnostics in the requested output format."""
    if not diagnostics:
        return "ERRORS: ['0']\nNo errors found."
    
    # Sort diagnostics by severity (ERROR first), then by file, then by line
    severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3}
    
    diagnostics.sort(key=lambda d: (
        severity_priority.get(d.severity, 4),
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
        
        # Clean message
        clean_message = diag.message.replace("\n", " ").replace("\r", " ")
        clean_message = " ".join(clean_message.split())
        
        if len(clean_message) > 200:
            clean_message = clean_message[:197] + "..."
        
        # Metadata
        metadata_parts = [f"severity: {diag.severity}"]
        if diag.code:
            metadata_parts.append(f"code: {diag.code}")
        if diag.source != "static_analysis":
            metadata_parts.append(f"source: {diag.source}")
        
        other_types = ", ".join(metadata_parts)
        
        diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
        output_lines.append(diagnostic_line)
    
    return "\n".join(output_lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Static Python Code Analysis Tool")
    parser.add_argument("repository", help="Repository URL or local path to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    print("🚀 STATIC PYTHON CODE ANALYSIS TOOL")
    print("=" * 60)
    print(f"📁 Target: {args.repository}")
    print("=" * 60)
    
    try:
        # Handle repository
        if args.repository.startswith("http") or args.repository.endswith(".git"):
            repo_path = clone_repository(args.repository)
        else:
            repo_path = os.path.abspath(args.repository)
            if not os.path.exists(repo_path):
                raise FileNotFoundError(f"Local path does not exist: {repo_path}")
            print(f"📂 Using local repository: {repo_path}")
        
        # Find Python files
        python_files = find_python_files(repo_path)
        print(f"📊 Found {len(python_files)} Python files to analyze")
        
        if len(python_files) == 0:
            print("⚠️  No Python files found")
            print("ERRORS: ['0']\nNo Python files found.")
            return
        
        # Analyze files
        all_diagnostics = []
        processed = 0
        
        for file_path in python_files:
            if args.verbose:
                print(f"📄 Analyzing {os.path.basename(file_path)}...")
            
            try:
                file_diagnostics = analyze_python_file(file_path)
                all_diagnostics.extend(file_diagnostics)
                processed += 1
                
                if args.verbose and len(file_diagnostics) > 0:
                    print(f"  ✅ Found {len(file_diagnostics)} issues")
                
            except Exception as e:
                if args.verbose:
                    print(f"  ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
        
        print(f"✅ Analyzed {processed}/{len(python_files)} files")
        
        # Format and output results
        result = format_results(all_diagnostics)
        
        print("\n" + "=" * 60)
        print("📋 STATIC ANALYSIS RESULTS")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Summary
        if all_diagnostics:
            severity_counts = {}
            for diag in all_diagnostics:
                severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
            
            print("\n📊 SUMMARY:")
            for severity, count in sorted(severity_counts.items()):
                print(f"  {severity}: {count}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        print(f"ERRORS: ['0']\nAnalysis failed: {e}")

if __name__ == "__main__":
    main()
