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
