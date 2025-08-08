#!/usr/bin/env python3
"""
Comprehensive Test Suite for Serena Bridge and Analysis

This test suite validates all edge cases, positive and negative scenarios,
and all analysis result types for the Serena bridge implementation.

Test Categories:
1. Bridge Component Tests (LSP, Project, Diagnostic)
2. Integration Tests (Full analysis workflows)
3. Edge Case Tests (Error conditions, malformed data)
4. Performance Tests (Large codebases, timeouts)
5. Compatibility Tests (Different languages, configurations)
"""

import unittest
import tempfile
import shutil
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Import the components to test
try:
    from serena_bridge import *
    from serena_bridge_part2 import *
    from serena_analysis import SerenaAnalysisInterface
except ImportError as e:
    print(f"❌ Failed to import test targets: {e}")
    print("Please ensure all bridge components are available")
    exit(1)


class TestSerenaLSPBridge(unittest.TestCase):
    """Test the LSP Bridge component with all edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bridge = SerenaLSPBridge(verbose=True, timeout=60)
        self.mock_project = Mock()
        self.mock_language_server = Mock()
    
    def test_initialization(self):
        """Test LSP bridge initialization."""
        # Positive case
        bridge = SerenaLSPBridge(verbose=True, timeout=120)
        self.assertEqual(bridge.timeout, 120)
        self.assertTrue(bridge.verbose)
        self.assertEqual(bridge.server_info.server_status, "not_started")
        
        # Edge case: minimal timeout
        bridge_min = SerenaLSPBridge(timeout=1)
        self.assertEqual(bridge_min.timeout, 1)
    
    @patch('serena_bridge.SolidLanguageServer')
    def test_create_language_server_success(self, mock_server_class):
        """Test successful language server creation."""
        # Setup mocks
        mock_server = Mock()
        self.mock_project.create_language_server.return_value = mock_server
        self.mock_project.language = Language.PYTHON
        
        # Test creation
        result = self.bridge.create_language_server(self.mock_project)
        
        self.assertEqual(result, mock_server)
        self.assertEqual(self.bridge.server_info.server_status, "created")
        self.assertEqual(self.bridge.server_info.language, Language.PYTHON)
    
    def test_create_language_server_failure(self):
        """Test language server creation failure."""
        # Setup failing project
        self.mock_project.create_language_server.side_effect = Exception("Creation failed")
        
        # Test failure handling
        with self.assertRaises(SolidLSPException):
            self.bridge.create_language_server(self.mock_project)
    
    def test_server_lifecycle_management(self):
        """Test complete server lifecycle."""
        # Mock server
        mock_server = Mock()
        mock_server.start.return_value = mock_server
        mock_server.is_running.return_value = True
        
        self.bridge.language_server = mock_server
        
        # Test start
        result = self.bridge.start_language_server()
        self.assertEqual(result, mock_server)
        mock_server.start.assert_called_once()
        
        # Test stop
        self.bridge.stop_language_server()
        mock_server.stop.assert_called_once()
    
    def test_server_termination_handling(self):
        """Test handling of server termination."""
        mock_server = Mock()
        mock_server.start.return_value = mock_server
        mock_server.is_running.side_effect = [False]  # Server not running after start
        
        self.bridge.language_server = mock_server
        
        with self.assertRaises(SolidLSPException):
            self.bridge.start_language_server()
    
    def test_get_server_status(self):
        """Test server status reporting."""
        status = self.bridge.get_server_status()
        
        expected_keys = [
            "status", "initialization_time", "message_count", 
            "error_count", "is_terminated", "language", 
            "last_error", "is_running"
        ]
        
        for key in expected_keys:
            self.assertIn(key, status)


class TestSerenaProjectBridge(unittest.TestCase):
    """Test the Project Bridge component with all scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bridge = SerenaProjectBridge(verbose=True)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test project structure
        self.test_project_path = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project_path)
        
        # Create test files for different languages
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self):
        """Create test files for language detection."""
        test_files = {
            "main.py": "print('Hello Python')",
            "app.js": "console.log('Hello JavaScript');",
            "index.ts": "console.log('Hello TypeScript');",
            "Main.java": "public class Main { }",
            "program.cs": "using System;",
            "main.cpp": "#include <iostream>",
            "main.rs": "fn main() { }",
            "main.go": "package main",
            "index.php": "<?php echo 'Hello'; ?>",
            "app.rb": "puts 'Hello Ruby'",
            "main.kt": "fun main() { }",
            "main.dart": "void main() { }",
            "requirements.txt": "flask==2.0.0",
            "package.json": '{"name": "test"}',
            "Cargo.toml": "[package]",
            "pom.xml": "<project></project>",
            ".gitignore": "*.pyc\nnode_modules/"
        }
        
        for filename, content in test_files.items():
            file_path = os.path.join(self.test_project_path, filename)
            with open(file_path, 'w') as f:
                f.write(content)
    
    def test_language_detection_python(self):
        """Test Python language detection."""
        # Create Python-heavy project
        py_project = os.path.join(self.temp_dir, "py_project")
        os.makedirs(py_project)
        
        for i in range(5):
            with open(os.path.join(py_project, f"module{i}.py"), 'w') as f:
                f.write(f"# Module {i}")
        
        detected = self.bridge.detect_language(py_project)
        self.assertEqual(detected, Language.PYTHON)
    
    def test_language_detection_javascript(self):
        """Test JavaScript language detection."""
        js_project = os.path.join(self.temp_dir, "js_project")
        os.makedirs(js_project)
        
        # Create JS files and package.json
        with open(os.path.join(js_project, "package.json"), 'w') as f:
            f.write('{"name": "test-js"}')
        
        for i in range(3):
            with open(os.path.join(js_project, f"script{i}.js"), 'w') as f:
                f.write(f"console.log('Script {i}');")
        
        detected = self.bridge.detect_language(js_project)
        self.assertEqual(detected, Language.JAVASCRIPT)
    
    def test_language_detection_mixed_project(self):
        """Test language detection in mixed-language project."""
        detected = self.bridge.detect_language(self.test_project_path)
        # Should detect the language with highest score
        self.assertIsInstance(detected, Language)
    
    def test_language_detection_empty_project(self):
        """Test language detection in empty project."""
        empty_project = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_project)
        
        detected = self.bridge.detect_language(empty_project)
        self.assertEqual(detected, Language.PYTHON)  # Default fallback
    
    def test_language_detection_nonexistent_path(self):
        """Test language detection with nonexistent path."""
        with self.assertRaises(FileNotFoundError):
            self.bridge.detect_language("/nonexistent/path")
    
    @patch('serena_bridge.Project')
    @patch('serena_bridge.ProjectConfig')
    def test_create_project_success(self, mock_config_class, mock_project_class):
        """Test successful project creation."""
        mock_project = Mock()
        mock_project_class.return_value = mock_project
        
        result = self.bridge.create_project(
            self.test_project_path, 
            Language.PYTHON, 
            "test_project"
        )
        
        self.assertEqual(result, mock_project)
        mock_project_class.assert_called_once()
        mock_config_class.assert_called_once()
    
    def test_create_project_nonexistent_path(self):
        """Test project creation with nonexistent path."""
        with self.assertRaises(FileNotFoundError):
            self.bridge.create_project("/nonexistent/path")
    
    def test_create_project_file_instead_of_directory(self):
        """Test project creation with file path instead of directory."""
        file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(file_path, 'w') as f:
            f.write("test")
        
        with self.assertRaises(ValueError):
            self.bridge.create_project(file_path)
    
    def test_is_git_url(self):
        """Test Git URL detection."""
        # Positive cases
        self.assertTrue(self.bridge.is_git_url("https://github.com/user/repo.git"))
        self.assertTrue(self.bridge.is_git_url("git@github.com:user/repo.git"))
        self.assertTrue(self.bridge.is_git_url("http://example.com/repo.git"))
        
        # Negative cases
        self.assertFalse(self.bridge.is_git_url("/local/path"))
        self.assertFalse(self.bridge.is_git_url("relative/path"))
        self.assertFalse(self.bridge.is_git_url(""))
    
    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_run):
        """Test successful repository cloning."""
        mock_run.return_value.returncode = 0
        
        result = self.bridge.clone_repository("https://github.com/test/repo.git")
        
        self.assertTrue(os.path.exists(result))
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_run):
        """Test repository cloning failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Clone failed"
        
        with self.assertRaises(RuntimeError):
            self.bridge.clone_repository("https://github.com/test/repo.git")
    
    @patch('subprocess.run')
    def test_clone_repository_timeout(self, mock_run):
        """Test repository cloning timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 300)
        
        with self.assertRaises(RuntimeError):
            self.bridge.clone_repository("https://github.com/test/repo.git")


