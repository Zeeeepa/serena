#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Launching Gemini CLI with Serena Integration...${NC}"

# Load .env file if it exists
if [ -f ".env" ]; then
    echo -e "${GREEN}📄 Loading environment variables from .env file...${NC}"
    source .env
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${GREEN}💡 Tip: Run ./deploy.sh to set up your GEMINI_API_KEY${NC}"
    echo "   Or manually set: export GEMINI_API_KEY=your-api-key-here"
    echo ""
else
    echo -e "${GREEN}✅ GEMINI_API_KEY loaded successfully${NC}"
    echo ""
fi

# Launch Gemini CLI
echo -e "${GREEN}Starting Gemini CLI...${NC}"
echo "Use '/mcp' to check Serena connection"
echo "Use '/help' to see available commands"
echo ""

exec gemini
