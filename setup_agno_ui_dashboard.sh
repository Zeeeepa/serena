#!/bin/bash

# 🎯 Agno-UI Dashboard with Serena Integration Setup Script
# This script sets up the complete orchestration dashboard system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

log_header "🎯 Agno-UI Dashboard with Serena Integration Setup"
log_info "Project root: $PROJECT_ROOT"

# Check system requirements
log_header "🔍 Checking System Requirements"

# Check for Python 3.11+
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $PYTHON_VERSION"
    
    # Check if version is 3.11+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        log_success "Python 3.11+ detected"
    else
        log_error "Python 3.11+ required. Current version: $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check for Node.js 18+
if command_exists node; then
    NODE_VERSION=$(node --version)
    log_info "Node.js version: $NODE_VERSION"
    
    # Extract major version number
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -ge 18 ]; then
        log_success "Node.js 18+ detected"
    else
        log_error "Node.js 18+ required. Current version: $NODE_VERSION"
        exit 1
    fi
else
    log_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check for pnpm
if ! command_exists pnpm; then
    log_warning "pnpm not found. Installing pnpm..."
    npm install -g pnpm
    log_success "pnpm installed"
else
    log_success "pnpm detected"
fi

# Check for uv
if ! command_exists uv; then
    log_warning "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    log_success "uv installed"
else
    log_success "uv detected"
fi

# Install system dependencies
log_header "📦 Installing System Dependencies"

# Detect OS and install dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_info "Detected Linux system"
    
    # Check if running on Ubuntu/Debian
    if command_exists apt-get; then
        log_info "Installing dependencies with apt-get..."
        sudo apt-get update
        sudo apt-get install -y \
            git \
            curl \
            wget \
            build-essential \
            python3-dev \
            python3-pip \
            nodejs \
            npm \
            sqlite3 \
            libsqlite3-dev
    elif command_exists yum; then
        log_info "Installing dependencies with yum..."
        sudo yum install -y \
            git \
            curl \
            wget \
            gcc \
            gcc-c++ \
            make \
            python3-devel \
            python3-pip \
            nodejs \
            npm \
            sqlite \
            sqlite-devel
    else
        log_warning "Unknown Linux distribution. Please install dependencies manually."
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "Detected macOS system"
    
    # Check if Homebrew is installed
    if command_exists brew; then
        log_info "Installing dependencies with Homebrew..."
        brew install git curl wget python@3.11 node sqlite3
    else
        log_warning "Homebrew not found. Please install dependencies manually."
    fi
    
else
    log_warning "Unknown operating system. Please install dependencies manually."
fi

# Setup Python environment
log_header "🐍 Setting up Python Environment"

cd "$PROJECT_ROOT"

# Install Python dependencies
log_info "Installing Serena with all extras..."
uv pip install --all-extras -r pyproject.toml -e .

log_success "Python environment setup complete"

# Setup agent-ui frontend
log_header "🎨 Setting up Agent-UI Frontend"

AGNO_UI_DIR="$PROJECT_ROOT/agno-ui"

if [ ! -d "$AGNO_UI_DIR" ]; then
    log_info "Cloning agent-ui repository..."
    git clone https://github.com/agno-agi/agent-ui.git "$AGNO_UI_DIR"
else
    log_info "Agent-UI directory already exists, updating..."
    cd "$AGNO_UI_DIR"
    git pull origin main
fi

cd "$AGNO_UI_DIR"

log_info "Installing frontend dependencies..."
pnpm install

log_success "Agent-UI frontend setup complete"

# Create environment configuration
log_header "⚙️ Creating Environment Configuration"

cd "$PROJECT_ROOT"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating .env file..."
    cat > .env << 'EOF'
# API Keys - Fill these in with your actual keys
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

# GitHub Integration (optional)
GITHUB_TOKEN=your_github_token_here
GITHUB_ORG=your_github_org_here
EOF
    log_warning "Created .env file. Please fill in your API keys!"
else
    log_info ".env file already exists"
