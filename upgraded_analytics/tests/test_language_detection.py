"""
Tests for language detection functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.language_detection import (
    get_file_language, should_ignore_path, detect_repository_languages,
    get_primary_language, get_supported_languages_for_solidlsp
)


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_get_file_language(self):
        """Test file language detection."""
        assert get_file_language("test.py") == "python"
        assert get_file_language("test.js") == "javascript"
        assert get_file_language("test.ts") == "typescript"
        assert get_file_language("test.java") == "java"
        assert get_file_language("test.cs") == "csharp"
        assert get_file_language("test.go") == "go"
        assert get_file_language("test.rs") == "rust"
        assert get_file_language("test.php") == "php"
        assert get_file_language("test.unknown") == "unknown"
        assert get_file_language("Dockerfile") == "dockerfile"
        assert get_file_language("Makefile") == "makefile"
    
    def test_should_ignore_path(self):
        """Test path ignoring logic."""
        # Should ignore
        assert should_ignore_path(".git/config")
        assert should_ignore_path("node_modules/package/index.js")
        assert should_ignore_path("__pycache__/module.pyc")
        assert should_ignore_path(".DS_Store")
        assert should_ignore_path("build/output.jar")
        
        # Should not ignore
        assert not should_ignore_path("src/main.py")
        assert not should_ignore_path("README.md")
        assert not should_ignore_path("package.json")
    
    def test_detect_repository_languages(self):
        """Test repository language detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "main.py").write_text("print('hello')\n" * 10)
            (Path(temp_dir) / "app.js").write_text("console.log('hello');\n" * 5)
            (Path(temp_dir) / "README.md").write_text("# Test\n")
            
            # Create subdirectory
            sub_dir = Path(temp_dir) / "src"
            sub_dir.mkdir()
            (sub_dir / "utils.py").write_text("def helper():\n    pass\n" * 3)
            
            languages = detect_repository_languages(temp_dir)
            
            assert "python" in languages
            assert "javascript" in languages
            assert languages["python"]["files"] == 2
            assert languages["javascript"]["files"] == 1
            assert languages["python"]["lines"] > languages["javascript"]["lines"]
    
    def test_get_primary_language(self):
        """Test primary language detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python files (more lines)
            (Path(temp_dir) / "main.py").write_text("print('hello')\n" * 20)
            (Path(temp_dir) / "utils.py").write_text("def helper():\n    pass\n" * 10)
            
            # Create JavaScript file (fewer lines)
            (Path(temp_dir) / "app.js").write_text("console.log('hello');\n" * 5)
            
            primary = get_primary_language(temp_dir)
            assert primary == "python"
    
    def test_get_supported_languages_for_solidlsp(self):
        """Test supported languages list."""
        supported = get_supported_languages_for_solidlsp()
        
        assert "python" in supported
        assert "typescript" in supported
        assert "java" in supported
        assert "csharp" in supported
        assert "go" in supported
        assert "rust" in supported
        
        # Should be a reasonable number of languages
        assert len(supported) >= 8

