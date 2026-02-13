# 🎯 Serena Orchestrator UI - Comprehensive Deployment Guide

## 🚀 **Complete Agno Orchestrator with Sub-Agent Creation & MCP Tools**

This guide covers the deployment of the enhanced Serena Orchestrator UI with comprehensive sub-agent management, MCP tools integration, health monitoring, and production-ready features.

---

## 📋 **Table of Contents**

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Architecture Overview](#architecture-overview)
4. [Installation Methods](#installation-methods)
5. [Configuration](#configuration)
6. [Sub-Agent Management](#sub-agent-management)
7. [MCP Tools Integration](#mcp-tools-integration)
8. [Health Monitoring](#health-monitoring)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)

---

## 🚀 **Quick Start**

### **One-Command Deployment**

```bash
# Clone and deploy
git clone https://github.com/Zeeeepa/serena.git
cd serena
./deploy_agno_orchestrator_UI.sh
```

### **Access Points**

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard UI** | http://localhost:3000 | Main orchestration interface |
| **Backend API** | http://localhost:8000 | Serena-Agno agent endpoint |
| **Health Monitor** | http://localhost:8000/health | System health dashboard |
| **Metrics** | http://localhost:8000/metrics | Performance metrics |

---

## 💻 **System Requirements**

### **Minimum Requirements**
- **OS**: Linux, macOS, Windows (with WSL2)
- **Python**: 3.11+
- **Node.js**: 18+
- **Memory**: 4GB RAM
- **Storage**: 10GB free space
- **Network**: Internet connection for API access

### **Recommended Requirements**
- **Memory**: 8GB+ RAM
- **CPU**: 4+ cores
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet

### **Production Requirements**
- **Memory**: 16GB+ RAM
- **CPU**: 8+ cores
- **Storage**: 100GB+ SSD
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Load Balancer**: Nginx/HAProxy

---

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERENA ORCHESTRATOR UI                       │
│                   (Agent-UI Frontend)                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ORCHESTRATION LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Sub-Agent      │  │   MCP Tools     │  │ Health Monitor  │ │
│  │   Manager       │  │    Manager      │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SERENA CORE                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Language Server │  │   Tool System   │  │ Memory System   │ │
│  │   (LSP)         │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 EXECUTION ENVIRONMENT                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     WSL2        │  │    Terminal     │  │   Web Search    │ │
│  │   (Windows)     │  │   Operations    │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Components**

1. **Frontend UI**: Modern React-based dashboard
2. **Sub-Agent Manager**: Multi-agent orchestration system
3. **MCP Tools Manager**: Environment and system access
4. **Health Monitor**: Comprehensive system monitoring
5. **Serena Core**: Semantic coding and LSP integration
6. **Execution Environment**: Sandboxed tool execution

---

## 📦 **Installation Methods**

### **Method 1: Automated Deployment (Recommended)**

```bash
# Download and run deployment script
curl -sSL https://raw.githubusercontent.com/Zeeeepa/serena/main/deploy_agno_orchestrator_UI.sh | bash
```

### **Method 2: Manual Installation**

```bash
# 1. Clone repository
git clone https://github.com/Zeeeepa/serena.git
cd serena

# 2. Install Python dependencies
python3 -m pip install uv
uv pip install --all-extras -r pyproject.toml -e .

# 3. Install Node.js dependencies
npm install -g pnpm
git clone https://github.com/agno-agi/agent-ui.git agno-ui
cd agno-ui && pnpm install && cd ..

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start services
./start_dashboard.sh
```

### **Method 3: Docker Deployment**

```bash
# Using Docker Compose
docker-compose up -d

# Or build from source
docker build -t serena-orchestrator .
docker run -p 3000:3000 -p 8000:8000 serena-orchestrator
```

---

## ⚙️ **Configuration**

### **Environment Variables**

Create a `.env` file with the following configuration:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Agno Configuration
AGNO_MONITOR=false
AGNO_TELEMETRY=true

# Serena Configuration
SERENA_LOG_LEVEL=INFO
SERENA_DEBUG=false

# MCP Configuration
MCP_SERVER_PORT=8000
MCP_CLIENT_TIMEOUT=30

# Dashboard Configuration
DASHBOARD_PORT=3000
WEBSOCKET_PORT=8080

# Database (Production)
DB_HOST=localhost
DB_NAME=serena_orchestrator
DB_USER=serena
DB_PASSWORD=your_secure_password

# Redis (Production)
REDIS_HOST=localhost
REDIS_PASSWORD=your_redis_password

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Feature Flags
ENABLE_SUB_AGENTS=true
ENABLE_MCP_TOOLS=true
ENABLE_HEALTH_CHECKS=true
ENABLE_MONITORING=true
```

### **Configuration Files**

The system uses YAML configuration files for different environments:

- `configs/environments/development.yaml` - Development settings
- `configs/environments/staging.yaml` - Staging settings
- `configs/environments/production.yaml` - Production settings

### **Agent Templates**

Configure agent templates in `configs/agents/`:

```yaml
# configs/agents/coding_agent.yaml
agent_type: "coding"
model: "gemini-1.5-pro"
max_tokens: 8192
temperature: 0.7
tools:
  - "file_tools"
  - "symbol_tools"
  - "git_tools"
memory_enabled: true
custom_instructions: |
  You are a specialized coding agent. Focus on:
  - Writing clean, maintainable code
  - Following best practices and patterns
  - Comprehensive error handling
  - Performance optimization
  - Security considerations
```

---

## 🤖 **Sub-Agent Management**

### **Agent Types Available**

1. **Coding Agent** - Code generation, refactoring, debugging
2. **Research Agent** - Information gathering and analysis
3. **Testing Agent** - Test creation and quality assurance
4. **Documentation Agent** - Comprehensive documentation
5. **Review Agent** - Code and document review
6. **Deployment Agent** - Deployment and infrastructure
7. **Monitoring Agent** - System monitoring and observability

### **Creating Sub-Agents**

```python
from src.serena.orchestration.sub_agent_manager import SubAgentManager, AgentType

# Initialize manager
manager = SubAgentManager()

# Create a coding agent
agent_id = await manager.create_agent(
    agent_type=AgentType.CODING,
    name="Senior Python Developer",
    custom_config={
        "model": "gemini-1.5-pro",
        "temperature": 0.7,
        "tools": ["file_tools", "symbol_tools", "git_tools"]
    }
)

# Start the agent
await manager.start_agent(agent_id)

# Execute a task
result = await manager.execute_task(
    agent_id=agent_id,
    task="Refactor this Python function for better performance",
    context={"file_path": "src/example.py"}
)
```

### **Agent Orchestration**

```python
# Create multiple agents for a complex task
coding_agent = await manager.create_agent(AgentType.CODING)
testing_agent = await manager.create_agent(AgentType.TESTING)
review_agent = await manager.create_agent(AgentType.REVIEW)

# Start all agents
await manager.start_agent(coding_agent)
await manager.start_agent(testing_agent)
await manager.start_agent(review_agent)

# Orchestrate workflow
code_result = await manager.execute_task(coding_agent, "Implement user authentication")
test_result = await manager.execute_task(testing_agent, "Create tests for authentication")
review_result = await manager.execute_task(review_agent, "Review authentication implementation")
```

### **Agent Health Monitoring**

```python
# Check agent status
status = await manager.get_agent_status(agent_id)
print(f"Agent {status['name']} is {status['status']}")

# List all agents
agents = await manager.list_agents()
for agent in agents:
    print(f"{agent['name']}: {agent['status']} ({agent['task_count']} tasks)")

# Health check
health = await manager.health_check()
print(f"Overall healthy: {health['overall_healthy']}")
```

---

## 🛠️ **MCP Tools Integration**

### **Available MCP Tools**

1. **WSL2 Manager** - Windows Subsystem for Linux operations
2. **Terminal Executor** - Safe terminal command execution
3. **Web Search** - Internet search capabilities
4. **File System** - Secure file operations
5. **Environment Manager** - System information and variables
6. **Docker Manager** - Container management (read-only)
7. **Git Operations** - Repository information (read-only)
8. **System Info** - Performance metrics and monitoring

### **Using MCP Tools**

```python
from src.serena.mcp_tools.mcp_manager import MCPToolsManager

# Initialize MCP tools manager
mcp_manager = MCPToolsManager()

# Execute terminal command
result = await mcp_manager.execute_terminal_command("ls -la")
print(result["output"])

# Perform web search
search_result = await mcp_manager.web_search("Python best practices")
for result in search_result["results"]:
    print(f"{result['title']}: {result['snippet']}")

# Get system metrics
metrics = await mcp_manager.get_system_metrics()
print(f"CPU: {metrics['metrics']['cpu_usage_percent']}%")

# WSL2 operations (Windows only)
if platform.system() == "Windows":
    wsl_result = await mcp_manager.execute_wsl2_command("python3 --version")
    print(wsl_result["output"])
```

### **Security Configuration**

MCP tools include comprehensive security features:

```yaml
# configs/mcp_tools.yaml
security:
  sandbox_mode: true
  allowed_commands:
    - "ls"
    - "pwd"
    - "cat"
    - "grep"
    - "find"
    - "python3"
    - "node"
    - "npm"
  forbidden_commands:
    - "rm -rf"
    - "sudo"
    - "su"
    - "chmod 777"
    - "format"
  max_execution_time: 30
  max_file_size: "10MB"
  allowed_paths:
    - "./"
    - "/tmp/"
  forbidden_paths:
    - "/etc/"
    - "/root/"
    - "/sys/"
```

---

## 📊 **Health Monitoring**

### **Health Check System**

The system includes comprehensive health monitoring:

```python
from src.serena.monitoring.health_monitor import HealthMonitor

# Initialize health monitor
monitor = HealthMonitor()

# Start monitoring
await monitor.start_monitoring()

# Get health summary
health = await monitor.get_health_summary()
print(f"Overall status: {health['overall_status']}")
print(f"Critical alerts: {health['stats']['critical_alerts']}")

# Get metrics history
metrics = await monitor.get_metrics_history(hours=1)
for metric in metrics[-5:]:  # Last 5 entries
    print(f"{metric['timestamp']}: CPU {metric['cpu_percent']}%")
```

### **Available Health Checks**

1. **System CPU Usage** - Monitor CPU utilization
2. **System Memory Usage** - Track memory consumption
3. **System Disk Usage** - Monitor disk space
4. **System Load Average** - Check system load
5. **Service Port Availability** - Verify service ports
6. **Agent Processes** - Monitor agent health
7. **MCP Tools Health** - Check tool availability
8. **Network Connectivity** - Test internet access
9. **Storage Health** - Monitor storage devices

### **Custom Health Checks**

```python
# Add custom health check
custom_check = HealthCheck(
    name="Custom API Health",
    component_type=ComponentType.SERVICE,
    description="Check external API availability",
    check_function="check_custom_api",
    interval_seconds=60,
    thresholds={"timeout": 5}
)

monitor.health_checks["custom_api"] = custom_check
```

### **Alerting Configuration**

```yaml
# configs/monitoring.yaml
alerting:
  enabled: true
  channels:
    - type: "email"
      recipients: ["admin@yourdomain.com"]
      severity: ["critical", "warning"]
    - type: "slack"
      webhook_url: "${SLACK_WEBHOOK_URL}"
      severity: ["critical"]
  
  thresholds:
    cpu_usage: 85
    memory_usage: 90
    disk_usage: 85
    response_time: 5000
    error_rate: 5
```

---

## 🏭 **Production Deployment**

### **Production Checklist**

- [ ] **Security**: SSL certificates, authentication, API keys
- [ ] **Database**: PostgreSQL with connection pooling
- [ ] **Cache**: Redis for session and data caching
- [ ] **Load Balancer**: Nginx or HAProxy configuration
- [ ] **Monitoring**: Prometheus, Grafana, alerting
- [ ] **Backup**: Automated database and config backups
- [ ] **Logging**: Centralized logging with log rotation
- [ ] **Scaling**: Auto-scaling configuration
- [ ] **Health Checks**: Comprehensive monitoring setup

### **Docker Production Deployment**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  serena-orchestrator:
    image: serena-orchestrator:latest
    ports:
      - "3000:3000"
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - DEPLOYMENT_MODE=production
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: serena_orchestrator
      POSTGRES_USER: serena
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - serena-orchestrator
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### **Kubernetes Deployment**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: serena-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: serena-orchestrator
  template:
    metadata:
      labels:
        app: serena-orchestrator
    spec:
      containers:
      - name: serena-orchestrator
        image: serena-orchestrator:latest
        ports:
        - containerPort: 3000
        - containerPort: 8000
        env:
        - name: DEPLOYMENT_MODE
          value: "production"
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: serena-secrets
              key: db-host
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### **Performance Optimization**

```yaml
# configs/environments/production.yaml
performance:
  caching:
    enabled: true
    default_ttl: 3600
    max_memory: "1GB"
    compression: true
  
  connection_pooling:
    enabled: true
    max_connections: 100
    min_connections: 10
    connection_timeout: 30
  
  resource_limits:
    max_memory_per_agent: "2GB"
    max_cpu_per_agent: 1.0
    max_concurrent_requests: 1000
    max_request_timeout: 300
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Port Already in Use**
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :8080  # MCP Server

# Kill processes if needed
sudo kill -9 $(lsof -t -i:3000)
```

#### **2. API Keys Not Working**
```bash
# Check environment variables
env | grep API_KEY

# Verify .env file
cat .env | grep API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### **3. Sub-Agents Not Starting**
```bash
# Check agent logs
tail -f logs/agents.log

# Verify agent configuration
python3 -c "
from src.serena.orchestration.sub_agent_manager import SubAgentManager
manager = SubAgentManager()
print(manager.agent_templates.keys())
"

# Test agent creation
python3 -c "
import asyncio
from src.serena.orchestration.sub_agent_manager import SubAgentManager, AgentType

async def test():
    manager = SubAgentManager()
    agent_id = await manager.create_agent(AgentType.CODING)
    print(f'Created agent: {agent_id}')

asyncio.run(test())
"
```

#### **4. MCP Tools Failing**
```bash
# Check MCP tools status
python3 -c "
import asyncio
from src.serena.mcp_tools.mcp_manager import MCPToolsManager

async def test():
    manager = MCPToolsManager()
    health = await manager.health_check()
    print(health)

asyncio.run(test())
"

# Test specific tool
python3 -c "
import asyncio
from src.serena.mcp_tools.mcp_manager import MCPToolsManager

async def test():
    manager = MCPToolsManager()
    result = await manager.execute_terminal_command('echo test')
    print(result)

asyncio.run(test())
"
```

#### **5. Health Monitoring Issues**
```bash
# Check health monitor status
curl http://localhost:8000/health

# View health logs
tail -f logs/health.log

# Test health checks manually
python3 -c "
import asyncio
from src.serena.monitoring.health_monitor import HealthMonitor

async def test():
    monitor = HealthMonitor()
    summary = await monitor.get_health_summary()
    print(summary)

asyncio.run(test())
"
```

### **Log Locations**

```bash
# Application logs
tail -f logs/app.log

# Agent logs
tail -f logs/agents.log

# MCP tools logs
tail -f logs/mcp_tools.log

# Health monitoring logs
tail -f logs/health.log

# System logs (Linux)
journalctl -u serena-orchestrator -f
```

### **Performance Debugging**

```bash
# Check system resources
htop
df -h
free -h

# Monitor network connections
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Check database connections (if using PostgreSQL)
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis (if using)
redis-cli info stats
```

---

## 📚 **API Reference**

### **Health Monitoring API**

```bash
# Get overall health status
GET /health

# Get detailed health summary
GET /api/v1/health/summary

# Get metrics history
GET /api/v1/health/metrics?hours=1

# Get specific health check
GET /api/v1/health/checks/{check_name}
```

### **Sub-Agent Management API**

```bash
# List all agents
GET /api/v1/agents

# Create new agent
POST /api/v1/agents
{
  "agent_type": "coding",
  "name": "Senior Developer",
  "config": {
    "model": "gemini-1.5-pro",
    "temperature": 0.7
  }
}

# Get agent status
GET /api/v1/agents/{agent_id}

# Execute task on agent
POST /api/v1/agents/{agent_id}/execute
{
  "task": "Refactor this function",
  "context": {"file_path": "src/example.py"}
}

# Start/stop agent
POST /api/v1/agents/{agent_id}/start
POST /api/v1/agents/{agent_id}/stop

# Remove agent
DELETE /api/v1/agents/{agent_id}
```

### **MCP Tools API**

```bash
# List available tools
GET /api/v1/mcp/tools

# Execute terminal command
POST /api/v1/mcp/terminal
{
  "command": "ls -la",
  "working_dir": "/home/user"
}

# Perform web search
POST /api/v1/mcp/search
{
  "query": "Python best practices",
  "max_results": 10
}

# Get file content
POST /api/v1/mcp/file
{
  "file_path": "/path/to/file.py"
}

# Get system metrics
GET /api/v1/mcp/system/metrics

# WSL2 operations (Windows only)
POST /api/v1/mcp/wsl2
{
  "command": "python3 --version",
  "distribution": "Ubuntu"
}
```

### **Configuration API**

```bash
# Get current configuration
GET /api/v1/config

# Update configuration
PUT /api/v1/config
{
  "feature_flags": {
    "enable_sub_agents": true,
    "enable_mcp_tools": true
  }
}

# Get environment info
GET /api/v1/config/environment
```

---

## 🎉 **Success!**

You now have a comprehensive Serena Orchestrator UI deployment with:

✅ **Sub-Agent Orchestration** - Multi-agent coordination and management  
✅ **MCP Tools Integration** - WSL2, terminal, web search capabilities  
✅ **Health Monitoring** - Comprehensive system monitoring and alerting  
✅ **Production Ready** - Security, scaling, and performance optimizations  
✅ **Complete Documentation** - Usage guides and troubleshooting  

### **Next Steps**

1. **Configure API Keys** - Add your LLM provider API keys
2. **Create Sub-Agents** - Set up agents for your specific use cases
3. **Customize MCP Tools** - Configure tools for your environment
4. **Set Up Monitoring** - Configure alerts and dashboards
5. **Deploy to Production** - Use production configuration templates

### **Support & Community**

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/serena/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/serena/discussions)
- **Discord**: [Community Discord](https://discord.gg/serena)

**Happy Orchestrating! 🎯**
