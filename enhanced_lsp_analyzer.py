#!/usr/bin/env python3
"""
Enhanced LSP Analyzer - Real LSP Integration for All Error Types

This enhanced analyzer properly integrates with real LSP servers to detect
all types of errors: Critical (syntax/type errors), Major (warnings), 
and Minor (style/info) issues from actual language servers.
"""

import os
import sys
import json
import time
import logging
import tempfile
import subprocess
import threading
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import argparse

# Try to import LSP client libraries
try:
    import pylsp
    from pylsp.config.config import config
    PYLSP_AVAILABLE = True
except ImportError:
    PYLSP_AVAILABLE = False

try:
    from pygls.server import LanguageServer
    from pygls.lsp.types import (
        TextDocumentItem, DidOpenTextDocumentParams,
        TextDocumentIdentifier, DocumentDiagnosticParams
    )
    PYGLS_AVAILABLE = True
except ImportError:
    PYGLS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class RealLSPDiagnostic:
    """Real LSP diagnostic from language server."""
    file_path: str
    line: int
    column: int
    severity: str  # ERROR, WARNING, INFO, HINT
    message: str
    code: Optional[str]
    source: str  # pylsp, mypy, flake8, etc.
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    business_impact: str = 'Minor'
    
    def get_severity_icon(self) -> str:
        """Get visual severity indicator."""
        icons = {
            'ERROR': '⚠️',
            'WARNING': '👉', 
            'INFO': '🔍',
            'HINT': '💡'
        }
        return icons.get(self.severity, '📝')
    
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


