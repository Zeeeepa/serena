#!/usr/bin/env python3
"""
Structure Validation Test for Serena Bridge Implementation

This test validates the structure and design of our Serena bridge
without requiring the actual Serena installation.
"""

import unittest
import os
import ast
import inspect
from typing import Dict, List, Any


class TestSerenaStructureValidation(unittest.TestCase):
    """Validate the structure and design of Serena bridge components."""
    
    def test_serena_bridge_file_exists(self):
        """Test that serena_bridge.py exists and is valid Python."""
        self.assertTrue(os.path.exists("serena_bridge.py"))
        
        # Test that it's valid Python syntax
        with open("serena_bridge.py", 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.fail(f"serena_bridge.py has syntax errors: {e}")
    
    def test_serena_bridge_part2_file_exists(self):
        """Test that serena_bridge_part2.py exists and is valid Python."""
        self.assertTrue(os.path.exists("serena_bridge_part2.py"))
        
        with open("serena_bridge_part2.py", 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.fail(f"serena_bridge_part2.py has syntax errors: {e}")
    
    def test_serena_analysis_file_exists(self):
        """Test that serena_analysis.py exists and is valid Python."""
        self.assertTrue(os.path.exists("serena_analysis.py"))
        
        with open("serena_analysis.py", 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.fail(f"serena_analysis.py has syntax errors: {e}")
    
    def test_serena_bridge_structure(self):
        """Test the structure of serena_bridge.py."""
        with open("serena_bridge.py", 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        # Verify expected classes exist
        expected_classes = [
            "EnhancedDiagnostic",
            "LSPServerInfo", 
            "AnalysisResults",
            "SerenaLSPBridge",
            "SerenaProjectBridge"
        ]
        
        for expected_class in expected_classes:
            self.assertIn(expected_class, class_names, 
                         f"Expected class {expected_class} not found in serena_bridge.py")
    
    def test_serena_bridge_part2_structure(self):
        """Test the structure of serena_bridge_part2.py."""
        with open("serena_bridge_part2.py", 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        # Verify expected classes exist
        expected_classes = [
            "SerenaDiagnosticBridge",
            "SerenaComprehensiveAnalyzer"
        ]
        
        for expected_class in expected_classes:
            self.assertIn(expected_class, class_names,
                         f"Expected class {expected_class} not found in serena_bridge_part2.py")
    
    def test_serena_analysis_structure(self):
        """Test the structure of serena_analysis.py."""
        with open("serena_analysis.py", 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        # Verify expected classes exist
        expected_classes = ["SerenaAnalysisInterface"]
        
        for expected_class in expected_classes:
            self.assertIn(expected_class, class_names,
                         f"Expected class {expected_class} not found in serena_analysis.py")
        
        # Find main function
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        function_names = [func.name for func in functions]
        
        self.assertIn("main", function_names, "main function not found in serena_analysis.py")
    
    def test_import_structure_validation(self):
        """Test that import structures are properly designed."""
        # Test serena_bridge.py imports
        with open("serena_bridge.py", 'r') as f:
            content = f.read()
        
        # Should have comprehensive try/except for imports
        self.assertIn("try:", content)
        self.assertIn("except ImportError", content)
        self.assertIn("solidlsp", content)
        self.assertIn("serena", content)
        
        # Test serena_bridge_part2.py imports
        with open("serena_bridge_part2.py", 'r') as f:
            content = f.read()
        
        self.assertIn("from serena_bridge import *", content)
        
        # Test serena_analysis.py imports
        with open("serena_analysis.py", 'r') as f:
            content = f.read()
        
        self.assertIn("from serena_bridge import *", content)
        self.assertIn("from serena_bridge_part2 import", content)
    
    def test_error_handling_patterns(self):
        """Test that proper error handling patterns are implemented."""
        files_to_check = ["serena_bridge.py", "serena_bridge_part2.py", "serena_analysis.py"]
        
        for filename in files_to_check:
            with open(filename, 'r') as f:
                content = f.read()
            
            # Should have comprehensive exception handling
            self.assertIn("except", content, f"{filename} should have exception handling")
            self.assertIn("try:", content, f"{filename} should have try blocks")
            
            # Should have logging
            self.assertIn("logger", content, f"{filename} should have logging")
            self.assertIn("logging", content, f"{filename} should import logging")
    
    def test_docstring_coverage(self):
        """Test that classes and methods have proper docstrings."""
        files_to_check = ["serena_bridge.py", "serena_bridge_part2.py", "serena_analysis.py"]
        
        for filename in files_to_check:
            with open(filename, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check module docstring
            if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
                self.assertIsInstance(tree.body[0].value.value, str, 
                                    f"{filename} should have module docstring")
            
            # Check class docstrings
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant)):
                        self.assertIsInstance(node.body[0].value.value, str,
                                            f"Class {node.name} in {filename} should have docstring")
    
    def test_comprehensive_test_file_structure(self):
        """Test that the comprehensive test file has proper structure."""
        self.assertTrue(os.path.exists("test_serena_comprehensive.py"))
        
        with open("test_serena_comprehensive.py", 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find all test classes
        test_classes = [node for node in ast.walk(tree) 
                       if isinstance(node, ast.ClassDef) and node.name.startswith("Test")]
        
        expected_test_classes = [
            "TestSerenaLSPBridge",
            "TestSerenaProjectBridge", 
            "TestSerenaDiagnosticBridge",
            "TestSerenaComprehensiveAnalyzer",
            "TestSerenaAnalysisInterface",
            "TestEdgeCasesAndErrorHandling",
            "TestPerformanceAndScalability"
        ]
        
        test_class_names = [cls.name for cls in test_classes]
        
        for expected_class in expected_test_classes:
            self.assertIn(expected_class, test_class_names,
                         f"Expected test class {expected_class} not found")
    
    def test_analysis_codebase_file_exists(self):
        """Test that the codebase analysis file exists."""
        self.assertTrue(os.path.exists("analyze_serena_codebase.py"))
        self.assertTrue(os.path.exists("serena_codebase_analysis.json"))
        
        # Validate JSON structure
        with open("serena_codebase_analysis.json", 'r') as f:
            analysis_data = f.read()
        
        import json
        try:
            data = json.loads(analysis_data)
            
            # Verify expected structure
            expected_keys = [
                "summary", "core_components", "important_classes",
                "important_functions", "modules", "dependency_graph"
            ]
            
            for key in expected_keys:
                self.assertIn(key, data, f"Expected key {key} not found in analysis")
            
            # Verify we found the expected number of components
            self.assertGreater(data["summary"]["total_modules"], 70)
            self.assertGreater(data["summary"]["total_classes"], 600)
            
        except json.JSONDecodeError as e:
            self.fail(f"serena_codebase_analysis.json is not valid JSON: {e}")
    
    def test_bridge_api_coverage(self):
        """Test that bridge components cover all major API areas."""
        with open("serena_bridge.py", 'r') as f:
            bridge_content = f.read()
        
        with open("serena_bridge_part2.py", 'r') as f:
            bridge2_content = f.read()
        
        # Test LSP coverage
        lsp_keywords = [
            "SolidLanguageServer", "LanguageServerRequest", "DiagnosticSeverity",
            "start_language_server", "stop_language_server", "is_running"
        ]
        
        for keyword in lsp_keywords:
            found = keyword in bridge_content or keyword in bridge2_content
            self.assertTrue(found, f"LSP keyword {keyword} not found in bridge")
        
        # Test Project coverage
        project_keywords = [
            "Project", "ProjectConfig", "detect_language", "gather_source_files",
            "create_project"
        ]
        
        for keyword in project_keywords:
            found = keyword in bridge_content or keyword in bridge2_content
            self.assertTrue(found, f"Project keyword {keyword} not found in bridge")
        
        # Test Diagnostic coverage
        diagnostic_keywords = [
            "collect_diagnostics", "parse_diagnostic", "EnhancedDiagnostic",
            "severity", "message", "range"
        ]
        
        for keyword in diagnostic_keywords:
            found = keyword in bridge_content or keyword in bridge2_content
            self.assertTrue(found, f"Diagnostic keyword {keyword} not found in bridge")
    
    def test_command_line_interface(self):
        """Test that serena_analysis.py has proper CLI interface."""
        with open("serena_analysis.py", 'r') as f:
            content = f.read()
        
        # Should have argparse
        self.assertIn("argparse", content)
        self.assertIn("ArgumentParser", content)
        
        # Should have expected arguments
        expected_args = [
            "repository", "severity", "language", "timeout", 
            "max-workers", "output", "verbose"
        ]
        
        for arg in expected_args:
            self.assertIn(arg, content, f"CLI argument {arg} not found")
        
        # Should have main execution guard
        self.assertIn('if __name__ == "__main__":', content)


if __name__ == "__main__":
    print("🧪 Running Serena Bridge Structure Validation Tests...")
    unittest.main(verbosity=2)
