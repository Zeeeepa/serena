#!/usr/bin/env python3
"""
Comprehensive Serena Codebase Analysis Tool

This script programmatically analyzes the entire Serena codebase to extract:
- All top-level classes and their methods
- All important functions and their signatures
- Module dependencies and imports
- Core architectural components
- LSP-related functionality
- Error handling patterns

The output will be used to create a robust serena_bridge.py abstraction layer.
"""

import ast
import os
import sys
import json
import inspect
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FunctionInfo:
    """Information about a function or method."""
    name: str
    module: str
    signature: str
    docstring: Optional[str]
    is_method: bool
    is_async: bool
    decorators: List[str]
    parameters: List[Dict[str, Any]]
    return_annotation: Optional[str]
    line_number: int


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    module: str
    docstring: Optional[str]
    bases: List[str]
    methods: List[FunctionInfo]
    class_variables: List[str]
    decorators: List[str]
    line_number: int
    is_abstract: bool
    is_dataclass: bool


@dataclass
class ModuleInfo:
    """Information about a module."""
    name: str
    path: str
    docstring: Optional[str]
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    constants: List[str]
    dependencies: Set[str]


class SerenaCodebaseAnalyzer:
    """Comprehensive analyzer for the Serena codebase."""
    
    def __init__(self, src_path: str = "src"):
        self.src_path = Path(src_path)
        self.modules: Dict[str, ModuleInfo] = {}
        self.all_classes: Dict[str, ClassInfo] = {}
        self.all_functions: Dict[str, FunctionInfo] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.core_components: Dict[str, List[str]] = {
            "lsp_core": [],
            "project_management": [],
            "analysis_tools": [],
            "configuration": [],
            "utilities": [],
            "exceptions": []
        }
        
    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of the entire codebase."""
        print("🔍 Starting comprehensive Serena codebase analysis...")
        
        # Find all Python files
        python_files = list(self.src_path.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
                continue
        
        # Categorize components
        self._categorize_components()
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Generate analysis report
        return self._generate_analysis_report()
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"⚠️  Skipping {file_path} due to encoding issues")
            return
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
            return
        
        # Get module name
        module_name = self._get_module_name(file_path)
        
        # Extract module information
        module_info = ModuleInfo(
            name=module_name,
            path=str(file_path),
            docstring=ast.get_docstring(tree),
            imports=[],
            classes=[],
            functions=[],
            constants=[],
            dependencies=set()
        )
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.append(alias.name)
                    module_info.dependencies.add(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_info.imports.append(f"from {node.module}")
                    module_info.dependencies.add(node.module)
            
            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node, module_name)
                module_info.classes.append(class_info)
                self.all_classes[f"{module_name}.{class_info.name}"] = class_info
            
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions
                if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    func_info = self._analyze_function(node, module_name, is_method=False)
                    module_info.functions.append(func_info)
                    self.all_functions[f"{module_name}.{func_info.name}"] = func_info
            
            elif isinstance(node, ast.Assign):
                # Constants (uppercase variables)
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        module_info.constants.append(target.id)
        
        self.modules[module_name] = module_info
    
    def _analyze_class(self, node: ast.ClassDef, module_name: str) -> ClassInfo:
        """Analyze a class definition."""
        methods = []
        
        # Analyze methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(item, module_name, is_method=True)
                methods.append(method_info)
        
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attribute_name(base))
        
        # Check for decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        return ClassInfo(
            name=node.name,
            module=module_name,
            docstring=ast.get_docstring(node),
            bases=bases,
            methods=methods,
            class_variables=[],
            decorators=decorators,
            line_number=node.lineno,
            is_abstract="abstractmethod" in str(node.decorator_list),
            is_dataclass="dataclass" in decorators
        )
    
    def _analyze_function(self, node: ast.FunctionDef, module_name: str, is_method: bool) -> FunctionInfo:
        """Analyze a function or method definition."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": None
            }
            parameters.append(param_info)
        
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Get return annotation
        return_annotation = ast.unparse(node.returns) if node.returns else None
        
        return FunctionInfo(
            name=node.name,
            module=module_name,
            signature=self._get_function_signature(node),
            docstring=ast.get_docstring(node),
            is_method=is_method,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
            parameters=parameters,
            return_annotation=return_annotation,
            line_number=node.lineno
        )
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        relative_path = file_path.relative_to(self.src_path)
        parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return self._get_attribute_name(node.func)
        return str(node)
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature as string."""
        try:
            return ast.unparse(node).split('\n')[0]
        except:
            return f"def {node.name}(...)"
    
    def _categorize_components(self) -> None:
        """Categorize components by functionality."""
        for module_name, module_info in self.modules.items():
            # LSP Core components
            if any(keyword in module_name.lower() for keyword in ['lsp', 'language_server', 'solidlsp']):
                self.core_components["lsp_core"].append(module_name)
            
            # Project management
            elif any(keyword in module_name.lower() for keyword in ['project', 'config']):
                self.core_components["project_management"].append(module_name)
            
            # Analysis tools
            elif any(keyword in module_name.lower() for keyword in ['analysis', 'diagnostic', 'search']):
                self.core_components["analysis_tools"].append(module_name)
            
            # Configuration
            elif any(keyword in module_name.lower() for keyword in ['config', 'settings']):
                self.core_components["configuration"].append(module_name)
            
            # Exceptions
            elif any(keyword in module_name.lower() for keyword in ['exception', 'error']):
                self.core_components["exceptions"].append(module_name)
            
            # Utilities
            else:
                self.core_components["utilities"].append(module_name)
    
    def _build_dependency_graph(self) -> None:
        """Build module dependency graph."""
        for module_name, module_info in self.modules.items():
            for dep in module_info.dependencies:
                # Only include internal dependencies
                if dep.startswith(('serena', 'solidlsp', 'interprompt')):
                    self.dependency_graph[module_name].add(dep)
    
    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        # Find most important classes and functions
        important_classes = self._find_important_classes()
        important_functions = self._find_important_functions()
        
        return {
            "summary": {
                "total_modules": len(self.modules),
                "total_classes": len(self.all_classes),
                "total_functions": len(self.all_functions),
                "core_components": {k: len(v) for k, v in self.core_components.items()}
            },
            "core_components": self.core_components,
            "important_classes": important_classes,
            "important_functions": important_functions,
            "modules": {name: asdict(info) for name, info in self.modules.items()},
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()},
            "lsp_api_surface": self._extract_lsp_api_surface(),
            "project_api_surface": self._extract_project_api_surface(),
            "exception_hierarchy": self._extract_exception_hierarchy()
        }
    
    def _find_important_classes(self) -> List[Dict[str, Any]]:
        """Find the most important classes based on various criteria."""
        important = []
        
        for full_name, class_info in self.all_classes.items():
            importance_score = 0
            
            # Core LSP classes
            if any(keyword in class_info.name.lower() for keyword in 
                   ['languageserver', 'project', 'diagnostic', 'config']):
                importance_score += 10
            
            # Classes with many methods
            importance_score += len(class_info.methods)
            
            # Abstract classes or base classes
            if class_info.is_abstract or class_info.bases:
                importance_score += 5
            
            # Public API classes (not starting with _)
            if not class_info.name.startswith('_'):
                importance_score += 3
            
            if importance_score >= 5:
                important.append({
                    "full_name": full_name,
                    "class_info": asdict(class_info),
                    "importance_score": importance_score
                })
        
        return sorted(important, key=lambda x: x["importance_score"], reverse=True)
    
    def _find_important_functions(self) -> List[Dict[str, Any]]:
        """Find the most important functions."""
        important = []
        
        for full_name, func_info in self.all_functions.items():
            importance_score = 0
            
            # Core functionality keywords
            if any(keyword in func_info.name.lower() for keyword in 
                   ['create', 'start', 'stop', 'analyze', 'request', 'get', 'find']):
                importance_score += 5
            
            # Public functions
            if not func_info.name.startswith('_'):
                importance_score += 3
            
            # Functions with docstrings
            if func_info.docstring:
                importance_score += 2
            
            if importance_score >= 5:
                important.append({
                    "full_name": full_name,
                    "function_info": asdict(func_info),
                    "importance_score": importance_score
                })
        
        return sorted(important, key=lambda x: x["importance_score"], reverse=True)
    
    def _extract_lsp_api_surface(self) -> Dict[str, Any]:
        """Extract LSP-related API surface."""
        lsp_api = {
            "classes": [],
            "functions": [],
            "constants": []
        }
        
        for module_name in self.core_components["lsp_core"]:
            if module_name in self.modules:
                module_info = self.modules[module_name]
                lsp_api["classes"].extend([asdict(cls) for cls in module_info.classes])
                lsp_api["functions"].extend([asdict(func) for func in module_info.functions])
                lsp_api["constants"].extend(module_info.constants)
        
        return lsp_api
    
    def _extract_project_api_surface(self) -> Dict[str, Any]:
        """Extract project management API surface."""
        project_api = {
            "classes": [],
            "functions": [],
            "constants": []
        }
        
        for module_name in self.core_components["project_management"]:
            if module_name in self.modules:
                module_info = self.modules[module_name]
                project_api["classes"].extend([asdict(cls) for cls in module_info.classes])
                project_api["functions"].extend([asdict(func) for func in module_info.functions])
                project_api["constants"].extend(module_info.constants)
        
        return project_api
    
    def _extract_exception_hierarchy(self) -> Dict[str, Any]:
        """Extract exception class hierarchy."""
        exceptions = {}
        
        for full_name, class_info in self.all_classes.items():
            if any(keyword in class_info.name.lower() for keyword in ['exception', 'error']) or \
               any('Exception' in base for base in class_info.bases):
                exceptions[full_name] = {
                    "name": class_info.name,
                    "module": class_info.module,
                    "bases": class_info.bases,
                    "methods": [method.name for method in class_info.methods]
                }
        
        return exceptions


def main():
    """Main analysis function."""
    analyzer = SerenaCodebaseAnalyzer()
    
    print("🚀 Starting comprehensive Serena codebase analysis...")
    analysis_result = analyzer.analyze_codebase()
    
    # Save detailed analysis
    with open("serena_codebase_analysis.json", "w") as f:
        json.dump(analysis_result, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("📊 SERENA CODEBASE ANALYSIS COMPLETE")
    print("="*80)
    
    summary = analysis_result["summary"]
    print(f"📁 Total modules analyzed: {summary['total_modules']}")
    print(f"🏗️  Total classes found: {summary['total_classes']}")
    print(f"⚙️  Total functions found: {summary['total_functions']}")
    
    print("\n🎯 Core Components:")
    for component, count in summary["core_components"].items():
        print(f"   {component}: {count} modules")
    
    print(f"\n🌟 Top 10 Most Important Classes:")
    for i, cls in enumerate(analysis_result["important_classes"][:10], 1):
        print(f"   {i}. {cls['full_name']} (score: {cls['importance_score']})")
    
    print(f"\n⚡ Top 10 Most Important Functions:")
    for i, func in enumerate(analysis_result["important_functions"][:10], 1):
        print(f"   {i}. {func['full_name']} (score: {func['importance_score']})")
    
    print(f"\n💾 Detailed analysis saved to: serena_codebase_analysis.json")
    print("="*80)
    
    return analysis_result


if __name__ == "__main__":
    main()

