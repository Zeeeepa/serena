# Serena Desktop Extension (DXT)

This is a Desktop Extension (DXT) package for **Serena**, a powerful coding agent toolkit that provides semantic retrieval and editing capabilities for LLMs.

## What is Serena?

Serena is a comprehensive coding agent toolkit that enhances LLM capabilities with:

- **Semantic Code Navigation**: Find symbols, references, and code structures at the symbol level
- **Advanced File Operations**: Read, create, edit files with precision
- **Memory Management**: Store and retrieve information across sessions  
- **Shell Integration**: Execute commands in your project environment
- **Language Server Integration**: Leverage LSP for accurate code understanding

## Installation

### Prerequisites

- **Python 3.11.x** (required - Serena does not support other Python versions)
- **Claude Desktop** or another MCP-compatible application

### Quick Install

1. Download the `serena-dxt.dxt` file (37.8MB - includes all dependencies)
2. Double-click to install in Claude Desktop, or use your MCP client's extension installer
3. Configure your project directory when prompted

### Manual Setup (if needed)

If automatic dependency installation fails:

```bash
# Extract the DXT file and navigate to the directory
cd serena-dxt/
python3 setup.py
```

## Configuration

When installing the extension, you'll be prompted to configure:

- **Project Directory**: The root directory of your coding project (required)
- **Context**: Built-in context name or path to custom context YAML (default: "default")
- **Log Level**: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Tool Timeout**: Maximum time for tool execution (5-300 seconds)
- **Web Dashboard**: Enable web-based monitoring (optional)
- **GUI Log Window**: Enable GUI log window (optional, may not work on all platforms)

## Available Tools

### File Operations (9 tools)
- `read_file_tool` - Read files with optional line ranges and content limits
- `create_text_file_tool` - Create or overwrite text files
- `list_dir_tool` - List directory contents with recursion (respects .gitignore)
- `find_file_tool` - Find files matching patterns using glob syntax
- `search_for_pattern_tool` - Search text patterns across files with context
- `replace_regex_tool` - Replace text using regular expressions with match counting
- `delete_lines_tool` - Delete specific line ranges from files
- `replace_lines_tool` - Replace specific line ranges with new content
- `insert_at_line_tool` - Insert text at specific line positions

### Symbol Navigation (7 tools - LSP-based)
- `get_symbols_overview_tool` - Get LSP-based overview of symbols in files
- `find_symbol_tool` - Find symbol definitions using LSP with precise locations
- `find_referencing_symbols_tool` - Find all symbol references using LSP
- `replace_symbol_body_tool` - Replace function/method bodies using LSP-guided editing
- `insert_after_symbol_tool` - Insert code after specific symbols using LSP positioning
- `insert_before_symbol_tool` - Insert code before specific symbols using LSP positioning
- `restart_language_server_tool` - Restart the LSP language server for improved resolution

### Memory Management (4 tools)
- `write_memory_tool` - Store information in persistent agent memory with key-value pairs
- `read_memory_tool` - Retrieve stored information from agent memory by key
- `list_memories_tool` - List all stored memory entries with keys and metadata
- `delete_memory_tool` - Delete specific memory entries by key

### Project Management (4 tools)
- `activate_project_tool` - Activate a project directory for the current Serena session
- `get_current_config_tool` - Get current Serena configuration including active tools
- `switch_modes_tool` - Switch between different Serena agent modes and tool sets
- `remove_project_tool` - Remove a project from Serena's project registry

### System Integration (1 tool)
- `execute_shell_command_tool` - Execute shell commands with output capture

## Usage Examples

Once installed, you can use Serena through your MCP client:

```
"Find all functions named 'process_data' in my project"
"Replace the body of the calculate_total function with improved logic"
"Search for all TODO comments in Python files"
"Create a new utility file with helper functions"
```

## Troubleshooting

### Python Version Issues
Serena requires exactly Python 3.11.x. If you have a different version:
- Install Python 3.11 using pyenv, conda, or your system package manager
- Make sure `python3` points to Python 3.11

### Dependency Issues
If you encounter import errors:
```bash
cd serena-dxt/
python3 setup.py
```

### Language Server Issues
If symbol navigation isn't working:
- Use the `restart_language_server` tool
- Ensure your project has proper language server support
- Check that required language servers are installed

## Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/serena/issues)
- **Documentation**: [Serena README](https://github.com/Zeeeepa/serena/blob/main/README.md)
- **Original Project**: [Serena Repository](https://github.com/Zeeeepa/serena)

## License

MIT License - see the original Serena project for full license details.
