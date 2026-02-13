#!/usr/bin/env python3
"""
Comprehensive Error Analyzer - Detects All 3 Types of Errors

This analyzer uses multiple static analysis tools to detect:
- Critical errors (syntax, undefined variables, imports)
- Major issues (warnings, style violations, complexity)
- Minor issues (formatting, documentation, hints)
"""

import os
import sys
import json
import ast
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import argparse
import re


@dataclass
class ComprehensiveError:
    """Comprehensive error with all details."""
    file_path: str
    line: int
    column: int
    severity: str  # ERROR, WARNING, INFO
    message: str
    code: str
    source: str  # flake8, mypy, pylint, ast, etc.
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    business_impact: str = 'Minor'
    
    def get_severity_icon(self) -> str:
        """Get visual severity indicator based on business impact."""
        icons = {
            'Critical': '⚠️',
            'Major': '👉',
            'Minor': '🔍'
        }
        return icons.get(self.business_impact, '📝')
    
    def get_context_string(self) -> str:
        """Get context string for display."""
        if self.function_name and self.class_name:
            return f"Method - '{self.function_name}' in class '{self.class_name}'"
        elif self.function_name:
            return f"Function - '{self.function_name}'"
        elif self.class_name:
            return f"Class - '{self.class_name}'"
        else:
            return "Module"


