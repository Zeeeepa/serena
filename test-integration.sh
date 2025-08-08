#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

echo "🧪 Testing Serena + Gemini CLI Integration"
echo "========================================"

# Test 1: Check required files exist
print_status "Checking configuration files..."

if [ -f ".serena/project.yml" ]; then
    print_success ".serena/project.yml exists"
else
    print_error ".serena/project.yml missing"
    exit 1
fi

if [ -f ".gemini/settings.json" ]; then
    print_success ".gemini/settings.json exists"
else
    print_error ".gemini/settings.json missing"
    exit 1
fi

if [ -f "start-serena-gemini.sh" ] && [ -x "start-serena-gemini.sh" ]; then
    print_success "start-serena-gemini.sh exists and is executable"
else
    print_error "start-serena-gemini.sh missing or not executable"
    exit 1
fi

# Test 2: Check dependencies
print_status "Checking dependencies..."

if command -v uv &> /dev/null; then
    print_success "uv is installed"
else
    print_error "uv not found"
    exit 1
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js is installed: $NODE_VERSION"
else
    print_error "Node.js not found"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_success "npm is installed: $NPM_VERSION"
else
    print_error "npm not found"
    exit 1
fi

# Test 3: Check Python dependencies
print_status "Checking Python environment..."

if uv run python --version &> /dev/null; then
    PYTHON_VERSION=$(uv run python --version)
    print_success "Python environment ready: $PYTHON_VERSION"
else
    print_warning "Python environment not ready, running uv sync..."
    uv sync
    if uv run python --version &> /dev/null; then
        print_success "Python environment fixed"
    else
        print_error "Failed to set up Python environment"
        exit 1
    fi
fi

# Test 4: Check Node.js dependencies
print_status "Checking Node.js dependencies..."

if [ -d "node_modules" ]; then
    print_success "Node.js dependencies installed"
else
    print_warning "Node.js dependencies missing, running npm install..."
    npm install
    print_success "Node.js dependencies installed"
fi

# Test 5: Validate configuration files
print_status "Validating configuration files..."

# Check .serena/project.yml
if grep -q "language:" .serena/project.yml; then
    LANGUAGE=$(grep "^language:" .serena/project.yml | cut -d' ' -f2)
    print_success "Serena language configured: $LANGUAGE"
else
    print_error "No language specified in .serena/project.yml"
    exit 1
fi

# Check .gemini/settings.json
if grep -q "serena" .gemini/settings.json; then
    print_success "Serena MCP server configured in Gemini CLI"
else
    print_error "Serena not configured in .gemini/settings.json"
    exit 1
fi

# Test 6: Test Serena MCP server (quick start/stop test)
print_status "Testing Serena MCP server startup..."

# Create a temporary test to see if Serena can start
if timeout 15s uv run serena-mcp-server --help > /dev/null 2>&1; then
    print_success "Serena MCP server can start"
else
    print_warning "Serena MCP server startup test failed (this might be due to missing dependencies)"
    print_status "Attempting to install missing dependencies..."
    uv sync
    if timeout 15s uv run serena-mcp-server --help > /dev/null 2>&1; then
        print_success "Serena MCP server fixed"
    else
        print_error "Serena MCP server still failing - check dependencies manually"
    fi
fi

# Test 7: Validate JSON configuration
print_status "Validating JSON configuration..."

if python3 -m json.tool .gemini/settings.json > /dev/null 2>&1; then
    print_success ".gemini/settings.json is valid JSON"
else
    print_error ".gemini/settings.json contains invalid JSON"
    exit 1
fi

# Test 8: Check for common issues
print_status "Checking for common issues..."

# Check if .gitignore excludes important files
if [ -f ".gitignore" ]; then
    if grep -q "\.gemini" .gitignore; then
        print_warning ".gemini directory is in .gitignore - configuration won't be shared"
    fi
    if grep -q "\.serena" .gitignore; then
        print_warning ".serena directory is in .gitignore - configuration won't be shared"
    fi
fi

# Check file permissions
if [ ! -r ".serena/project.yml" ]; then
    print_error ".serena/project.yml is not readable"
    exit 1
fi

if [ ! -r ".gemini/settings.json" ]; then
    print_error ".gemini/settings.json is not readable"
    exit 1
fi

# Test 9: Environment variables
print_status "Checking environment variables..."

if [ -z "$GEMINI_API_KEY" ]; then
    print_warning "GEMINI_API_KEY not set - you'll need this to use Gemini CLI"
else
    print_success "GEMINI_API_KEY is set"
fi

# Test 10: Port availability (if we can test)
print_status "Checking port availability..."

if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":3000 "; then
        print_warning "Port 3000 is already in use"
    else
        print_success "Port 3000 is available"
    fi
    
    if netstat -tuln | grep -q ":8080 "; then
        print_warning "Port 8080 is already in use"
    else
        print_success "Port 8080 is available"
    fi
else
    print_warning "Cannot check port availability (netstat not available)"
fi

echo ""
echo "🎉 Integration Test Summary"
echo "=========================="
print_success "All critical tests passed!"
print_status "You can now run: ./start-serena-gemini.sh"
print_status "Or use Docker: docker-compose -f docker-compose.serena-gemini.yml up"
echo ""
print_status "Next steps:"
echo "  1. Set GEMINI_API_KEY environment variable"
echo "  2. Run ./start-serena-gemini.sh"
echo "  3. Use '/mcp' command in Gemini CLI to verify connection"
echo "  4. Try asking Gemini to analyze your code!"
echo ""
print_success "Happy coding! 🚀"

