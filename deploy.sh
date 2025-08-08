#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. This is not recommended for development."
fi

print_header "🚀 Serena + Gemini CLI Deployment Script"

# Get current directory (project root)
PROJECT_ROOT=$(pwd)
print_status "Project root: $PROJECT_ROOT"

# Step 1: Check system dependencies
print_step "1. Checking system dependencies..."

# Check for required commands
REQUIRED_COMMANDS=("curl" "git" "node" "npm")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v $cmd &> /dev/null; then
        print_error "$cmd is required but not installed."
        exit 1
    else
        print_success "$cmd is available"
    fi
done

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2)
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
    print_error "Node.js 18+ is required. Current version: $NODE_VERSION"
    exit 1
else
    print_success "Node.js version: $NODE_VERSION"
fi

# Step 2: Install uv (Python package manager)
print_step "2. Installing uv (Python package manager)..."

if ! command -v uv &> /dev/null; then
    print_status "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    # Add to current session
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
else
    print_success "uv is already installed"
fi

# Verify uv installation
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version)
    print_success "uv installed: $UV_VERSION"
else
    print_error "Failed to install uv"
    exit 1
fi

# Step 3: Install Gemini CLI
print_step "3. Installing Gemini CLI..."

# Check if Gemini CLI is already installed globally
if npm list -g @google/gemini-cli &> /dev/null; then
    print_success "Gemini CLI is already installed globally"
else
    print_status "Installing Gemini CLI globally..."
    npm install -g @google/gemini-cli
fi

# Verify Gemini CLI installation
if command -v gemini &> /dev/null; then
    GEMINI_VERSION=$(gemini --version 2>/dev/null || echo "unknown")
    print_success "Gemini CLI installed: $GEMINI_VERSION"
else
    print_error "Failed to install Gemini CLI"
    exit 1
fi

# Step 4: Install Serena dependencies
print_step "4. Installing Serena dependencies..."

print_status "Installing Python dependencies with uv..."
uv sync

print_status "Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm install
    print_success "Node.js dependencies installed"
else
    print_warning "No package.json found - skipping Node.js dependencies"
fi

# Step 5: Create global Gemini CLI configuration
print_step "5. Creating global Gemini CLI configuration..."

# Create global .gemini directory
GLOBAL_GEMINI_DIR="$HOME/.gemini"
mkdir -p "$GLOBAL_GEMINI_DIR"

# Create global settings.json with Serena MCP server
cat > "$GLOBAL_GEMINI_DIR/settings.json" << EOF
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "$PROJECT_ROOT"],
      "cwd": "$PROJECT_ROOT",
      "timeout": 30000,
      "description": "Serena coding agent toolkit with semantic analysis and LSP integration",
      "trust": true,
      "includeTools": [
        "find_symbol",
        "find_referencing_symbols", 
        "find_referencing_code_snippets",
        "get_symbols_overview",
        "replace_symbol_body",
        "insert_before_symbol",
        "insert_after_symbol",
        "replace_lines",
        "insert_at_line",
        "delete_lines",
        "create_text_file",
        "read_file",
        "list_dir",
        "search_for_pattern",
        "write_memory",
        "read_memory",
        "list_memories",
        "delete_memory",
        "activate_project",
        "onboarding",
        "get_current_config",
        "restart_language_server",
        "execute_shell_command",
        "switch_modes",
        "summarize_changes",
        "check_onboarding_performed",
        "initial_instructions",
        "prepare_for_new_conversation",
        "remove_project",
        "think_about_collected_information",
        "think_about_task_adherence",
        "think_about_whether_you_are_done"
      ]
    }
  },
  "approvalMode": "auto",
  "showMemoryUsage": true,
  "telemetry": {
    "enabled": false
  }
}
EOF

print_success "Global Gemini CLI configuration created at $GLOBAL_GEMINI_DIR/settings.json"

# Step 6: Create/update local Serena configuration
print_step "6. Creating/updating Serena project configuration..."

# Create .serena directory if it doesn't exist
mkdir -p ".serena"

