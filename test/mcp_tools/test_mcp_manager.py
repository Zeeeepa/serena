"""
Comprehensive Test Suite for MCP Tools Manager
Tests all MCP tools including WSL2, terminal, web search, and system operations
"""

import pytest
import asyncio
import platform
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import json
import os

from src.serena.mcp_tools.mcp_manager import (
    MCPToolsManager,
    MCPToolType,
    MCPToolConfig
)


class TestMCPToolsManager:
    """Comprehensive test suite for MCPToolsManager"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_config_dir):
        """Create MCPToolsManager instance for testing"""
        return MCPToolsManager(config_dir=temp_config_dir)
    
    def test_initialization(self, manager):
        """Test MCPToolsManager initialization"""
        assert isinstance(manager, MCPToolsManager)
        assert manager.config_dir.exists()
        assert len(manager.tools) == 8  # All MCP tool types
        
        # Verify all tool types are loaded
        expected_tools = {
            "wsl2_manager", "terminal_executor", "web_search", "file_system",
            "environment", "docker", "git", "system_info"
        }
        assert set(manager.tools.keys()) == expected_tools
    
    def test_tool_configurations(self, manager):
        """Test that all tools are properly configured"""
        for tool_name, tool_config in manager.tools.items():
            assert isinstance(tool_config, MCPToolConfig)
            assert tool_config.name
            assert tool_config.description
            assert tool_config.tool_type in MCPToolType
            assert isinstance(tool_config.enabled, bool)
            assert isinstance(tool_config.config, dict)
            assert tool_config.security_level in ["low", "medium", "high"]
            assert tool_config.timeout > 0
    
    def test_tool_security_levels(self, manager):
        """Test security level assignments"""
        # High security tools
        high_security = ["wsl2_manager", "terminal_executor", "docker"]
        for tool_name in high_security:
            assert manager.tools[tool_name].security_level == "high"
        
        # Medium security tools
        medium_security = ["file_system", "environment", "git"]
        for tool_name in medium_security:
            assert manager.tools[tool_name].security_level == "medium"
        
        # Low security tools
        low_security = ["web_search", "system_info"]
        for tool_name in low_security:
            assert manager.tools[tool_name].security_level == "low"


class TestTerminalExecutor:
    """Test terminal command execution functionality"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @patch('src.serena.mcp_tools.mcp_manager.asyncio.create_subprocess_shell')
    async def test_execute_terminal_command_success(self, mock_subprocess, manager):
        """Test successful terminal command execution"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"test output", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        result = await manager.execute_terminal_command("ls")
        
        assert result["success"] is True
        assert result["command"] == "ls"
        assert result["output"] == "test output"
        assert result["error"] == ""
        assert result["return_code"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_forbidden_command(self, manager):
        """Test execution of forbidden command"""
        result = await manager.execute_terminal_command("sudo rm -rf /")
        
        assert result["success"] is False
        assert "Command not allowed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_command_disabled_tool(self, manager):
        """Test command execution when tool is disabled"""
        manager.tools["terminal_executor"].enabled = False
        
        result = await manager.execute_terminal_command("ls")
        
        assert result["success"] is False
        assert "Terminal tool is disabled" in result["error"]
    
    @pytest.mark.asyncio
    @patch('src.serena.mcp_tools.mcp_manager.asyncio.create_subprocess_shell')
    async def test_execute_command_with_error(self, mock_subprocess, manager):
        """Test command execution with error output"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"command not found")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        result = await manager.execute_terminal_command("nonexistent_command")
        
        assert result["success"] is True  # Command executed, but failed
        assert result["return_code"] == 1
        assert result["error"] == "command not found"
    
    def test_command_safety_check(self, manager):
        """Test command safety validation"""
        # Safe commands
        assert manager._is_command_safe("ls", ["ls", "pwd"], ["rm -rf"])
        assert manager._is_command_safe("pwd", ["ls", "pwd"], ["rm -rf"])
        
        # Unsafe commands
        assert not manager._is_command_safe("rm -rf /", ["ls", "pwd"], ["rm -rf"])
        assert not manager._is_command_safe("sudo something", ["ls", "pwd"], ["sudo"])
        
        # Command not in allowed list
        assert not manager._is_command_safe("unknown_cmd", ["ls", "pwd"], [])


