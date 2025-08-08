#!/usr/bin/env python3
"""
Enhanced Python Code Analysis Tool
Detects runtime errors, type issues, and complex code problems
"""

import ast
import os
import sys
import tempfile
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set
import traceback
import re

@dataclass
class EnhancedDiagnostic:
    """Enhanced diagnostic with runtime error detection"""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: str = "enhanced_analysis"
    category: str = "general"

class EnhancedPythonAnalyzer(ast.NodeVisitor):
    """Enhanced AST-based Python analyzer that detects runtime errors"""
    
    def __init__(self, file_path: str, file_content: str):
        self.file_path = file_path
        self.file_content = file_content
        self.lines = file_content.split('\n')
        self.diagnostics = []
        self.imports = set()
        self.defined_names = set()
        self.used_names = set()
        self.function_calls = []
        self.attribute_accesses = []
        self.variables = {}
        self.current_scope = []
        
    def add_diagnostic(self, node, severity: str, message: str, code: str = None, category: str = "general"):
        """Add a diagnostic for a node"""
        diagnostic = EnhancedDiagnostic(
            file_path=self.file_path,
            line=getattr(node, 'lineno', 1),
            column=getattr(node, 'col_offset', 0) + 1,
            severity=severity,
            message=message,
            code=code,
            source="enhanced_analysis",
            category=category
        )
        self.diagnostics.append(diagnostic)
    
    def visit_Import(self, node):
        """Check import statements for potential runtime errors"""
        for alias in node.names:
            self.imports.add(alias.name)
            # Check for common problematic imports
            if alias.name in ['os', 'subprocess', 'eval', 'exec']:
                self.add_diagnostic(node, "WARNING", f"Potentially dangerous import: {alias.name}", "W101", "security")
            
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
                self.add_diagnostic(node, "ERROR", "Wildcard import can cause runtime NameError", "E101", "runtime")
            else:
                if alias.asname:
                    self.defined_names.add(alias.asname)
                else:
                    self.defined_names.add(alias.name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Check function definitions for runtime issues"""
        self.defined_names.add(node.name)
        self.current_scope.append(node.name)
        
        # Check for functions with mutable default arguments
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.add_diagnostic(default, "ERROR", f"Mutable default argument in function '{node.name}' can cause runtime bugs", "E102", "runtime")
        
        # Check for functions with too many arguments (can cause runtime errors)
        total_args = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
        if total_args > 15:
            self.add_diagnostic(node, "WARNING", f"Function '{node.name}' has {total_args} parameters, may cause runtime issues", "W102", "runtime")
        
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_Call(self, node):
        """Check function calls for potential runtime errors"""
        # Track function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_calls.append(func_name)
            
            # Check for dangerous function calls
            dangerous_funcs = ['eval', 'exec', 'compile', '__import__']
            if func_name in dangerous_funcs:
                self.add_diagnostic(node, "ERROR", f"Dangerous function call: {func_name}() can cause runtime security issues", "E103", "security")
            
            # Check for common runtime error patterns
            if func_name == 'open' and len(node.args) == 1:
                self.add_diagnostic(node, "WARNING", "open() without mode specified may cause runtime issues", "W103", "runtime")
            
            if func_name in ['int', 'float'] and len(node.args) > 0:
                self.add_diagnostic(node, "WARNING", f"{func_name}() conversion may raise ValueError at runtime", "W104", "runtime")
        
        elif isinstance(node.func, ast.Attribute):
            # Check method calls
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                method_name = node.func.attr
                
                # Check for common runtime error patterns
                if method_name in ['pop', 'remove'] and obj_name not in self.defined_names:
                    self.add_diagnostic(node, "WARNING", f"Method {method_name}() on undefined variable '{obj_name}' may cause runtime error", "W105", "runtime")
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        """Check subscript operations for potential runtime errors"""
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if var_name not in self.defined_names:
                self.add_diagnostic(node, "ERROR", f"Subscript on undefined variable '{var_name}' will cause NameError", "E104", "runtime")
        
        # Check for potential KeyError/IndexError
        if isinstance(node.slice, ast.Constant):
            self.add_diagnostic(node, "WARNING", "Hard-coded subscript may cause KeyError/IndexError at runtime", "W106", "runtime")
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Check attribute access for potential runtime errors"""
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            attr_name = node.attr
            
            if obj_name not in self.defined_names and obj_name not in ['self', 'cls']:
                self.add_diagnostic(node, "ERROR", f"Attribute access on undefined variable '{obj_name}' will cause NameError", "E105", "runtime")
            
            # Track attribute accesses
            self.attribute_accesses.append((obj_name, attr_name))
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Check name usage for undefined variables"""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
            # Check for undefined variables (potential NameError)
            if (node.id not in self.defined_names and 
                node.id not in self.get_builtin_names() and
                node.id not in ['self', 'cls'] and
                not node.id.startswith('__')):
                self.add_diagnostic(node, "ERROR", f"Undefined variable '{node.id}' will cause NameError at runtime", "E106", "runtime")
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Check try-except blocks for runtime issues"""
        for handler in node.handlers:
            if handler.type is None:
                self.add_diagnostic(handler, "ERROR", "Bare except clause can hide runtime errors", "E107", "runtime")
            elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                self.add_diagnostic(handler, "WARNING", "Catching generic Exception may hide specific runtime errors", "W107", "runtime")
        self.generic_visit(node)
    
    def visit_Raise(self, node):
        """Check raise statements"""
        if node.exc is None:
            self.add_diagnostic(node, "WARNING", "Re-raising without exception context may cause runtime issues", "W108", "runtime")
        self.generic_visit(node)
    
    def visit_Assert(self, node):
        """Check assert statements"""
        self.add_diagnostic(node, "WARNING", "Assert statements are removed in optimized mode, may cause runtime issues", "W109", "runtime")
        self.generic_visit(node)
    
    def visit_Global(self, node):
        """Check global statements"""
        for name in node.names:
            self.add_diagnostic(node, "WARNING", f"Global variable '{name}' may cause runtime scoping issues", "W110", "runtime")
        self.generic_visit(node)
    
    def visit_Nonlocal(self, node):
        """Check nonlocal statements"""
        for name in node.names:
            self.add_diagnostic(node, "WARNING", f"Nonlocal variable '{name}' may cause runtime scoping issues", "W111", "runtime")
        self.generic_visit(node)
    
    def visit_Delete(self, node):
        """Check delete statements"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_diagnostic(node, "WARNING", f"Deleting variable '{target.id}' may cause NameError in subsequent access", "W112", "runtime")
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Check comparisons for runtime issues"""
        # Check for comparison with None using == instead of is
        for i, comparator in enumerate(node.comparators):
            if isinstance(comparator, ast.Constant) and comparator.value is None:
                op = node.ops[i]
                if isinstance(op, ast.Eq):
                    self.add_diagnostic(node, "WARNING", "Use 'is None' instead of '== None'", "W113", "runtime")
                elif isinstance(op, ast.NotEq):
                    self.add_diagnostic(node, "WARNING", "Use 'is not None' instead of '!= None'", "W114", "runtime")
        
        # Check for chained comparisons that might be confusing
        if len(node.ops) > 2:
            self.add_diagnostic(node, "WARNING", "Complex chained comparison may cause runtime logic errors", "W115", "runtime")
        
        self.generic_visit(node)
    
    def visit_BinOp(self, node):
        """Check binary operations for runtime issues"""
        # Check for division operations
        if isinstance(node.op, ast.Div):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.add_diagnostic(node, "ERROR", "Division by zero will cause ZeroDivisionError at runtime", "E108", "runtime")
            else:
                self.add_diagnostic(node, "WARNING", "Division operation may cause ZeroDivisionError at runtime", "W116", "runtime")
        
        # Check for modulo operations
        if isinstance(node.op, ast.Mod):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.add_diagnostic(node, "ERROR", "Modulo by zero will cause ZeroDivisionError at runtime", "E109", "runtime")
        
        self.generic_visit(node)
    
    def visit_ListComp(self, node):
        """Check list comprehensions for runtime issues"""
        # Check for complex list comprehensions that might cause performance issues
        if len(node.generators) > 2:
            self.add_diagnostic(node, "WARNING", "Complex list comprehension may cause runtime performance issues", "W117", "performance")
        self.generic_visit(node)
    
    def check_string_formatting(self):
        """Check for string formatting issues in the file content"""
        for i, line in enumerate(self.lines, 1):
            # Check for old-style string formatting
            if re.search(r'%[sdif]', line):
                diagnostic = EnhancedDiagnostic(
                    file_path=self.file_path,
                    line=i,
                    column=1,
                    severity="WARNING",
                    message="Old-style string formatting may cause runtime TypeError",
                    code="W118",
                    source="enhanced_analysis",
                    category="runtime"
                )
                self.diagnostics.append(diagnostic)
            
            # Check for f-string with undefined variables (basic check)
            f_string_matches = re.findall(r'f["\'].*?\{([^}]+)\}.*?["\']', line)
            for match in f_string_matches:
                var_name = match.strip().split('.')[0].split('[')[0]
                if (var_name not in self.defined_names and 
                    var_name not in self.get_builtin_names() and
                    var_name not in ['self', 'cls']):
                    diagnostic = EnhancedDiagnostic(
                        file_path=self.file_path,
                        line=i,
                        column=1,
                        severity="ERROR",
                        message=f"f-string references undefined variable '{var_name}', will cause NameError",
                        code="E110",
                        source="enhanced_analysis",
                        category="runtime"
                    )
                    self.diagnostics.append(diagnostic)
    
    def get_builtin_names(self) -> Set[str]:
        """Get set of Python builtin names"""
        return {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'sum',
            'min', 'max', 'abs', 'round', 'open', 'type', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'delattr', 'callable', 'iter', 'next', 'all', 'any',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'ImportError', 'ModuleNotFoundError', 'FileNotFoundError', 'OSError', 'IOError',
            'NameError', 'ZeroDivisionError', 'RuntimeError', 'NotImplementedError',
            'True', 'False', 'None', '__name__', '__file__', '__doc__', '__package__'
        }
    
    def finalize_analysis(self):
        """Finalize analysis with additional checks"""
        self.check_string_formatting()
        
        # Check for unused imports (potential cleanup needed)
        unused_imports = self.imports - self.used_names
        for unused in unused_imports:
            if unused not in ['os', 'sys', 'typing']:  # Common false positives
                diagnostic = EnhancedDiagnostic(
                    file_path=self.file_path,
                    line=1,
                    column=1,
                    severity="INFO",
                    message=f"Unused import: {unused}",
                    code="I101",
                    source="enhanced_analysis",
                    category="cleanup"
                )
                self.diagnostics.append(diagnostic)

def analyze_python_file_enhanced(file_path: str) -> List[EnhancedDiagnostic]:
    """Enhanced analysis of a single Python file"""
    diagnostics = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Try to parse the file
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            diagnostic = EnhancedDiagnostic(
                file_path=file_path,
                line=e.lineno or 1,
                column=(e.offset or 0) + 1,
                severity="ERROR",
                message=f"Syntax error: {e.msg}",
                code="E001",
                source="syntax_check",
                category="syntax"
            )
            diagnostics.append(diagnostic)
            return diagnostics
        
        # Run enhanced analysis
        analyzer = EnhancedPythonAnalyzer(file_path, content)
        analyzer.visit(tree)
        analyzer.finalize_analysis()
        
        diagnostics.extend(analyzer.diagnostics)
        
    except Exception as e:
        diagnostic = EnhancedDiagnostic(
            file_path=file_path,
            line=1,
            column=1,
            severity="ERROR",
            message=f"Failed to analyze file: {str(e)}",
            code="E002",
            source="file_error",
            category="system"
        )
        diagnostics.append(diagnostic)
    
    return diagnostics

def clone_repository(repo_url: str) -> str:
    """Clone a Git repository to a temporary directory."""
    print(f"📥 Cloning repository: {repo_url}")
    
    temp_dir = tempfile.mkdtemp(prefix="enhanced_analysis_")
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

def format_enhanced_results(diagnostics: List[EnhancedDiagnostic]) -> str:
    """Format enhanced diagnostics with better categorization"""
    if not diagnostics:
        return "ERRORS: ['0']\nNo errors found."
    
    # Sort diagnostics by severity (ERROR first), then by category, then by file
    severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3}
    
    diagnostics.sort(key=lambda d: (
        severity_priority.get(d.severity, 4),
        d.category,
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
        
        # Enhanced metadata
        metadata_parts = [f"severity: {diag.severity}"]
        if diag.code:
            metadata_parts.append(f"code: {diag.code}")
        if diag.category != "general":
            metadata_parts.append(f"category: {diag.category}")
        if diag.source != "enhanced_analysis":
            metadata_parts.append(f"source: {diag.source}")
        
        other_types = ", ".join(metadata_parts)
        
        diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
        output_lines.append(diagnostic_line)
    
    return "\n".join(output_lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Python Code Analysis Tool - Detects Runtime Errors")
    parser.add_argument("repository", help="Repository URL or local path to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--max-files", type=int, default=100, help="Maximum files to analyze (default: 100)")
    
    args = parser.parse_args()
    
    print("🚀 ENHANCED PYTHON CODE ANALYSIS TOOL")
    print("🔍 RUNTIME ERROR DETECTION ENABLED")
    print("=" * 60)
    print(f"📁 Target: {args.repository}")
    print(f"📊 Max files: {args.max_files}")
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
        print(f"📊 Found {len(python_files)} Python files")
        
        # Limit files for performance
        if len(python_files) > args.max_files:
            python_files = python_files[:args.max_files]
            print(f"🎯 Analyzing first {args.max_files} files for performance")
        
        if len(python_files) == 0:
            print("⚠️  No Python files found")
            print("ERRORS: ['0']\nNo Python files found.")
            return
        
        # Analyze files with enhanced detection
        all_diagnostics = []
        processed = 0
        
        for file_path in python_files:
            if args.verbose:
                print(f"🔍 Analyzing {os.path.basename(file_path)}...")
            
            try:
                file_diagnostics = analyze_python_file_enhanced(file_path)
                all_diagnostics.extend(file_diagnostics)
                processed += 1
                
                if args.verbose and len(file_diagnostics) > 0:
                    runtime_errors = len([d for d in file_diagnostics if d.category == "runtime"])
                    if runtime_errors > 0:
                        print(f"  🚨 Found {runtime_errors} runtime errors, {len(file_diagnostics)} total issues")
                    else:
                        print(f"  ✅ Found {len(file_diagnostics)} issues")
                
            except Exception as e:
                if args.verbose:
                    print(f"  ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
        
        print(f"✅ Analyzed {processed}/{len(python_files)} files")
        
        # Format and output results
        result = format_enhanced_results(all_diagnostics)
        
        print("\n" + "=" * 60)
        print("🔍 ENHANCED ANALYSIS RESULTS")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Enhanced summary
        if all_diagnostics:
            severity_counts = {}
            category_counts = {}
            
            for diag in all_diagnostics:
                severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
                category_counts[diag.category] = category_counts.get(diag.category, 0) + 1
            
            print("\n🎯 SUMMARY BY SEVERITY:")
            for severity, count in sorted(severity_counts.items()):
                icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "🔍")
                print(f"  {icon} {severity}: {count}")
            
            print("\n🔍 SUMMARY BY CATEGORY:")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                icon = {"runtime": "🚨", "security": "🔒", "performance": "⚡", "syntax": "❌"}.get(category, "📋")
                print(f"  {icon} {category}: {count}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        print(f"ERRORS: ['0']\nAnalysis failed: {e}")

if __name__ == "__main__":
    main()
