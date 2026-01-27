"""
MCP Tools Manager for Serena Orchestrator
Handles WSL2, terminal operations, web search, and environment management
"""

import asyncio
import json
import logging
import subprocess
import shutil
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import aiohttp
import yaml


class MCPToolType(Enum):
    """Types of MCP tools available"""
    WSL2 = "wsl2"
    TERMINAL = "terminal"
    WEB_SEARCH = "web_search"
    FILE_SYSTEM = "file_system"
    ENVIRONMENT = "environment"
    DOCKER = "docker"
    GIT = "git"
    SYSTEM_INFO = "system_info"


@dataclass
class MCPToolConfig:
    """Configuration for an MCP tool"""
    tool_type: MCPToolType
    name: str
    description: str
    enabled: bool = True
    config: Dict[str, Any] = None
    security_level: str = "medium"  # low, medium, high
    timeout: int = 30
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class MCPToolsManager:
    """Manages MCP tools for agent access to system resources"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("configs/mcp_tools")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.tools: Dict[str, MCPToolConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available MCP tools"""
        tools_config = {
            "wsl2_manager": MCPToolConfig(
                tool_type=MCPToolType.WSL2,
                name="WSL2 Manager",
                description="Manage WSL2 instances and execute commands",
                config={
                    "default_distribution": "Ubuntu",
                    "allowed_commands": ["ls", "cd", "pwd", "cat", "grep", "find", "python3", "node", "npm", "git"],
                    "forbidden_commands": ["rm -rf", "sudo rm", "format", "fdisk"],
                    "max_execution_time": 60,
                    "working_directory": "/home"
                },
                security_level="high"
            ),
            "terminal_executor": MCPToolConfig(
                tool_type=MCPToolType.TERMINAL,
                name="Terminal Executor",
                description="Execute terminal commands with safety checks",
                config={
                    "allowed_commands": ["ls", "pwd", "cat", "grep", "find", "echo", "which", "python", "node", "npm"],
                    "forbidden_commands": ["rm -rf", "sudo", "su", "chmod 777", "format"],
                    "max_execution_time": 30,
                    "sandbox_mode": True
                },
                security_level="high"
            ),
            "web_search": MCPToolConfig(
                tool_type=MCPToolType.WEB_SEARCH,
                name="Web Search",
                description="Search the web for information",
                config={
                    "search_engines": ["duckduckgo", "bing"],
                    "max_results": 10,
                    "safe_search": True,
                    "timeout": 10
                },
                security_level="low"
            ),
            "file_system": MCPToolConfig(
                tool_type=MCPToolType.FILE_SYSTEM,
                name="File System Access",
                description="Safe file system operations",
                config={
                    "allowed_paths": ["./", "../", "/tmp/", "/home/"],
                    "forbidden_paths": ["/etc/", "/root/", "/sys/", "/proc/"],
                    "max_file_size": "10MB",
                    "allowed_extensions": [".txt", ".md", ".py", ".js", ".json", ".yaml", ".yml"]
                },
                security_level="medium"
            ),
            "environment": MCPToolConfig(
                tool_type=MCPToolType.ENVIRONMENT,
                name="Environment Manager",
                description="Manage environment variables and system info",
                config={
                    "allowed_env_vars": ["PATH", "HOME", "USER", "SHELL"],
                    "forbidden_env_vars": ["PASSWORD", "SECRET", "TOKEN", "KEY"],
                    "read_only": True
                },
                security_level="medium"
            ),
            "docker": MCPToolConfig(
                tool_type=MCPToolType.DOCKER,
                name="Docker Manager",
                description="Manage Docker containers and images",
                config={
                    "allowed_commands": ["ps", "images", "logs", "inspect"],
                    "forbidden_commands": ["rm", "rmi", "kill", "stop"],
                    "read_only": True
                },
                security_level="high"
            ),
            "git": MCPToolConfig(
                tool_type=MCPToolType.GIT,
                name="Git Operations",
                description="Git repository operations",
                config={
                    "allowed_commands": ["status", "log", "diff", "show", "branch", "remote"],
                    "forbidden_commands": ["push", "pull", "merge", "rebase", "reset --hard"],
                    "read_only": True
                },
                security_level="medium"
            ),
            "system_info": MCPToolConfig(
                tool_type=MCPToolType.SYSTEM_INFO,
                name="System Information",
                description="Get system information and metrics",
                config={
                    "include_metrics": ["cpu", "memory", "disk", "network"],
                    "exclude_sensitive": True
                },
                security_level="low"
            )
        }
        
        self.tools = tools_config
        self.logger.info(f"Initialized {len(tools_config)} MCP tools")
    
    async def execute_wsl2_command(self, command: str, distribution: str = None) -> Dict[str, Any]:
        """Execute command in WSL2"""
        try:
            tool_config = self.tools["wsl2_manager"]
            if not tool_config.enabled:
                raise ValueError("WSL2 tool is disabled")
            
            # Security check
            if not self._is_command_safe(command, tool_config.config["allowed_commands"], 
                                        tool_config.config["forbidden_commands"]):
                raise ValueError(f"Command not allowed: {command}")
            
            # Check if WSL2 is available
            if platform.system() != "Windows":
                raise ValueError("WSL2 is only available on Windows")
            
            # Use default distribution if not specified
            dist = distribution or tool_config.config["default_distribution"]
            
            # Construct WSL command
            wsl_command = f"wsl -d {dist} -- {command}"
            
            # Execute command
            result = await self._execute_command(
                wsl_command, 
                timeout=tool_config.config["max_execution_time"]
            )
            
            return {
                "success": True,
                "command": command,
                "distribution": dist,
                "output": result["output"],
                "error": result["error"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            self.logger.error(f"WSL2 command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def execute_terminal_command(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """Execute terminal command with safety checks"""
        try:
            tool_config = self.tools["terminal_executor"]
            if not tool_config.enabled:
                raise ValueError("Terminal tool is disabled")
            
            # Security check
            if not self._is_command_safe(command, tool_config.config["allowed_commands"], 
                                        tool_config.config["forbidden_commands"]):
                raise ValueError(f"Command not allowed: {command}")
            
            # Execute command
            result = await self._execute_command(
                command,
                cwd=working_dir,
                timeout=tool_config.config["max_execution_time"]
            )
            
            return {
                "success": True,
                "command": command,
                "working_directory": working_dir or os.getcwd(),
                "output": result["output"],
                "error": result["error"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            self.logger.error(f"Terminal command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def web_search(self, query: str, max_results: int = None) -> Dict[str, Any]:
        """Perform web search"""
        try:
            tool_config = self.tools["web_search"]
            if not tool_config.enabled:
                raise ValueError("Web search tool is disabled")
            
            max_results = max_results or tool_config.config["max_results"]
            
            # Use DuckDuckGo for privacy-focused search
            search_results = await self._duckduckgo_search(query, max_results)
            
            return {
                "success": True,
                "query": query,
                "results": search_results,
                "count": len(search_results)
            }
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get file content with safety checks"""
        try:
            tool_config = self.tools["file_system"]
            if not tool_config.enabled:
                raise ValueError("File system tool is disabled")
            
            path = Path(file_path)
            
            # Security checks
            if not self._is_path_safe(str(path), tool_config.config["allowed_paths"], 
                                    tool_config.config["forbidden_paths"]):
                raise ValueError(f"Path not allowed: {file_path}")
            
            if not path.exists():
                raise ValueError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Check file size
            file_size = path.stat().st_size
            max_size = self._parse_size(tool_config.config["max_file_size"])
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")
            
            # Check file extension
            if path.suffix not in tool_config.config["allowed_extensions"]:
                raise ValueError(f"File extension not allowed: {path.suffix}")
            
            # Read file content
            content = path.read_text(encoding='utf-8')
            
            return {
                "success": True,
                "file_path": str(path),
                "content": content,
                "size": file_size,
                "extension": path.suffix
            }
            
        except Exception as e:
            self.logger.error(f"File read failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        try:
            tool_config = self.tools["environment"]
            if not tool_config.enabled:
                raise ValueError("Environment tool is disabled")
            
            env_info = {}
            
            # Get allowed environment variables
            for var in tool_config.config["allowed_env_vars"]:
                env_info[var] = os.environ.get(var, "Not set")
            
            # Get system information
            system_info = {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
            
            return {
                "success": True,
                "environment_variables": env_info,
                "system_info": system_info
            }
            
        except Exception as e:
            self.logger.error(f"Environment info failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_docker_info(self) -> Dict[str, Any]:
        """Get Docker information"""
        try:
            tool_config = self.tools["docker"]
            if not tool_config.enabled:
                raise ValueError("Docker tool is disabled")
            
            # Check if Docker is available
            if not shutil.which("docker"):
                raise ValueError("Docker not found")
            
            # Get Docker containers
            containers_result = await self._execute_command("docker ps -a --format json")
            containers = []
            if containers_result["return_code"] == 0:
                for line in containers_result["output"].strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
            
            # Get Docker images
            images_result = await self._execute_command("docker images --format json")
            images = []
            if images_result["return_code"] == 0:
                for line in images_result["output"].strip().split('\n'):
                    if line:
                        images.append(json.loads(line))
            
            return {
                "success": True,
                "containers": containers,
                "images": images,
                "docker_available": True
            }
            
        except Exception as e:
            self.logger.error(f"Docker info failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "docker_available": False
            }
    
    async def get_git_info(self, repo_path: str = ".") -> Dict[str, Any]:
        """Get Git repository information"""
        try:
            tool_config = self.tools["git"]
            if not tool_config.enabled:
                raise ValueError("Git tool is disabled")
            
            # Check if path is a git repository
            git_dir = Path(repo_path) / ".git"
            if not git_dir.exists():
                raise ValueError(f"Not a git repository: {repo_path}")
            
            # Get git status
            status_result = await self._execute_command("git status --porcelain", cwd=repo_path)
            
            # Get current branch
            branch_result = await self._execute_command("git branch --show-current", cwd=repo_path)
            
            # Get recent commits
            log_result = await self._execute_command("git log --oneline -10", cwd=repo_path)
            
            # Get remote info
            remote_result = await self._execute_command("git remote -v", cwd=repo_path)
            
            return {
                "success": True,
                "repository_path": repo_path,
                "current_branch": branch_result["output"].strip() if branch_result["return_code"] == 0 else "unknown",
                "status": status_result["output"].strip() if status_result["return_code"] == 0 else "",
                "recent_commits": log_result["output"].strip().split('\n') if log_result["return_code"] == 0 else [],
                "remotes": remote_result["output"].strip().split('\n') if remote_result["return_code"] == 0 else []
            }
            
        except Exception as e:
            self.logger.error(f"Git info failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository_path": repo_path
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics and information"""
        try:
            tool_config = self.tools["system_info"]
            if not tool_config.enabled:
                raise ValueError("System info tool is disabled")
            
            metrics = {}
            
            # CPU information
            if "cpu" in tool_config.config["include_metrics"]:
                cpu_result = await self._execute_command("python3 -c \"import psutil; print(psutil.cpu_percent(interval=1))\"")
                if cpu_result["return_code"] == 0:
                    metrics["cpu_usage_percent"] = float(cpu_result["output"].strip())
            
            # Memory information
            if "memory" in tool_config.config["include_metrics"]:
                mem_result = await self._execute_command("python3 -c \"import psutil; m=psutil.virtual_memory(); print(f'{m.percent},{m.total},{m.available}')\"")
                if mem_result["return_code"] == 0:
                    mem_data = mem_result["output"].strip().split(',')
                    metrics["memory"] = {
                        "usage_percent": float(mem_data[0]),
                        "total_bytes": int(mem_data[1]),
                        "available_bytes": int(mem_data[2])
                    }
            
            # Disk information
            if "disk" in tool_config.config["include_metrics"]:
                disk_result = await self._execute_command("python3 -c \"import psutil; d=psutil.disk_usage('/'); print(f'{d.percent},{d.total},{d.free}')\"")
                if disk_result["return_code"] == 0:
                    disk_data = disk_result["output"].strip().split(',')
                    metrics["disk"] = {
                        "usage_percent": float(disk_data[0]),
                        "total_bytes": int(disk_data[1]),
                        "free_bytes": int(disk_data[2])
                    }
            
            return {
                "success": True,
                "metrics": metrics,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"System metrics failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_command_safe(self, command: str, allowed: List[str], forbidden: List[str]) -> bool:
        """Check if command is safe to execute"""
        command_lower = command.lower()
        
        # Check forbidden commands
        for forbidden_cmd in forbidden:
            if forbidden_cmd.lower() in command_lower:
                return False
        
        # Check if command starts with allowed command
        command_parts = command.split()
        if command_parts:
            base_command = command_parts[0]
            return base_command in allowed
        
        return False
    
    def _is_path_safe(self, path: str, allowed: List[str], forbidden: List[str]) -> bool:
        """Check if path is safe to access"""
        path_normalized = os.path.normpath(path)
        
        # Check forbidden paths
        for forbidden_path in forbidden:
            if path_normalized.startswith(forbidden_path):
                return False
        
        # Check allowed paths
        for allowed_path in allowed:
            if path_normalized.startswith(allowed_path):
                return True
        
        return False
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    async def _execute_command(self, command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute command safely"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "output": stdout.decode('utf-8', errors='ignore'),
                "error": stderr.decode('utf-8', errors='ignore'),
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise ValueError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise ValueError(f"Command execution failed: {e}")
    
    async def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform DuckDuckGo search"""
        try:
            # Simple DuckDuckGo instant answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    data = await response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Instant Answer"),
                    "snippet": data.get("Abstract"),
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo Instant Answer"
                })
            
            # Add related topics
            for topic in data.get("RelatedTopics", [])[:max_results-len(results)]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo Related"
                    })
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP tools"""
        health_status = {
            "total_tools": len(self.tools),
            "enabled_tools": 0,
            "disabled_tools": 0,
            "tools": []
        }
        
        for tool_name, tool_config in self.tools.items():
            tool_health = {
                "name": tool_name,
                "type": tool_config.tool_type.value,
                "enabled": tool_config.enabled,
                "security_level": tool_config.security_level,
                "healthy": True
            }
            
            if tool_config.enabled:
                health_status["enabled_tools"] += 1
            else:
                health_status["disabled_tools"] += 1
            
            health_status["tools"].append(tool_health)
        
        health_status["overall_healthy"] = True
        
        return health_status
    
    def get_tool_config(self, tool_name: str) -> Optional[MCPToolConfig]:
        """Get configuration for a specific tool"""
        return self.tools.get(tool_name)
    
    def enable_tool(self, tool_name: str) -> bool:
        """Enable a specific tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = True
            self.logger.info(f"Enabled MCP tool: {tool_name}")
            return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """Disable a specific tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = False
            self.logger.info(f"Disabled MCP tool: {tool_name}")
            return True
        return False