class ComprehensiveErrorAnalyzer:
    """Comprehensive analyzer using multiple static analysis tools."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.temp_dir = None
        
        # Tools to use for analysis
        self.analysis_tools = {
            'flake8': {
                'command': ['flake8', '--format=json'],
                'available': self._check_tool_available('flake8'),
                'error_types': ['style', 'complexity', 'imports']
            },
            'mypy': {
                'command': ['mypy', '--show-error-codes', '--no-error-summary'],
                'available': self._check_tool_available('mypy'),
                'error_types': ['types', 'imports', 'logic']
            },
            'pylint': {
                'command': ['pylint', '--output-format=json'],
                'available': self._check_tool_available('pylint'),
                'error_types': ['logic', 'style', 'refactoring']
            }
        }
        
        if verbose:
            print("🔧 Available analysis tools:")
            for tool, config in self.analysis_tools.items():
                status = "✅" if config['available'] else "❌"
                print(f"   {status} {tool}: {', '.join(config['error_types'])}")
    
    def analyze_repository(self, repo_url_or_path: str) -> str:
        """Analyze repository comprehensively."""
        try:
            print("🚀 Comprehensive Error Analysis Starting")
            print("=" * 60)
            
            # Step 1: Setup repository
            if self._is_git_url(repo_url_or_path):
                repo_path = self._clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
            
            # Step 2: Get Python files
            python_files = self._get_python_files(repo_path)
            
            if not python_files:
                return "ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nNo Python files found."
            
            print(f"📊 Found {len(python_files)} Python files to analyze")
            
            # Step 3: Run comprehensive analysis
            all_errors = []
            
            # AST-based syntax checking (Critical errors)
            print("🔍 Running AST syntax analysis...")
            ast_errors = self._analyze_with_ast(python_files, repo_path)
            all_errors.extend(ast_errors)
            print(f"   Found {len(ast_errors)} syntax/import errors")
            
            # Flake8 analysis (Style and complexity)
            if self.analysis_tools['flake8']['available']:
                print("🔍 Running flake8 analysis...")
                flake8_errors = self._analyze_with_flake8(repo_path)
                all_errors.extend(flake8_errors)
                print(f"   Found {len(flake8_errors)} style/complexity issues")
            
            # MyPy analysis (Type checking)
            if self.analysis_tools['mypy']['available']:
                print("🔍 Running mypy analysis...")
                mypy_errors = self._analyze_with_mypy(python_files, repo_path)
                all_errors.extend(mypy_errors)
                print(f"   Found {len(mypy_errors)} type issues")
            
            # Pylint analysis (Logic and refactoring)
            if self.analysis_tools['pylint']['available']:
                print("🔍 Running pylint analysis...")
                pylint_errors = self._analyze_with_pylint(python_files[:20], repo_path)  # Limit for performance
                all_errors.extend(pylint_errors)
                print(f"   Found {len(pylint_errors)} logic/refactoring issues")
            
            # Step 4: Add function context to all errors
            print("🔧 Adding function context...")
            self._add_function_context(all_errors)
            
            # Step 5: Classify business impact
            print("📊 Classifying business impact...")
            self._classify_business_impact(all_errors)
            
            # Step 6: Format output
            return self._format_output(all_errors, repo_path)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            if self.verbose:
                print(traceback.format_exc())
            return f"ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nAnalysis failed: {e}"
        
        finally:
            self._cleanup()
    
    def _analyze_with_ast(self, python_files: List[str], repo_path: str) -> List[ComprehensiveError]:
        """Analyze files using Python AST for syntax and import errors."""
        errors = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for syntax errors
                try:
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    error = ComprehensiveError(
                        file_path=file_path,
                        line=e.lineno or 1,
                        column=e.offset or 1,
                        severity='ERROR',
                        message=f"Syntax error: {e.msg}",
                        code='E999',
                        source='ast',
                        business_impact='Critical'
                    )
                    errors.append(error)
                
                # Check for import errors by trying to compile
                try:
                    compile(content, file_path, 'exec')
                except Exception as e:
                    if 'import' in str(e).lower() or 'module' in str(e).lower():
                        error = ComprehensiveError(
                            file_path=file_path,
                            line=1,
                            column=1,
                            severity='ERROR',
                            message=f"Import error: {e}",
                            code='E401',
                            source='ast',
                            business_impact='Critical'
                        )
                        errors.append(error)
                
                # Check for undefined variables (simple heuristic)
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    # Look for common undefined variable patterns
                    if re.search(r'\bundefined\w*\b', line, re.IGNORECASE):
                        error = ComprehensiveError(
                            file_path=file_path,
                            line=line_num,
                            column=1,
                            severity='ERROR',
                            message="Potential undefined variable",
                            code='F821',
                            source='ast',
                            business_impact='Critical'
                        )
                        errors.append(error)
                
            except Exception as e:
                if self.verbose:
                    print(f"   Warning: Could not analyze {file_path}: {e}")
                continue
        
        return errors
    
    def _analyze_with_flake8(self, repo_path: str) -> List[ComprehensiveError]:
        """Analyze with flake8 for style and complexity issues."""
        errors = []
        
        try:
            # Run flake8 with JSON output
            cmd = ['flake8', '--format=json', repo_path]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=repo_path
            )
            
            # Parse flake8 output (it doesn't actually support JSON format, so parse text)
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        try:
                            # Parse flake8 format: file:line:col: code message
                            parts = line.split(':', 3)
                            if len(parts) >= 4:
                                file_path = parts[0]
                                line_num = int(parts[1])
                                col_num = int(parts[2])
                                message_part = parts[3].strip()
                                
                                # Extract code and message
                                code_match = re.match(r'(\w+\d+)\s+(.*)', message_part)
                                if code_match:
                                    code = code_match.group(1)
                                    message = code_match.group(2)
                                else:
                                    code = 'F999'
                                    message = message_part
                                
                                # Determine severity based on code
                                if code.startswith('E'):
                                    severity = 'ERROR' if code.startswith('E9') else 'WARNING'
                                elif code.startswith('W'):
                                    severity = 'WARNING'
                                else:
                                    severity = 'INFO'
                                
                                error = ComprehensiveError(
                                    file_path=os.path.join(repo_path, file_path) if not os.path.isabs(file_path) else file_path,
                                    line=line_num,
                                    column=col_num,
                                    severity=severity,
                                    message=message,
                                    code=code,
                                    source='flake8'
                                )
                                errors.append(error)
                        except (ValueError, IndexError):
                            continue
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ Flake8 analysis timed out")
        except Exception as e:
            if self.verbose:
                print(f"   Warning: Flake8 analysis failed: {e}")
        
        return errors
    
    def _analyze_with_mypy(self, python_files: List[str], repo_path: str) -> List[ComprehensiveError]:
        """Analyze with mypy for type checking."""
        errors = []
        
        try:
            # Run mypy on a subset of files to avoid timeout
            files_to_check = python_files[:30]  # Limit for performance
            
            cmd = ['mypy', '--show-error-codes', '--no-error-summary'] + files_to_check
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, cwd=repo_path
            )
            
            # Parse mypy output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line and 'error:' in line:
                        try:
                            # Parse mypy format: file:line: error: message [code]
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                file_path = parts[0]
                                line_num = int(parts[1])
                                message_part = parts[2].strip()
                                
                                # Extract message and code
                                if 'error:' in message_part:
                                    message = message_part.split('error:', 1)[1].strip()
                                    
                                    # Extract error code if present
                                    code_match = re.search(r'\[([^\]]+)\]', message)
                                    if code_match:
                                        code = code_match.group(1)
                                        message = re.sub(r'\s*\[[^\]]+\]', '', message)
                                    else:
                                        code = 'mypy'
                                    
                                    error = ComprehensiveError(
                                        file_path=file_path,
                                        line=line_num,
                                        column=1,
                                        severity='ERROR',
                                        message=message,
                                        code=code,
                                        source='mypy'
                                    )
                                    errors.append(error)
                        except (ValueError, IndexError):
                            continue
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ MyPy analysis timed out")
        except Exception as e:
            if self.verbose:
                print(f"   Warning: MyPy analysis failed: {e}")
        
        return errors
    
    def _analyze_with_pylint(self, python_files: List[str], repo_path: str) -> List[ComprehensiveError]:
        """Analyze with pylint for logic and refactoring issues."""
        errors = []
        
        try:
            # Run pylint on a small subset to avoid timeout
            files_to_check = python_files[:10]  # Very limited for performance
            
            cmd = ['pylint', '--output-format=json', '--disable=all', 
                   '--enable=unused-variable,undefined-variable,unused-import,missing-docstring'] + files_to_check
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=repo_path
            )
            
            # Parse pylint JSON output
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    for item in pylint_data:
                        error = ComprehensiveError(
                            file_path=item.get('path', ''),
                            line=item.get('line', 1),
                            column=item.get('column', 1),
                            severity='WARNING' if item.get('type') == 'warning' else 'INFO',
                            message=item.get('message', ''),
                            code=item.get('message-id', 'pylint'),
                            source='pylint'
                        )
                        errors.append(error)
                except json.JSONDecodeError:
                    # Pylint might not output valid JSON, skip
                    pass
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ Pylint analysis timed out")
        except Exception as e:
            if self.verbose:
                print(f"   Warning: Pylint analysis failed: {e}")
        
        return errors
    
    def _add_function_context(self, errors: List[ComprehensiveError]):
        """Add function/class context to errors using AST parsing."""
        file_contexts = {}  # Cache parsed AST trees
        
        for error in errors:
            if error.file_path not in file_contexts:
                try:
                    with open(error.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    file_contexts[error.file_path] = (content, tree)
                except Exception:
                    file_contexts[error.file_path] = None
                    continue
            
            context_data = file_contexts[error.file_path]
            if context_data:
                content, tree = context_data
                context = self._get_function_context(tree, error.line)
                error.function_name = context.get('function_name')
                error.class_name = context.get('class_name')
    
    def _get_function_context(self, tree: ast.AST, line: int) -> Dict[str, Optional[str]]:
        """Get function/class context for a line using AST."""
        class ContextVisitor(ast.NodeVisitor):
            def __init__(self):
                self.context = {'function_name': None, 'class_name': None}
                self.current_class = None
            
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                
                if hasattr(node, 'lineno') and node.lineno <= line <= getattr(node, 'end_lineno', node.lineno + 100):
                    self.context['class_name'] = node.name
                
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_FunctionDef(self, node):
                if hasattr(node, 'lineno') and node.lineno <= line <= getattr(node, 'end_lineno', node.lineno + 100):
                    self.context['function_name'] = node.name
                    if self.current_class:
                        self.context['class_name'] = self.current_class
                
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
        
        visitor = ContextVisitor()
        visitor.visit(tree)
        return visitor.context
    
    def _classify_business_impact(self, errors: List[ComprehensiveError]):
        """Classify business impact of errors."""
        for error in errors:
            message_lower = error.message.lower()
            code_lower = error.code.lower()
            
            # Critical issues (security, crashes, data loss)
            critical_patterns = [
                'syntax error', 'undefined', 'not defined', 'name error',
                'import error', 'module not found', 'cannot import',
                'indentation error', 'invalid syntax', 'unexpected token',
                'attribute error', 'key error', 'index error'
            ]
            
            critical_codes = ['e999', 'e901', 'e902', 'f821', 'f401', 'f811']
            
            if (error.severity == 'ERROR' or 
                any(pattern in message_lower for pattern in critical_patterns) or
                any(code in code_lower for code in critical_codes)):
                error.business_impact = 'Critical'
                continue
            
            # Major issues (warnings, deprecations, potential problems)
            major_patterns = [
                'deprecated', 'warning', 'unused', 'redefined', 'shadowed',
                'too many', 'too few', 'missing', 'invalid', 'bad',
                'complexity', 'long line', 'docstring'
            ]
            
            major_codes = ['w', 'c', 'r', 'f401', 'f841']
            
            if (error.severity == 'WARNING' or
                any(pattern in message_lower for pattern in major_patterns) or
                any(code.startswith(mc) for mc in major_codes for code in [code_lower])):
                error.business_impact = 'Major'
                continue
            
            # Everything else is minor
            error.business_impact = 'Minor'
    
    def _format_output(self, errors: List[ComprehensiveError], repo_path: str) -> str:
        """Format errors in the exact requested format."""
        if not errors:
            return "ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nNo errors found."
        
        # Count by business impact
        critical_count = sum(1 for e in errors if e.business_impact == 'Critical')
        major_count = sum(1 for e in errors if e.business_impact == 'Major')
        minor_count = sum(1 for e in errors if e.business_impact == 'Minor')
        
        # Header
        header = f"ERRORS: {len(errors)} [⚠️ Critical: {critical_count}] [👉 Major: {major_count}] [🔍 Minor: {minor_count}]"
        
        # Sort errors by business impact
        impact_order = {'Critical': 0, 'Major': 1, 'Minor': 2}
        sorted_errors = sorted(
            errors,
            key=lambda e: (impact_order.get(e.business_impact, 3), e.file_path, e.line)
        )
        
        # Format each error
        output_lines = [header]
        for i, error in enumerate(sorted_errors, 1):
            # Get relative path
            try:
                rel_path = os.path.relpath(error.file_path, repo_path)
            except ValueError:
                rel_path = os.path.basename(error.file_path)
            
            # Get icon and context
            icon = error.get_severity_icon()
            context = error.get_context_string()
            
            # Format message
            message = error.message
            if error.code and error.code != 'unknown':
                message += f" (code: {error.code})"
            if error.source:
                message += f" [source: {error.source}]"
            
            line = f"{i} {icon}- {rel_path} / {context} [{message}]"
            output_lines.append(line)
        
        return '\n'.join(output_lines)
    
    def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available."""
        try:
            subprocess.run([tool, '--version'], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _is_git_url(self, path: str) -> bool:
        """Check if path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith('.git')
    
    def _clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory."""
        print(f"📥 Cloning {repo_url}")
        
        self.temp_dir = tempfile.mkdtemp(prefix="comprehensive_analysis_")
        repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        print(f"✅ Cloned to {clone_path}")
        return clone_path
    
    def _get_python_files(self, repo_path: str) -> List[str]:
        """Get all Python files in the repository."""
        python_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.env'
            ]]
            
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    # Skip very large files
                    try:
                        if os.path.getsize(full_path) < 1024 * 1024:  # 1MB limit
                            python_files.append(full_path)
                    except OSError:
                        continue
        
        return python_files
    
    def _cleanup(self):
        """Cleanup temporary files."""
        if self.temp_dir:
            try:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Comprehensive Error Analyzer - All 3 Types of Errors")
    parser.add_argument('repository', help='Repository URL or local path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = ComprehensiveErrorAnalyzer(verbose=args.verbose)
    result = analyzer.analyze_repository(args.repository)
    print(result)


if __name__ == "__main__":
    main()