fi

# Create startup scripts
log_header "🚀 Creating Startup Scripts"

# Create backend startup script
cat > "$PROJECT_ROOT/start_backend.sh" << 'EOF'
#!/bin/bash
# Start Serena-Agno backend

cd "$(dirname "$0")"

echo "🚀 Starting Serena-Agno backend..."
echo "📍 Project root: $(pwd)"

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the agno agent
echo "🤖 Starting Agno agent with Serena integration..."
uv run python scripts/agno_agent.py
EOF

# Create frontend startup script
cat > "$PROJECT_ROOT/start_frontend.sh" << 'EOF'
#!/bin/bash
# Start Agent-UI frontend

cd "$(dirname "$0")/agno-ui"

echo "🎨 Starting Agent-UI frontend..."
echo "📍 Frontend directory: $(pwd)"

# Start the frontend
pnpm dev
EOF

# Create MCP server startup script
cat > "$PROJECT_ROOT/start_mcp_server.sh" << 'EOF'
#!/bin/bash
# Start Serena MCP server

cd "$(dirname "$0")"

echo "🔧 Starting Serena MCP server..."
echo "📍 Project root: $(pwd)"

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the MCP server
uv run python scripts/mcp_server.py
EOF

# Create complete startup script
cat > "$PROJECT_ROOT/start_dashboard.sh" << 'EOF'
#!/bin/bash
# Start complete Agno-UI Dashboard with Serena integration

cd "$(dirname "$0")"

echo "🎯 Starting Agno-UI Dashboard with Serena Integration"
echo "📍 Project root: $(pwd)"

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    jobs -p | xargs -r kill
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found. Please create one with your API keys."
fi

# Start MCP server in background
echo "🔧 Starting MCP server..."
./start_mcp_server.sh &
MCP_PID=$!
sleep 2

# Start backend in background
echo "🤖 Starting Serena-Agno backend..."
./start_backend.sh &
BACKEND_PID=$!
sleep 5

# Start frontend in background
echo "🎨 Starting Agent-UI frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🎉 Dashboard services started!"
echo "📊 Frontend: http://localhost:3000"
echo "🤖 Backend: http://localhost:8000"
echo "🔧 MCP Server: Running"
echo ""
echo "💡 Connect the UI to the agent and start orchestrating!"
echo "🛑 Press Ctrl+C to stop all services"

# Wait for all background processes
wait
EOF

# Make scripts executable
chmod +x "$PROJECT_ROOT/start_backend.sh"
chmod +x "$PROJECT_ROOT/start_frontend.sh"
chmod +x "$PROJECT_ROOT/start_mcp_server.sh"
chmod +x "$PROJECT_ROOT/start_dashboard.sh"

log_success "Startup scripts created"

# Add aliases to bashrc
log_header "🔗 Adding Aliases to Shell Configuration"

# Determine shell configuration file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
fi

log_info "Adding aliases to $SHELL_CONFIG"

# Create alias section
ALIAS_SECTION="
# 🎯 Agno-UI Dashboard with Serena Integration Aliases
export AGNO_SERENA_ROOT=\"$PROJECT_ROOT\"

# Navigation aliases
alias agno-cd=\"cd \$AGNO_SERENA_ROOT\"
alias agno-ui-cd=\"cd \$AGNO_SERENA_ROOT/agno-ui\"

# Service startup aliases
alias start-backend=\"\$AGNO_SERENA_ROOT/start_backend.sh\"
alias start-frontend=\"\$AGNO_SERENA_ROOT/start_frontend.sh\"
alias start-mcp=\"\$AGNO_SERENA_ROOT/start_mcp_server.sh\"

# Main dashboard startup alias
alias start=\"\$AGNO_SERENA_ROOT/start_dashboard.sh\"

# Utility aliases
alias agno-logs=\"tail -f \$AGNO_SERENA_ROOT/logs/*.log\"
alias agno-status=\"ps aux | grep -E '(agno|serena|mcp)' | grep -v grep\"
alias agno-env=\"cat \$AGNO_SERENA_ROOT/.env\"

