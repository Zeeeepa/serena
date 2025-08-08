#!/usr/bin/env python3
"""
Functional Python Code Analysis Tool
Detects missing imports, unused code, dead code, and dysfunctional patterns
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
class FunctionalDiagnostic:
    """Functional code diagnostic"""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: str = "functional_analysis"
    category: str = "general"

class FunctionalPythonAnalyzer(ast.NodeVisitor):
    """AST-based analyzer focused on functional code issues"""
    
    def __init__(self, file_path: str, file_content: str):
        self.file_path = file_path
        self.file_content = file_content
        self.lines = file_content.split('\n')
        self.diagnostics = []
        
        # Track imports and usage
        self.imports = {}  # module_name -> line_number
        self.from_imports = {}  # name -> (module, line_number)
        self.defined_names = set()
        self.used_names = set()
        self.function_definitions = {}  # name -> line_number
        self.class_definitions = {}  # name -> line_number
        self.variable_assignments = {}  # name -> line_number
        
        # Track function/method calls
        self.function_calls = set()
        self.method_calls = set()
        self.attribute_accesses = set()
        
        # Track control flow
        self.unreachable_code = []
        self.current_scope = []
        
    def add_diagnostic(self, node, severity: str, message: str, code: str = None, category: str = "general"):
        """Add a diagnostic for a node"""
        diagnostic = FunctionalDiagnostic(
            file_path=self.file_path,
            line=getattr(node, 'lineno', 1),
            column=getattr(node, 'col_offset', 0) + 1,
            severity=severity,
            message=message,
            code=code,
            source="functional_analysis",
            category=category
        )
        self.diagnostics.append(diagnostic)
    
    def visit_Import(self, node):
        """Track import statements"""
        for alias in node.names:
            module_name = alias.asname if alias.asname else alias.name
            self.imports[module_name] = node.lineno
            self.defined_names.add(module_name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Track from-import statements"""
        if node.module:
            for alias in node.names:
                if alias.name == '*':
                    self.add_diagnostic(node, "ERROR", "Wildcard import makes code unpredictable and can cause NameError", "E201", "imports")
                else:
                    name = alias.asname if alias.asname else alias.name
                    self.from_imports[name] = (node.module, node.lineno)
                    self.defined_names.add(name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Track function definitions"""
        self.function_definitions[node.name] = node.lineno
        self.defined_names.add(node.name)
        self.current_scope.append(f"function:{node.name}")
        
        # Check for functions with mutable default arguments
        for i, default in enumerate(node.args.defaults):
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                param_name = node.args.args[-(len(node.args.defaults) - i)].arg
                self.add_diagnostic(default, "ERROR", f"Mutable default argument '{param_name}' in function '{node.name}' causes shared state bugs", "E202", "bugs")
        
        # Check for empty functions (potential dead code)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.add_diagnostic(node, "WARNING", f"Empty function '{node.name}' - potential dead code", "W201", "dead_code")
        
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_AsyncFunctionDef(self, node):
        """Track async function definitions"""
        self.function_definitions[node.name] = node.lineno
        self.defined_names.add(node.name)
        self.current_scope.append(f"async_function:{node.name}")
        
        # Check for empty async functions
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.add_diagnostic(node, "WARNING", f"Empty async function '{node.name}' - potential dead code", "W202", "dead_code")
        
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_ClassDef(self, node):
        """Track class definitions"""
        self.class_definitions[node.name] = node.lineno
        self.defined_names.add(node.name)
        self.current_scope.append(f"class:{node.name}")
        
        # Check for empty classes (potential dead code)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.add_diagnostic(node, "WARNING", f"Empty class '{node.name}' - potential dead code", "W203", "dead_code")
        
        self.generic_visit(node)
        self.current_scope.pop()
    
    def visit_Assign(self, node):
        """Track variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_assignments[target.id] = node.lineno
                self.defined_names.add(target.id)
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """Track annotated assignments"""
        if isinstance(node.target, ast.Name):
            self.variable_assignments[node.target.id] = node.lineno
            self.defined_names.add(node.target.id)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Track function calls and detect issues"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_calls.add(func_name)
            self.used_names.add(func_name)
            
            # Check for common problematic patterns
            if func_name in ['int', 'float', 'str'] and len(node.args) == 0:
                self.add_diagnostic(node, "WARNING", f"{func_name}() called without arguments - likely unintended", "W204", "usage")
            
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                method_name = node.func.attr
                self.method_calls.add((obj_name, method_name))
                self.used_names.add(obj_name)
                
                # Check for method calls on potentially undefined objects
                if obj_name not in self.defined_names and obj_name not in ['self', 'cls']:
                    self.add_diagnostic(node, "ERROR", f"Method '{method_name}()' called on undefined object '{obj_name}'", "E203", "missing")
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Track attribute access"""
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            attr_name = node.attr
            self.attribute_accesses.add((obj_name, attr_name))
            self.used_names.add(obj_name)
            
            # Check for attribute access on undefined objects
            if obj_name not in self.defined_names and obj_name not in ['self', 'cls']:
                self.add_diagnostic(node, "ERROR", f"Attribute '{attr_name}' accessed on undefined object '{obj_name}'", "E204", "missing")
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Track name usage and detect undefined variables"""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
            
            # Check for undefined variables
            if (node.id not in self.defined_names and 
                node.id not in self.get_builtin_names() and
                node.id not in ['self', 'cls'] and
                not node.id.startswith('__')):
                self.add_diagnostic(node, "ERROR", f"Undefined variable '{node.id}' will cause NameError", "E205", "missing")
                
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Check return statements"""
        # Check for unreachable code after return
        if hasattr(node, 'lineno'):
            # This is a simplified check - in practice, you'd need more sophisticated control flow analysis
            pass
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Check try-except blocks for issues"""
        for handler in node.handlers:
            if handler.type is None:
                self.add_diagnostic(handler, "ERROR", "Bare except clause hides all errors and makes debugging impossible", "E206", "bugs")
            
            # Check for empty except blocks (potential dead code)
            if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                self.add_diagnostic(handler, "WARNING", "Empty except block - errors are silently ignored", "W205", "dead_code")
        
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Check if statements for dead code"""
        # Check for if True: or if False: patterns
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                if node.orelse:
                    self.add_diagnostic(node, "WARNING", "else clause after 'if True:' is dead code", "W206", "dead_code")
            elif node.test.value is False:
                self.add_diagnostic(node, "WARNING", "'if False:' block is dead code", "W207", "dead_code")
        
        self.generic_visit(node)
    
    def visit_While(self, node):
        """Check while loops for dead code"""
        if isinstance(node.test, ast.Constant):
            if node.test.value is False:
                self.add_diagnostic(node, "WARNING", "'while False:' loop is dead code", "W208", "dead_code")
        
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Check comparisons for issues"""
        # Check for comparison with None using == instead of is
        for i, comparator in enumerate(node.comparators):
            if isinstance(comparator, ast.Constant) and comparator.value is None:
                op = node.ops[i]
                if isinstance(op, ast.Eq):
                    self.add_diagnostic(node, "WARNING", "Use 'is None' instead of '== None' for None comparison", "W209", "usage")
                elif isinstance(op, ast.NotEq):
                    self.add_diagnostic(node, "WARNING", "Use 'is not None' instead of '!= None' for None comparison", "W210", "usage")
        
        self.generic_visit(node)
    
    def visit_BinOp(self, node):
        """Check binary operations for issues"""
        # Check for division by zero
        if isinstance(node.op, ast.Div):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.add_diagnostic(node, "ERROR", "Division by zero will cause ZeroDivisionError", "E207", "bugs")
        
        # Check for modulo by zero
        if isinstance(node.op, ast.Mod):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.add_diagnostic(node, "ERROR", "Modulo by zero will cause ZeroDivisionError", "E208", "bugs")
        
        self.generic_visit(node)
    
    def check_unused_imports(self):
        """Check for unused imports"""
        # Check regular imports
        for module_name, line_no in self.imports.items():
            if module_name not in self.used_names:
                # Skip common false positives
                if module_name not in ['typing', '__future__']:
                    diagnostic = FunctionalDiagnostic(
                        file_path=self.file_path,
                        line=line_no,
                        column=1,
                        severity="WARNING",
                        message=f"Unused import: {module_name}",
                        code="W211",
                        source="functional_analysis",
                        category="unused"
                    )
                    self.diagnostics.append(diagnostic)
        
        # Check from imports
        for name, (module, line_no) in self.from_imports.items():
            if name not in self.used_names:
                diagnostic = FunctionalDiagnostic(
                    file_path=self.file_path,
                    line=line_no,
                    column=1,
                    severity="WARNING",
                    message=f"Unused import: {name} from {module}",
                    code="W212",
                    source="functional_analysis",
                    category="unused"
                )
                self.diagnostics.append(diagnostic)
    
    def check_unused_variables(self):
        """Check for unused variables"""
        for var_name, line_no in self.variable_assignments.items():
            if (var_name not in self.used_names and 
                not var_name.startswith('_') and  # Skip private variables
                var_name not in ['self', 'cls']):
                diagnostic = FunctionalDiagnostic(
                    file_path=self.file_path,
                    line=line_no,
                    column=1,
                    severity="WARNING",
                    message=f"Unused variable: {var_name}",
                    code="W213",
                    source="functional_analysis",
                    category="unused"
                )
                self.diagnostics.append(diagnostic)
    
    def check_unused_functions(self):
        """Check for unused functions"""
        for func_name, line_no in self.function_definitions.items():
            if (func_name not in self.used_names and 
                not func_name.startswith('_') and  # Skip private functions
                func_name not in ['main', '__init__', '__str__', '__repr__']):  # Skip special functions
                diagnostic = FunctionalDiagnostic(
                    file_path=self.file_path,
                    line=line_no,
                    column=1,
                    severity="WARNING",
                    message=f"Unused function: {func_name}",
                    code="W214",
                    source="functional_analysis",
                    category="dead_code"
                )
                self.diagnostics.append(diagnostic)
    
    def check_unused_classes(self):
        """Check for unused classes"""
        for class_name, line_no in self.class_definitions.items():
            if (class_name not in self.used_names and 
                not class_name.startswith('_')):  # Skip private classes
                diagnostic = FunctionalDiagnostic(
                    file_path=self.file_path,
                    line=line_no,
                    column=1,
                    severity="WARNING",
                    message=f"Unused class: {class_name}",
                    code="W215",
                    source="functional_analysis",
                    category="dead_code"
                )
                self.diagnostics.append(diagnostic)
    
    def check_string_issues(self):
        """Check for string-related issues"""
        for i, line in enumerate(self.lines, 1):
            # Check for f-string with undefined variables
            f_string_matches = re.findall(r'f["\'].*?\{([^}]+)\}.*?["\']', line)
            for match in f_string_matches:
                var_name = match.strip().split('.')[0].split('[')[0].split('(')[0]
                if (var_name not in self.defined_names and 
                    var_name not in self.get_builtin_names() and
                    var_name not in ['self', 'cls'] and
                    not var_name.isdigit()):
                    diagnostic = FunctionalDiagnostic(
                        file_path=self.file_path,
                        line=i,
                        column=1,
                        severity="ERROR",
                        message=f"f-string references undefined variable '{var_name}'",
                        code="E209",
                        source="functional_analysis",
                        category="missing"
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
        """Run final analysis checks"""
        self.check_unused_imports()
        self.check_unused_variables()
        self.check_unused_functions()
        self.check_unused_classes()
        self.check_string_issues()

def analyze_python_file_functional(file_path: str) -> List[FunctionalDiagnostic]:
    """Functional analysis of a single Python file"""
    diagnostics = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Try to parse the file
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            diagnostic = FunctionalDiagnostic(
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
        
        # Run functional analysis
        analyzer = FunctionalPythonAnalyzer(file_path, content)
        analyzer.visit(tree)
        analyzer.finalize_analysis()
        
        diagnostics.extend(analyzer.diagnostics)
        
    except Exception as e:
        diagnostic = FunctionalDiagnostic(
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
    
    temp_dir = tempfile.mkdtemp(prefix="functional_analysis_")
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

def format_functional_results(diagnostics: List[FunctionalDiagnostic]) -> str:
    """Format functional diagnostics"""
    if not diagnostics:
        return "ERRORS: ['0']\nNo functional issues found."
    
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
        
        other_types = ", ".join(metadata_parts)
        
        diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
        output_lines.append(diagnostic_line)
    
    return "\n".join(output_lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Functional Python Code Analysis - Missing/Unused/Dead Code Detection")
    parser.add_argument("repository", help="Repository URL or local path to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--max-files", type=int, default=100, help="Maximum files to analyze (default: 100)")
    
    args = parser.parse_args()
    
    print("🚀 FUNCTIONAL PYTHON CODE ANALYSIS TOOL")
    print("🔍 MISSING/UNUSED/DEAD CODE DETECTION")
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
        
        # Analyze files with functional detection
        all_diagnostics = []
        processed = 0
        
        for file_path in python_files:
            if args.verbose:
                print(f"🔍 Analyzing {os.path.basename(file_path)}...")
            
            try:
                file_diagnostics = analyze_python_file_functional(file_path)
                all_diagnostics.extend(file_diagnostics)
                processed += 1
                
                if args.verbose and len(file_diagnostics) > 0:
                    missing_errors = len([d for d in file_diagnostics if d.category == "missing"])
                    unused_warnings = len([d for d in file_diagnostics if d.category in ["unused", "dead_code"]])
                    if missing_errors > 0:
                        print(f"  🚨 Found {missing_errors} missing/broken references, {len(file_diagnostics)} total issues")
                    elif unused_warnings > 0:
                        print(f"  📋 Found {unused_warnings} unused/dead code issues, {len(file_diagnostics)} total issues")
                    else:
                        print(f"  ✅ Found {len(file_diagnostics)} issues")
                
            except Exception as e:
                if args.verbose:
                    print(f"  ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
        
        print(f"✅ Analyzed {processed}/{len(python_files)} files")
        
        # Format and output results
        result = format_functional_results(all_diagnostics)
        
        print("\n" + "=" * 60)
        print("🔍 FUNCTIONAL ANALYSIS RESULTS")
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
                icon = {
                    "missing": "🚨", 
                    "unused": "📋", 
                    "dead_code": "💀", 
                    "bugs": "🐛",
                    "usage": "⚠️",
                    "imports": "📦"
                }.get(category, "📋")
                print(f"  {icon} {category}: {count}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        print(f"ERRORS: ['0']\nAnalysis failed: {e}")

if __name__ == "__main__":
    main()
