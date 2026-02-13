#!/bin/bash

# Serena + MCPHub Startup Script
# This script starts MCPHub with Serena MCP server integration

set -e

echo "🚀 Starting Serena + MCPHub Integration"
echo "======================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is required but not installed. Please install docker-compose first."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Validate Serena DXT structure
if [ ! -f "server/serena_mcp.py" ]; then
    echo "❌ Serena MCP server not found. Make sure you're in the serena-dxt directory."
    exit 1
fi

if [ ! -d "server/lib" ]; then
    echo "❌ Serena dependencies not found. Make sure the DXT package was properly extracted."
    exit 1
fi

echo "✅ Serena DXT structure validated"

# Test Serena MCP server
echo "🧪 Testing Serena MCP server..."
cd server
if timeout 5 python3 -c "
import sys
sys.path.insert(0, 'lib')
from serena.mcp import SerenaMCPFactorySingleProcess
print('✅ Serena imports working')
" 2>/dev/null; then
    echo "✅ Serena MCP server test passed"
else
    echo "❌ Serena MCP server test failed. Check dependencies."
    exit 1
fi
cd ..

# Start MCPHub with Docker Compose
echo "🐳 Starting MCPHub with Docker Compose..."
docker-compose -f docker-compose.mcphub.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if MCPHub is running
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ MCPHub is running successfully!"
else
    echo "⚠️  MCPHub may still be starting up..."
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📊 MCPHub Dashboard: http://localhost:3000"
echo "🔑 Default Login: admin / admin123"
echo ""
echo "🔗 API Endpoints:"
echo "   All servers: http://localhost:3000/mcp"
echo "   Serena only: http://localhost:3000/mcp/serena"
echo "   Development group: http://localhost:3000/mcp/development"
echo "   Smart routing: http://localhost:3000/mcp/\$smart"
echo ""
echo "🛠️  Available Serena Tools: 33 total"
echo "   - File Operations (9 tools)"
echo "   - Symbol Navigation (7 tools)"
echo "   - Memory Management (4 tools)"
echo "   - Project Management (4 tools)"
echo "   - System Integration (1 tool)"
echo "   - Agent Intelligence (8 tools)"
echo ""
echo "📚 For detailed usage instructions, see MCPHUB_SETUP.md"
echo ""
echo "🔧 To stop: docker-compose -f docker-compose.mcphub.yml down"

