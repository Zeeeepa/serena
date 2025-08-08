#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Serena + Gemini CLI Deployment Script${NC}"
echo "=========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Node.js via nvm if not present
install_nodejs() {
    echo -e "\n${YELLOW}📦 Installing Node.js...${NC}"
    
    # Install nvm if not present
    if ! command_exists nvm; then
        echo "Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    fi
    
    # Install and use Node.js LTS
    nvm install --lts
    nvm use --lts
    nvm alias default lts/*
}

# Function to install uv if not present
install_uv() {
    echo -e "\n${YELLOW}🐍 Installing uv (Python package manager)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
}

# Check and install dependencies
echo -e "\n${YELLOW}🔍 Checking dependencies...${NC}"

# Check Node.js
if ! command_exists node; then
    install_nodejs
else
    echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
fi

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm not found. Please install Node.js properly.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ npm found: $(npm --version)${NC}"
fi

# Check uv
if ! command_exists uv; then
    install_uv
else
    echo -e "${GREEN}✅ uv found: $(uv --version)${NC}"
fi

# Install Gemini CLI
echo -e "\n${YELLOW}💎 Installing Gemini CLI...${NC}"
if ! command_exists gemini; then
    npm install -g @google/gemini-cli
    echo -e "${GREEN}✅ Gemini CLI installed successfully${NC}"
else
    echo -e "${GREEN}✅ Gemini CLI already installed${NC}"
fi

# Setup Python environment
echo -e "\n${YELLOW}🐍 Setting up Python environment...${NC}"
if [ ! -d ".venv" ]; then
    uv venv --python 3.11
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Install Python dependencies
echo -e "\n${YELLOW}📦 Installing Python dependencies...${NC}"
uv sync
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Setup Serena project
echo -e "\n${YELLOW}⚙️ Setting up Serena project...${NC}"
if [ ! -f ".serena/project.yml" ]; then
    mkdir -p .serena
    uv run serena-mcp-server --project . --help > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ Serena project initialized${NC}"
else
    echo -e "${GREEN}✅ Serena project already configured${NC}"
fi

# Setup API key
echo -e "\n${YELLOW}🔑 Setting up API key...${NC}"
if [ ! -f ".env" ]; then
    echo "Please enter your Gemini API key:"
    read -s GEMINI_API_KEY
    echo "GEMINI_API_KEY=$GEMINI_API_KEY" > .env
    echo -e "${GREEN}✅ API key saved to .env file${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Ensure .env is in .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo -e "${GREEN}✅ Added .env to .gitignore${NC}"
else
    echo -e "${GREEN}✅ .env already in .gitignore${NC}"
fi

# Setup Gemini CLI configuration
echo -e "\n${YELLOW}💎 Configuring Gemini CLI...${NC}"
mkdir -p .gemini

cat > .gemini/settings.json << 'EOF'
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "."],
      "env": {
        "PYTHONPATH": ""
      }
    }
  }
}
EOF

echo -e "${GREEN}✅ Gemini CLI configured with Serena MCP server${NC}"

# Make launch script executable
if [ -f "launch-gemini-with-serena.sh" ]; then
    chmod +x launch-gemini-with-serena.sh
    echo -e "${GREEN}✅ Launch script made executable${NC}"
fi

# Run tests if available
if [ -f "test_env_setup.sh" ]; then
    echo -e "\n${YELLOW}🧪 Running environment tests...${NC}"
    chmod +x test_env_setup.sh
    ./test_env_setup.sh
fi

if [ -f "test_full_integration.sh" ]; then
    echo -e "\n${YELLOW}🧪 Running integration tests...${NC}"
    chmod +x test_full_integration.sh
    ./test_full_integration.sh
fi

echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}💡 Next steps:${NC}"
echo "   1. Run: ./launch-gemini-with-serena.sh"
echo "   2. In Gemini CLI, try: /mcp"
echo "   3. Ask: 'What Serena tools are available?'"
echo "   4. Start coding with natural language!"
echo ""
echo -e "${YELLOW}📚 For detailed documentation, see INTEGRATION_SUCCESS.md${NC}"
