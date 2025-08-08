# 🚀 Serena + Gemini CLI Quick Start

## One-Command Setup

```bash
# 1. Test the integration
./test-integration.sh

# 2. Start the integrated environment
./start-serena-gemini.sh
```

## Essential Commands

### In Gemini CLI:
```bash
# Check MCP server status
/mcp

# Get help on available tools
/help

# Example interactions:
"Find all functions that call the authenticate method"
"Show me the structure of this Python project"
"Refactor the UserService class to use dependency injection"
"Create a memory note about the authentication flow"
```

## Key Serena Tools Available

| Category | Tool | Description |
|----------|------|-------------|
| 🔍 **Analysis** | `find_symbol` | Search for symbols globally |
| | `find_referencing_symbols` | Find what references a symbol |
| | `get_symbols_overview` | Get file/directory symbol overview |
| ✏️ **Editing** | `replace_symbol_body` | Replace complete symbol definitions |
| | `insert_before_symbol` | Insert before symbol |
| | `replace_lines` | Replace line ranges |
| 📁 **Files** | `read_file` | Read file contents |
| | `create_text_file` | Create/overwrite files |
| | `search_for_pattern` | Search patterns in project |
| 🧠 **Memory** | `write_memory` | Store project knowledge |
| | `read_memory` | Retrieve stored knowledge |
| | `list_memories` | List available memories |
| ⚙️ **Project** | `onboarding` | Analyze project structure |
| | `activate_project` | Switch projects |
| | `restart_language_server` | Restart LSP servers |

## Configuration Files

- **`.serena/project.yml`** - Serena project settings
- **`.gemini/settings.json`** - Gemini CLI MCP configuration
- **`start-serena-gemini.sh`** - Integration startup script

## Troubleshooting

```bash
# Check status
/mcp

# Restart if needed
# Exit Gemini CLI and run:
./start-serena-gemini.sh

# Test configuration
./test-integration.sh
```

## Environment Variables

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Docker Alternative

```bash
# Build and run with Docker
docker-compose -f docker-compose.serena-gemini.yml up

# Run standalone Serena MCP server
docker-compose -f docker-compose.serena-gemini.yml --profile standalone up serena-mcp
```

---

**Need help?** Check `SERENA_GEMINI_INTEGRATION.md` for detailed documentation.

