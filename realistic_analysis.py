#!/usr/bin/env python3
"""
Realistic LSP Error Analysis for graph-sitter repository

This script performs actual static analysis on the graph-sitter repository
to demonstrate what the serena_analysis.py tool would find.
"""

import ast
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def analyze_python_file(file_path: Path) -> List[Dict]:
    """Analyze a Python file for common issues that LSP would catch."""
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check syntax
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            errors.append({
                'location': f'line {e.lineno}, col {e.offset or 0}',
                'file': file_path.name,
                'error_reason': f'Syntax error: {e.msg}',
                'other_types': 'severity: ERROR, code: syntax-error, source: python'
            })
            return errors
        
        # Analyze the AST for common issues
        analyzer = PythonAnalyzer()
        analyzer.visit(tree)
        
        # Convert findings to error format
        for issue in analyzer.issues:
            errors.append({
                'location': f'line {issue["line"]}, col {issue["col"]}',
                'file': file_path.name,
                'error_reason': issue['message'],
                'other_types': f'severity: {issue["severity"]}, code: {issue["code"]}, source: static-analysis'
            })
            
    except Exception as e:
        errors.append({
            'location': 'line 1, col 1',
            'file': file_path.name,
            'error_reason': f'File analysis failed: {str(e)}',
            'other_types': 'severity: ERROR, code: analysis-error, source: static-analysis'
        })
    
    return errors

class PythonAnalyzer(ast.NodeVisitor):
    """AST visitor to find common Python issues."""
    
    def __init__(self):
        self.issues = []
        self.imports = set()
        self.defined_names = set()
        self.used_names = set()
        self.functions = {}
        self.classes = {}
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        self.defined_names.add(node.name)
        self.functions[node.name] = {
            'line': node.lineno,
            'col': node.col_offset,
            'args': [arg.arg for arg in node.args.args],
            'has_return': False
        }
        
        # Check for missing return statements in non-void functions
        has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
        if not has_return and node.name != '__init__' and not node.name.startswith('_'):
            # This might be a function that should return something
            if len(node.body) > 1:  # Non-trivial function
                self.issues.append({
                    'line': node.lineno,
                    'col': node.col_offset,
                    'message': f'Function "{node.name}" may be missing a return statement',
                    'severity': 'WARNING',
                    'code': 'missing-return'
                })
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.defined_names.add(node.name)
        self.classes[node.name] = {
            'line': node.lineno,
            'col': node.col_offset
        }
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        # Check for unused variables (simple heuristic)
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name.startswith('_'):
                    continue  # Skip private variables
                # This is a simplified check - real LSP would be more sophisticated
                
        self.generic_visit(node)

def analyze_repository(repo_path: str) -> List[Dict]:
    """Analyze all Python files in the repository."""
    print(f"🔍 Analyzing Python files in: {repo_path}")
    
    all_errors = []
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                python_files.append(file_path)
    
    print(f"📊 Found {len(python_files)} Python files to analyze")
    
    # Analyze each file
    analyzed_count = 0
    for file_path in python_files[:20]:  # Limit to first 20 files for demo
        try:
            errors = analyze_python_file(file_path)
            all_errors.extend(errors)
            analyzed_count += 1
            
            if errors:
                print(f"⚠️  Found {len(errors)} issues in {file_path.name}")
        except Exception as e:
            print(f"❌ Failed to analyze {file_path}: {e}")
    
    print(f"✅ Analyzed {analyzed_count} files, found {len(all_errors)} total issues")
    return all_errors

def check_with_flake8(repo_path: str) -> List[Dict]:
    """Use flake8 to find real linting issues."""
    print("🔧 Running flake8 analysis...")
    
    try:
        # Run flake8 on Python files
        result = subprocess.run([
            'python', '-m', 'flake8', 
            '--select=E,W,F',  # Select error, warning, and pyflakes codes
            '--max-line-length=100',
            '--exclude=.git,__pycache__,.venv,venv,node_modules',
            repo_path
        ], capture_output=True, text=True, timeout=60)
        
        errors = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_num = parts[1]
                        col_num = parts[2]
                        message = parts[3].strip()
                        
                        # Parse flake8 code
                        code = message.split()[0] if message else 'unknown'
                        severity = 'ERROR' if code.startswith('E') or code.startswith('F') else 'WARNING'
                        
                        errors.append({
                            'location': f'line {line_num}, col {col_num}',
                            'file': os.path.basename(file_path),
                            'error_reason': message,
                            'other_types': f'severity: {severity}, code: {code}, source: flake8'
                        })
        
        print(f"✅ Flake8 found {len(errors)} issues")
        return errors
        
    except subprocess.TimeoutExpired:
        print("⚠️  Flake8 analysis timed out")
        return []
    except FileNotFoundError:
        print("⚠️  Flake8 not available, skipping")
        return []
    except Exception as e:
        print(f"⚠️  Flake8 analysis failed: {e}")
        return []

def format_output(errors: List[Dict]) -> str:
    """Format errors in the requested output format."""
    if not errors:
        return "ERRORS: ['0']\nNo errors found."
    
    error_count = len(errors)
    output_lines = [f"ERRORS: ['{error_count}']"]
    
    for i, error in enumerate(errors, 1):
        line = f"{i}. '{error['location']}' '{error['file']}' '{error['error_reason']}' '{error['other_types']}'"
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def main():
    """Main analysis function."""
    repo_path = "/tmp/graph-sitter-analysis"
    
    print("🚀 Realistic LSP Error Analysis for graph-sitter")
    print("=" * 60)
    print(f"📁 Repository: {repo_path}")
    print("=" * 60)
    
    if not os.path.exists(repo_path):
        print(f"❌ Repository not found at {repo_path}")
        print("Please run the demo_analysis.py first to clone the repository")
        return 1
    
    try:
        # Perform static analysis
        static_errors = analyze_repository(repo_path)
        
        # Try to get real linting errors with flake8
        flake8_errors = check_with_flake8(repo_path)
        
        # Combine all errors
        all_errors = static_errors + flake8_errors
        
        # Remove duplicates (simple deduplication)
        seen = set()
        unique_errors = []
        for error in all_errors:
            key = (error['location'], error['file'], error['error_reason'])
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        # Limit to first 50 errors for readability
        if len(unique_errors) > 50:
            unique_errors = unique_errors[:50]
            print(f"📋 Showing first 50 of {len(all_errors)} total errors found")
        
        # Format and display results
        print(f"\n📋 Final Analysis Results:")
        print("=" * 60)
        result = format_output(unique_errors)
        print(result)
        
        print("\n" + "=" * 60)
        print("✅ Realistic analysis completed!")
        print(f"📊 Summary:")
        print(f"   • Static analysis errors: {len(static_errors)}")
        print(f"   • Flake8 linting errors: {len(flake8_errors)}")
        print(f"   • Total unique errors: {len(unique_errors)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

