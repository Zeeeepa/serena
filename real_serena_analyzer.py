#!/usr/bin/env python3
"""
Real Serena Codebase Analyzer

This tool analyzes the actual Serena codebase using Python AST parsing
to find real errors, issues, and provide comprehensive analysis.

Usage:
    python real_serena_analyzer.py [options]

Example:
    python real_serena_analyzer.py --verbose --symbols
"""

import argparse
import ast
import json
import os
import sys
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import re


@dataclass
class ErrorInfo:
    """Real error information found in the codebase."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    error_type: str
    code: Optional[str] = None
    context: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.severity} {self.file_path}:{self.line}:{self.column} - {self.message}"


@dataclass
class SymbolInfo:
    """Symbol information from AST analysis."""
    name: str
    type: str  # function, class, variable, import
    file_path: str
    line: int
    column: int
    scope: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class AnalysisResults:
    """Comprehensive analysis results."""
    total_files: int
    analyzed_files: int
    total_errors: int
    errors_by_type: Dict[str, int]
    errors_by_severity: Dict[str, int]
    errors: List[ErrorInfo]
    symbols: List[SymbolInfo]
    file_stats: Dict[str, Dict[str, Any]]
    performance_stats: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RealSerenaAnalyzer:
    """Analyzes the actual Serena codebase for real errors and issues."""

    def __init__(self, verbose: bool = False, enable_symbols: bool = False):
        self.verbose = verbose
        self.enable_symbols = enable_symbols
        
        # Analysis results
        self.errors: List[ErrorInfo] = []
        self.symbols: List[SymbolInfo] = []
        self.file_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.performance_stats = {
            "file_discovery": 0,
            "ast_parsing": 0,
            "error_analysis": 0,
            "symbol_analysis": 0,
            "total_time": 0
        }
        
        # Error tracking
        self.undefined_names: Set[str] = set()
        self.unused_imports: Dict[str, List[str]] = defaultdict(list)
        self.missing_docstrings: List[Dict[str, Any]] = []
        self.complex_functions: List[Dict[str, Any]] = []

    def find_python_files(self, root_path: str) -> List[str]:
        """Find all Python files in the codebase."""
        start_time = time.time()
        
        python_files = []
        exclude_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            'build', 'dist', '.venv', 'venv', '.tox'
        }
        
        for root, dirs, files in os.walk(root_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        self.performance_stats["file_discovery"] = time.time() - start_time
        
        if self.verbose:
            print(f"📁 Found {len(python_files)} Python files")
        
        return python_files

    def parse_file(self, file_path: str) -> Optional[ast.AST]:
        """Parse a Python file into AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            return tree
            
        except SyntaxError as e:
            self.errors.append(ErrorInfo(
                file_path=file_path,
                line=e.lineno or 1,
                column=e.offset or 1,
                severity="ERROR",
                message=f"Syntax error: {e.msg}",
                error_type="SyntaxError",
                code="E0001"
            ))
            return None
            
        except Exception as e:
            self.errors.append(ErrorInfo(
                file_path=file_path,
                line=1,
                column=1,
                severity="ERROR",
                message=f"Failed to parse file: {e}",
                error_type="ParseError",
                code="E0002"
            ))
            return None

    def analyze_undefined_names(self, tree: ast.AST, file_path: str):
        """Find potentially undefined names."""
        class NameAnalyzer(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.file_path = file_path
                self.defined_names = set()
                self.used_names = set()
                self.imports = set()
                self.scope_stack = []

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    self.defined_names.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    self.used_names.add(node.id)
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports.add(name)
                    self.defined_names.add(name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports.add(name)
                    self.defined_names.add(name)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                self.defined_names.add(node.name)
                # Add parameters to defined names
                for arg in node.args.args:
                    self.defined_names.add(arg.arg)
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                self.defined_names.add(node.name)
                self.generic_visit(node)

        analyzer = NameAnalyzer(self)
        analyzer.visit(tree)
        
        # Find potentially undefined names
        builtin_names = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'max', 'min', 'abs',
            'open', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
            'ImportError', 'RuntimeError', 'NotImplementedError', 'StopIteration',
            'True', 'False', 'None', '__name__', '__file__', '__doc__'
        }
        
        undefined = analyzer.used_names - analyzer.defined_names - builtin_names
        
        for name in undefined:
            # Skip common patterns that are likely defined elsewhere
            if not (name.startswith('_') or name.isupper() or '.' in name):
                self.errors.append(ErrorInfo(
                    file_path=file_path,
                    line=1,  # Would need more complex analysis to get exact line
                    column=1,
                    severity="WARNING",
                    message=f"Potentially undefined name: '{name}'",
                    error_type="UndefinedName",
                    code="W0001"
                ))

    def analyze_imports(self, tree: ast.AST, file_path: str):
        """Analyze import usage."""
        class ImportAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.imports = {}  # name -> line
                self.used_names = set()

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    self.imports[name] = node.lineno

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports[name] = node.lineno

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.used_names.add(node.id)

            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name):
                    self.used_names.add(node.value.id)
                self.generic_visit(node)

        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        # Find unused imports
        for import_name, line in analyzer.imports.items():
            if import_name not in analyzer.used_names:
                self.errors.append(ErrorInfo(
                    file_path=file_path,
                    line=line,
                    column=1,
                    severity="INFO",
                    message=f"Unused import: '{import_name}'",
                    error_type="UnusedImport",
                    code="I0001"
                ))

    def analyze_functions(self, tree: ast.AST, file_path: str):
        """Analyze function definitions."""
        class FunctionAnalyzer(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.file_path = file_path

            def visit_FunctionDef(self, node):
                # Check for missing docstring
                if not ast.get_docstring(node):
                    if not node.name.startswith('_'):  # Skip private functions
                        self.analyzer.errors.append(ErrorInfo(
                            file_path=self.file_path,
                            line=node.lineno,
                            column=node.col_offset,
                            severity="INFO",
                            message=f"Function '{node.name}' missing docstring",
                            error_type="MissingDocstring",
                            code="I0002"
                        ))

                # Check function complexity (simple cyclomatic complexity)
                complexity = self.calculate_complexity(node)
                if complexity > 10:
                    self.analyzer.errors.append(ErrorInfo(
                        file_path=self.file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        severity="WARNING",
                        message=f"Function '{node.name}' is too complex (complexity: {complexity})",
                        error_type="ComplexFunction",
                        code="W0002"
                    ))

                # Check for too many parameters
                total_args = len(node.args.args) + len(node.args.kwonlyargs)
                if total_args > 7:
                    self.analyzer.errors.append(ErrorInfo(
                        file_path=self.file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        severity="WARNING",
                        message=f"Function '{node.name}' has too many parameters ({total_args})",
                        error_type="TooManyParameters",
                        code="W0003"
                    ))

                self.generic_visit(node)

            def calculate_complexity(self, node):
                """Calculate cyclomatic complexity."""
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                        complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                return complexity

        analyzer = FunctionAnalyzer(self)
        analyzer.visit(tree)

    def collect_symbols(self, tree: ast.AST, file_path: str):
        """Collect symbol information."""
        if not self.enable_symbols:
            return

        class SymbolCollector(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.file_path = file_path

            def visit_FunctionDef(self, node):
                docstring = ast.get_docstring(node)
                self.analyzer.symbols.append(SymbolInfo(
                    name=node.name,
                    type="function",
                    file_path=self.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    docstring=docstring
                ))
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                docstring = ast.get_docstring(node)
                self.analyzer.symbols.append(SymbolInfo(
                    name=node.name,
                    type="class",
                    file_path=self.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    docstring=docstring
                ))
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.analyzer.symbols.append(SymbolInfo(
                        name=name,
                        type="import",
                        file_path=self.file_path,
                        line=node.lineno,
                        column=node.col_offset
                    ))

        collector = SymbolCollector(self)
        collector.visit(tree)

    def analyze_file(self, file_path: str):
        """Analyze a single Python file."""
        if self.verbose:
            print(f"🔍 Analyzing {os.path.relpath(file_path)}")

        # Parse the file
        tree = self.parse_file(file_path)
        if not tree:
            return

        # Collect file statistics
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            self.file_stats[file_path] = {
                'lines': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
                'size_bytes': len(content.encode('utf-8'))
            }
        except Exception:
            pass

        # Run various analyses
        self.analyze_undefined_names(tree, file_path)
        self.analyze_imports(tree, file_path)
        self.analyze_functions(tree, file_path)
        self.collect_symbols(tree, file_path)

    def analyze_codebase(self, root_path: str = ".") -> AnalysisResults:
        """Analyze the entire codebase."""
        start_time = time.time()
        
        print("🚀 REAL SERENA CODEBASE ANALYSIS")
        print("=" * 60)
        print(f"📁 Analyzing: {os.path.abspath(root_path)}")
        print(f"🔍 Symbol analysis: {'ENABLED' if self.enable_symbols else 'DISABLED'}")
        print("=" * 60)

        # Find all Python files
        python_files = self.find_python_files(root_path)
        
        if not python_files:
            print("❌ No Python files found!")
            return AnalysisResults(
                total_files=0, analyzed_files=0, total_errors=0,
                errors_by_type={}, errors_by_severity={},
                errors=[], symbols=[], file_stats={},
                performance_stats=self.performance_stats
            )

        # Analyze each file
        ast_start = time.time()
        analyzed_files = 0
        
        for file_path in python_files:
            try:
                self.analyze_file(file_path)
                analyzed_files += 1
            except Exception as e:
                if self.verbose:
                    print(f"❌ Error analyzing {file_path}: {e}")
                self.errors.append(ErrorInfo(
                    file_path=file_path,
                    line=1,
                    column=1,
                    severity="ERROR",
                    message=f"Analysis failed: {e}",
                    error_type="AnalysisError",
                    code="E0003"
                ))

        self.performance_stats["ast_parsing"] = time.time() - ast_start

        # Calculate statistics
        errors_by_type = Counter(error.error_type for error in self.errors)
        errors_by_severity = Counter(error.severity for error in self.errors)

        total_time = time.time() - start_time
        self.performance_stats["total_time"] = total_time

        # Print summary
        print("\n🎉 Analysis Complete!")
        print("=" * 60)
        print(f"📊 Files analyzed: {analyzed_files}/{len(python_files)}")
        print(f"🔍 Total errors found: {len(self.errors)}")
        print(f"⚠️  Errors: {errors_by_severity.get('ERROR', 0)}")
        print(f"👉 Warnings: {errors_by_severity.get('WARNING', 0)}")
        print(f"ℹ️  Info: {errors_by_severity.get('INFO', 0)}")
        if self.enable_symbols:
            print(f"📚 Symbols found: {len(self.symbols)}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print("=" * 60)

        return AnalysisResults(
            total_files=len(python_files),
            analyzed_files=analyzed_files,
            total_errors=len(self.errors),
            errors_by_type=dict(errors_by_type),
            errors_by_severity=dict(errors_by_severity),
            errors=self.errors,
            symbols=self.symbols,
            file_stats=self.file_stats,
            performance_stats=self.performance_stats
        )

    def format_output(self, results: AnalysisResults) -> str:
        """Format analysis results for display."""
        if not results.errors:
            return "ERRORS: 0\nNo errors found in the codebase! 🎉"

        # Sort errors by severity and file
        severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2}
        sorted_errors = sorted(results.errors, key=lambda e: (
            severity_priority.get(e.severity, 3),
            e.file_path,
            e.line
        ))

        error_count = len(sorted_errors)
        critical_count = results.errors_by_severity.get('ERROR', 0)
        warning_count = results.errors_by_severity.get('WARNING', 0)
        info_count = results.errors_by_severity.get('INFO', 0)

        output_lines = [
            f"ERRORS: {error_count} [⚠️ Critical: {critical_count}] [👉 Warnings: {warning_count}] [ℹ️ Info: {info_count}]"
        ]

        for i, error in enumerate(sorted_errors, 1):
            severity_icon = "⚠️" if error.severity == "ERROR" else "👉" if error.severity == "WARNING" else "ℹ️"
            
            # Shorten file path
            short_path = os.path.relpath(error.file_path)
            if len(short_path) > 50:
                short_path = "..." + short_path[-47:]

            # Clean message
            clean_message = error.message.replace("\n", " ").strip()
            if len(clean_message) > 100:
                clean_message = clean_message[:97] + "..."

            # Format line
            line = f"{i} {severity_icon}- {short_path} / line {error.line}, col {error.column} - '{clean_message}' [type: {error.error_type}]"
            output_lines.append(line)

        return "\n".join(output_lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Real Serena Codebase Analyzer"
    )
    
    parser.add_argument("--path", default=".", help="Path to analyze (default: current directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--symbols", action="store_true", help="Enable symbol collection")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()

    try:
        analyzer = RealSerenaAnalyzer(
            verbose=args.verbose,
            enable_symbols=args.symbols
        )
        
        results = analyzer.analyze_codebase(args.path)
        
        if args.json:
            output = json.dumps(results.to_dict(), indent=2, default=str)
        else:
            output = analyzer.format_output(results)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"📄 Results written to {args.output}")
        else:
            print("\n" + "=" * 60)
            print("📋 ANALYSIS RESULTS")
            print("=" * 60)
            print(output)
            print("=" * 60)

    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

