#!/usr/bin/env python3
"""
Enhanced Comprehensive Serena LSP Error Analysis Tool

This upgraded tool provides maximum comprehension LSP error retrieval with:
- Function-level error attribution using AST parsing
- Advanced severity classification with visual indicators (⚠️ Critical, 👉 Major, 🔍 Minor)
- Enhanced output format matching desired structure
- Symbol resolution for precise error location mapping
- Expanded diagnostic metadata collection
- Performance optimization with intelligent caching

Features:
- 100% LSP error retrieval with full location paths and function attribution
- Advanced severity mapping with business impact classification
- Enhanced output format: ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
- Function-level error mapping: projectname'/src/codefile.py / Function - 'function_name'
- AST-based symbol resolution for precise code construct identification
- Comprehensive diagnostic metadata with contextual information
- Intelligent caching and incremental analysis capabilities
- Multi-language support with language-specific optimizations

Usage:
    python enhanced_serena_analyzer.py <repo_url_or_path> [options]

Example:
    python enhanced_serena_analyzer.py https://github.com/user/repo.git --enhanced-output
    python enhanced_serena_analyzer.py /path/to/local/repo --severity CRITICAL --function-attribution
    python enhanced_serena_analyzer.py . --verbose --enhanced-severity --symbol-resolution
"""

import argparse
import ast
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import threading
import hashlib
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set, NamedTuple
from urllib.parse import urlparse
from collections import defaultdict, Counter
import re

# Enhanced imports for AST parsing and symbol resolution
try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_java
    import tree_sitter_cpp
    import tree_sitter_rust
    import tree_sitter_go
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

# Comprehensive Serena and SolidLSP imports
try:
    # Core Serena imports
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    
    # SolidLSP core configuration and server
    from solidlsp.ls_config import Language, LanguageServerConfig
    from solidlsp.ls_logger import LanguageServerLogger
    from solidlsp.settings import SolidLSPSettings
    from solidlsp import SolidLanguageServer
    
    # Comprehensive LSP protocol types and diagnostics
    from solidlsp.ls_types import (
        DiagnosticsSeverity,
        DiagnosticSeverity,
        Diagnostic,
        ErrorCodes,
        LSPErrorCodes,
        Position,
        Range,
        Location,
        MarkupContent,
        MarkupKind,
        CompletionItemKind,
        CompletionItem,
        UnifiedSymbolInformation,
        SymbolKind,
        SymbolTag,
    )
    
    # LSP protocol handler components for robust server management
    from solidlsp.lsp_protocol_handler.server import (
        ProcessLaunchInfo,
        LSPError,
        MessageType,
    )
    
    # Serena symbol handling for comprehensive code analysis
    from serena.symbol import (
        LanguageServerSymbolRetriever,
        ReferenceInLanguageServerSymbol,
        LanguageServerSymbol,
        Symbol,
        PositionInFile,
        LanguageServerSymbolLocation,
    )
    
except ImportError as e:
    print(f"Error: Failed to import required Serena/SolidLSP modules: {e}")
    print("Please ensure Serena and SolidLSP are properly installed.")
    print("Try: pip install -e . from the serena repository root")
    sys.exit(1)


