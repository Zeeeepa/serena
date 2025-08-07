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

1. Download the `serena.dxt` file
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

### File Operations
- `read_file` - Read files with optional line ranges
- `create_text_file` - Create or overwrite files
- `list_dir` - List directory contents with recursion
- `find_file` - Find files matching patterns
- `search_for_pattern` - Search text patterns across files

### File Editing
- `replace_regex` - Replace text using regular expressions
- `delete_lines` - Delete specific lines
- `replace_lines` - Replace specific lines
- `insert_at_line` - Insert text at specific positions

### Symbol Navigation
- `find_symbol` - Find functions, classes, variables
- `find_referencing_symbols` - Find all symbol references
- `get_symbols_overview` - Get symbol overview
- `replace_symbol_body` - Replace function/method bodies
- `insert_after_symbol` - Insert code after symbols
- `insert_before_symbol` - Insert code before symbols

### System Integration
- `execute_shell_command` - Run shell commands
- `restart_language_server` - Restart LSP for better accuracy

### Memory Management
- `write_memory` - Store information
- `read_memory` - Retrieve stored information
- `list_memories` - List all memories
- `delete_memory` - Delete memory entries

### Project Management
- `activate_project` - Activate projects
- `get_current_config` - View current configuration

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