class TestSerenaDiagnosticBridge(unittest.TestCase):
    """Test the Diagnostic Bridge component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bridge = SerenaDiagnosticBridge(verbose=True)
        self.mock_language_server = Mock()
    
    def test_collect_diagnostics_success(self):
        """Test successful diagnostic collection."""
        # Mock LSP response
        mock_response = {
            "items": [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 10}
                    },
                    "severity": 1,  # Error
                    "message": "Test error message",
                    "code": "E001",
                    "source": "test-lsp"
                }
            ]
        }
        
        self.mock_language_server.request_text_document_diagnostics.return_value = mock_response
        
        diagnostics, error = self.bridge.collect_diagnostics_from_file(
            self.mock_language_server, "test.py"
        )
        
        self.assertIsNone(error)
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].severity, "ERROR")
        self.assertEqual(diagnostics[0].message, "Test error message")
        self.assertEqual(diagnostics[0].line, 1)  # Converted from 0-based
    
    def test_collect_diagnostics_empty_response(self):
        """Test diagnostic collection with empty response."""
        self.mock_language_server.request_text_document_diagnostics.return_value = None
        
        diagnostics, error = self.bridge.collect_diagnostics_from_file(
            self.mock_language_server, "test.py"
        )
        
        self.assertIsNone(error)
        self.assertEqual(len(diagnostics), 0)
    
    def test_collect_diagnostics_lsp_exception(self):
        """Test diagnostic collection with LSP exception."""
        mock_exception = SolidLSPException("LSP server error")
        mock_exception.is_language_server_terminated = Mock(return_value=False)
        
        self.mock_language_server.request_text_document_diagnostics.side_effect = mock_exception
        
        diagnostics, error = self.bridge.collect_diagnostics_from_file(
            self.mock_language_server, "test.py"
        )
        
        self.assertIsNotNone(error)
        self.assertEqual(len(diagnostics), 0)
        self.assertIn("LSP Exception", error)
    
    def test_collect_diagnostics_server_terminated(self):
        """Test diagnostic collection with terminated server."""
        mock_exception = SolidLSPException("Server terminated")
        mock_exception.is_language_server_terminated = Mock(return_value=True)
        
        self.mock_language_server.request_text_document_diagnostics.side_effect = mock_exception
        
        diagnostics, error = self.bridge.collect_diagnostics_from_file(
            self.mock_language_server, "test.py"
        )
        
        self.assertIsNotNone(error)
        self.assertIn("Server terminated", error)
    
    def test_parse_diagnostic_all_severities(self):
        """Test parsing diagnostics with all severity levels."""
        severities = [
            (1, "ERROR"),
            (2, "WARNING"),
            (3, "INFO"),
            (4, "HINT")
        ]
        
        for severity_value, expected_severity in severities:
            diag_data = {
                "range": {
                    "start": {"line": 5, "character": 10},
                    "end": {"line": 5, "character": 20}
                },
                "severity": severity_value,
                "message": f"Test {expected_severity} message",
                "code": f"{expected_severity[0]}001"
            }
            
            result = self.bridge._parse_diagnostic(diag_data, "test.py")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.severity, expected_severity)
            self.assertEqual(result.line, 6)  # 0-based to 1-based conversion
            self.assertEqual(result.column, 11)
    
    def test_parse_diagnostic_with_tags(self):
        """Test parsing diagnostic with tags."""
        diag_data = {
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 5}},
            "severity": 2,
            "message": "Deprecated function",
            "tags": [DiagnosticTag.Deprecated, DiagnosticTag.Unnecessary]
        }
        
        result = self.bridge._parse_diagnostic(diag_data, "test.py")
        
        self.assertIn("deprecated", result.tags)
        self.assertIn("unnecessary", result.tags)
    
    def test_collect_diagnostics_batch(self):
        """Test batch diagnostic collection."""
        # Mock responses for multiple files
        def mock_collect(server, file_path, severity_filter=None):
            if "error" in file_path:
                return [], "Mock error"
            else:
                return [Mock(severity="ERROR", file_path=file_path)], None
        
        with patch.object(self.bridge, 'collect_diagnostics_from_file', side_effect=mock_collect):
            files = ["file1.py", "file2.py", "error_file.py"]
            
            all_diagnostics, error_map = self.bridge.collect_diagnostics_batch(
                self.mock_language_server, files, max_workers=2
            )
            
            self.assertEqual(len(all_diagnostics), 2)  # 2 successful files
            self.assertEqual(len(error_map), 1)  # 1 error file
            self.assertIn("error_file.py", error_map)


class TestSerenaComprehensiveAnalyzer(unittest.TestCase):
    """Test the comprehensive analyzer with integration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_repo = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.test_repo)
        
        # Create a simple Python project
        with open(os.path.join(self.test_repo, "main.py"), 'w') as f:
            f.write("print('Hello World')")
        
        with open(os.path.join(self.test_repo, "requirements.txt"), 'w') as f:
            f.write("requests==2.25.1")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('serena_bridge_part2.SerenaLSPBridge')
    @patch('serena_bridge_part2.SerenaProjectBridge')
    @patch('serena_bridge_part2.SerenaDiagnosticBridge')
    def test_analyze_repository_success(self, mock_diag_bridge, mock_proj_bridge, mock_lsp_bridge):
        """Test successful repository analysis."""
        # Setup mocks
        mock_project = Mock()
        mock_project.language.value = "python"
        mock_project.project_config.project_name = "test_repo"
        mock_project.project_config.ignored_paths = []
        
        mock_proj_bridge_instance = mock_proj_bridge.return_value
        mock_proj_bridge_instance.is_git_url.return_value = False
        mock_proj_bridge_instance.create_project.return_value = mock_project
        mock_proj_bridge_instance.gather_source_files.return_value = ["main.py"]
        
        mock_lsp_bridge_instance = mock_lsp_bridge.return_value
        mock_lsp_bridge_instance.create_language_server.return_value = Mock()
        mock_lsp_bridge_instance.start_language_server.return_value = Mock()
        mock_lsp_bridge_instance.get_server_status.return_value = {"status": "ready"}
        
        mock_diag_bridge_instance = mock_diag_bridge.return_value
        mock_diag_bridge_instance.collect_diagnostics_batch.return_value = ([], {})
        
        # Test analysis
        analyzer = SerenaComprehensiveAnalyzer(verbose=False, timeout=60)
        result = analyzer.analyze_repository(self.test_repo, output_format="json")
        
        self.assertIsInstance(result, dict)
        self.assertIn("total_files", result)
        self.assertIn("diagnostics", result)
    
    def test_analyze_nonexistent_repository(self):
        """Test analysis of nonexistent repository."""
        analyzer = SerenaComprehensiveAnalyzer(verbose=False)
        
        result = analyzer.analyze_repository("/nonexistent/path", output_format="json")
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
    
    def test_context_manager_cleanup(self):
        """Test proper cleanup in context manager."""
        with patch('serena_bridge_part2.SerenaLSPBridge') as mock_lsp:
            mock_lsp_instance = mock_lsp.return_value
            
            with SerenaComprehensiveAnalyzer() as analyzer:
                pass  # Just test cleanup
            
            mock_lsp_instance.stop_language_server.assert_called_once()


