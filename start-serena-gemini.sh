#!/bin/bash
set -e

echo "🚀 Starting Serena + Gemini CLI Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
print_status "Checking project structure..."

if [ ! -f ".serena/project.yml" ]; then
    print_error ".serena/project.yml not found. Please run from project root."
    print_status "Creating basic Serena configuration..."
    
    mkdir -p .serena
    cat > .serena/project.yml << 'EOF'
# Serena project configuration
language: python
ignore_all_files_in_gitignore: true
ignored_paths: []
read_only: false
excluded_tools: []
initial_prompt: ""
project_name: "serena-gemini-integration"
EOF
    print_success "Created .serena/project.yml"
fi

if [ ! -f ".gemini/settings.json" ]; then
    print_error ".gemini/settings.json not found. Please configure Gemini CLI first."
    print_status "Run the following command to see the configuration guide:"
    print_status "cat SERENA_GEMINI_INTEGRATION.md"
    exit 1
fi

if [ ! -f "package.json" ]; then
    print_error "package.json not found. This doesn't appear to be a Gemini CLI project."
    exit 1
fi

# Check dependencies
print_status "Checking dependencies..."

if ! command -v uv &> /dev/null; then
    print_error "uv not found. Please install uv: https://docs.astral.sh/uv/"
    exit 1
fi

if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js 20+."
    exit 1
fi

# Check if Serena can start (quick test)
print_status "Testing Serena MCP server..."
if ! timeout 10s uv run serena-mcp-server --help > /dev/null 2>&1; then
    print_warning "Serena MCP server test failed. Installing dependencies..."
    uv sync
fi

# Check if Gemini CLI dependencies are installed
print_status "Checking Gemini CLI dependencies..."
if [ ! -d "node_modules" ]; then
    print_status "Installing Gemini CLI dependencies..."
    npm install
fi

# Display configuration summary
print_status "Configuration Summary:"
echo "  📁 Project: $(pwd)"
echo "  🐍 Serena Config: .serena/project.yml"
echo "  🤖 Gemini Config: .gemini/settings.json"
echo "  🔧 Language: $(grep '^language:' .serena/project.yml | cut -d' ' -f2)"

# Start Gemini CLI (it will automatically start Serena MCP server)
print_status "Starting Gemini CLI with Serena integration..."
print_status "Gemini CLI will automatically connect to Serena MCP server"
print_status "Use '/mcp' command in Gemini CLI to verify the connection"

echo ""
print_success "🎉 Integration ready! Starting Gemini CLI..."
echo ""
print_status "Available Serena tools will be prefixed with 'serena__' if there are conflicts"
print_status "Use natural language to interact with your codebase through Serena's tools"
echo ""

# Start Gemini CLI
exec npm run start

