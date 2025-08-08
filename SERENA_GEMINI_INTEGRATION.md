# Serena + Gemini CLI Integration Guide

This guide shows you how to configure Serena's powerful coding agent toolkit to work seamlessly with Gemini CLI, combining Gemini's conversational AI interface with Serena's advanced semantic code analysis capabilities.

## Overview

**What you'll get:**
- ✅ **Enhanced Code Analysis** - Gemini CLI gains access to Serena's LSP-based semantic analysis
- ✅ **Advanced Symbol Operations** - Find references, navigate code, edit symbols precisely  
- ✅ **Multi-language Support** - Python, TypeScript, Go, Rust, Java, C#, and more
- ✅ **Project Memory** - Persistent knowledge storage across sessions
- ✅ **Unified Workflow** - Single interface combining conversational AI with deep code understanding

## Architecture

```
┌─────────────────┐    MCP Protocol    ┌──────────────────┐
│   Gemini CLI    │◄──────────────────►│  Serena MCP      │
│                 │                    │  Server          │
│ - Conversation  │                    │                  │
│ - Built-in Tools│                    │ - Symbol Analysis│
│ - Web Search    │                    │ - Code Editing   │
│ - File Ops      │                    │ - Memory System  │
└─────────────────┘                    │ - LSP Integration│
                                       └──────────────────┘
```

## Prerequisites

1. **Python 3.11+** with `uv` package manager
2. **Node.js 20+** for Gemini CLI
3. **Git** for version control

## Installation & Setup

### Step 1: Install Dependencies

```bash
# Install Serena dependencies
cd /path/to/your/project
uv sync

# Install Gemini CLI dependencies  
npm install
```

### Step 2: Configure Serena Project

Create or update `.serena/project.yml`:

```yaml
# Language of the project
language: python  # or typescript, go, rust, java, etc.

# Use gitignore for file filtering
ignore_all_files_in_gitignore: true
ignored_paths: []

# Enable all tools (recommended)
excluded_tools: []

# Project-specific settings
read_only: false
project_name: "your-project-name"
initial_prompt: ""
```

### Step 3: Configure Gemini CLI MCP Connection

Create `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "."],
      "cwd": ".",
      "timeout": 30000,
      "description": "Serena coding agent toolkit with semantic analysis",
      "trust": true
    }
  }
}
```

### Step 4: Create Integration Startup Script

Create `start-serena-gemini.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting Serena + Gemini CLI Integration..."

# Check if we're in the right directory
if [ ! -f ".serena/project.yml" ]; then
    echo "❌ Error: .serena/project.yml not found. Please run from project root."
    exit 1
fi

if [ ! -f ".gemini/settings.json" ]; then
    echo "❌ Error: .gemini/settings.json not found. Please configure Gemini CLI first."
    exit 1
fi

# Start Gemini CLI (it will automatically start Serena MCP server)
echo "🔧 Starting Gemini CLI with Serena integration..."
npm run start

echo "✅ Integration started successfully!"
```

Make it executable:
```bash
chmod +x start-serena-gemini.sh
```

## Available Serena Tools

When integrated, Gemini CLI will have access to these powerful Serena tools:

### 🔍 **Code Analysis & Navigation**
- `find_symbol` - Global/local symbol search with filtering
- `find_referencing_symbols` - Find symbols that reference a given symbol
- `find_referencing_code_snippets` - Find code snippets referencing a symbol
- `get_symbols_overview` - Overview of symbols in files/directories

### ✏️ **Code Editing**
- `replace_symbol_body` - Replace complete symbol definitions
- `insert_before_symbol` - Insert content before symbol definitions
- `insert_after_symbol` - Insert content after symbol definitions
- `replace_lines` - Replace line ranges with new content
- `insert_at_line` - Insert content at specific lines
- `delete_lines` - Delete line ranges

### 📁 **File Operations**
- `create_text_file` - Create/overwrite files
- `read_file` - Read file contents
- `list_dir` - List directory contents with recursion
- `search_for_pattern` - Pattern search across project

### 🧠 **Memory & Knowledge**
- `write_memory` - Store project knowledge
- `read_memory` - Retrieve stored knowledge
- `list_memories` - List available memories
- `delete_memory` - Remove stored memories

