# 🔑 Environment Setup Guide

This guide explains how the Serena + Gemini CLI integration handles your Gemini API key securely through `.env` file management.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
# Run the deployment script - it will prompt for your API key if needed
./deploy.sh
```

The deployment script will:
1. Check if `.env` file exists with `GEMINI_API_KEY`
2. If not found, prompt you to enter your API key
3. Create/update `.env` file with your API key
4. Add `.env` to `.gitignore` for security
5. Continue with the full deployment

### Option 2: Manual Setup
```bash
# Create .env file manually
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Add to .gitignore for security
echo ".env" >> .gitignore

# Run deployment
./deploy.sh
```

## 🔐 Security Features

### Automatic .gitignore Protection
- The deployment script automatically adds `.env` to `.gitignore`
- This prevents your API key from being committed to version control
- Your API key stays local and secure

### Visible Input
- When prompted for your API key, the input is **not hidden**
- This allows you to see what you're typing and verify correctness
- The key is immediately saved to `.env` for future use

## 🎯 How It Works

### 1. Deployment Script Behavior
```bash
# If .env exists with GEMINI_API_KEY
✅ Loads existing API key automatically
✅ Continues with deployment

# If .env doesn't exist or is empty
📝 Prompts: "Please enter your Gemini API key: "
💾 Saves to .env file
🔒 Adds to .gitignore
✅ Continues with deployment
```

### 2. Launch Script Behavior
```bash
./launch-gemini-with-serena.sh
```

The launch script will:
1. Check for `.env` file
2. Load `GEMINI_API_KEY` if found
3. Display success/warning messages
4. Launch Gemini CLI with proper environment

## 🧪 Testing Your Setup

### Test .env Functionality
```bash
# Run the test script to verify everything is working
./test_env_setup.sh
```

This will verify:
- ✅ `.env` file exists
- ✅ `GEMINI_API_KEY` is present and loaded
- ✅ `.gitignore` contains `.env` entry
- ✅ Launch script will load `.env`

### Test Integration
```bash
# Test the full integration
./launch-gemini-with-serena.sh

# In Gemini CLI, try:
What Serena tools are available?
```

## 🔄 Updating Your API Key

### Method 1: Re-run Deployment
```bash
# Delete existing .env and re-run deployment
rm .env
./deploy.sh
# You'll be prompted for a new API key
```

### Method 2: Edit .env Directly
```bash
# Edit the .env file
nano .env

# Update the line:
GEMINI_API_KEY=your-new-api-key-here
```

## 📁 File Structure

After setup, your project will have:
```
project/
├── .env                          # Your API key (git-ignored)
├── .gitignore                    # Contains .env entry
├── deploy.sh                     # Enhanced deployment script
├── launch-gemini-with-serena.sh  # Enhanced launch script
├── test_env_setup.sh             # Test script for .env functionality
└── .gemini/
    └── settings.json             # Gemini CLI configuration
```

## 🆘 Troubleshooting

### "No API key provided" Error
```bash
# Check if .env exists and has content
cat .env

# If empty or missing, re-run deployment
./deploy.sh
```

### "GEMINI_API_KEY not loaded" Warning
```bash
# Test .env loading
source .env
echo $GEMINI_API_KEY

# If empty, check .env file format
cat .env
# Should show: GEMINI_API_KEY=your-key-here
```

### API Key Not Working
```bash
# Verify your API key at Google AI Studio
# https://aistudio.google.com/app/apikey

# Update .env with correct key
echo "GEMINI_API_KEY=correct-key-here" > .env
```

## 🔗 Getting Your API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Use it when prompted by `./deploy.sh`

## ✨ Benefits

- 🔐 **Secure**: API key never committed to git
- 🚀 **Automatic**: Loads on every launch
- 🔄 **Persistent**: Survives system restarts
- 🧪 **Testable**: Built-in verification tools
- 📝 **User-friendly**: Clear prompts and feedback

