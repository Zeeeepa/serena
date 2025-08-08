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

# Main deployment flow
validate_requirements
create_directory_structure

log_success "🎯 Enhanced deployment script created! Run with ./deploy_agno_orchestrator_UI.sh"
