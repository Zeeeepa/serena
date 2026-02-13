# 🎯 **Agno-UI Dashboard with Serena Integration - Complete Setup**

## 🚀 **One-Command Setup**

Run this single command to set up everything:

```bash
./setup_agno_ui_dashboard.sh
```

## 📋 **What the Setup Script Does**

### ✅ **System Requirements Check**
- Verifies Python 3.11+
- Verifies Node.js 18+
- Installs `pnpm` if missing
- Installs `uv` if missing

### 📦 **Dependencies Installation**
- **Linux**: Installs via `apt-get` or `yum`
- **macOS**: Installs via Homebrew
- **Python**: Installs Serena with all extras
- **Frontend**: Clones and sets up agent-ui

### ⚙️ **Configuration Setup**
- Creates `.env` file with API key templates
- Sets up project structure
- Creates startup scripts

### 🔗 **Shell Integration**
- Adds convenient aliases to `.bashrc`/`.zshrc`
- Creates navigation shortcuts
- Sets up service management commands

---

## 🎯 **Quick Start Commands**

After running the setup script:

### **Start Complete Dashboard**
```bash
start
```

### **Individual Services**
```bash
start-backend    # Start Serena-Agno backend
start-frontend   # Start Agent-UI frontend  
start-mcp        # Start MCP server
```

### **Navigation**
```bash
agno-cd          # Go to project root
agno-ui-cd       # Go to frontend directory
```

### **Monitoring**
```bash
agno-status      # Check running services
agno-logs        # View logs
```

---

## 🌐 **Access Points**

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard UI** | http://localhost:3000 | Main orchestration interface |
| **Backend API** | http://localhost:8000 | Serena-Agno agent endpoint |
| **MCP Server** | Background | Tool integration server |

---

## 🔧 **Configuration**

### **1. API Keys Setup**
Edit the `.env` file with your API keys:

```bash
nano .env
```

Required keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  
GOOGLE_API_KEY=your_google_api_key_here
```

### **2. Reload Shell**
After setup, reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc for zsh
```

---

## 🎯 **Dashboard Features**

### **🤖 Orchestration Capabilities**
- **Sub-agent Creation** - Async multi-threaded agent spawning
- **MCP Tool Integration** - Access to environment and system tools
- **Progress Tracking** - Real-time updates and execution traces
- **GitHub Integration** - Project selection and repository access

### **🔧 Serena Integration**
- **Semantic Code Analysis** - LSP-based operations across 13+ languages
- **Memory System** - Project knowledge persistence
- **Symbol Operations** - Precise code editing and navigation
- **Multi-language Support** - Python, TypeScript, Go, Java, Rust, and more

### **🎨 Agent-UI Features**
- **Real-time Chat** - Interactive agent communication
- **Tool Execution** - Visual tool call tracking
- **Progress Monitoring** - Live updates and status tracking
- **Project Management** - GitHub repository integration

---

## 🛠️ **Development Commands**

### **Testing**
```bash
agno-test        # Run test suite
agno-format      # Format code
agno-type-check  # Type checking
```

### **Environment**
```bash
agno-env         # View environment variables
agno-status      # Check service status
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Check what's using the ports
   lsof -i :3000  # Frontend
   lsof -i :8000  # Backend
   ```

2. **API Keys Not Working**
   ```bash
   # Check environment variables
   agno-env
   ```

3. **Services Not Starting**
   ```bash
   # Check service status
   agno-status
   
   # View logs
   agno-logs
   ```

### **Manual Restart**
```bash
# Stop all services (Ctrl+C)
# Then restart
start
```

---

## 📁 **Project Structure**

```
serena/
├── setup_agno_ui_dashboard.sh    # Main setup script
├── start_dashboard.sh            # Complete dashboard startup
├── start_backend.sh              # Backend only
├── start_frontend.sh             # Frontend only  
├── start_mcp_server.sh           # MCP server only
├── .env                          # Environment configuration
├── agno-ui/                      # Frontend application
├── scripts/                      # Serena scripts
│   ├── agno_agent.py            # Agno agent integration
│   └── mcp_server.py            # MCP server
└── src/serena/                   # Serena core
    ├── agno.py                  # Agno integration
    └── tools/                   # Tool implementations
```

---

## 🎉 **Ready to Orchestrate!**

Your complete agno-ui dashboard with Serena integration is now ready:

1. **✅ Setup Complete** - All dependencies installed
2. **✅ Services Ready** - Backend, frontend, and MCP server configured  
3. **✅ Aliases Added** - Convenient shell commands available
4. **✅ Documentation** - Quick start guide and troubleshooting

**🚀 Start orchestrating with: `start`**

