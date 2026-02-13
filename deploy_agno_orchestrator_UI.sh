#!/bin/bash

# 🎯 Comprehensive Agno Orchestrator UI Deployment Script
# Enhanced deployment with sub-agent creation and MCP tools integration
# Version: 2.0 - Production Ready

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_VERSION="2.0"
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-production}"
ENABLE_SUB_AGENTS="${ENABLE_SUB_AGENTS:-true}"
ENABLE_MCP_TOOLS="${ENABLE_MCP_TOOLS:-true}"
ENABLE_HEALTH_CHECKS="${ENABLE_HEALTH_CHECKS:-true}"
ENABLE_MONITORING="${ENABLE_MONITORING:-true}"

# Logging functions with timestamps
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}${BOLD}=== $1 ===${NC}\n"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    log_error "Deployment failed. Check logs above for details."
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate system requirements
validate_requirements() {
    log_step "Validating system requirements..."
    
    # Check Python 3.11+
    if ! command_exists python3; then
        error_exit "Python 3 not found. Please install Python 3.11+"
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        error_exit "Python 3.11+ required. Current version: $PYTHON_VERSION"
    fi
    log_success "Python $PYTHON_VERSION detected"
    
    # Check Node.js 18+
    if ! command_exists node; then
        error_exit "Node.js not found. Please install Node.js 18+"
    fi
    
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -lt 18 ]; then
        error_exit "Node.js 18+ required. Current version: $NODE_VERSION"
    fi
    log_success "Node.js $NODE_VERSION detected"
    
    # Check available ports
    for port in 3000 8000 8080 9000; do
        if lsof -i :$port >/dev/null 2>&1; then
            log_warning "Port $port is in use. This may cause conflicts."
        fi
    done
    
    log_success "System requirements validated"
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Create directory structure
create_directory_structure() {
    log_step "Creating enhanced directory structure..."
    
    # Core directories
    mkdir -p "$PROJECT_ROOT/configs/environments"
    mkdir -p "$PROJECT_ROOT/configs/agents"
    mkdir -p "$PROJECT_ROOT/configs/mcp_tools"
    mkdir -p "$PROJECT_ROOT/scripts/agents"
    mkdir -p "$PROJECT_ROOT/scripts/health_checks"
    mkdir -p "$PROJECT_ROOT/scripts/deployment"
    mkdir -p "$PROJECT_ROOT/templates/agent_configs"
    mkdir -p "$PROJECT_ROOT/templates/production"
    mkdir -p "$PROJECT_ROOT/src/serena/orchestration"
    mkdir -p "$PROJECT_ROOT/src/serena/mcp_tools"
    mkdir -p "$PROJECT_ROOT/src/serena/monitoring"
    mkdir -p "$PROJECT_ROOT/test/deployment"
    mkdir -p "$PROJECT_ROOT/test/orchestration"
    mkdir -p "$PROJECT_ROOT/docs/deployment"
    mkdir -p "$PROJECT_ROOT/docs/orchestration"
    mkdir -p "$PROJECT_ROOT/logs"
    
    log_success "Directory structure created"
}

log_header "🎯 Agno Orchestrator UI - Comprehensive Deployment v$SCRIPT_VERSION"
log_info "Project root: $PROJECT_ROOT"
log_info "Deployment mode: $DEPLOYMENT_MODE"
log_info "Sub-agents enabled: $ENABLE_SUB_AGENTS"
log_info "MCP tools enabled: $ENABLE_MCP_TOOLS"
log_info "Health checks enabled: $ENABLE_HEALTH_CHECKS"

# Function to install Python dependencies
install_python_deps() {
    log_header "Installing Python Dependencies"
    
    # Install uv if not present
    if ! command -v uv >/dev/null 2>&1; then
        log_info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Install Serena with all extras
    log_info "Installing Serena with all dependencies..."
    cd "$PROJECT_ROOT"
    uv pip install --all-extras -e .
    
    # Install additional dependencies for orchestration
    uv pip install agno pytest pytest-asyncio pytest-cov pytest-mock psutil aiohttp pyyaml
    
    log_success "Python dependencies installed"
}

# Function to setup frontend
setup_frontend() {
    log_header "Setting up Frontend (Agno UI)"
    
    # Install pnpm if not present
    if ! command -v pnpm >/dev/null 2>&1; then
        log_info "Installing pnpm..."
        npm install -g pnpm
    fi
    
    # Clone agent-ui if not exists
    if [ ! -d "$PROJECT_ROOT/agno-ui" ]; then
        log_info "Cloning Agno UI repository..."
        git clone https://github.com/agno-agi/agent-ui.git "$PROJECT_ROOT/agno-ui"
    fi
    
    # Install frontend dependencies
    log_info "Installing frontend dependencies..."
    cd "$PROJECT_ROOT/agno-ui"
    pnpm install
    
    # Build frontend
    log_info "Building frontend..."
    pnpm build
    
    log_success "Frontend setup completed"
}

# Function to create configuration files
create_config_files() {
    log_header "Creating Configuration Files"
    
    # Create .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_info "Creating .env file..."
        cat > "$PROJECT_ROOT/.env" << EOF
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

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

# Feature Flags
ENABLE_SUB_AGENTS=true
ENABLE_MCP_TOOLS=true
ENABLE_HEALTH_CHECKS=true
ENABLE_MONITORING=true

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here
EOF
        log_success ".env file created"
    else
        log_info ".env file already exists"
    fi
    
    # Create agent configuration
    mkdir -p "$PROJECT_ROOT/configs/agents"
    if [ ! -f "$PROJECT_ROOT/configs/agents/coding_agent.yaml" ]; then
        log_info "Creating agent configuration..."
        cat > "$PROJECT_ROOT/configs/agents/coding_agent.yaml" << EOF
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
EOF
        log_success "Agent configuration created"
    fi
    
    # Create MCP tools configuration
    mkdir -p "$PROJECT_ROOT/configs/mcp"
    if [ ! -f "$PROJECT_ROOT/configs/mcp/tools.yaml" ]; then
        log_info "Creating MCP tools configuration..."
        cat > "$PROJECT_ROOT/configs/mcp/tools.yaml" << EOF
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
EOF
        log_success "MCP tools configuration created"
    fi
}

