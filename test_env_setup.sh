#!/bin/bash

# Test script for .env file functionality
# This script tests the API key setup functionality

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing .env file functionality${NC}"
echo "=================================="

# Test 1: Check if .env file exists
echo -e "\n${YELLOW}Test 1: Checking .env file existence${NC}"
if [[ -f ".env" ]]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Test 2: Check if GEMINI_API_KEY is in .env
    echo -e "\n${YELLOW}Test 2: Checking GEMINI_API_KEY in .env${NC}"
    if grep -q "GEMINI_API_KEY=" ".env"; then
        echo -e "${GREEN}✅ GEMINI_API_KEY found in .env${NC}"
        
        # Test 3: Load and validate API key
        echo -e "\n${YELLOW}Test 3: Loading API key from .env${NC}"
        source .env
        
        if [[ -n "$GEMINI_API_KEY" ]]; then
            echo -e "${GREEN}✅ GEMINI_API_KEY loaded successfully${NC}"
            echo -e "${BLUE}   API key length: ${#GEMINI_API_KEY} characters${NC}"
            echo -e "${BLUE}   API key prefix: ${GEMINI_API_KEY:0:10}...${NC}"
        else
            echo -e "${RED}❌ GEMINI_API_KEY is empty${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ GEMINI_API_KEY not found in .env${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ .env file does not exist${NC}"
    echo -e "${YELLOW}💡 Run ./deploy.sh to create .env file with API key${NC}"
    exit 1
fi

# Test 4: Check .gitignore
echo -e "\n${YELLOW}Test 4: Checking .gitignore for .env entry${NC}"
if [[ -f ".gitignore" ]] && grep -q "^\.env$" ".gitignore"; then
    echo -e "${GREEN}✅ .env is properly ignored in .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  .env not found in .gitignore (security concern)${NC}"
fi

# Test 5: Test launch script .env loading
echo -e "\n${YELLOW}Test 5: Testing launch script .env loading${NC}"
if [[ -f "launch-gemini-with-serena.sh" ]]; then
    if grep -q "source .env" "launch-gemini-with-serena.sh"; then
        echo -e "${GREEN}✅ Launch script will load .env file${NC}"
    else
        echo -e "${RED}❌ Launch script does not load .env file${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Launch script not found${NC}"
fi

echo -e "\n${GREEN}🎉 All .env functionality tests passed!${NC}"
echo -e "${BLUE}💡 Your API key is properly configured and will be automatically loaded${NC}"

