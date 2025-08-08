"""
Comprehensive Test Suite for Sub-Agent Manager
Tests all aspects of sub-agent creation, management, and orchestration
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import yaml

from src.serena.orchestration.sub_agent_manager import (
    SubAgentManager, 
    AgentType, 
    AgentStatus, 
    AgentConfig, 
    AgentInstance
)


class TestSubAgentManager:
    """Comprehensive test suite for SubAgentManager"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_config_dir):
        """Create SubAgentManager instance for testing"""
        return SubAgentManager(config_dir=temp_config_dir)
    
    @pytest.fixture
    def mock_agno(self):
        """Mock Agno instance for testing"""
        mock = Mock()
        mock.run = AsyncMock(return_value="Mock result")
        return mock
    
    def test_initialization(self, manager):
        """Test SubAgentManager initialization"""
        assert isinstance(manager, SubAgentManager)
        assert manager.config_dir.exists()
        assert len(manager.agent_templates) == 7  # All agent types
        assert len(manager.agents) == 0
        
        # Verify all agent types are loaded
        expected_types = {
            AgentType.CODING, AgentType.RESEARCH, AgentType.TESTING,
            AgentType.DOCUMENTATION, AgentType.REVIEW, 
            AgentType.DEPLOYMENT, AgentType.MONITORING
        }
        actual_types = {template.agent_type for template in manager.agent_templates.values()}
        assert actual_types == expected_types
    
    def test_agent_templates_configuration(self, manager):
        """Test that agent templates are properly configured"""
        for agent_type, template in manager.agent_templates.items():
            assert isinstance(template, AgentConfig)
            assert template.agent_type == agent_type
            assert template.name
            assert template.description
            assert template.model
            assert template.max_tokens > 0
            assert 0 <= template.temperature <= 1
            assert isinstance(template.tools, list)
            assert isinstance(template.custom_instructions, str)
            assert len(template.custom_instructions) > 0
    
    @pytest.mark.asyncio
    async def test_create_agent_success(self, manager):
        """Test successful agent creation"""
        agent_id = await manager.create_agent(
            agent_type=AgentType.CODING,
            name="Test Coding Agent"
        )
        
        assert agent_id in manager.agents
        agent = manager.agents[agent_id]
        assert isinstance(agent, AgentInstance)
        assert agent.config.agent_type == AgentType.CODING
        assert agent.config.name == "Test Coding Agent"
        assert agent.status == AgentStatus.CREATED
        assert agent.created_at is not None
        assert agent.task_count == 0
    
    @pytest.mark.asyncio
    async def test_create_agent_with_custom_config(self, manager):
        """Test agent creation with custom configuration"""
        custom_config = {
            "model": "custom-model",
            "temperature": 0.5,
            "max_tokens": 4096,
            "tools": ["custom_tool"]
        }
        
        agent_id = await manager.create_agent(
            agent_type=AgentType.RESEARCH,
            name="Custom Research Agent",
            custom_config=custom_config
        )
        
        agent = manager.agents[agent_id]
        assert agent.config.model == "custom-model"
        assert agent.config.temperature == 0.5
        assert agent.config.max_tokens == 4096
        assert "custom_tool" in agent.config.tools
    
    @pytest.mark.asyncio
    async def test_create_multiple_agents(self, manager):
        """Test creating multiple agents of different types"""
        agent_types = [AgentType.CODING, AgentType.TESTING, AgentType.REVIEW]
        agent_ids = []
        
        for agent_type in agent_types:
            agent_id = await manager.create_agent(agent_type)
            agent_ids.append(agent_id)
        
        assert len(manager.agents) == 3
        assert all(agent_id in manager.agents for agent_id in agent_ids)
        
        # Verify each agent has correct type
        for i, agent_id in enumerate(agent_ids):
            assert manager.agents[agent_id].config.agent_type == agent_types[i]
    
    @pytest.mark.asyncio
    @patch('src.serena.orchestration.sub_agent_manager.Agno')
    async def test_start_agent_success(self, mock_agno_class, manager, mock_agno):
        """Test successful agent startup"""
        mock_agno_class.return_value = mock_agno
        
        agent_id = await manager.create_agent(AgentType.CODING)
        result = await manager.start_agent(agent_id)
        
        assert result is True
        agent = manager.agents[agent_id]
        assert agent.status == AgentStatus.RUNNING
        assert agent.agno_instance == mock_agno
        assert agent.last_activity is not None
        
        # Verify Agno was initialized with correct config
        mock_agno_class.assert_called_once()
        call_args = mock_agno_class.call_args[1]
        assert call_args["model"] == agent.config.model
        assert call_args["max_tokens"] == agent.config.max_tokens
        assert call_args["temperature"] == agent.config.temperature
    
    @pytest.mark.asyncio
    async def test_start_nonexistent_agent(self, manager):
        """Test starting non-existent agent"""
        fake_id = str(uuid.uuid4())
        result = await manager.start_agent(fake_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('src.serena.orchestration.sub_agent_manager.Agno')
    async def test_start_agent_failure(self, mock_agno_class, manager):
        """Test agent startup failure"""
        mock_agno_class.side_effect = Exception("Startup failed")
        
        agent_id = await manager.create_agent(AgentType.CODING)
        result = await manager.start_agent(agent_id)
        
        assert result is False
        agent = manager.agents[agent_id]
        assert agent.status == AgentStatus.ERROR
        assert "Startup failed" in agent.error_message
    
    @pytest.mark.asyncio
    async def test_stop_agent_success(self, manager):
        """Test successful agent stop"""
        agent_id = await manager.create_agent(AgentType.CODING)
        
        # Manually set agent to running state
        agent = manager.agents[agent_id]
        agent.status = AgentStatus.RUNNING
        agent.agno_instance = Mock()
        
        result = await manager.stop_agent(agent_id)
        
        assert result is True
        assert agent.status == AgentStatus.STOPPED
        assert agent.agno_instance is None
    
    @pytest.mark.asyncio
    async def test_stop_nonexistent_agent(self, manager):
        """Test stopping non-existent agent"""
        fake_id = str(uuid.uuid4())
        result = await manager.stop_agent(fake_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('src.serena.orchestration.sub_agent_manager.Agno')
    async def test_execute_task_success(self, mock_agno_class, manager, mock_agno):
        """Test successful task execution"""
        mock_agno_class.return_value = mock_agno
        mock_agno.run.return_value = "Task completed successfully"
        
        agent_id = await manager.create_agent(AgentType.CODING)
        await manager.start_agent(agent_id)
        
        result = await manager.execute_task(
            agent_id=agent_id,
            task="Write a Python function",
            context={"language": "python"}
        )
        
        assert result == "Task completed successfully"
        agent = manager.agents[agent_id]
        assert agent.task_count == 1
        assert agent.last_activity is not None
        
        # Verify task was called with correct parameters
        mock_agno.run.assert_called_once_with(
            "Write a Python function",
            {"language": "python"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_task_agent_not_running(self, manager):
        """Test task execution on non-running agent"""
        agent_id = await manager.create_agent(AgentType.CODING)
        
        with pytest.raises(ValueError, match="is not running"):
            await manager.execute_task(agent_id, "Test task")
    
    @pytest.mark.asyncio
    async def test_execute_task_nonexistent_agent(self, manager):
        """Test task execution on non-existent agent"""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            await manager.execute_task(fake_id, "Test task")
    
    @pytest.mark.asyncio
    @patch('src.serena.orchestration.sub_agent_manager.Agno')
    async def test_execute_task_failure(self, mock_agno_class, manager, mock_agno):
        """Test task execution failure"""
        mock_agno_class.return_value = mock_agno
        mock_agno.run.side_effect = Exception("Task execution failed")
        
        agent_id = await manager.create_agent(AgentType.CODING)
        await manager.start_agent(agent_id)
        
        with pytest.raises(Exception, match="Task execution failed"):
            await manager.execute_task(agent_id, "Failing task")
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, manager):
        """Test getting agent status"""
        agent_id = await manager.create_agent(
            AgentType.CODING,
            name="Status Test Agent"
        )
        
        status = await manager.get_agent_status(agent_id)
        
        assert status["agent_id"] == agent_id
        assert status["name"] == "Status Test Agent"
        assert status["type"] == "coding"
        assert status["status"] == "created"
        assert status["task_count"] == 0
        assert status["is_running"] is False
        assert "created_at" in status
        assert "last_activity" in status
    
    @pytest.mark.asyncio
    async def test_get_status_nonexistent_agent(self, manager):
        """Test getting status of non-existent agent"""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            await manager.get_agent_status(fake_id)
    
    @pytest.mark.asyncio
    async def test_list_agents_empty(self, manager):
        """Test listing agents when none exist"""
        agents = await manager.list_agents()
        assert agents == []
    
    @pytest.mark.asyncio
    async def test_list_agents_multiple(self, manager):
        """Test listing multiple agents"""
        agent_ids = []
        for agent_type in [AgentType.CODING, AgentType.TESTING]:
            agent_id = await manager.create_agent(agent_type)
            agent_ids.append(agent_id)
        
        agents = await manager.list_agents()
        
        assert len(agents) == 2
        returned_ids = [agent["agent_id"] for agent in agents]
        assert set(returned_ids) == set(agent_ids)
    
    @pytest.mark.asyncio
    async def test_remove_agent_success(self, manager, temp_config_dir):
        """Test successful agent removal"""
        agent_id = await manager.create_agent(AgentType.CODING)
        
        # Verify config file was created
        config_file = temp_config_dir / f"{agent_id}.yaml"
        assert config_file.exists()
        
        result = await manager.remove_agent(agent_id)
        
        assert result is True
        assert agent_id not in manager.agents
        assert not config_file.exists()
    
    @pytest.mark.asyncio
    async def test_remove_running_agent(self, manager):
        """Test removing a running agent"""
        agent_id = await manager.create_agent(AgentType.CODING)
        
        # Set agent to running state
        agent = manager.agents[agent_id]
        agent.status = AgentStatus.RUNNING
        agent.agno_instance = Mock()
        
        result = await manager.remove_agent(agent_id)
        
        assert result is True
        assert agent_id not in manager.agents
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_agent(self, manager):
        """Test removing non-existent agent"""
        fake_id = str(uuid.uuid4())
        result = await manager.remove_agent(fake_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_agent_config(self, manager, temp_config_dir):
        """Test saving agent configuration to file"""
        agent_id = await manager.create_agent(AgentType.CODING)
        config_file = temp_config_dir / f"{agent_id}.yaml"
        
        assert config_file.exists()
        
        # Load and verify config
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config["agent_id"] == agent_id
        assert saved_config["agent_type"] == "coding"
        assert saved_config["name"] == "Coding Agent"
        assert saved_config["model"] == "gemini-1.5-pro"
    
    @pytest.mark.asyncio
    async def test_load_agent_configs(self, manager, temp_config_dir):
        """Test loading agent configurations from files"""
        # Create a config file manually
        agent_id = str(uuid.uuid4())
        config_data = {
            "agent_id": agent_id,
            "agent_type": "research",
            "name": "Test Research Agent",
            "description": "Test agent",
            "model": "test-model",
            "max_tokens": 4096,
            "temperature": 0.3,
            "tools": ["test_tool"],
            "memory_enabled": True,
            "custom_instructions": "Test instructions",
            "environment_vars": {}
        }
        
        config_file = temp_config_dir / f"{agent_id}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configs
        await manager.load_agent_configs()
        
        assert agent_id in manager.agents
        agent = manager.agents[agent_id]
        assert agent.config.agent_type == AgentType.RESEARCH
        assert agent.config.name == "Test Research Agent"
        assert agent.status == AgentStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_health_check_empty(self, manager):
        """Test health check with no agents"""
        health = await manager.health_check()
        
        assert health["total_agents"] == 0
        assert health["running_agents"] == 0
        assert health["stopped_agents"] == 0
        assert health["error_agents"] == 0
        assert health["overall_healthy"] is True
        assert health["agents"] == []
    
    @pytest.mark.asyncio
    async def test_health_check_multiple_agents(self, manager):
        """Test health check with multiple agents in different states"""
        # Create agents in different states
        coding_id = await manager.create_agent(AgentType.CODING)
        testing_id = await manager.create_agent(AgentType.TESTING)
        review_id = await manager.create_agent(AgentType.REVIEW)
        
        # Set different statuses
        manager.agents[coding_id].status = AgentStatus.RUNNING
        manager.agents[testing_id].status = AgentStatus.STOPPED
        manager.agents[review_id].status = AgentStatus.ERROR
        manager.agents[review_id].error_message = "Test error"
        
        health = await manager.health_check()
        
        assert health["total_agents"] == 3
        assert health["running_agents"] == 1
        assert health["stopped_agents"] == 1
        assert health["error_agents"] == 1
        assert health["overall_healthy"] is False  # Due to error agent
        assert len(health["agents"]) == 3
        
        # Find error agent in health report
        error_agent = next(
            agent for agent in health["agents"] 
            if agent["agent_id"] == review_id
        )
        assert error_agent["healthy"] is False
        assert error_agent["error_message"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, manager):
        """Test concurrent agent operations"""
        # Create multiple agents concurrently
        tasks = [
            manager.create_agent(AgentType.CODING),
            manager.create_agent(AgentType.TESTING),
            manager.create_agent(AgentType.REVIEW)
        ]
        
        agent_ids = await asyncio.gather(*tasks)
        
        assert len(agent_ids) == 3
        assert len(manager.agents) == 3
        assert all(agent_id in manager.agents for agent_id in agent_ids)
    
    @pytest.mark.asyncio
    @patch('src.serena.orchestration.sub_agent_manager.Agno')
    async def test_agent_lifecycle_complete(self, mock_agno_class, manager, mock_agno):
        """Test complete agent lifecycle"""
        mock_agno_class.return_value = mock_agno
        mock_agno.run.return_value = "Lifecycle test result"
        
        # Create agent
        agent_id = await manager.create_agent(
            AgentType.CODING,
            name="Lifecycle Test Agent"
        )
        assert manager.agents[agent_id].status == AgentStatus.CREATED
        
        # Start agent
        await manager.start_agent(agent_id)
        assert manager.agents[agent_id].status == AgentStatus.RUNNING
        
        # Execute task
        result = await manager.execute_task(agent_id, "Test task")
        assert result == "Lifecycle test result"
        assert manager.agents[agent_id].task_count == 1
        
        # Stop agent
        await manager.stop_agent(agent_id)
        assert manager.agents[agent_id].status == AgentStatus.STOPPED
        
        # Remove agent
        await manager.remove_agent(agent_id)
        assert agent_id not in manager.agents
    
    def test_agent_config_validation(self, manager):
        """Test agent configuration validation"""
        # Test valid config
        config = AgentConfig(
            agent_id="test-id",
            agent_type=AgentType.CODING,
            name="Test Agent",
            description="Test description"
        )
        
        assert config.agent_id == "test-id"
        assert config.agent_type == AgentType.CODING
        assert config.tools == []  # Default empty list
        assert config.environment_vars == {}  # Default empty dict
    
    def test_agent_instance_creation(self):
        """Test agent instance creation"""
        config = AgentConfig(
            agent_id="test-id",
            agent_type=AgentType.CODING,
            name="Test Agent",
            description="Test description"
        )
        
        instance = AgentInstance(
            config=config,
            status=AgentStatus.CREATED
        )
        
        assert instance.config == config
        assert instance.status == AgentStatus.CREATED
        assert instance.created_at is not None
        assert instance.last_activity is not None
        assert instance.task_count == 0
        assert instance.error_message == ""
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_agent_type(self, manager):
        """Test error handling for invalid agent type"""
        # This should be caught by type system, but test runtime behavior
        with pytest.raises(Exception):
            await manager.create_agent("invalid_type")
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_on_removal(self, manager):
        """Test that memory is properly cleaned up when removing agents"""
        initial_count = len(manager.agents)
        
        # Create and remove multiple agents
        for _ in range(5):
            agent_id = await manager.create_agent(AgentType.CODING)
            await manager.remove_agent(agent_id)
        
        assert len(manager.agents) == initial_count
    
    @pytest.mark.asyncio
    async def test_agent_task_metrics(self, manager):
        """Test agent task execution metrics"""
        agent_id = await manager.create_agent(AgentType.CODING)
        agent = manager.agents[agent_id]
        
        # Mock running state
        agent.status = AgentStatus.RUNNING
        agent.agno_instance = AsyncMock()
        agent.agno_instance.run.return_value = "Task result"
        
        initial_time = agent.last_activity
        initial_count = agent.task_count
        
        # Execute task
        await manager.execute_task(agent_id, "Test task")
        
        assert agent.task_count == initial_count + 1
        assert agent.last_activity > initial_time


class TestAgentTypes:
    """Test agent type enumeration and properties"""
    
    def test_all_agent_types_exist(self):
        """Test that all expected agent types exist"""
        expected_types = {
            "coding", "research", "testing", "documentation", 
            "review", "deployment", "monitoring"
        }
        actual_types = {agent_type.value for agent_type in AgentType}
        assert actual_types == expected_types
    
    def test_agent_type_values(self):
        """Test agent type string values"""
        assert AgentType.CODING.value == "coding"
        assert AgentType.RESEARCH.value == "research"
        assert AgentType.TESTING.value == "testing"
        assert AgentType.DOCUMENTATION.value == "documentation"
        assert AgentType.REVIEW.value == "review"
        assert AgentType.DEPLOYMENT.value == "deployment"
        assert AgentType.MONITORING.value == "monitoring"


class TestAgentStatus:
    """Test agent status enumeration"""
    
    def test_all_status_values_exist(self):
        """Test that all expected status values exist"""
        expected_statuses = {
            "created", "starting", "running", "paused", 
            "stopping", "stopped", "error"
        }
        actual_statuses = {status.value for status in AgentStatus}
        assert actual_statuses == expected_statuses
    
    def test_status_transitions(self):
        """Test logical status transitions"""
        # Test typical lifecycle
        assert AgentStatus.CREATED.value == "created"
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.STOPPING.value == "stopping"
        assert AgentStatus.STOPPED.value == "stopped"
        assert AgentStatus.ERROR.value == "error"


@pytest.mark.integration
class TestSubAgentManagerIntegration:
    """Integration tests for SubAgentManager with real Agno instances"""
    
    @pytest.fixture
    def real_manager(self):
        """Create manager with real configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SubAgentManager(config_dir=Path(temp_dir))
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration"),
        reason="Integration tests require --integration flag"
    )
    async def test_real_agent_creation_and_execution(self, real_manager):
        """Test with real Agno instance (requires API key)"""
        # This test requires actual API key and network access
        agent_id = await real_manager.create_agent(
            AgentType.CODING,
            custom_config={"model": "gemini-1.5-flash"}
        )
        
        # Start agent (this will create real Agno instance)
        success = await real_manager.start_agent(agent_id)
        assert success
        
        # Execute simple task
        result = await real_manager.execute_task(
            agent_id,
            "Say hello and confirm you are working",
            context={"test": True}
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Clean up
        await real_manager.stop_agent(agent_id)
        await real_manager.remove_agent(agent_id)


# Performance tests
@pytest.mark.performance
class TestSubAgentManagerPerformance:
    """Performance tests for SubAgentManager"""
    
    @pytest.mark.asyncio
    async def test_create_many_agents_performance(self):
        """Test performance of creating many agents"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SubAgentManager(config_dir=Path(temp_dir))
            
            start_time = time.time()
            
            # Create 100 agents
            tasks = [
                manager.create_agent(AgentType.CODING) 
                for _ in range(100)
            ]
            agent_ids = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(agent_ids) == 100
            assert duration < 5.0  # Should complete in under 5 seconds
            
            # Clean up
            for agent_id in agent_ids:
                await manager.remove_agent(agent_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self):
        """Test performance of concurrent operations"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SubAgentManager(config_dir=Path(temp_dir))
            
            # Create some agents first
            agent_ids = []
            for _ in range(10):
                agent_id = await manager.create_agent(AgentType.CODING)
                agent_ids.append(agent_id)
            
            start_time = time.time()
            
            # Perform concurrent operations
            tasks = []
            for agent_id in agent_ids:
                tasks.append(manager.get_agent_status(agent_id))
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(results) == 10
            assert duration < 1.0  # Should complete quickly
            
            # Clean up
            for agent_id in agent_ids:
                await manager.remove_agent(agent_id)


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src.serena.orchestration.sub_agent_manager",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