### ⚙️ **Project Management**
- `activate_project` - Switch between projects
- `onboarding` - Analyze project structure
- `get_current_config` - View current configuration
- `restart_language_server` - Restart LSP servers

### 🔧 **Workflow Tools**
- `execute_shell_command` - Run shell commands
- `switch_modes` - Change operational modes
- `summarize_changes` - Summarize codebase changes

## Usage Examples

### Example 1: Code Analysis
```
You: "Find all functions that call the authenticate method"

Gemini CLI will use:
1. find_symbol to locate the authenticate method
2. find_referencing_symbols to find callers
3. get_symbols_overview to provide context
```

### Example 2: Refactoring
```
You: "Rename the UserService class to AccountService and update all references"

Gemini CLI will use:
1. find_symbol to locate UserService
2. find_referencing_code_snippets to find all usages
3. replace_symbol_body to rename the class
4. replace_lines to update references
```

### Example 3: Project Understanding
```
You: "Help me understand this codebase structure"

Gemini CLI will use:
1. onboarding to analyze project structure
2. get_symbols_overview for key files
3. write_memory to store findings
4. list_dir to explore directories
```

## Troubleshooting

### Common Issues

**1. MCP Server Connection Failed**
```bash
# Check if Serena can start
uv run serena-mcp-server --help

# Check dependencies
uv sync
```

**2. Tools Not Appearing**
```bash
# In Gemini CLI, check MCP status
/mcp

# Verify configuration
cat .gemini/settings.json
```

**3. Language Server Issues**
```bash
# Restart language servers
# In Gemini CLI: "Please restart the language server"
# Or use the restart_language_server tool
```

**4. Permission Errors**
```bash
# Make sure scripts are executable
chmod +x start-serena-gemini.sh

# Check file permissions
ls -la .serena/
ls -la .gemini/
```

### Debug Mode

Enable debug logging in `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", ".", "--log-level", "DEBUG"],
      "cwd": ".",
      "timeout": 30000,
      "trust": true
    }
  }
}
```

## Advanced Configuration

### Custom Tool Selection

Exclude specific tools in `.serena/project.yml`:

```yaml
excluded_tools:
  - "execute_shell_command"  # Disable shell access
  - "delete_lines"          # Disable line deletion
```

### Multiple Projects

Configure multiple Serena projects:

```json
{
  "mcpServers": {
    "serena-main": {
      "command": "uv",
      "args": ["run", "serena-mcp-server", "--project", "."],
      "cwd": ".",
      "timeout": 30000
    },
    "serena-backend": {
      "command": "uv", 
      "args": ["run", "serena-mcp-server", "--project", "./backend"],
      "cwd": "./backend",
      "timeout": 30000
    }
  }
}
```

### Performance Tuning

For large projects, optimize performance:

```yaml
# In .serena/project.yml
ignored_paths:
  - "node_modules/**"
  - "dist/**"
  - "build/**"
  - ".git/**"
  - "*.log"
```

## Best Practices

1. **Start Simple** - Begin with basic file operations, then explore advanced features
2. **Use Memory** - Store important project insights using write_memory
3. **Leverage Symbols** - Use symbol-based operations for precise code changes
4. **Monitor Performance** - Watch for language server startup times
5. **Regular Cleanup** - Restart language servers if they become unresponsive

## Security Considerations

- **Trust Settings** - Only set `trust: true` for servers you control
- **Shell Access** - Consider excluding `execute_shell_command` in production
- **File Access** - Serena respects `.serena/project.yml` file restrictions
- **Network Access** - MCP communication is local by default

## Next Steps

1. **Try the Integration** - Run `./start-serena-gemini.sh`
2. **Explore Tools** - Use `/mcp` command to see available tools
3. **Test Workflows** - Try code analysis and editing tasks
4. **Customize Configuration** - Adjust settings for your project needs
5. **Share Feedback** - Report issues and suggest improvements

---

**Happy Coding!** 🚀

This integration combines the best of both worlds: Gemini's natural language interface with Serena's deep code understanding capabilities.

