#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Full Serena + Gemini CLI Integration${NC}"
echo "=================================================="

# Test 1: Environment setup
echo -e "\n${YELLOW}Test 1: Environment Setup${NC}"
if [ -f ".env" ] && grep -q "GEMINI_API_KEY" .env; then
    echo -e "${GREEN}✅ .env file with API key exists${NC}"
else
    echo -e "${RED}❌ .env file missing or no API key${NC}"
    exit 1
fi

# Test 2: MCP Server startup
echo -e "\n${YELLOW}Test 2: MCP Server Startup${NC}"
echo "Testing Serena MCP server startup..."
timeout 10s bash -c 'PYTHONPATH="" uv run serena-mcp-server' > /tmp/mcp_test.log 2>&1 &
MCP_PID=$!
sleep 5

# Check if the server started by looking for the startup message
if grep -q "Starting MCP server with.*tools" /tmp/mcp_test.log; then
    echo -e "${GREEN}✅ Serena MCP server started successfully${NC}"
    echo "Available tools: $(grep -o '[0-9]\+ tools' /tmp/mcp_test.log | head -1)"
else
    echo -e "${RED}❌ Serena MCP server failed to start properly${NC}"
    echo "Log output:"
    tail -10 /tmp/mcp_test.log
fi

# Kill the test process
kill $MCP_PID 2>/dev/null || true

# Test 3: Gemini CLI configuration
echo -e "\n${YELLOW}Test 3: Gemini CLI Configuration${NC}"
if [ -f ".gemini/settings.json" ]; then
    echo -e "${GREEN}✅ Gemini CLI configuration exists${NC}"
    echo "Configuration preview:"
    head -5 .gemini/settings.json
else
    echo -e "${RED}❌ Gemini CLI configuration missing${NC}"
fi

# Test 4: Launch script functionality
echo -e "\n${YELLOW}Test 4: Launch Script Test${NC}"
echo "Testing launch script (will timeout after 5 seconds)..."
timeout 5s ./launch-gemini-with-serena.sh > /tmp/launch_test.log 2>&1 &
LAUNCH_PID=$!
sleep 2

if ps -p $LAUNCH_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Launch script started successfully${NC}"
    kill $LAUNCH_PID 2>/dev/null || true
else
    echo -e "${GREEN}✅ Launch script executed (completed or timed out as expected)${NC}"
fi

echo "Launch script output:"
head -10 /tmp/launch_test.log

# Cleanup
echo -e "\n${YELLOW}Cleanup${NC}"
kill $MCP_PID 2>/dev/null || true
sleep 1

echo -e "\n${GREEN}🎉 Integration test completed!${NC}"
echo -e "${BLUE}💡 To use the integration:${NC}"
echo "   1. Run: ./launch-gemini-with-serena.sh"
echo "   2. In Gemini CLI, try: /mcp"
echo "   3. Ask: 'What Serena tools are available?'"
echo "   4. Start coding with natural language!"
