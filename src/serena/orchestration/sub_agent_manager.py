"""
Sub-Agent Management System for Serena Orchestrator
Handles creation, configuration, and lifecycle management of multiple AI agents
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

import yaml
from agno import Agno


class AgentType(Enum):
    """Types of sub-agents available for orchestration"""
    CODING = "coding"
    RESEARCH = "research"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class AgentStatus(Enum):
    """Status of sub-agents"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for a sub-agent"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    model: str = "gemini-1.5-pro"
    max_tokens: int = 8192
    temperature: float = 0.7
    tools: List[str] = None
    memory_enabled: bool = True
    custom_instructions: str = ""
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.environment_vars is None:
            self.environment_vars = {}


@dataclass
class AgentInstance:
    """Runtime instance of a sub-agent"""
    config: AgentConfig
    status: AgentStatus
    agno_instance: Optional[Agno] = None
    created_at: datetime = None
    last_activity: datetime = None
    task_count: int = 0
    error_message: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()


class SubAgentManager:
    """Manages multiple sub-agents for orchestrated tasks"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("configs/agents")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_templates: Dict[AgentType, AgentConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load agent templates
        self._load_agent_templates()
    
    def _load_agent_templates(self):
        """Load predefined agent templates"""
        templates = {
            AgentType.CODING: AgentConfig(
                agent_id="template_coding",
                agent_type=AgentType.CODING,
                name="Coding Agent",
                description="Specialized in code generation, refactoring, and debugging",
                tools=["file_tools", "symbol_tools", "git_tools"],
                custom_instructions="""You are a specialized coding agent. Focus on:
- Writing clean, maintainable code
- Following best practices and patterns
- Comprehensive error handling
- Performance optimization
- Security considerations"""
            ),
            AgentType.RESEARCH: AgentConfig(
                agent_id="template_research",
                agent_type=AgentType.RESEARCH,
                name="Research Agent",
                description="Specialized in information gathering and analysis",
                tools=["web_search", "document_analysis", "knowledge_base"],
                custom_instructions="""You are a research specialist. Focus on:
- Thorough information gathering
- Source verification and credibility
- Comprehensive analysis
- Clear documentation of findings
- Actionable insights and recommendations"""
            ),
            AgentType.TESTING: AgentConfig(
                agent_id="template_testing",
                agent_type=AgentType.TESTING,
                name="Testing Agent",
                description="Specialized in test creation and quality assurance",
                tools=["test_tools", "coverage_tools", "performance_tools"],
                custom_instructions="""You are a testing specialist. Focus on:
- Comprehensive test coverage
- Edge case identification
- Performance testing
- Security testing
- Test automation and CI/CD integration"""
            ),
            AgentType.DOCUMENTATION: AgentConfig(
                agent_id="template_documentation",
                agent_type=AgentType.DOCUMENTATION,
                name="Documentation Agent",
                description="Specialized in creating comprehensive documentation",
                tools=["document_tools", "diagram_tools", "markdown_tools"],
                custom_instructions="""You are a documentation specialist. Focus on:
- Clear, comprehensive documentation
- User-friendly guides and tutorials
- API documentation
- Architecture diagrams
- Maintenance of documentation consistency"""
            ),
            AgentType.REVIEW: AgentConfig(
                agent_id="template_review",
                agent_type=AgentType.REVIEW,
                name="Review Agent",
                description="Specialized in code and document review",
                tools=["analysis_tools", "quality_tools", "security_tools"],
                custom_instructions="""You are a review specialist. Focus on:
- Thorough code review
- Security vulnerability assessment
- Performance analysis
- Best practice compliance
- Constructive feedback and suggestions"""
            ),
            AgentType.DEPLOYMENT: AgentConfig(
                agent_id="template_deployment",
                agent_type=AgentType.DEPLOYMENT,
                name="Deployment Agent",
                description="Specialized in deployment and infrastructure",
                tools=["deployment_tools", "infrastructure_tools", "monitoring_tools"],
                custom_instructions="""You are a deployment specialist. Focus on:
- Reliable deployment processes
- Infrastructure as code
- Monitoring and alerting
- Rollback strategies
- Security and compliance"""
            ),
            AgentType.MONITORING: AgentConfig(
                agent_id="template_monitoring",
                agent_type=AgentType.MONITORING,
                name="Monitoring Agent",
                description="Specialized in system monitoring and observability",
                tools=["monitoring_tools", "alerting_tools", "analytics_tools"],
                custom_instructions="""You are a monitoring specialist. Focus on:
- Comprehensive system monitoring
- Performance metrics and KPIs
- Alerting and incident response
- Log analysis and troubleshooting
- Capacity planning and optimization"""
            )
        }
        
        self.agent_templates = templates
        self.logger.info(f"Loaded {len(templates)} agent templates")
    
    async def create_agent(self, agent_type: AgentType, name: str = None, 
                          custom_config: Dict[str, Any] = None) -> str:
        """Create a new sub-agent instance"""
        try:
            # Get template and create config
            template = self.agent_templates[agent_type]
            agent_id = str(uuid.uuid4())
            
            config = AgentConfig(
                agent_id=agent_id,
                agent_type=agent_type,
                name=name or template.name,
                description=template.description,
                model=template.model,
                max_tokens=template.max_tokens,
                temperature=template.temperature,
                tools=template.tools.copy(),
                memory_enabled=template.memory_enabled,
                custom_instructions=template.custom_instructions,
                environment_vars=template.environment_vars.copy()
            )
            
            # Apply custom configuration
            if custom_config:
                for key, value in custom_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            # Create agent instance
            instance = AgentInstance(
                config=config,
                status=AgentStatus.CREATED
            )
            
            self.agents[agent_id] = instance
            
            # Save configuration
            await self._save_agent_config(config)
            
            self.logger.info(f"Created {agent_type.value} agent: {agent_id}")
            return agent_id
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise
    
    async def start_agent(self, agent_id: str) -> bool:
        """Start a sub-agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            instance = self.agents[agent_id]
            instance.status = AgentStatus.STARTING
            
            # Initialize Agno instance
            agno_config = {
                "model": instance.config.model,
                "max_tokens": instance.config.max_tokens,
                "temperature": instance.config.temperature,
                "tools": instance.config.tools,
                "memory": instance.config.memory_enabled,
                "instructions": instance.config.custom_instructions
            }
            
            # Add environment variables
            for key, value in instance.config.environment_vars.items():
                agno_config[key] = value
            
            instance.agno_instance = Agno(**agno_config)
            instance.status = AgentStatus.RUNNING
            instance.last_activity = datetime.now()
            
            self.logger.info(f"Started agent: {agent_id}")
            return True
            
        except Exception as e:
            if agent_id in self.agents:
                self.agents[agent_id].status = AgentStatus.ERROR
                self.agents[agent_id].error_message = str(e)
            self.logger.error(f"Failed to start agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a sub-agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            instance = self.agents[agent_id]
            instance.status = AgentStatus.STOPPING
            
            # Cleanup Agno instance
            if instance.agno_instance:
                # Perform any necessary cleanup
                instance.agno_instance = None
            
            instance.status = AgentStatus.STOPPED
            
            self.logger.info(f"Stopped agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def execute_task(self, agent_id: str, task: str, context: Dict[str, Any] = None) -> Any:
        """Execute a task on a specific agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            instance = self.agents[agent_id]
            
            if instance.status != AgentStatus.RUNNING:
                raise ValueError(f"Agent {agent_id} is not running (status: {instance.status.value})")
            
            if not instance.agno_instance:
                raise ValueError(f"Agent {agent_id} has no active Agno instance")
            
            # Execute task
            result = await instance.agno_instance.run(task, context or {})
            
            # Update metrics
            instance.task_count += 1
            instance.last_activity = datetime.now()
            
            self.logger.info(f"Executed task on agent {agent_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute task on agent {agent_id}: {e}")
            raise
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status information for an agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        instance = self.agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "name": instance.config.name,
            "type": instance.config.agent_type.value,
            "status": instance.status.value,
            "created_at": instance.created_at.isoformat(),
            "last_activity": instance.last_activity.isoformat(),
            "task_count": instance.task_count,
            "error_message": instance.error_message,
            "is_running": instance.status == AgentStatus.RUNNING
        }
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents and their status"""
        return [await self.get_agent_status(agent_id) for agent_id in self.agents.keys()]
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Stop agent if running
            if self.agents[agent_id].status == AgentStatus.RUNNING:
                await self.stop_agent(agent_id)
            
            # Remove from memory
            del self.agents[agent_id]
            
            # Remove config file
            config_file = self.config_dir / f"{agent_id}.yaml"
            if config_file.exists():
                config_file.unlink()
            
            self.logger.info(f"Removed agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove agent {agent_id}: {e}")
            return False
    
    async def _save_agent_config(self, config: AgentConfig):
        """Save agent configuration to file"""
        config_file = self.config_dir / f"{config.agent_id}.yaml"
        
        config_dict = asdict(config)
        config_dict["agent_type"] = config.agent_type.value
        
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    async def load_agent_configs(self):
        """Load existing agent configurations"""
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    config_dict = yaml.safe_load(f)
                
                config_dict["agent_type"] = AgentType(config_dict["agent_type"])
                config = AgentConfig(**config_dict)
                
                instance = AgentInstance(
                    config=config,
                    status=AgentStatus.STOPPED
                )
                
                self.agents[config.agent_id] = instance
                
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_file}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents"""
        health_status = {
            "total_agents": len(self.agents),
            "running_agents": 0,
            "stopped_agents": 0,
            "error_agents": 0,
            "agents": []
        }
        
        for agent_id, instance in self.agents.items():
            agent_health = {
                "agent_id": agent_id,
                "name": instance.config.name,
                "status": instance.status.value,
                "healthy": instance.status in [AgentStatus.RUNNING, AgentStatus.STOPPED]
            }
            
            if instance.status == AgentStatus.RUNNING:
                health_status["running_agents"] += 1
            elif instance.status == AgentStatus.STOPPED:
                health_status["stopped_agents"] += 1
            elif instance.status == AgentStatus.ERROR:
                health_status["error_agents"] += 1
                agent_health["error_message"] = instance.error_message
            
            health_status["agents"].append(agent_health)
        
        health_status["overall_healthy"] = health_status["error_agents"] == 0
        
        return health_status