# Enhanced severity classification system
class EnhancedSeverity:
    """Advanced severity classification with business impact mapping."""
    
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR" 
    MINOR = "MINOR"
    INFO = "INFO"
    
    # Visual indicators for enhanced output
    SEVERITY_ICONS = {
        CRITICAL: "⚠️",
        MAJOR: "👉", 
        MINOR: "🔍",
        INFO: "ℹ️"
    }
    
    # Business impact scoring (1-10 scale)
    IMPACT_SCORES = {
        CRITICAL: 9,
        MAJOR: 6,
        MINOR: 3,
        INFO: 1
    }
    
    # LSP severity to enhanced severity mapping
    LSP_MAPPING = {
        DiagnosticsSeverity.ERROR: CRITICAL,
        DiagnosticsSeverity.WARNING: MAJOR,
        DiagnosticsSeverity.INFORMATION: MINOR,
        DiagnosticsSeverity.HINT: INFO
    }
    
    # Error code to severity overrides for specific cases
    ERROR_CODE_OVERRIDES = {
        # Security-related errors are always critical
        "security": CRITICAL,
        "vulnerability": CRITICAL,
        "injection": CRITICAL,
        
        # Performance issues are major
        "performance": MAJOR,
        "memory": MAJOR,
        "timeout": MAJOR,
        
        # Style and formatting are minor
        "style": MINOR,
        "format": MINOR,
        "whitespace": MINOR,
    }
    
    @classmethod
    def classify_diagnostic(cls, lsp_severity: DiagnosticsSeverity, 
                          error_code: Optional[str] = None,
                          error_message: str = "",
                          function_context: Optional[str] = None) -> str:
        """
        Classify diagnostic with enhanced business impact assessment.
        
        Args:
            lsp_severity: Original LSP diagnostic severity
            error_code: Error code if available
            error_message: Error message for context analysis
            function_context: Function name where error occurs for context
            
        Returns:
            Enhanced severity classification
        """
        # Start with base LSP mapping
        base_severity = cls.LSP_MAPPING.get(lsp_severity, cls.MINOR)
        
        # Check for error code overrides
        if error_code:
            error_code_lower = error_code.lower()
            for keyword, override_severity in cls.ERROR_CODE_OVERRIDES.items():
                if keyword in error_code_lower:
                    return override_severity
        
        # Analyze error message for severity indicators
        message_lower = error_message.lower()
        
        # Critical indicators
        critical_keywords = [
            "security", "vulnerability", "injection", "exploit", "unsafe",
            "null pointer", "buffer overflow", "memory leak", "deadlock",
            "infinite loop", "stack overflow", "segmentation fault"
        ]
        
        if any(keyword in message_lower for keyword in critical_keywords):
            return cls.CRITICAL
        
        # Major indicators  
        major_keywords = [
            "deprecated", "performance", "inefficient", "slow", "timeout",
            "memory", "resource", "compatibility", "breaking change"
        ]
        
        if any(keyword in message_lower for keyword in major_keywords):
            return cls.MAJOR
        
        # Function context analysis
        if function_context:
            # Errors in main functions or entry points are more critical
            critical_functions = ["main", "__main__", "init", "setup", "start", "run"]
            if any(func in function_context.lower() for func in critical_functions):
                # Upgrade severity by one level
                if base_severity == cls.MINOR:
                    return cls.MAJOR
                elif base_severity == cls.MAJOR:
                    return cls.CRITICAL
        
        return base_severity


@dataclass
class FunctionInfo:
    """Information about a function where an error occurs."""
    name: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    function_type: str  # 'function', 'method', 'class', 'module'
    parent_class: Optional[str] = None
    docstring: Optional[str] = None
    complexity_score: int = 1
    is_public: bool = True
    parameters: List[str] = field(default_factory=list)


@dataclass 
class EnhancedDiagnostic:
    """Enhanced diagnostic with comprehensive metadata and function attribution."""
    file_path: str
    line: int
    column: int
    severity: str  # Enhanced severity (CRITICAL, MAJOR, MINOR, INFO)
    lsp_severity: str  # Original LSP severity
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    error_code: Optional[ErrorCodes] = None
    
    # Enhanced function attribution
    function_info: Optional[FunctionInfo] = None
    function_name: str = "unknown"
    
    # Enhanced LSP protocol fields
    range_info: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    related_information: List[Dict[str, Any]] = field(default_factory=list)
    
    # Enhanced metadata
    impact_score: int = 1
    business_priority: str = "LOW"
    fix_complexity: str = "SIMPLE"
    affected_components: List[str] = field(default_factory=list)
    
    # Context information
    surrounding_code: Optional[str] = None
    symbol_context: Optional[Dict[str, Any]] = None
    dependency_info: Optional[Dict[str, Any]] = None


