# Using Serena with MCPHub

This guide shows how to integrate the Serena DXT extension with [MCPHub](https://github.com/samanhappy/mcphub), a unified hub for managing multiple MCP servers.

## 🎯 Overview

MCPHub allows you to:
- Manage multiple MCP servers from a single dashboard
- Access servers via HTTP/SSE endpoints
- Group servers by functionality
- Monitor server status in real-time
- Use smart routing to automatically find relevant tools

## 🚀 Quick Setup

### 1. Install MCPHub

```bash
# Using Docker (Recommended)
docker run -p 3000:3000 samanhappy/mcphub

# Or clone and run locally
git clone https://github.com/samanhappy/mcphub.git
cd mcphub
pnpm install
pnpm dev
```

### 2. Extract Serena DXT

```bash
# Extract the DXT package to get the server files
mkdir -p ~/serena-mcp
cd ~/serena-mcp

# If you have the .dxt file, extract it:
unzip serena-dxt.dxt

# Or clone from the repository:
git clone https://github.com/Zeeeepa/serena.git
cd serena/serena-dxt
```

### 3. Configure MCPHub

Create or update your `mcp_settings.json` file:

```json
{
  "mcpServers": {
    "serena": {
      "command": "python3",
      "args": [
        "/absolute/path/to/serena-dxt/server/serena_mcp.py",
        "--context=desktop-app",
        "--log-level=INFO"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/serena-dxt/server/lib",
        "SERENA_LOG_LEVEL": "INFO"
      },
      "description": "Serena AI coding agent with 33 tools for development",
      "category": "development"
    }
  }
}
```

**Important**: Replace `/absolute/path/to/serena-dxt` with the actual path where you extracted the Serena DXT files.

### 4. Start MCPHub with Configuration

```bash
# Using Docker with custom config
docker run -p 3000:3000 \
  -v ./mcp_settings.json:/app/mcp_settings.json \
  -v /absolute/path/to/serena-dxt:/app/serena-dxt \
  samanhappy/mcphub

# Or if running locally
pnpm dev
```

## 🖥️ Access Methods

### MCPHub Dashboard
- Open `http://localhost:3000`
- Login with `admin` / `admin123` (default credentials)
- Monitor Serena server status
- Enable/disable the server
- View available tools

### HTTP Endpoints

#### All Servers (including Serena)
```
http://localhost:3000/mcp
```

#### Serena Server Only
```
http://localhost:3000/mcp/serena
```

#### Smart Routing (Experimental)
```
http://localhost:3000/mcp/$smart
```

#### Development Group (if you create one)
```
http://localhost:3000/mcp/development
```

## 🛠️ Serena Tools Available

When connected through MCPHub, you'll have access to all 33 Serena tools:

### File Operations (9 tools)
- `read_file` - Read file contents
- `create_text_file` - Create/overwrite files
- `list_dir` - List directory contents
- `find_file` - Find files by name/pattern
- `replace_regex` - Replace text using regex
- `delete_lines` - Delete specific lines
- `replace_lines` - Replace specific lines
- `insert_at_line` - Insert text at line
- `search_for_pattern` - Search for patterns

### Symbol Navigation (7 tools)
- `get_symbols_overview` - Get file/directory symbols
- `find_symbol` - Find symbols by name
- `find_referencing_symbols` - Find symbol references
- `replace_symbol_body` - Replace symbol definition
- `insert_after_symbol` - Insert after symbol
- `insert_before_symbol` - Insert before symbol
- `restart_language_server` - Restart LSP

### Memory Management (4 tools)
- `write_memory` - Store information
- `read_memory` - Retrieve information
- `list_memories` - List stored memories
- `delete_memory` - Delete memories

### Project Management (4 tools)
- `activate_project` - Activate project
- `remove_project` - Remove project
- `switch_modes` - Switch agent modes
- `get_current_config` - Get configuration

### System Integration (1 tool)
- `execute_shell_command` - Run shell commands

### Agent Intelligence (8 tools)
- `onboarding` - Project onboarding
- `check_onboarding_performed` - Check onboarding status
- `think_about_collected_information` - Analyze information
- `think_about_task_adherence` - Check task progress
- `think_about_whether_you_are_done` - Completion check
- `summarize_changes` - Summarize modifications
- `prepare_for_new_conversation` - Prepare context
- `initial_instructions` - Get initial guidance

## 🔧 Configuration Options

### Environment Variables
```json
{
  "env": {
    "PYTHONPATH": "/path/to/serena-dxt/server/lib",
    "SERENA_LOG_LEVEL": "DEBUG|INFO|WARNING|ERROR|CRITICAL",
    "SERENA_PROJECT_DIR": "/path/to/your/project"
  }
}
```

### Command Arguments
```json
{
  "args": [
    "/path/to/serena_mcp.py",
    "--context=desktop-app",
    "--log-level=INFO",
    "--project=/path/to/project",
    "--tool-timeout=30.0"
  ]
}
```

## 🎯 Usage Examples

### With Claude Desktop
Configure Claude Desktop to use MCPHub:

```json
{
  "mcpServers": {
    "mcphub-serena": {
      "command": "curl",
      "args": [
        "-N",
        "-H", "Accept: text/event-stream",
        "http://localhost:3000/sse/serena"
      ]
    }
  }
}
```

### With Cursor
Add to your Cursor MCP configuration:
```
http://localhost:3000/mcp/serena
```

### With Custom AI Applications
Use the HTTP endpoint directly:
```javascript
const response = await fetch('http://localhost:3000/mcp/serena', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    method: 'tools/call',
    params: {
      name: 'read_file',
      arguments: {
        path: 'src/main.py'
      }
    }
  })
});
```

## 🐛 Troubleshooting

### Server Won't Start
1. Check that Python 3 is available: `python3 --version`
2. Verify the path to `serena_mcp.py` is correct
3. Ensure `PYTHONPATH` points to the `server/lib` directory
4. Check MCPHub logs in the dashboard

### Tools Not Available
1. Verify Serena server shows as "Running" in MCPHub dashboard
2. Check that all 33 tools are listed in the server details
3. Restart the Serena server from the dashboard

### Permission Issues
1. Ensure the serena-dxt directory is readable
2. Check that Python can access the lib directory
3. Verify file permissions on the server files

### Connection Issues
1. Confirm MCPHub is running on port 3000
2. Test the endpoint: `curl http://localhost:3000/mcp/serena`
3. Check firewall settings if accessing remotely

## 📚 Advanced Usage

### Server Groups
Create a "development" group in MCPHub dashboard and add Serena to it:
```
http://localhost:3000/mcp/development
```

### Smart Routing
Enable smart routing in MCPHub settings to automatically find the best Serena tool for any task:
```
http://localhost:3000/mcp/$smart
```

### Multiple Projects
Run multiple Serena instances for different projects:
```json
{
  "mcpServers": {
    "serena-project-a": {
      "command": "python3",
      "args": ["/path/to/serena_mcp.py", "--project=/path/to/project-a"],
      "env": {"PYTHONPATH": "/path/to/serena-dxt/server/lib"}
    },
    "serena-project-b": {
      "command": "python3", 
      "args": ["/path/to/serena_mcp.py", "--project=/path/to/project-b"],
      "env": {"PYTHONPATH": "/path/to/serena-dxt/server/lib"}
    }
  }
}
```

## 🔗 Resources

- [MCPHub Repository](https://github.com/samanhappy/mcphub)
- [MCPHub Discord](https://discord.gg/qMKNsn5Q)
- [Serena Repository](https://github.com/Zeeeepa/serena)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## 📝 Notes

- MCPHub provides a web dashboard for monitoring and managing Serena
- HTTP endpoints are more compatible than SSE with various AI clients
- Smart routing can automatically select the best Serena tool for tasks
- Group-based access allows organizing Serena with other development tools