class TestWebSearch:
    """Test web search functionality"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_web_search_success(self, mock_get, manager):
        """Test successful web search"""
        # Mock DuckDuckGo API response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "Abstract": "Test abstract",
            "Heading": "Test heading",
            "AbstractURL": "https://example.com",
            "RelatedTopics": [
                {
                    "Text": "Related topic 1",
                    "FirstURL": "https://example1.com"
                },
                {
                    "Text": "Related topic 2", 
                    "FirstURL": "https://example2.com"
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await manager.web_search("test query")
        
        assert result["success"] is True
        assert result["query"] == "test query"
        assert len(result["results"]) >= 1
        assert result["results"][0]["title"] == "Test heading"
        assert result["results"][0]["snippet"] == "Test abstract"
    
    @pytest.mark.asyncio
    async def test_web_search_disabled(self, manager):
        """Test web search when disabled"""
        manager.tools["web_search"].enabled = False
        
        result = await manager.web_search("test query")
        
        assert result["success"] is False
        assert "Web search tool is disabled" in result["error"]
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_web_search_network_error(self, mock_get, manager):
        """Test web search with network error"""
        mock_get.side_effect = Exception("Network error")
        
        result = await manager.web_search("test query")
        
        assert result["success"] is False
        assert "Network error" in result["error"]


class TestFileSystem:
    """Test file system operations"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file content")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_get_file_content_success(self, manager, temp_file):
        """Test successful file content retrieval"""
        result = await manager.get_file_content(temp_file)
        
        assert result["success"] is True
        assert result["content"] == "Test file content"
        assert result["file_path"] == temp_file
        assert result["extension"] == ".txt"
    
    @pytest.mark.asyncio
    async def test_get_file_content_nonexistent(self, manager):
        """Test file content retrieval for nonexistent file"""
        result = await manager.get_file_content("/nonexistent/file.txt")
        
        assert result["success"] is False
        assert "File not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_file_content_forbidden_path(self, manager):
        """Test file access to forbidden path"""
        result = await manager.get_file_content("/etc/passwd")
        
        assert result["success"] is False
        assert "Path not allowed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_file_content_forbidden_extension(self, manager):
        """Test file access with forbidden extension"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            temp_path = f.name
        
        try:
            result = await manager.get_file_content(temp_path)
            assert result["success"] is False
            assert "File extension not allowed" in result["error"]
        finally:
            os.unlink(temp_path)
    
    def test_path_safety_check(self, manager):
        """Test path safety validation"""
        allowed_paths = ["./", "/tmp/"]
        forbidden_paths = ["/etc/", "/root/"]
        
        # Safe paths
        assert manager._is_path_safe("./test.txt", allowed_paths, forbidden_paths)
        assert manager._is_path_safe("/tmp/test.txt", allowed_paths, forbidden_paths)
        
        # Unsafe paths
        assert not manager._is_path_safe("/etc/passwd", allowed_paths, forbidden_paths)
        assert not manager._is_path_safe("/root/secret", allowed_paths, forbidden_paths)
        
        # Path not in allowed list
        assert not manager._is_path_safe("/home/user/file", allowed_paths, forbidden_paths)


class TestEnvironmentManager:
    """Test environment information retrieval"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    async def test_get_environment_info_success(self, manager):
        """Test successful environment info retrieval"""
        result = await manager.get_environment_info()
        
        assert result["success"] is True
        assert "environment_variables" in result
        assert "system_info" in result
        
        # Check system info fields
        system_info = result["system_info"]
        assert "platform" in system_info
        assert "architecture" in system_info
        assert "python_version" in system_info
    
    @pytest.mark.asyncio
    async def test_get_environment_info_disabled(self, manager):
        """Test environment info when tool is disabled"""
        manager.tools["environment"].enabled = False
        
        result = await manager.get_environment_info()
        
        assert result["success"] is False
        assert "Environment tool is disabled" in result["error"]