# Function to run tests
run_tests() {
    log_header "Running Tests"
    
    cd "$PROJECT_ROOT"
    
    # Set environment variables for testing
    export PYTHONPATH="$PROJECT_ROOT/src"
    export TESTING=true
    export LOG_LEVEL=DEBUG
    
    # Run basic functionality tests
    log_info "Testing core components..."
    
    # Test AgentType enum
    python3 -c "
import sys
sys.path.insert(0, 'src')
from src.serena.orchestration.sub_agent_manager import AgentType
print('✅ AgentType imported successfully')
print('Available types:', [t.value for t in AgentType])
"
    
    # Test MCP Tools Manager
    python3 -c "
import sys
sys.path.insert(0, 'src')
from src.serena.mcp_tools.mcp_manager import MCPToolsManager
manager = MCPToolsManager()
print('✅ MCPToolsManager initialized successfully')
print('Available tools:', list(manager.tools.keys()))
"
    
    # Test Health Monitor
    python3 -c "
import sys
sys.path.insert(0, 'src')
from src.serena.monitoring.health_monitor import HealthMonitor
monitor = HealthMonitor()
print('✅ HealthMonitor initialized successfully')
print('Health checks:', list(monitor.health_checks.keys()))
"
    
    log_success "Core component tests passed"
}

# Function to create startup scripts
create_startup_scripts() {
    log_header "Creating Startup Scripts"
    
    # Create backend startup script
    cat > "$PROJECT_ROOT/start_backend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src"
source .env 2>/dev/null || true
python3 -m src.serena.server --port 8000
EOF
    chmod +x "$PROJECT_ROOT/start_backend.sh"
    
    # Create frontend startup script
    cat > "$PROJECT_ROOT/start_frontend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/agno-ui"
pnpm dev --port 3000
EOF
    chmod +x "$PROJECT_ROOT/start_frontend.sh"
    
    # Create combined startup script
    cat > "$PROJECT_ROOT/start_dashboard.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Starting Serena Orchestrator UI..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Health: http://localhost:8000/health"
echo ""

# Start backend in background
echo "Starting backend..."
./start_backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait
EOF
    chmod +x "$PROJECT_ROOT/start_dashboard.sh"
    
    log_success "Startup scripts created"
}

# Function to display final instructions
display_final_instructions() {
    log_header "🎉 Deployment Complete!"
    
    echo -e "${GREEN}✅ Serena Orchestrator UI has been successfully deployed!${NC}"
    echo ""
    echo -e "${CYAN}📋 Next Steps:${NC}"
    echo -e "1. ${YELLOW}Configure API Keys:${NC} Edit .env file with your API keys"
    echo -e "2. ${YELLOW}Start Services:${NC} Run ./start_dashboard.sh"
    echo -e "3. ${YELLOW}Access Dashboard:${NC} Open http://localhost:3000"
    echo -e "4. ${YELLOW}Check Health:${NC} Visit http://localhost:8000/health"
    echo ""
    echo -e "${CYAN}🔧 Available Commands:${NC}"
    echo -e "• ${GREEN}./start_dashboard.sh${NC} - Start both frontend and backend"
    echo -e "• ${GREEN}./start_backend.sh${NC} - Start backend only"
    echo -e "• ${GREEN}./start_frontend.sh${NC} - Start frontend only"
    echo ""
    echo -e "${CYAN}📁 Key Directories:${NC}"
    echo -e "• ${GREEN}src/serena/orchestration/${NC} - Sub-agent management"
    echo -e "• ${GREEN}src/serena/mcp_tools/${NC} - MCP tools integration"
    echo -e "• ${GREEN}src/serena/monitoring/${NC} - Health monitoring"
    echo -e "• ${GREEN}configs/${NC} - Configuration files"
    echo -e "• ${GREEN}test/${NC} - Test suites"
    echo ""
    echo -e "${CYAN}🚀 Features Enabled:${NC}"
    echo -e "• ${GREEN}Sub-Agent Creation${NC} - Multi-agent orchestration"
    echo -e "• ${GREEN}MCP Tools Integration${NC} - WSL2, terminal, web search"
    echo -e "• ${GREEN}Health Monitoring${NC} - Comprehensive system monitoring"
    echo -e "• ${GREEN}Production Ready${NC} - Security and performance optimizations"
    echo ""
    echo -e "${PURPLE}Happy Orchestrating! 🎯${NC}"
}

# Main deployment flow
main() {
    log_header "🎯 Agno Orchestrator UI - Comprehensive Deployment v$SCRIPT_VERSION"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Deployment mode: $DEPLOYMENT_MODE"
    log_info "Sub-agents enabled: $ENABLE_SUB_AGENTS"
    log_info "MCP tools enabled: $ENABLE_MCP_TOOLS"
    log_info "Health checks enabled: $ENABLE_HEALTH_CHECKS"
    
    validate_requirements
    create_directory_structure
    install_python_deps
    setup_frontend
    create_config_files
    run_tests
    create_startup_scripts
    display_final_instructions
}

# Run main function
main "$@"