class TestSerenaAnalysisInterface(unittest.TestCase):
    """Test the high-level analysis interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.interface = SerenaAnalysisInterface(verbose=False)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_input_validation_empty_repo(self):
        """Test validation with empty repository path."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs("", None, None, 60, 4, "text")
    
    def test_input_validation_invalid_severity(self):
        """Test validation with invalid severity."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs(".", "INVALID", None, 60, 4, "text")
    
    def test_input_validation_invalid_language(self):
        """Test validation with invalid language."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs(".", None, "invalid_lang", 60, 4, "text")
    
    def test_input_validation_invalid_timeout(self):
        """Test validation with invalid timeout."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs(".", None, None, -1, 4, "text")
    
    def test_input_validation_invalid_workers(self):
        """Test validation with invalid worker count."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs(".", None, None, 60, 0, "text")
    
    def test_input_validation_invalid_output_format(self):
        """Test validation with invalid output format."""
        with self.assertRaises(ValueError):
            self.interface._validate_inputs(".", None, None, 60, 4, "invalid")
    
    @patch('serena_analysis.SerenaComprehensiveAnalyzer')
    def test_quick_analysis(self, mock_analyzer_class):
        """Test quick analysis mode."""
        mock_analyzer = Mock()
        mock_analyzer.__enter__ = Mock(return_value=mock_analyzer)
        mock_analyzer.__exit__ = Mock(return_value=None)
        mock_analyzer.analyze_repository.return_value = "Quick result"
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.interface.quick_analysis(".")
        
        self.assertTrue(result["success"])
        mock_analyzer.analyze_repository.assert_called_once()
        
        # Verify quick analysis parameters
        call_args = mock_analyzer.analyze_repository.call_args
        self.assertEqual(call_args.kwargs["severity_filter"], "ERROR")
        self.assertEqual(call_args.kwargs["output_format"], "json")
    
    @patch('serena_analysis.SerenaComprehensiveAnalyzer')
    def test_detailed_analysis(self, mock_analyzer_class):
        """Test detailed analysis mode."""
        mock_analyzer = Mock()
        mock_analyzer.__enter__ = Mock(return_value=mock_analyzer)
        mock_analyzer.__exit__ = Mock(return_value=None)
        mock_analyzer.analyze_repository.return_value = "Detailed result"
        mock_analyzer_class.return_value = mock_analyzer
        
        result = self.interface.detailed_analysis(".", language_override="python")
        
        self.assertTrue(result["success"])
        
        # Verify detailed analysis parameters
        call_args = mock_analyzer.analyze_repository.call_args
        self.assertEqual(call_args.kwargs["language_override"], "python")
        self.assertEqual(call_args.kwargs["timeout"], 900)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios."""
    
    def test_malformed_diagnostic_data(self):
        """Test handling of malformed diagnostic data."""
        bridge = SerenaDiagnosticBridge()
        
        # Test with missing required fields
        malformed_data = {"message": "Error without range"}
        
        result = bridge._parse_diagnostic(malformed_data, "test.py")
        
        # Should handle gracefully and return None or default values
        self.assertIsNotNone(result)
        self.assertEqual(result.line, 1)  # Default line
        self.assertEqual(result.column, 1)  # Default column
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters in diagnostics."""
        bridge = SerenaDiagnosticBridge()
        
        unicode_data = {
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 5}},
            "severity": 1,
            "message": "Unicode error: 测试错误 🚀",
            "code": "U001"
        }
        
        result = bridge._parse_diagnostic(unicode_data, "测试.py")
        
        self.assertIsNotNone(result)
        self.assertIn("测试错误", result.message)
        self.assertIn("🚀", result.message)
    
    def test_very_large_diagnostic_message(self):
        """Test handling of very large diagnostic messages."""
        bridge = SerenaDiagnosticBridge()
        
        large_message = "Error: " + "x" * 10000  # Very long message
        
        large_data = {
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 5}},
            "severity": 1,
            "message": large_message
        }
        
        result = bridge._parse_diagnostic(large_data, "test.py")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.message), len(large_message))
    
    def test_concurrent_access(self):
        """Test thread safety of bridge components."""
        import threading
        
        bridge = SerenaLSPBridge()
        results = []
        errors = []
        
        def test_status():
            try:
                status = bridge.get_server_status()
                results.append(status)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=test_status) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors and all results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)