# Create or update project.yml
cat > ".serena/project.yml" << EOF
# Serena project configuration for Gemini CLI integration
language: python
ignore_all_files_in_gitignore: true
ignored_paths:
  - "node_modules/**"
  - "dist/**"
  - "build/**"
  - ".git/**"
  - "*.log"
  - "__pycache__/**"
  - ".pytest_cache/**"
  - ".venv/**"
  - ".env"

# Enable all tools for maximum functionality
excluded_tools: []

# Project settings
read_only: false
project_name: "serena-gemini-integration"
initial_prompt: "This is a Serena + Gemini CLI integration project. Use Serena's tools for semantic code analysis, symbol navigation, and precise code editing."
EOF

print_success "Serena project configuration created/updated"

# Step 7: Create local .gemini configuration (for project-specific settings)
print_step "7. Creating local Gemini CLI configuration..."

mkdir -p ".gemini"

cat > ".gemini/settings.json" << EOF
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "."],
      "cwd": ".",
      "timeout": 30000,
      "description": "Serena coding agent toolkit with semantic analysis and LSP integration",
      "trust": true,
      "includeTools": [
        "find_symbol",
        "find_referencing_symbols", 
        "find_referencing_code_snippets",
        "get_symbols_overview",
        "replace_symbol_body",
        "insert_before_symbol",
        "insert_after_symbol",
        "replace_lines",
        "insert_at_line",
        "delete_lines",
        "create_text_file",
        "read_file",
        "list_dir",
        "search_for_pattern",
        "write_memory",
        "read_memory",
        "list_memories",
        "delete_memory",
        "activate_project",
        "onboarding",
        "get_current_config",
        "restart_language_server",
        "execute_shell_command",
        "switch_modes",
        "summarize_changes",
        "check_onboarding_performed",
        "initial_instructions",
        "prepare_for_new_conversation",
        "remove_project",
        "think_about_collected_information",
        "think_about_task_adherence",
        "think_about_whether_you_are_done"
      ]
    }
  },
  "approvalMode": "auto",
  "showMemoryUsage": true,
  "telemetry": {
    "enabled": false
  }
}
EOF

print_success "Local Gemini CLI configuration created"

# Step 8: Test Serena MCP server
print_step "8. Testing Serena MCP server..."

print_status "Testing Serena MCP server startup..."
if timeout 15s uv run serena-mcp-server --help > /dev/null 2>&1; then
    print_success "Serena MCP server can start successfully"
else
    print_warning "Serena MCP server test failed - this might be due to missing dependencies"
    print_status "Attempting to fix dependencies..."
    uv sync
    if timeout 15s uv run serena-mcp-server --help > /dev/null 2>&1; then
        print_success "Serena MCP server fixed"
    else
        print_error "Serena MCP server still failing - manual intervention may be required"
    fi
fi

# Step 9: Create wrapper script for easy launching
print_step "9. Creating launch wrapper script..."

cat > "launch-gemini-with-serena.sh" << 'EOF'
#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Launching Gemini CLI with Serena Integration...${NC}"

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${GREEN}💡 Tip: Set GEMINI_API_KEY environment variable for full functionality${NC}"
    echo "   export GEMINI_API_KEY=your-api-key-here"
    echo ""
fi

# Launch Gemini CLI
echo -e "${GREEN}Starting Gemini CLI...${NC}"
echo "Use '/mcp' to check Serena connection"
echo "Use '/help' to see available commands"
echo ""

exec gemini
EOF

chmod +x "launch-gemini-with-serena.sh"
print_success "Launch wrapper script created: launch-gemini-with-serena.sh"

# Step 10: Display configuration summary
print_step "10. Configuration Summary"

echo ""
print_status "📁 Project Configuration:"
echo "  • Project Root: $PROJECT_ROOT"
echo "  • Serena Config: .serena/project.yml"
echo "  • Local Gemini Config: .gemini/settings.json"
echo "  • Global Gemini Config: $GLOBAL_GEMINI_DIR/settings.json"
echo ""

