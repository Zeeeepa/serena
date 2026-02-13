"""
Test configuration and utilities for comprehensive Serena Orchestrator testing
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG if os.getenv("TESTING") else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def pytest_configure(config):
    """Configure pytest with custom settings for orchestrator tests"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require external services)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests (may take longer)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (may take more than 10 seconds)"
    )
    config.addinivalue_line(
        "markers", "network: Tests requiring network access"
    )
    config.addinivalue_line(
        "markers", "api: Tests requiring API keys"
    )
    config.addinivalue_line(
        "markers", "system: Tests requiring system resources"
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_agno():
    """Create a mock Agno instance for testing"""
    mock = Mock()
    mock.run = AsyncMock(return_value="Mock Agno response")
    mock.model = "gemini-1.5-pro"
    mock.temperature = 0.7
    mock.max_tokens = 4096
    return mock


@pytest.fixture
def sample_config():
    """Provide sample configuration for testing"""
    return {
        "agent": {
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30
        },
        "mcp_tools": {
            "terminal": {
                "enabled": True,
                "timeout": 10,
                "allowed_commands": ["ls", "pwd", "echo"]
            },
            "web_search": {
                "enabled": True,
                "timeout": 15,
                "max_results": 10
            }
        },
        "monitoring": {
            "enabled": True,
            "interval": 60,
            "retention_hours": 24
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Set Gemini API key if provided
    if os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    
    # Ensure we don't accidentally use production services
    if "PRODUCTION" in os.environ:
        del os.environ["PRODUCTION"]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_health_check():
    """Create a mock health check result"""
    try:
        from src.serena.monitoring.health_monitor import HealthResult, HealthStatus
        from datetime import datetime
        
        return HealthResult(
            check_name="Mock Health Check",
            status=HealthStatus.HEALTHY,
            message="Mock health check passed",
            timestamp=datetime.now(),
            metrics={"test_metric": 100},
            duration_ms=50
        )
    except ImportError:
        # Return a simple mock if imports fail
        return {
            "check_name": "Mock Health Check",
            "status": "healthy",
            "message": "Mock health check passed",
            "metrics": {"test_metric": 100}
        }


@pytest.fixture
def mock_system_metrics():
    """Create mock system metrics"""
    try:
        from src.serena.monitoring.health_monitor import SystemMetrics
        from datetime import datetime
        
        return SystemMetrics(
            cpu_percent=25.0,
            memory_percent=60.0,
            disk_percent=45.0,
            load_average=[1.0, 1.2, 1.1],
            network_io={"bytes_sent": 1000, "bytes_recv": 2000},
            disk_io={"read_bytes": 1024, "write_bytes": 512},
            process_count=50,
            uptime_seconds=3600,
            timestamp=datetime.now()
        )
    except ImportError:
        # Return a simple dict if imports fail
        return {
            "cpu_percent": 25.0,
            "memory_percent": 60.0,
            "disk_percent": 45.0,
            "process_count": 50,
            "uptime_seconds": 3600
        }


@pytest.fixture
def mock_agent_config():
    """Create a mock agent configuration"""
    try:
        from src.serena.orchestration.sub_agent_manager import AgentConfig, AgentType
        
        return AgentConfig(
            agent_id="test-agent-123",
            agent_type=AgentType.CODING,
            name="Test Coding Agent",
            description="A test coding agent",
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=4096,
            tools=["terminal", "web_search"],
            memory_enabled=True,
            custom_instructions="You are a helpful coding assistant.",
            environment_vars={"TEST_MODE": "true"}
        )
    except ImportError:
        # Return a simple dict if imports fail
        return {
            "agent_id": "test-agent-123",
            "agent_type": "coding",
            "name": "Test Coding Agent",
            "model": "gemini-1.5-pro"
        }


@pytest.fixture
def mock_mcp_tool_config():
    """Create a mock MCP tool configuration"""
    try:
        from src.serena.mcp_tools.mcp_manager import MCPToolConfig, MCPToolType
        
        return MCPToolConfig(
            name="Test Terminal Tool",
            tool_type=MCPToolType.TERMINAL,
            description="A test terminal tool",
            enabled=True,
            config={
                "timeout": 10,
                "allowed_commands": ["ls", "pwd", "echo"]
            },
            security_level="medium",
            timeout=10
        )
    except ImportError:
        # Return a simple dict if imports fail
        return {
            "name": "Test Terminal Tool",
            "tool_type": "terminal",
            "enabled": True,
            "config": {"timeout": 10}
        }


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


@pytest.fixture
def mock_http_session():
    """Create a mock HTTP session for testing"""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.text.return_value = "Mock response"
    
    mock_session.get.return_value.__aenter__.return_value = mock_response
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    return mock_session


# Test utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = ".txt") -> Path:
        """Create a temporary file with content"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return Path(f.name)
    
    @staticmethod
    def create_temp_config(config_dict: dict) -> Path:
        """Create a temporary YAML config file"""
        import yaml
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            return Path(f.name)
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to become true"""
        import asyncio
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
        return False


# Skip conditions for different environments
def skip_if_no_api_key():
    """Skip test if no API key is available"""
    return pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Test requires GEMINI_API_KEY environment variable"
    )


def skip_if_no_network():
    """Skip test if network is disabled"""
    return pytest.mark.skipif(
        os.getenv("NO_NETWORK"),
        reason="Network tests disabled"
    )


def skip_if_no_system_access():
    """Skip test if system access is disabled"""
    return pytest.mark.skipif(
        os.getenv("NO_SYSTEM_TESTS"),
        reason="System tests disabled"
    )