class TestPerformanceAndScalability(unittest.TestCase):
    """Test performance and scalability scenarios."""
    
    def test_large_file_list_processing(self):
        """Test processing of large file lists."""
        bridge = SerenaDiagnosticBridge()
        mock_server = Mock()
        
        # Create large file list
        large_file_list = [f"file_{i}.py" for i in range(1000)]
        
        # Mock the single file collection to return quickly
        def quick_collect(server, file_path, severity_filter=None):
            return [], None
        
        with patch.object(bridge, 'collect_diagnostics_from_file', side_effect=quick_collect):
            start_time = time.time()
            
            diagnostics, errors = bridge.collect_diagnostics_batch(
                mock_server, large_file_list, max_workers=8
            )
            
            end_time = time.time()
            
            # Should complete in reasonable time (less than 30 seconds for mocked calls)
            self.assertLess(end_time - start_time, 30)
            self.assertEqual(len(errors), 0)
    
    def test_memory_usage_with_many_diagnostics(self):
        """Test memory usage with large numbers of diagnostics."""
        # Create many diagnostic objects
        diagnostics = []
        
        for i in range(10000):
            diag = EnhancedDiagnostic(
                file_path=f"file_{i % 100}.py",
                line=i % 1000,
                column=i % 80,
                severity="ERROR",
                message=f"Error message {i}",
                code=f"E{i:04d}"
            )
            diagnostics.append(diag)
        
        # Test serialization
        results = AnalysisResults(
            total_files=100,
            processed_files=100,
            failed_files=0,
            total_diagnostics=len(diagnostics),
            diagnostics_by_severity={"ERROR": len(diagnostics)},
            diagnostics_by_file={},
            diagnostics=diagnostics,
            performance_stats={},
            language_detected="python",
            repository_path="/test",
            analysis_timestamp="2024-01-01 00:00:00"
        )
        
        # Should be able to serialize without memory issues
        json_data = json.dumps(results.to_dict(), default=str)
        self.assertIsInstance(json_data, str)
        self.assertGreater(len(json_data), 1000)


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