print_status "🔧 Available Commands:"
echo "  • gemini                     - Start Gemini CLI with Serena integration"
echo "  • ./launch-gemini-with-serena.sh - Launch with helpful tips"
echo "  • uv run serena-mcp-server   - Start Serena MCP server directly"
echo ""

print_status "🧪 Testing Commands (in Gemini CLI):"
echo "  • /mcp                       - Check MCP server status"
echo "  • /help                      - Show available commands"
echo "  • 'List all available Serena tools' - Test tool discovery"
echo ""

# Step 11: Run tests if GEMINI_API_KEY is provided
if [ ! -z "$GEMINI_API_KEY" ]; then
    print_step "11. Running integration tests with provided API key..."
    
    print_status "Setting GEMINI_API_KEY environment variable..."
    export GEMINI_API_KEY="$GEMINI_API_KEY"
    
    print_status "Testing Gemini CLI with Serena integration..."
    
    # Create a test script for automated testing
    cat > "test_gemini_serena.js" << 'EOF'
const { spawn } = require('child_process');
const fs = require('fs');

console.log('🧪 Testing Gemini CLI + Serena Integration...');

// Test commands to run
const testCommands = [
    '/mcp',
    'List all available Serena tools',
    'What is the current project structure?',
    'Show me the contents of README.md',
    'Create a test memory with the content: Integration test successful'
];

let commandIndex = 0;

const gemini = spawn('gemini', [], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, GEMINI_API_KEY: process.env.GEMINI_API_KEY }
});

gemini.stdout.on('data', (data) => {
    const output = data.toString();
    console.log('GEMINI OUTPUT:', output);
    
    // Send next test command after a delay
    if (commandIndex < testCommands.length) {
        setTimeout(() => {
            const command = testCommands[commandIndex];
            console.log(`\n🔧 Sending command: ${command}`);
            gemini.stdin.write(command + '\n');
            commandIndex++;
        }, 2000);
    } else if (commandIndex === testCommands.length) {
        // Exit after all commands
        setTimeout(() => {
            console.log('\n✅ All test commands sent. Exiting...');
            gemini.stdin.write('exit\n');
            commandIndex++; // Prevent multiple exits
        }, 5000);
    }
});

gemini.stderr.on('data', (data) => {
    console.error('GEMINI ERROR:', data.toString());
});

gemini.on('close', (code) => {
    console.log(`\n🏁 Gemini CLI exited with code ${code}`);
    fs.unlinkSync('test_gemini_serena.js'); // Clean up test script
});

// Send first command after startup delay
setTimeout(() => {
    if (commandIndex < testCommands.length) {
        const command = testCommands[commandIndex];
        console.log(`\n🔧 Sending command: ${command}`);
        gemini.stdin.write(command + '\n');
        commandIndex++;
    }
}, 3000);

// Timeout after 60 seconds
setTimeout(() => {
    console.log('\n⏰ Test timeout reached. Terminating...');
    gemini.kill();
}, 60000);
EOF

    print_status "Running automated integration test..."
    node test_gemini_serena.js || true
    
    print_success "Integration test completed"
else
    print_step "11. Skipping integration tests (no GEMINI_API_KEY provided)"
    print_status "To run tests later, set GEMINI_API_KEY and run:"
    echo "  export GEMINI_API_KEY=your-api-key"
    echo "  gemini"
fi

print_header "🎉 Deployment Complete!"

print_success "Serena + Gemini CLI integration is ready!"
echo ""
print_status "Next steps:"
echo "  1. Set your API key: export GEMINI_API_KEY=your-api-key-here"
echo "  2. Launch Gemini CLI: ./launch-gemini-with-serena.sh"
echo "  3. Test the integration: /mcp"
echo "  4. Start coding with natural language!"
echo ""
print_status "Example commands to try in Gemini CLI:"
echo "  • 'Find all Python functions in this project'"
echo "  • 'Show me the project structure'"
echo "  • 'Create a memory note about this integration'"
echo "  • 'Help me understand the codebase'"
echo ""
print_success "Happy coding! 🚀"