class TestDockerManager:
    """Test Docker operations"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @patch('shutil.which')
    @patch('src.serena.mcp_tools.mcp_manager.MCPToolsManager._execute_command')
    async def test_get_docker_info_success(self, mock_execute, mock_which, manager):
        """Test successful Docker info retrieval"""
        mock_which.return_value = "/usr/bin/docker"
        mock_execute.side_effect = [
            {"return_code": 0, "output": '{"Names":"test-container"}\n{"Names":"test-container2"}'},
            {"return_code": 0, "output": '{"Repository":"test-image"}\n{"Repository":"test-image2"}'}
        ]
        
        result = await manager.get_docker_info()
        
        assert result["success"] is True
        assert result["docker_available"] is True
        assert len(result["containers"]) == 2
        assert len(result["images"]) == 2
    
    @pytest.mark.asyncio
    @patch('shutil.which')
    async def test_get_docker_info_not_available(self, mock_which, manager):
        """Test Docker info when Docker is not available"""
        mock_which.return_value = None
        
        result = await manager.get_docker_info()
        
        assert result["success"] is False
        assert result["docker_available"] is False
        assert "Docker not found" in result["error"]


class TestGitOperations:
    """Test Git repository operations"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create temporary git repository for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()
            yield temp_dir
    
    @pytest.mark.asyncio
    @patch('src.serena.mcp_tools.mcp_manager.MCPToolsManager._execute_command')
    async def test_get_git_info_success(self, mock_execute, manager, temp_git_repo):
        """Test successful Git info retrieval"""
        mock_execute.side_effect = [
            {"return_code": 0, "output": "M file1.py\nA file2.py"},
            {"return_code": 0, "output": "main"},
            {"return_code": 0, "output": "abc123 Initial commit\ndef456 Second commit"},
            {"return_code": 0, "output": "origin https://github.com/test/repo.git (fetch)"}
        ]
        
        result = await manager.get_git_info(temp_git_repo)
        
        assert result["success"] is True
        assert result["current_branch"] == "main"
        assert len(result["recent_commits"]) == 2
        assert len(result["remotes"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_git_info_not_git_repo(self, manager):
        """Test Git info on non-git directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await manager.get_git_info(temp_dir)
            
            assert result["success"] is False
            assert "Not a git repository" in result["error"]


class TestSystemMetrics:
    """Test system metrics collection"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @patch('src.serena.mcp_tools.mcp_manager.MCPToolsManager._execute_command')
    async def test_get_system_metrics_success(self, mock_execute, manager):
        """Test successful system metrics collection"""
        mock_execute.side_effect = [
            {"return_code": 0, "output": "25.5"},  # CPU
            {"return_code": 0, "output": "60.2,8589934592,3435973836"},  # Memory
            {"return_code": 0, "output": "45.8,1000000000,542000000"}  # Disk
        ]
        
        result = await manager.get_system_metrics()
        
        assert result["success"] is True
        assert "metrics" in result
        assert "timestamp" in result
        
        metrics = result["metrics"]
        assert "cpu_usage_percent" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_disabled(self, manager):
        """Test system metrics when tool is disabled"""
        manager.tools["system_info"].enabled = False
        
        result = await manager.get_system_metrics()
        
        assert result["success"] is False
        assert "System info tool is disabled" in result["error"]


@pytest.mark.skipif(platform.system() != "Windows", reason="WSL2 tests require Windows")
class TestWSL2Manager:
    """Test WSL2 operations (Windows only)"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @patch('src.serena.mcp_tools.mcp_manager.MCPToolsManager._execute_command')
    async def test_execute_wsl2_command_success(self, mock_execute, manager):
        """Test successful WSL2 command execution"""
        mock_execute.return_value = {
            "output": "Python 3.9.7",
            "error": "",
            "return_code": 0
        }
        
        result = await manager.execute_wsl2_command("python3 --version")
        
        assert result["success"] is True
        assert result["command"] == "python3 --version"
        assert result["output"] == "Python 3.9.7"
        assert result["return_code"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_wsl2_forbidden_command(self, manager):
        """Test WSL2 execution of forbidden command"""
        result = await manager.execute_wsl2_command("sudo rm -rf /")
        
        assert result["success"] is False
        assert "Command not allowed" in result["error"]


class TestHealthCheck:
    """Test MCP tools health checking"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    async def test_health_check_all_enabled(self, manager):
        """Test health check with all tools enabled"""
        health = await manager.health_check()
        
        assert health["total_tools"] == 8
        assert health["enabled_tools"] == 8
        assert health["disabled_tools"] == 0
        assert health["overall_healthy"] is True
        assert len(health["tools"]) == 8
    
    @pytest.mark.asyncio
    async def test_health_check_some_disabled(self, manager):
        """Test health check with some tools disabled"""
        manager.tools["web_search"].enabled = False
        manager.tools["docker"].enabled = False
        
        health = await manager.health_check()
        
        assert health["total_tools"] == 8
        assert health["enabled_tools"] == 6
        assert health["disabled_tools"] == 2
        assert health["overall_healthy"] is True


class TestToolManagement:
    """Test tool enable/disable functionality"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    def test_enable_tool(self, manager):
        """Test enabling a tool"""
        manager.tools["web_search"].enabled = False
        
        result = manager.enable_tool("web_search")
        
        assert result is True
        assert manager.tools["web_search"].enabled is True
    
    def test_enable_nonexistent_tool(self, manager):
        """Test enabling non-existent tool"""
        result = manager.enable_tool("nonexistent_tool")
        
        assert result is False
    
    def test_disable_tool(self, manager):
        """Test disabling a tool"""
        result = manager.disable_tool("web_search")
        
        assert result is True
        assert manager.tools["web_search"].enabled is False
    
    def test_disable_nonexistent_tool(self, manager):
        """Test disabling non-existent tool"""
        result = manager.disable_tool("nonexistent_tool")
        
        assert result is False
    
    def test_get_tool_config(self, manager):
        """Test getting tool configuration"""
        config = manager.get_tool_config("web_search")
        
        assert config is not None
        assert isinstance(config, MCPToolConfig)
        assert config.tool_type == MCPToolType.WEB_SEARCH
    
    def test_get_nonexistent_tool_config(self, manager):
        """Test getting configuration for non-existent tool"""
        config = manager.get_tool_config("nonexistent_tool")
        
        assert config is None


class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.fixture
    def manager(self):
        return MCPToolsManager()
    
    def test_parse_size(self, manager):
        """Test size string parsing"""
        assert manager._parse_size("1024") == 1024
        assert manager._parse_size("1KB") == 1024
        assert manager._parse_size("1MB") == 1024 * 1024
        assert manager._parse_size("1GB") == 1024 * 1024 * 1024
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_shell')
    async def test_execute_command_timeout(self, mock_subprocess, manager):
        """Test command execution timeout"""
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process
        
        with pytest.raises(ValueError, match="timed out"):
            await manager._execute_command("sleep 100", timeout=1)


@pytest.mark.integration
class TestMCPToolsIntegration:
    """Integration tests for MCP tools with real system operations"""
    
    @pytest.fixture
    def real_manager(self):
        """Create manager for real system testing"""
        return MCPToolsManager()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration"),
        reason="Integration tests require --integration flag"
    )
    async def test_real_terminal_execution(self, real_manager):
        """Test real terminal command execution"""
        result = await real_manager.execute_terminal_command("echo 'Hello World'")
        
        assert result["success"] is True
        assert "Hello World" in result["output"]
        assert result["return_code"] == 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration"),
        reason="Integration tests require --integration flag"
    )
    async def test_real_environment_info(self, real_manager):
        """Test real environment information retrieval"""
        result = await real_manager.get_environment_info()
        
        assert result["success"] is True
        assert "environment_variables" in result
        assert "system_info" in result
        assert result["system_info"]["platform"] == platform.system()


@pytest.mark.performance
class TestMCPToolsPerformance:
    """Performance tests for MCP tools"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self):
        """Test concurrent tool operations performance"""
        import time
        
        manager = MCPToolsManager()
        
        start_time = time.time()
        
        # Execute multiple operations concurrently
        tasks = [
            manager.get_environment_info(),
            manager.get_system_metrics(),
            manager.health_check()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(results) == 3
        assert duration < 5.0  # Should complete quickly
        
        # Check that all operations succeeded (or failed gracefully)
        for result in results:
            if isinstance(result, dict):
                assert "success" in result


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src.serena.mcp_tools.mcp_manager",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