class RealLSPClient:
    """Real LSP client that communicates with actual language servers."""
    
    def __init__(self, server_command: List[str], cwd: str):
        self.server_command = server_command
        self.cwd = cwd
        self.process = None
        self.server_id = 0
        self.logger = logging.getLogger(f"LSPClient-{server_command[0]}")
        
    def start(self) -> bool:
        """Start the LSP server process."""
        try:
            self.logger.info(f"Starting LSP server: {' '.join(self.server_command)}")
            
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
                text=True,
                bufsize=0
            )
            
            # Send initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": f"file://{self.cwd}",
                    "capabilities": {
                        "textDocument": {
                            "diagnostic": {"dynamicRegistration": True},
                            "publishDiagnostics": {"relatedInformation": True}
                        }
                    }
                }
            }
            
            self._send_request(initialize_request)
            response = self._read_response()
            
            if response and "result" in response:
                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {}
                }
                self._send_request(initialized_notification)
                self.logger.info("LSP server initialized successfully")
                return True
            else:
                self.logger.error(f"Failed to initialize LSP server: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start LSP server: {e}")
            return False
    
    def get_diagnostics(self, file_path: str, content: str) -> List[RealLSPDiagnostic]:
        """Get diagnostics for a file from the LSP server."""
        if not self.process:
            return []
        
        try:
            file_uri = f"file://{os.path.abspath(file_path)}"
            
            # Send textDocument/didOpen
            did_open_params = {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": file_uri,
                        "languageId": self._get_language_id(file_path),
                        "version": 1,
                        "text": content
                    }
                }
            }
            
            self._send_request(did_open_params)
            
            # Wait a bit for diagnostics to be computed
            time.sleep(0.5)
            
            # Request diagnostics
            diagnostic_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "textDocument/diagnostic",
                "params": {
                    "textDocument": {"uri": file_uri}
                }
            }
            
            self._send_request(diagnostic_request)
            response = self._read_response()
            
            diagnostics = []
            if response and "result" in response:
                items = response["result"].get("items", [])
                for item in items:
                    diag = self._parse_diagnostic(file_path, item)
                    if diag:
                        diagnostics.append(diag)
            
            # Also check for publishDiagnostics notifications
            for _ in range(5):  # Check for up to 5 notifications
                notification = self._read_response(timeout=0.1)
                if notification and notification.get("method") == "textDocument/publishDiagnostics":
                    params = notification.get("params", {})
                    if params.get("uri") == file_uri:
                        for item in params.get("diagnostics", []):
                            diag = self._parse_diagnostic(file_path, item)
                            if diag:
                                diagnostics.append(diag)
            
            return diagnostics
            
        except Exception as e:
            self.logger.error(f"Failed to get diagnostics for {file_path}: {e}")
            return []
    
    def _parse_diagnostic(self, file_path: str, item: Dict) -> Optional[RealLSPDiagnostic]:
        """Parse LSP diagnostic item."""
        try:
            range_info = item.get("range", {})
            start_pos = range_info.get("start", {})
            
            # Map LSP severity to our severity
            lsp_severity = item.get("severity", 3)
            severity_map = {1: "ERROR", 2: "WARNING", 3: "INFO", 4: "HINT"}
            severity = severity_map.get(lsp_severity, "INFO")
            
            # Classify business impact based on severity and source
            source = item.get("source", "lsp")
            business_impact = self._classify_business_impact(severity, source, item.get("message", ""))
            
            return RealLSPDiagnostic(
                file_path=file_path,
                line=start_pos.get("line", 0) + 1,  # Convert to 1-based
                column=start_pos.get("character", 0) + 1,
                severity=severity,
                message=item.get("message", "No message"),
                code=str(item.get("code", "")),
                source=source,
                business_impact=business_impact
            )
        except Exception as e:
            self.logger.error(f"Failed to parse diagnostic: {e}")
            return None
    
    def _classify_business_impact(self, severity: str, source: str, message: str) -> str:
        """Classify business impact based on severity, source, and message."""
        message_lower = message.lower()
        
        # Critical issues (security, crashes, data loss)
        critical_patterns = [
            'syntax error', 'undefined', 'not defined', 'name error',
            'import error', 'module not found', 'cannot import',
            'indentation error', 'invalid syntax', 'unexpected token',
            'type error', 'attribute error', 'key error', 'index error'
        ]
        
        if severity == "ERROR" or any(pattern in message_lower for pattern in critical_patterns):
            return "Critical"
        
        # Major issues (warnings, deprecations, potential problems)
        major_patterns = [
            'deprecated', 'warning', 'unused', 'redefined', 'shadowed',
            'too many', 'too few', 'missing', 'invalid', 'bad'
        ]
        
        if severity == "WARNING" or any(pattern in message_lower for pattern in major_patterns):
            return "Major"
        
        # Everything else is minor
        return "Minor"
    
    def _get_language_id(self, file_path: str) -> str:
        """Get language ID for file."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.php': 'php',
            '.rb': 'ruby'
        }
        return language_map.get(ext, 'text')
    
    def _next_id(self) -> int:
        """Get next request ID."""
        self.server_id += 1
        return self.server_id
    
    def _send_request(self, request: Dict):
        """Send JSON-RPC request to server."""
        if not self.process or not self.process.stdin:
            return
        
        content = json.dumps(request)
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        
        self.process.stdin.write(message)
        self.process.stdin.flush()
    
    def _read_response(self, timeout: float = 2.0) -> Optional[Dict]:
        """Read JSON-RPC response from server."""
        if not self.process or not self.process.stdout:
            return None
        
        try:
            # Read headers
            headers = {}
            while True:
                line = self.process.stdout.readline()
                if not line or line.strip() == "":
                    break
                
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            
            # Read content
            content_length = int(headers.get("Content-Length", 0))
            if content_length > 0:
                content = self.process.stdout.read(content_length)
                return json.loads(content)
            
        except Exception as e:
            self.logger.debug(f"Failed to read response: {e}")
        
        return None
    
    def shutdown(self):
        """Shutdown the LSP server."""
        if self.process:
            try:
                # Send shutdown request
                shutdown_request = {
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "shutdown",
                    "params": {}
                }
                self._send_request(shutdown_request)
                
                # Send exit notification
                exit_notification = {
                    "jsonrpc": "2.0",
                    "method": "exit",
                    "params": {}
                }
                self._send_request(exit_notification)
                
                # Wait for process to terminate
                self.process.wait(timeout=5)
                
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")
            finally:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                    if self.process.poll() is None:
                        self.process.kill()


class EnhancedLSPAnalyzer:
    """Enhanced analyzer with real LSP integration."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger("EnhancedLSPAnalyzer")
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        self.temp_dir = None
        self.lsp_clients = {}
        
        # Language server configurations
        self.server_configs = {
            'python': {
                'command': ['pylsp'],
                'extensions': ['.py'],
                'fallback_commands': [
                    ['python', '-m', 'pylsp'],
                    ['python3', '-m', 'pylsp']
                ]
            },
            'javascript': {
                'command': ['typescript-language-server', '--stdio'],
                'extensions': ['.js', '.jsx'],
                'fallback_commands': [
                    ['node', 'typescript-language-server', '--stdio']
                ]
            },
            'typescript': {
                'command': ['typescript-language-server', '--stdio'],
                'extensions': ['.ts', '.tsx'],
                'fallback_commands': [
                    ['node', 'typescript-language-server', '--stdio']
                ]
            }
        }
    
    def analyze_repository(self, repo_url_or_path: str) -> str:
        """Analyze repository with real LSP integration."""
        try:
            self.logger.info("🚀 Enhanced LSP Analysis Starting")
            self.logger.info("=" * 60)
            
            # Step 1: Setup repository
            if self._is_git_url(repo_url_or_path):
                repo_path = self._clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
            
            # Step 2: Detect language and get files
            language = self._detect_language(repo_path)
            source_files = self._get_source_files(repo_path, language)
            
            if not source_files:
                return "ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nNo source files found."
            
            self.logger.info(f"📊 Found {len(source_files)} {language} files to analyze")
            
            # Step 3: Start LSP server
            lsp_client = self._start_lsp_server(language, repo_path)
            if not lsp_client:
                self.logger.warning("⚠️ LSP server not available, using fallback analysis")
                return self._fallback_analysis(source_files, language, repo_path)
            
            # Step 4: Collect real LSP diagnostics
            all_diagnostics = []
            
            self.logger.info("🔍 Collecting real LSP diagnostics...")
            for i, file_path in enumerate(source_files[:100]):  # Limit for demo
                if i % 20 == 0:
                    self.logger.info(f"   Progress: {i}/{len(source_files[:100])} files...")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    diagnostics = lsp_client.get_diagnostics(file_path, content)
                    
                    # Add function context
                    for diag in diagnostics:
                        context = self._get_function_context(file_path, diag.line, content)
                        diag.function_name = context.get('function_name')
                        diag.class_name = context.get('class_name')
                    
                    all_diagnostics.extend(diagnostics)
                    
                    if self.verbose and diagnostics:
                        self.logger.debug(f"✅ Found {len(diagnostics)} diagnostics in {os.path.basename(file_path)}")
                
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")
                    continue
            
            # Step 5: Format output
            return self._format_output(all_diagnostics, repo_path)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            if self.verbose:
                self.logger.error(traceback.format_exc())
            return f"ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nAnalysis failed: {e}"
        
        finally:
            self._cleanup()
    
    def _start_lsp_server(self, language: str, cwd: str) -> Optional[RealLSPClient]:
        """Start appropriate LSP server for language."""
        config = self.server_configs.get(language)
        if not config:
            return None
        
        # Try main command first
        commands_to_try = [config['command']] + config.get('fallback_commands', [])
        
        for command in commands_to_try:
            try:
                client = RealLSPClient(command, cwd)
                if client.start():
                    self.logger.info(f"✅ Started {language} LSP server: {' '.join(command)}")
                    return client
                else:
                    client.shutdown()
            except Exception as e:
                self.logger.debug(f"Failed to start {' '.join(command)}: {e}")
                continue
        
        self.logger.warning(f"⚠️ Could not start any LSP server for {language}")
        return None
    
    def _get_function_context(self, file_path: str, line: int, content: str) -> Dict[str, Optional[str]]:
        """Get function/class context for a line using AST parsing."""
        if not file_path.endswith('.py'):
            return {'function_name': None, 'class_name': None}
        
        try:
            import ast
            
            tree = ast.parse(content)
            
            class ContextVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.context = {'function_name': None, 'class_name': None}
                    self.current_class = None
                
                def visit_ClassDef(self, node):
                    old_class = self.current_class
                    self.current_class = node.name
                    
                    if hasattr(node, 'lineno') and node.lineno <= line <= getattr(node, 'end_lineno', node.lineno):
                        self.context['class_name'] = node.name
                    
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    if hasattr(node, 'lineno') and node.lineno <= line <= getattr(node, 'end_lineno', node.lineno):
                        self.context['function_name'] = node.name
                        if self.current_class:
                            self.context['class_name'] = self.current_class
                    
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    self.visit_FunctionDef(node)
            
            visitor = ContextVisitor()
            visitor.visit(tree)
            return visitor.context
            
        except Exception as e:
            self.logger.debug(f"Failed to get context for {file_path}:{line}: {e}")
            return {'function_name': None, 'class_name': None}
    
    def _format_output(self, diagnostics: List[RealLSPDiagnostic], repo_path: str) -> str:
        """Format diagnostics in the exact requested format."""
        if not diagnostics:
            return "ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nNo errors found."
        
        # Count by business impact
        critical_count = sum(1 for d in diagnostics if d.business_impact == 'Critical')
        major_count = sum(1 for d in diagnostics if d.business_impact == 'Major')
        minor_count = sum(1 for d in diagnostics if d.business_impact == 'Minor')
        
        # Header
        header = f"ERRORS: {len(diagnostics)} [⚠️ Critical: {critical_count}] [👉 Major: {major_count}] [🔍 Minor: {minor_count}]"
        
        # Sort diagnostics by business impact
        impact_order = {'Critical': 0, 'Major': 1, 'Minor': 2}
        sorted_diagnostics = sorted(
            diagnostics,
            key=lambda d: (impact_order.get(d.business_impact, 3), d.file_path, d.line)
        )
        
        # Format each diagnostic
        output_lines = [header]
        for i, diag in enumerate(sorted_diagnostics, 1):
            # Get relative path
            try:
                rel_path = os.path.relpath(diag.file_path, repo_path)
            except ValueError:
                rel_path = os.path.basename(diag.file_path)
            
            # Get icon and context
            icon = diag.get_severity_icon()
            context = diag.get_context_string()
            
            # Format message
            message = diag.message
            if diag.code:
                message += f" (code: {diag.code})"
            if diag.source:
                message += f" [source: {diag.source}]"
            
            line = f"{i} {icon}- {rel_path} / {context} [{message}]"
            output_lines.append(line)
        
        return '\n'.join(output_lines)
    
    def _fallback_analysis(self, source_files: List[str], language: str, repo_path: str) -> str:
        """Fallback analysis when LSP not available."""
        # Simple syntax checking for Python files
        diagnostics = []
        
        for file_path in source_files[:50]:  # Limit for demo
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if file_path.endswith('.py'):
                    # Try to compile Python code
                    try:
                        compile(content, file_path, 'exec')
                    except SyntaxError as e:
                        diag = RealLSPDiagnostic(
                            file_path=file_path,
                            line=e.lineno or 1,
                            column=e.offset or 1,
                            severity='ERROR',
                            message=f"Syntax error: {e.msg}",
                            code='syntax-error',
                            source='python-compiler',
                            business_impact='Critical'
                        )
                        diagnostics.append(diag)
                    
                    # Check for common issues
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        # Check for undefined variables (simple heuristic)
                        if 'undefined' in line.lower() or 'not defined' in line.lower():
                            diag = RealLSPDiagnostic(
                                file_path=file_path,
                                line=line_num,
                                column=1,
                                severity='ERROR',
                                message="Potential undefined variable",
                                code='undefined-variable',
                                source='fallback-analyzer',
                                business_impact='Critical'
                            )
                            diagnostics.append(diag)
                        
                        # Check for warnings
                        if 'TODO' in line or 'FIXME' in line:
                            diag = RealLSPDiagnostic(
                                file_path=file_path,
                                line=line_num,
                                column=1,
                                severity='WARNING',
                                message="TODO/FIXME comment found",
                                code='todo-comment',
                                source='fallback-analyzer',
                                business_impact='Major'
                            )
                            diagnostics.append(diag)
            
            except Exception as e:
                continue
        
        return self._format_output(diagnostics, repo_path)
    
    def _is_git_url(self, path: str) -> bool:
        """Check if path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith('.git')
    
    def _clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory."""
        self.logger.info(f"📥 Cloning {repo_url}")
        
        self.temp_dir = tempfile.mkdtemp(prefix="enhanced_lsp_analysis_")
        repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        self.logger.info(f"✅ Cloned to {clone_path}")
        return clone_path
    
    def _detect_language(self, repo_path: str) -> str:
        """Detect primary language of repository."""
        language_scores = {'python': 0, 'javascript': 0, 'typescript': 0}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py'):
                    language_scores['python'] += 1
                elif file.endswith(('.js', '.jsx')):
                    language_scores['javascript'] += 1
                elif file.endswith(('.ts', '.tsx')):
                    language_scores['typescript'] += 1
        
        detected = max(language_scores, key=language_scores.get)
        self.logger.info(f"✅ Detected language: {detected} (score: {language_scores[detected]})")
        return detected
    
    def _get_source_files(self, repo_path: str, language: str) -> List[str]:
        """Get source files for the language."""
        extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx']
        }.get(language, ['.py'])
        
        source_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) < 1024 * 1024:  # Skip files > 1MB
                        source_files.append(full_path)
        
        return source_files
    
    def _cleanup(self):
        """Cleanup resources."""
        # Shutdown LSP clients
        for client in self.lsp_clients.values():
            try:
                client.shutdown()
            except Exception:
                pass
        
        # Remove temp directory
        if self.temp_dir:
            try:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced LSP Analyzer with Real LSP Integration")
    parser.add_argument('repository', help='Repository URL or local path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = EnhancedLSPAnalyzer(verbose=args.verbose)
    result = analyzer.analyze_repository(args.repository)
    print(result)


if __name__ == "__main__":
    main()
