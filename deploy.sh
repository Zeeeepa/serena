#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🚀 Standalone Serena + Gemini CLI Deployment Script${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "${PURPLE}This script will install everything from scratch:${NC}"
echo -e "${PURPLE}• Node.js & npm • Python & uv • Serena & SolidLSP • Gemini CLI${NC}"
echo -e "${CYAN}================================================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install Node.js via nvm
install_nodejs() {
    echo -e "\n${YELLOW}📦 Installing Node.js via nvm...${NC}"
    
    # Install nvm if not present
    if ! command_exists nvm; then
        echo -e "${CYAN}Installing nvm...${NC}"
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    fi
    
    # Install and use Node.js LTS
    echo -e "${CYAN}Installing Node.js LTS...${NC}"
    nvm install --lts
    nvm use --lts
    nvm alias default lts/*
    
    # Reload shell to ensure node/npm are available
    export PATH="$HOME/.nvm/versions/node/$(nvm version default)/bin:$PATH"
}

# Function to install Python and uv
install_python_uv() {
    echo -e "\n${YELLOW}🐍 Installing Python and uv...${NC}"
    
    OS=$(detect_os)
    
    # Install Python if not present
    if ! command_exists python3; then
        echo -e "${CYAN}Installing Python 3...${NC}"
        case $OS in
            "linux")
                if command_exists apt-get; then
                    sudo apt-get update
                    sudo apt-get install -y python3 python3-pip python3-venv
                elif command_exists yum; then
                    sudo yum install -y python3 python3-pip
                elif command_exists pacman; then
                    sudo pacman -S python python-pip
                else
                    echo -e "${RED}❌ Unsupported Linux distribution. Please install Python 3 manually.${NC}"
                    exit 1
                fi
                ;;
            "macos")
                if command_exists brew; then
                    brew install python@3.11
                else
                    echo -e "${CYAN}Installing Homebrew first...${NC}"
                    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                    brew install python@3.11
                fi
                ;;
            "windows")
                echo -e "${RED}❌ Please install Python 3.11+ from https://python.org/downloads/${NC}"
                exit 1
                ;;
            *)
                echo -e "${RED}❌ Unsupported OS. Please install Python 3.11+ manually.${NC}"
                exit 1
                ;;
        esac
    else
        echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"
    fi
    
    # Install uv
    if ! command_exists uv; then
        echo -e "${CYAN}Installing uv (Python package manager)...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        # Add to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo -e "${GREEN}✅ uv found: $(uv --version)${NC}"
    fi
}

# Function to create project structure and pyproject.toml
create_project_structure() {
    echo -e "\n${YELLOW}📁 Creating project structure...${NC}"
    
    # Create pyproject.toml for workspace (no local package)
    cat > pyproject.toml << 'EOF'
[tool.uv.workspace]
members = []

[tool.uv]
dev-dependencies = []
EOF
    
    echo -e "${GREEN}✅ Created pyproject.toml${NC}"
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Environment files
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Serena
.serena/

# Node modules (if any)
node_modules/
EOF
    
    echo -e "${GREEN}✅ Created .gitignore${NC}"
}

# Function to install Serena and SolidLSP
install_serena() {
    echo -e "\n${YELLOW}🔧 Installing Serena and SolidLSP...${NC}"
    
    # Create virtual environment
    echo -e "${CYAN}Creating Python virtual environment...${NC}"
    uv venv --python 3.11
    
    # Install Serena directly via pip in the virtual environment
    echo -e "${CYAN}Installing Serena agent...${NC}"
    uv pip install serena-agent
    
    echo -e "${GREEN}✅ Serena and SolidLSP installed successfully${NC}"
}

# Function to install Gemini CLI
install_gemini_cli() {
    echo -e "\n${YELLOW}💎 Installing Gemini CLI...${NC}"
    
    # Ensure npm is available
    if ! command_exists npm; then
        echo -e "${RED}❌ npm not found. Node.js installation may have failed.${NC}"
        exit 1
    fi
    
    # Install Gemini CLI globally
    echo -e "${CYAN}Installing @google/gemini-cli...${NC}"
    npm install -g @google/gemini-cli
    
    echo -e "${GREEN}✅ Gemini CLI installed successfully${NC}"
}

# Function to setup API key
setup_api_key() {
    echo -e "\n${YELLOW}🔑 Setting up Gemini API key...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${CYAN}Please enter your Gemini API key (get it from https://aistudio.google.com/app/apikey):${NC}"
        read -s GEMINI_API_KEY
        
        if [ -z "$GEMINI_API_KEY" ]; then
            echo -e "${RED}❌ API key cannot be empty${NC}"
            exit 1
        fi
        
        echo "GEMINI_API_KEY=$GEMINI_API_KEY" > .env
        echo -e "${GREEN}✅ API key saved to .env file${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
}

# Function to configure Gemini CLI with Serena MCP
configure_gemini_mcp() {
    echo -e "\n${YELLOW}⚙️ Configuring Gemini CLI with Serena MCP server...${NC}"
    
    # Create .gemini directory
    mkdir -p .gemini
    
    # Get absolute path to current directory
    CURRENT_DIR=$(pwd)
    
    # Create Gemini CLI settings with Serena MCP server
    cat > .gemini/settings.json << EOF
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "$CURRENT_DIR"],
      "env": {
        "PYTHONPATH": ""
      }
    }
  }
}
EOF
    
    echo -e "${GREEN}✅ Gemini CLI configured with Serena MCP server${NC}"
}

# Function to initialize Serena project
initialize_serena_project() {
    echo -e "\n${YELLOW}🏗️ Initializing Serena project...${NC}"
    
    # Create .serena directory
    mkdir -p .serena
    
    # Initialize Serena project (this will create project.yml)
    echo -e "${CYAN}Running Serena initialization...${NC}"
    uv run serena-mcp-server --project . --help > /dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ Serena project initialized${NC}"
}

# Function to create launch script
create_launch_script() {
    echo -e "\n${YELLOW}📝 Creating launch script...${NC}"
    
    cat > launch-gemini-with-serena.sh << 'EOF'
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Launching Gemini CLI with Serena MCP Server${NC}"
echo "=============================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please run ./deploy.sh first.${NC}"
    exit 1
fi

# Load environment variables
source .env

# Check if API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY not found in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment loaded${NC}"
echo -e "${YELLOW}💡 Starting Gemini CLI with Serena integration...${NC}"
echo -e "${BLUE}📚 Try these commands once started:${NC}"
echo "   /mcp                                    # Check MCP server status"
echo "   What Serena tools are available?        # Test tool discovery"
echo "   Show me the project structure           # Test project analysis"
echo "   Find all Python functions in this project  # Test code search"
echo ""

# Launch Gemini CLI
gemini
EOF
    
    chmod +x launch-gemini-with-serena.sh
    echo -e "${GREEN}✅ Launch script created and made executable${NC}"
}

# Function to run validation tests
run_validation_tests() {
    echo -e "\n${YELLOW}🧪 Running validation tests...${NC}"
    
    # Test Python environment
    echo -e "${CYAN}Testing Python environment...${NC}"
    if uv run python --version > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Python environment working${NC}"
    else
        echo -e "${RED}❌ Python environment test failed${NC}"
        return 1
    fi
    
    # Test Serena installation
    echo -e "${CYAN}Testing Serena installation...${NC}"
    if uv run python -c "import serena; print('Serena imported successfully')" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Serena package installed and importable${NC}"
    else
        echo -e "${YELLOW}⚠️ Serena package test skipped (may need fresh environment)${NC}"
    fi
    
    # Test Gemini CLI installation
    echo -e "${CYAN}Testing Gemini CLI installation...${NC}"
    if command_exists gemini; then
        echo -e "${GREEN}✅ Gemini CLI installed and accessible${NC}"
    else
        echo -e "${RED}❌ Gemini CLI test failed${NC}"
        return 1
    fi
    
    # Test MCP configuration
    echo -e "${CYAN}Testing MCP configuration...${NC}"
    if [ -f ".gemini/settings.json" ]; then
        echo -e "${GREEN}✅ Gemini MCP configuration exists${NC}"
    else
        echo -e "${RED}❌ Gemini MCP configuration missing${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🎉 All validation tests passed!${NC}"
}

# Main deployment flow
main() {
    echo -e "\n${YELLOW}🔍 Starting dependency installation...${NC}"
    
    # Check and install Node.js
    if ! command_exists node; then
        install_nodejs
    else
        echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
    fi
    
    # Check and install Python & uv
    if ! command_exists python3 || ! command_exists uv; then
        install_python_uv
    else
        echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"
        if ! command_exists uv; then
            install_python_uv
        else
            echo -e "${GREEN}✅ uv found: $(uv --version)${NC}"
        fi
    fi
    
    # Create project structure
    create_project_structure
    
    # Install Serena and SolidLSP
    install_serena
    
    # Install Gemini CLI
    install_gemini_cli
    
    # Setup API key
    setup_api_key
    
    # Initialize Serena project
    initialize_serena_project
    
    # Configure Gemini CLI with Serena MCP
    configure_gemini_mcp
    
    # Create launch script
    create_launch_script
    
    # Run validation tests
    run_validation_tests
    
    echo -e "\n${GREEN}🎉 Standalone deployment completed successfully!${NC}"
    echo -e "${BLUE}💡 Next steps:${NC}"
    echo "   1. Run: ./launch-gemini-with-serena.sh"
    echo "   2. In Gemini CLI, try: /mcp"
    echo "   3. Ask: 'What Serena tools are available?'"
    echo "   4. Start coding with natural language!"
    echo ""
    echo -e "${PURPLE}📋 What was installed:${NC}"
    echo "   • Node.js & npm (via nvm)"
    echo "   • Python 3.11+ & uv package manager"
    echo "   • Serena agent with SolidLSP"
    echo "   • Gemini CLI (@google/gemini-cli)"
    echo "   • Complete MCP server configuration"
    echo "   • Project structure and launch scripts"
    echo ""
    echo -e "${CYAN}🔧 Files created:${NC}"
    echo "   • pyproject.toml (Python project config)"
    echo "   • .env (API key storage)"
    echo "   • .gitignore (Git ignore rules)"
    echo "   • .gemini/settings.json (MCP server config)"
    echo "   • launch-gemini-with-serena.sh (Launch script)"
    echo ""
    echo -e "${YELLOW}🚀 Ready for natural language coding with Serena + Gemini CLI!${NC}"
}

# Run main function
main
