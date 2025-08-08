"""
Full System Integration Tests
Tests the complete Serena Orchestrator system with real Gemini API integration
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.serena.orchestration.sub_agent_manager import SubAgentManager, AgentType
from src.serena.mcp_tools.mcp_manager import MCPToolsManager
from src.serena.monitoring.health_monitor import HealthMonitor


@pytest.mark.integration
class TestFullSystemIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def agent_manager(self, temp_dir):
        """Create SubAgentManager for integration testing"""
        return SubAgentManager(config_dir=temp_dir / "agents")
    
    @pytest.fixture
    def mcp_manager(self, temp_dir):
        """Create MCPToolsManager for integration testing"""
        return MCPToolsManager(config_dir=temp_dir / "mcp_tools")
    
    @pytest.fixture
    def health_monitor(self, temp_dir):
        """Create HealthMonitor for integration testing"""
        return HealthMonitor(config_dir=temp_dir / "monitoring")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Integration tests require GEMINI_API_KEY environment variable"
    )
    async def test_complete_agent_workflow(self, agent_manager, mcp_manager, health_monitor):
        """Test complete workflow with real Gemini API"""
        # Set up environment
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        
        # 1. Create and start a coding agent
        agent_id = await agent_manager.create_agent(
            AgentType.CODING,
            name="Integration Test Coding Agent",
            custom_config={
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 1024
            }
        )
        
        assert agent_id is not None
        
        # Start the agent
        start_success = await agent_manager.start_agent(agent_id)
        assert start_success is True
        
        # 2. Execute a simple coding task
        task_result = await agent_manager.execute_task(
            agent_id,
            "Write a simple Python function that adds two numbers and returns the result. Include a docstring.",
            context={"language": "python", "test": True}
        )
        
        assert task_result is not None
        assert isinstance(task_result, str)
        assert len(task_result) > 0
        assert "def" in task_result.lower()  # Should contain function definition
        
        # 3. Test MCP tools integration
        # Test terminal command
        terminal_result = await mcp_manager.execute_terminal_command("echo 'Integration test'")
        assert terminal_result["success"] is True
        assert "Integration test" in terminal_result["output"]
        
        # Test environment info
        env_result = await mcp_manager.get_environment_info()
        assert env_result["success"] is True
        assert "system_info" in env_result
        
        # 4. Test health monitoring
        await health_monitor.start_monitoring()
        
        # Wait a moment for monitoring to collect data
        await asyncio.sleep(2)
        
        health_summary = await health_monitor.get_health_summary()
        assert "overall_status" in health_summary
        assert "checks" in health_summary
        assert "metrics" in health_summary
        
        await health_monitor.stop_monitoring()
        
        # 5. Test agent status and metrics
        agent_status = await agent_manager.get_agent_status(agent_id)
        assert agent_status["is_running"] is True
        assert agent_status["task_count"] == 1
        
        # 6. Clean up
        await agent_manager.stop_agent(agent_id)
        await agent_manager.remove_agent(agent_id)
        
        # Verify cleanup
        agents = await agent_manager.list_agents()
        assert len(agents) == 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Integration tests require GEMINI_API_KEY environment variable"
    )
    async def test_multi_agent_orchestration(self, agent_manager):
        """Test orchestration of multiple agents"""
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        
        # Create multiple agents
        coding_agent = await agent_manager.create_agent(
            AgentType.CODING,
            name="Coding Agent",
            custom_config={"model": "gemini-1.5-flash", "temperature": 0.1}
        )
        
        research_agent = await agent_manager.create_agent(
            AgentType.RESEARCH,
            name="Research Agent", 
            custom_config={"model": "gemini-1.5-flash", "temperature": 0.3}
        )
        
        # Start both agents
        await agent_manager.start_agent(coding_agent)
        await agent_manager.start_agent(research_agent)
        
        # Execute tasks on both agents concurrently
        coding_task = agent_manager.execute_task(
            coding_agent,
            "Create a simple Python class for a calculator with add and subtract methods."
        )
        
        research_task = agent_manager.execute_task(
            research_agent,
            "Explain the benefits of using Python for data science in 2-3 sentences."
        )
        
        # Wait for both tasks to complete
        coding_result, research_result = await asyncio.gather(coding_task, research_task)
        
        # Verify results
        assert coding_result is not None
        assert "class" in coding_result.lower()
        assert "def" in coding_result.lower()
        
        assert research_result is not None
        assert "python" in research_result.lower()
        assert len(research_result) > 50  # Should be substantial response
        
        # Check agent statuses
        coding_status = await agent_manager.get_agent_status(coding_agent)
        research_status = await agent_manager.get_agent_status(research_agent)
        
        assert coding_status["task_count"] == 1
        assert research_status["task_count"] == 1
        
        # Clean up
        await agent_manager.stop_agent(coding_agent)
        await agent_manager.stop_agent(research_agent)
        await agent_manager.remove_agent(coding_agent)
        await agent_manager.remove_agent(research_agent)
    
    @pytest.mark.asyncio
    async def test_mcp_tools_comprehensive(self, mcp_manager):
        """Test comprehensive MCP tools functionality"""
        # Test multiple MCP tools
        results = {}
        
        # Terminal operations
        results["terminal"] = await mcp_manager.execute_terminal_command("pwd")
        
        # Environment info
        results["environment"] = await mcp_manager.get_environment_info()
        
        # System metrics
        results["metrics"] = await mcp_manager.get_system_metrics()
        
        # Health check
        results["health"] = await mcp_manager.health_check()
        
        # Verify all operations succeeded
        for tool_name, result in results.items():
            assert result["success"] is True, f"{tool_name} tool failed: {result.get('error', 'Unknown error')}"
        
        # Verify specific results
        assert results["terminal"]["return_code"] == 0
        assert "system_info" in results["environment"]
        assert "metrics" in results["metrics"]
        assert results["health"]["overall_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_health_monitoring_comprehensive(self, health_monitor):
        """Test comprehensive health monitoring"""
        # Start monitoring
        await health_monitor.start_monitoring()
        
        # Let it run for a few seconds to collect data
        await asyncio.sleep(3)
        
        # Get health summary
        summary = await health_monitor.get_health_summary()
        
        # Verify health summary structure
        assert "overall_status" in summary
        assert "checks" in summary
        assert "metrics" in summary
        assert "alerts" in summary
        assert "stats" in summary
        
        # Verify stats
        stats = summary["stats"]
        assert stats["total_checks"] > 0
        assert stats["enabled_checks"] > 0
        assert "monitoring_active" in stats
        assert stats["monitoring_active"] is True
        
        # Get metrics history
        metrics_history = await health_monitor.get_metrics_history(hours=1)
        assert len(metrics_history) > 0
        
        # Verify metrics structure
        latest_metrics = metrics_history[-1]
        assert "timestamp" in latest_metrics
        assert "cpu_percent" in latest_metrics
        assert "memory_percent" in latest_metrics
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        
        # Verify monitoring stopped
        final_summary = await health_monitor.get_health_summary()
        assert final_summary["stats"]["monitoring_active"] is False
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"),
        reason="Integration tests require GEMINI_API_KEY environment variable"
    )
    async def test_error_handling_and_recovery(self, agent_manager):
        """Test error handling and recovery scenarios"""
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        
        # Create agent
        agent_id = await agent_manager.create_agent(AgentType.CODING)
        await agent_manager.start_agent(agent_id)
        
        # Test with invalid task (should handle gracefully)
        try:
            result = await agent_manager.execute_task(
                agent_id,
                "",  # Empty task
                context={}
            )
            # Should either succeed with empty response or handle gracefully
            assert result is not None
        except Exception as e:
            # Should be a handled exception, not a crash
            assert isinstance(e, (ValueError, RuntimeError))
        
        # Agent should still be functional
        status = await agent_manager.get_agent_status(agent_id)
        assert status["status"] in ["running", "error"]  # Should not crash
        
        # Test recovery with valid task
        recovery_result = await agent_manager.execute_task(
            agent_id,
            "Say hello and confirm you are working correctly."
        )
        
        assert recovery_result is not None
        assert len(recovery_result) > 0
        
        # Clean up
        await agent_manager.stop_agent(agent_id)
        await agent_manager.remove_agent(agent_id)
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, agent_manager, mcp_manager):
        """Test system performance under load"""
        import time
        
        # Set up environment if available
        if os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
            
            # Create multiple agents
            agents = []
            for i in range(3):
                agent_id = await agent_manager.create_agent(
                    AgentType.CODING,
                    name=f"Load Test Agent {i}",
                    custom_config={"model": "gemini-1.5-flash"}
                )
                await agent_manager.start_agent(agent_id)
                agents.append(agent_id)
        
        # Test MCP tools under load
        start_time = time.time()
        
        # Execute multiple MCP operations concurrently
        mcp_tasks = [
            mcp_manager.get_environment_info(),
            mcp_manager.get_system_metrics(),
            mcp_manager.health_check(),
            mcp_manager.execute_terminal_command("echo 'load test'"),
        ]
        
        mcp_results = await asyncio.gather(*mcp_tasks, return_exceptions=True)
        
        mcp_duration = time.time() - start_time
        
        # Verify MCP operations completed quickly
        assert mcp_duration < 10.0  # Should complete within 10 seconds
        
        # Verify most operations succeeded
        successful_mcp = [r for r in mcp_results if isinstance(r, dict) and r.get("success")]
        assert len(successful_mcp) >= 3  # At least 3 should succeed
        
        # Test agent operations under load if API key available
        if os.getenv("GEMINI_API_KEY") and agents:
            start_time = time.time()
            
            # Execute simple tasks on all agents concurrently
            agent_tasks = [
                agent_manager.execute_task(agent_id, f"Return the number {i}")
                for i, agent_id in enumerate(agents)
            ]
            
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            agent_duration = time.time() - start_time
            
            # Verify agent operations completed
            assert agent_duration < 30.0  # Should complete within 30 seconds
            
            # Verify results
            successful_agents = [r for r in agent_results if isinstance(r, str)]
            assert len(successful_agents) >= 2  # At least 2 should succeed
            
            # Clean up agents
            for agent_id in agents:
                await agent_manager.stop_agent(agent_id)
                await agent_manager.remove_agent(agent_id)


@pytest.mark.integration
class TestSystemConfiguration:
    """Test system configuration and setup"""
    
    def test_environment_variables(self):
        """Test required environment variables"""
        # Check if Gemini API key is available for integration tests
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            assert len(gemini_key) > 20  # Should be substantial key
            assert gemini_key.startswith("AIza")  # Gemini keys start with AIza
    
    @pytest.mark.asyncio
    async def test_system_dependencies(self):
        """Test system dependencies are available"""
        # Test Python modules
        try:
            import psutil
            import aiohttp
            import yaml
            assert True
        except ImportError as e:
            pytest.fail(f"Required dependency missing: {e}")
        
        # Test system commands
        import shutil
        
        # These should be available on most systems
        basic_commands = ["echo", "pwd"]
        for cmd in basic_commands:
            if shutil.which(cmd):
                assert True
            else:
                pytest.skip(f"System command '{cmd}' not available")
    
    def test_file_permissions(self):
        """Test file system permissions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test directory creation
            test_dir = temp_path / "test_config"
            test_dir.mkdir()
            assert test_dir.exists()
            
            # Test file creation
            test_file = test_dir / "test.yaml"
            test_file.write_text("test: value")
            assert test_file.exists()
            
            # Test file reading
            content = test_file.read_text()
            assert "test: value" in content


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--tb=short"
    ])
