# Installing Serena DXT Extension

## Quick Installation

1. **Download** the `serena-dxt.dxt` file
2. **Install** in Claude Desktop:
   - Open Claude Desktop
   - Go to Settings → Extensions
   - Click "Install Extension" 
   - Select the `serena-dxt.dxt` file
3. **Configure** when prompted:
   - Set your project directory path
   - Adjust other settings as needed

## Manual Installation (Alternative)

If you prefer to install manually or need to customize:

1. **Extract** the DXT contents:
   ```bash
   # The DXT file is essentially a ZIP archive
   unzip serena-dxt.dxt -d serena-extension/
   ```

2. **Install dependencies**:
   ```bash
   cd serena-extension/
   python3 setup.py
   ```

3. **Configure MCP client** to use the server:
   ```json
   {
     "mcpServers": {
       "serena": {
         "command": "python3",
         "args": ["/path/to/serena-extension/server/serena_mcp.py", "--project=/your/project/path"],
         "env": {
           "PYTHONPATH": "/path/to/serena-extension/server/lib"
         }
       }
     }
   }
   ```

## Requirements

- **Python 3.11.x** (exactly - other versions not supported)
- **Claude Desktop** or MCP-compatible client
- **Project directory** to work with

## Verification

After installation, test with a simple command:
```
"List the files in my project directory"
```

If working correctly, Serena should show your project files and be ready for more advanced operations.

## Troubleshooting

- **Python version errors**: Install Python 3.11 specifically
- **Import errors**: Run the setup.py script to install dependencies
- **Symbol navigation issues**: Use `restart_language_server` tool

For more help, see the main README.md file.