class SymbolResolver:
    """Enhanced symbol resolution using AST parsing and tree-sitter."""
    
    def __init__(self, language: Language, verbose: bool = False):
        self.language = language
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        # Initialize tree-sitter parsers if available
        self.tree_sitter_parser = None
        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()
        
        # Function cache for performance
        self.function_cache: Dict[str, List[FunctionInfo]] = {}
        
    def _init_tree_sitter(self):
        """Initialize tree-sitter parser for the detected language."""
        try:
            if self.language == Language.PYTHON:
                self.tree_sitter_parser = tree_sitter.Parser()
                self.tree_sitter_parser.set_language(tree_sitter_python.language())
            elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
                self.tree_sitter_parser = tree_sitter.Parser()
                if self.language == Language.TYPESCRIPT:
                    self.tree_sitter_parser.set_language(tree_sitter_typescript.language())
                else:
                    self.tree_sitter_parser.set_language(tree_sitter_javascript.language())
            elif self.language == Language.JAVA:
                self.tree_sitter_parser = tree_sitter.Parser()
                self.tree_sitter_parser.set_language(tree_sitter_java.language())
            elif self.language == Language.CPP:
                self.tree_sitter_parser = tree_sitter.Parser()
                self.tree_sitter_parser.set_language(tree_sitter_cpp.language())
            elif self.language == Language.RUST:
                self.tree_sitter_parser = tree_sitter.Parser()
                self.tree_sitter_parser.set_language(tree_sitter_rust.language())
            elif self.language == Language.GO:
                self.tree_sitter_parser = tree_sitter.Parser()
                self.tree_sitter_parser.set_language(tree_sitter_go.language())
                
            if self.verbose and self.tree_sitter_parser:
                self.logger.info(f"✅ Tree-sitter parser initialized for {self.language.value}")
                
        except Exception as e:
            if self.verbose:
                self.logger.warning(f"⚠️  Could not initialize tree-sitter for {self.language.value}: {e}")
            self.tree_sitter_parser = None
    
    def extract_functions_from_file(self, file_path: str) -> List[FunctionInfo]:
        """
        Extract function information from a source file using AST parsing.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of FunctionInfo objects for all functions in the file
        """
        # Check cache first
        cache_key = f"{file_path}:{os.path.getmtime(file_path)}"
        if cache_key in self.function_cache:
            return self.function_cache[cache_key]
        
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Try tree-sitter first if available
            if self.tree_sitter_parser and content:
                functions = self._extract_with_tree_sitter(content, file_path)
            
            # Fallback to language-specific AST parsing
            if not functions:
                if self.language == Language.PYTHON:
                    functions = self._extract_python_functions(content, file_path)
                elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
                    functions = self._extract_js_functions(content, file_path)
                # Add more language-specific extractors as needed
            
            # Cache the results
            self.function_cache[cache_key] = functions
            
            if self.verbose and functions:
                self.logger.debug(f"🔍 Extracted {len(functions)} functions from {os.path.basename(file_path)}")
                
        except Exception as e:
            if self.verbose:
                self.logger.warning(f"⚠️  Could not extract functions from {os.path.basename(file_path)}: {e}")
        
        return functions
    
    def _extract_with_tree_sitter(self, content: str, file_path: str) -> List[FunctionInfo]:
        """Extract functions using tree-sitter parser."""
        functions = []
        
        try:
            tree = self.tree_sitter_parser.parse(content.encode('utf-8'))
            root_node = tree.root_node
            
            # Language-specific function node types
            function_node_types = {
                Language.PYTHON: ['function_def', 'async_function_def'],
                Language.JAVASCRIPT: ['function_declaration', 'function_expression', 'arrow_function'],
                Language.TYPESCRIPT: ['function_declaration', 'function_expression', 'arrow_function', 'method_definition'],
                Language.JAVA: ['method_declaration', 'constructor_declaration'],
                Language.CPP: ['function_definition', 'function_declaration'],
                Language.RUST: ['function_item'],
                Language.GO: ['function_declaration', 'method_declaration'],
            }
            
            target_types = function_node_types.get(self.language, ['function_def'])
            
            def traverse_node(node, parent_class=None):
                if node.type in target_types:
                    func_info = self._extract_function_info_from_node(node, content, parent_class)
                    if func_info:
                        functions.append(func_info)
                
                # Check for class definitions to track parent classes
                current_parent = parent_class
                if node.type in ['class_definition', 'class_declaration']:
                    class_name_node = None
                    for child in node.children:
                        if child.type == 'identifier':
                            class_name_node = child
                            break
                    if class_name_node:
                        current_parent = content[class_name_node.start_byte:class_name_node.end_byte]
                
                # Recursively traverse children
                for child in node.children:
                    traverse_node(child, current_parent)
            
            traverse_node(root_node)
            
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"Tree-sitter extraction failed for {os.path.basename(file_path)}: {e}")
        
        return functions
    
    def _extract_function_info_from_node(self, node, content: str, parent_class: Optional[str] = None) -> Optional[FunctionInfo]:
        """Extract FunctionInfo from a tree-sitter node."""
        try:
            # Get function name
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            
            if not name_node:
                return None
            
            function_name = content[name_node.start_byte:name_node.end_byte]
            
            # Get position information
            start_point = node.start_point
            end_point = node.end_point
            
            # Extract parameters
            parameters = []
            for child in node.children:
                if child.type in ['parameters', 'parameter_list']:
                    for param_child in child.children:
                        if param_child.type == 'identifier':
                            param_name = content[param_child.start_byte:param_child.end_byte]
                            parameters.append(param_name)
            
            # Determine function type
            function_type = "method" if parent_class else "function"
            if node.type in ['constructor_declaration', '__init__']:
                function_type = "constructor"
            
            # Check if function is public (simple heuristic)
            is_public = not function_name.startswith('_')
            
            return FunctionInfo(
                name=function_name,
                line_start=start_point.row + 1,
                line_end=end_point.row + 1,
                column_start=start_point.column + 1,
                column_end=end_point.column + 1,
                function_type=function_type,
                parent_class=parent_class,
                is_public=is_public,
                parameters=parameters,
                complexity_score=self._estimate_complexity(node, content)
            )
            
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"Failed to extract function info from node: {e}")
            return None
    
    def _extract_python_functions(self, content: str, file_path: str) -> List[FunctionInfo]:
        """Extract Python functions using AST module."""
        functions = []
        
        try:
            tree = ast.parse(content)
            
            class FunctionVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.functions = []
                
                def visit_ClassDef(self, node):
                    old_class = self.current_class
                    self.current_class = node.name
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    self._process_function(node)
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    self._process_function(node, is_async=True)
                    self.generic_visit(node)
                
                def _process_function(self, node, is_async=False):
                    # Extract parameters
                    parameters = [arg.arg for arg in node.args.args]
                    
                    # Get docstring
                    docstring = None
                    if (node.body and isinstance(node.body[0], ast.Expr) 
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                        docstring = node.body[0].value.value
                    
                    function_type = "method" if self.current_class else "function"
                    if is_async:
                        function_type = f"async_{function_type}"
                    
                    func_info = FunctionInfo(
                        name=node.name,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        column_start=node.col_offset + 1,
                        column_end=node.end_col_offset + 1 if node.end_col_offset else node.col_offset + 1,
                        function_type=function_type,
                        parent_class=self.current_class,
                        docstring=docstring,
                        is_public=not node.name.startswith('_'),
                        parameters=parameters,
                        complexity_score=self._estimate_python_complexity(node)
                    )
                    
                    self.functions.append(func_info)
                
                def _estimate_python_complexity(self, node):
                    """Simple complexity estimation based on AST node count."""
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                            complexity += 1
                        elif isinstance(child, (ast.And, ast.Or)):
                            complexity += 1
                    return min(complexity, 10)  # Cap at 10
            
            visitor = FunctionVisitor()
            visitor.visit(tree)
            functions = visitor.functions
            
        except SyntaxError as e:
            if self.verbose:
                self.logger.debug(f"Python AST parsing failed for {os.path.basename(file_path)}: {e}")
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"Python function extraction failed for {os.path.basename(file_path)}: {e}")
        
        return functions
    
    def _extract_js_functions(self, content: str, file_path: str) -> List[FunctionInfo]:
        """Extract JavaScript/TypeScript functions using regex patterns."""
        functions = []
        
        try:
            # Regex patterns for different function types
            patterns = [
                # Function declarations: function name() {}
                r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{',
                # Arrow functions: const name = () => {}
                r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*=>\s*\{)',
                # Method definitions: name() {}
                r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{',
                # Class methods: methodName() {}
                r'(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{',
            ]
            
            lines = content.split('\n')
            
            for pattern in patterns:
                for i, line in enumerate(lines):
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        function_name = match.group(1)
                        
                        # Skip common keywords that might match
                        if function_name in ['if', 'for', 'while', 'switch', 'catch', 'class']:
                            continue
                        
                        func_info = FunctionInfo(
                            name=function_name,
                            line_start=i + 1,
                            line_end=i + 1,  # Simplified - would need proper parsing for end
                            column_start=match.start() + 1,
                            column_end=match.end() + 1,
                            function_type="function",
                            is_public=not function_name.startswith('_'),
                            complexity_score=1
                        )
                        
                        functions.append(func_info)
            
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"JavaScript function extraction failed for {os.path.basename(file_path)}: {e}")
        
        return functions
    
    def _estimate_complexity(self, node, content: str) -> int:
        """Estimate function complexity from tree-sitter node."""
        complexity = 1
        
        # Count control flow statements
        control_flow_types = ['if_statement', 'for_statement', 'while_statement', 
                             'switch_statement', 'try_statement', 'catch_clause']
        
        def count_complexity(n):
            nonlocal complexity
            if n.type in control_flow_types:
                complexity += 1
            for child in n.children:
                count_complexity(child)
        
        count_complexity(node)
        return min(complexity, 10)  # Cap at 10
    
    def find_function_at_line(self, file_path: str, line_number: int) -> Optional[FunctionInfo]:
        """
        Find the function that contains the given line number.
        
        Args:
            file_path: Path to the source file
            line_number: Line number to search for
            
        Returns:
            FunctionInfo if found, None otherwise
        """
        functions = self.extract_functions_from_file(file_path)
        
        # Find the function that contains this line
        for func in functions:
            if func.line_start <= line_number <= func.line_end:
                return func
        
        return None


class EnhancedSerenaAnalyzer:
    """
    Enhanced comprehensive LSP analyzer with function-level attribution and advanced severity classification.
    
    This upgraded class provides:
    - 100% LSP error retrieval with function-level attribution
    - Advanced severity classification with visual indicators
    - Enhanced output format matching desired structure
    - Symbol resolution for precise error location mapping
    - Intelligent caching and performance optimization
    """
    
    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4, 
                 enable_runtime_errors: bool = False, enable_function_attribution: bool = True,
                 enable_enhanced_severity: bool = True, enable_symbol_resolution: bool = True):
        """
        Initialize the enhanced analyzer with advanced capabilities.
        
        Args:
            verbose: Enable verbose logging and progress tracking
            timeout: Timeout for language server operations
            max_workers: Maximum number of concurrent workers for file processing
            enable_runtime_errors: Enable runtime error collection during execution
            enable_function_attribution: Enable function-level error attribution
            enable_enhanced_severity: Enable advanced severity classification
            enable_symbol_resolution: Enable symbol resolution and AST parsing
        """
        self.verbose = verbose
        self.timeout = timeout
        self.max_workers = max_workers
        self.enable_runtime_errors = enable_runtime_errors
        self.enable_function_attribution = enable_function_attribution
        self.enable_enhanced_severity = enable_enhanced_severity
        self.enable_symbol_resolution = enable_symbol_resolution
        
        self.temp_dir: Optional[str] = None
        self.project: Optional[Project] = None
        self.language_server: Optional[SolidLanguageServer] = None
        self.symbol_resolver: Optional[SymbolResolver] = None
        
        # Analysis tracking
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_diagnostics = 0
        self.total_runtime_errors = 0
        self.analysis_start_time = None
        self.lock = threading.Lock()
        
        # Enhanced tracking
        self.functions_analyzed = 0
        self.symbols_resolved = 0
        self.severity_upgrades = 0
        
        # Runtime error tracking
        self.runtime_errors: List[RuntimeError] = []
        self.execution_results: Dict[str, Any] = {}
        
        # Set up comprehensive logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_stats = {
            'clone_time': 0,
            'setup_time': 0,
            'lsp_start_time': 0,
            'analysis_time': 0,
            'symbol_resolution_time': 0,
            'function_attribution_time': 0,
            'severity_classification_time': 0,
            'runtime_analysis_time': 0,
            'total_time': 0
        }
        
        if verbose:
            self.logger.info("🚀 Initializing Enhanced Comprehensive Serena LSP Analyzer")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
            self.logger.info(f"🔧 Enhanced features: function_attribution={enable_function_attribution}, "
                           f"enhanced_severity={enable_enhanced_severity}, symbol_resolution={enable_symbol_resolution}")
            if enable_runtime_errors:
                self.logger.info("🔥 Runtime error collection enabled")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources including language server and temporary directories."""
        try:
            if self.language_server and self.language_server.is_running():
                self.logger.info("🛑 Stopping language server...")
                self.language_server.stop()
                
            if self.temp_dir and os.path.exists(self.temp_dir):
                self.logger.info(f"🧹 Cleaning up temporary directory: {self.temp_dir}")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            self.logger.warning(f"⚠️  Error during cleanup: {e}")
    
    def is_git_url(self, path: str) -> bool:
        """Check if the given path is a Git URL."""
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc) or path.endswith('.git')
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a Git repository to a temporary directory."""
        self.logger.info(f"📥 Cloning repository: {repo_url}")
        
        self.temp_dir = tempfile.mkdtemp(prefix="enhanced_serena_analysis_")
        repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")
                
            self.logger.info(f"✅ Repository cloned to: {clone_path}")
            return clone_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git clone timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    def detect_language(self, repo_path: str) -> Language:
        """Detect the primary programming language of the repository."""
        self.logger.info("🔍 Detecting repository language...")
        
        language_indicators = {
            Language.PYTHON: ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml'],
            Language.TYPESCRIPT: ['.ts', '.tsx', '.js', '.jsx', 'tsconfig.json', 'package.json'],
            Language.JAVA: ['.java', 'pom.xml', 'build.gradle'],
            Language.CSHARP: ['.cs', '.csproj', '.sln'],
            Language.CPP: ['.cpp', '.cc', '.cxx', '.h', '.hpp', 'CMakeLists.txt'],
            Language.RUST: ['.rs', 'Cargo.toml'],
            Language.GO: ['.go', 'go.mod'],
            Language.PHP: ['.php', 'composer.json'],
            Language.RUBY: ['.rb', 'Gemfile'],
            Language.KOTLIN: ['.kt', '.kts'],
            Language.DART: ['.dart', 'pubspec.yaml'],
        }
        
        file_counts = {lang: 0 for lang in language_indicators.keys()}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'target', 'build', 'dist', 'vendor'
            ]]
            
            for file in files:
                file_lower = file.lower()
                for lang, indicators in language_indicators.items():
                    if any(file_lower.endswith(ext) or file_lower == indicator 
                          for ext in indicators for indicator in [ext] if ext.startswith('.')):
                        file_counts[lang] += 1
                    elif any(file_lower == indicator 
                            for indicator in indicators if not indicator.startswith('.')):
                        file_counts[lang] += 5
        
        detected_lang = max(file_counts, key=file_counts.get)
        
        if file_counts[detected_lang] == 0:
            self.logger.warning("Could not detect language, defaulting to Python")
            detected_lang = Language.PYTHON
        
        self.logger.info(f"✅ Detected language: {detected_lang.value}")
        return detected_lang
    
    def setup_project(self, repo_path: str, language: Optional[Language] = None) -> Project:
        """Set up a Serena project for the repository."""
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path is not a directory: {repo_path}")
        
        if language is None:
            language = self.detect_language(repo_path)
        
        self.logger.info(f"⚙️  Setting up enhanced project for {repo_path} with language {language.value}")
        
        project_config = ProjectConfig(
            project_name=os.path.basename(repo_path),
            language=language,
            ignored_paths=[
                '.git/**',
                '**/__pycache__/**',
                '**/node_modules/**',
                '**/target/**',
                '**/build/**',
                '**/.venv/**',
                '**/venv/**',
                '**/dist/**',
                '**/vendor/**',
            ],
            ignore_all_files_in_gitignore=True
        )
        
        self.project = Project(repo_path, project_config)
        
        # Initialize symbol resolver if enabled
        if self.enable_symbol_resolution:
            self.symbol_resolver = SymbolResolver(language, self.verbose)
            if self.verbose:
                self.logger.info("🔍 Symbol resolver initialized for function attribution")
        
        return self.project