# Development aliases
alias agno-test=\"cd \$AGNO_SERENA_ROOT && uv run poe test\"
alias agno-format=\"cd \$AGNO_SERENA_ROOT && uv run poe format\"
alias agno-type-check=\"cd \$AGNO_SERENA_ROOT && uv run poe type-check\"
"

# Check if aliases already exist
if grep -q "Agno-UI Dashboard with Serena Integration Aliases" "$SHELL_CONFIG" 2>/dev/null; then
    log_info "Aliases already exist in $SHELL_CONFIG"
else
    echo "$ALIAS_SECTION" >> "$SHELL_CONFIG"
    log_success "Aliases added to $SHELL_CONFIG"
fi

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Create quick start guide
log_header "📚 Creating Quick Start Guide"

cat > "$PROJECT_ROOT/QUICK_START.md" << 'EOF'
# 🎯 Agno-UI Dashboard with Serena Integration - Quick Start

## 🚀 Starting the Dashboard

### Option 1: Use the alias (recommended)
```bash
start
```

### Option 2: Use the script directly
```bash
./start_dashboard.sh
```

### Option 3: Start services individually
```bash
# Start MCP server
./start_mcp_server.sh

# Start backend (in new terminal)
./start_backend.sh

# Start frontend (in new terminal)
./start_frontend.sh
```

## 🌐 Access Points

- **Dashboard UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **MCP Server**: Running in background

## 🔧 Configuration

1. **Edit `.env` file** with your API keys:
   ```bash
   nano .env
   ```

2. **Required API Keys**:
   - `OPENAI_API_KEY` - For OpenAI models
   - `ANTHROPIC_API_KEY` - For Claude models  
   - `GOOGLE_API_KEY` - For Gemini models

## 🎯 Using the Dashboard

1. **Open** http://localhost:3000 in your browser
2. **Connect** the UI to the running agent
3. **Start orchestrating** your coding tasks!

## 🛠️ Available Aliases

- `start` - Start complete dashboard
- `start-backend` - Start only backend
- `start-frontend` - Start only frontend
- `start-mcp` - Start only MCP server
- `agno-cd` - Navigate to project root
- `agno-status` - Check running services
- `agno-logs` - View logs

## 🔍 Troubleshooting

- **Check logs**: `agno-logs`
- **Check services**: `agno-status`
- **Restart**: Stop with Ctrl+C and run `start` again

## 🎉 Features

- **Project Selection** with GitHub integration
- **Real-time Progress Tracking** 
- **MCP Tool Integration**
- **Sub-agent Orchestration**
- **Semantic Code Analysis** via Serena
- **Multi-language Support** (13+ languages)
EOF

# Final setup completion
log_header "✅ Setup Complete!"

echo -e "${GREEN}"
cat << 'EOF'
🎉 Agno-UI Dashboard with Serena Integration Setup Complete!

📋 What was installed:
✅ Python dependencies with uv
✅ Agent-UI frontend with pnpm
✅ Startup scripts and aliases
✅ Environment configuration
✅ Shell aliases added

🚀 Next Steps:
1. Edit .env file with your API keys:
   nano .env

2. Reload your shell or run:
   source ~/.bashrc  (or ~/.zshrc)

3. Start the dashboard:
   start

4. Open http://localhost:3000 in your browser

📚 Documentation:
- Quick Start Guide: ./QUICK_START.md
- Project Root: $PROJECT_ROOT

🎯 Ready to orchestrate with Serena + Agno!
EOF
echo -e "${NC}"

# Print the start command
log_header "🎯 Dashboard Start Command"
echo -e "${CYAN}To start the complete dashboard system:${NC}"
echo -e "${YELLOW}start${NC}"
echo ""
echo -e "${CYAN}Or use the full path:${NC}"
echo -e "${YELLOW}$PROJECT_ROOT/start_dashboard.sh${NC}"

log_success "Setup script completed successfully!"

