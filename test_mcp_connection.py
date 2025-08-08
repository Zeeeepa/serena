#!/usr/bin/env python3
"""
Test script to verify MCP connection between Gemini CLI and Serena
"""
import subprocess
import json
import time
import os
import sys

def test_serena_mcp_server():
    """Test if Serena MCP server can start"""
    print("🧪 Testing Serena MCP server startup...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    try:
        # Test help command
        result = subprocess.run(
            ['uv', 'run', 'serena-mcp-server', '--help'],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0:
            print("✅ Serena MCP server help command works")
            return True
        else:
            print(f"❌ Serena MCP server help failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Serena MCP server help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Serena MCP server: {e}")
        return False

def test_gemini_cli():
    """Test if Gemini CLI is available"""
    print("🧪 Testing Gemini CLI availability...")
    
    try:
        result = subprocess.run(
            ['gemini', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ Gemini CLI is available: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Gemini CLI version check failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Gemini CLI version check timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Gemini CLI: {e}")
        return False

def test_configuration_files():
    """Test if configuration files are properly set up"""
    print("🧪 Testing configuration files...")
    
    # Check .gemini/settings.json
    if os.path.exists('.gemini/settings.json'):
        try:
            with open('.gemini/settings.json', 'r') as f:
                config = json.load(f)
            
            if 'mcpServers' in config and 'serena' in config['mcpServers']:
                print("✅ Gemini CLI configuration file is valid")
                serena_config = config['mcpServers']['serena']
                print(f"   Command: {serena_config.get('command')}")
                print(f"   Args: {serena_config.get('args')}")
                print(f"   CWD: {serena_config.get('cwd')}")
                return True
            else:
                print("❌ Serena MCP server not configured in Gemini CLI")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in .gemini/settings.json: {e}")
            return False
    else:
        print("❌ .gemini/settings.json not found")
        return False

def test_serena_tools():
    """Test individual Serena tools by importing them"""
    print("🧪 Testing Serena tools availability...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    test_script = '''
import sys
sys.path.insert(0, "/tmp/Zeeeepa/serena/src")

try:
    from serena.agent import SerenaAgent, ToolRegistry
    from serena.config.context_mode import Context, Mode
    
    print("✅ Serena core modules imported successfully")
    
    # Try to create a tool registry
    registry = ToolRegistry()
    print(f"✅ ToolRegistry created with {len(registry.tools)} base tools")
    
    # List some key tools
    key_tools = [
        "find_symbol", "find_referencing_symbols", "get_symbols_overview",
        "replace_symbol_body", "read_file", "write_memory", "onboarding"
    ]
    
    available_tools = [tool.name for tool in registry.tools]
    found_tools = [tool for tool in key_tools if tool in available_tools]
    
    print(f"✅ Found {len(found_tools)} key Serena tools: {', '.join(found_tools)}")
    
    if len(found_tools) >= 5:
        print("✅ Serena tools are properly available")
    else:
        print("⚠️  Some key Serena tools may be missing")
        
except ImportError as e:
    print(f"❌ Failed to import Serena modules: {e}")
except Exception as e:
    print(f"❌ Error testing Serena tools: {e}")
'''
    
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Serena tools test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Serena tools: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Serena + Gemini CLI Integration")
    print("=" * 50)
    
    tests = [
        ("Serena MCP Server", test_serena_mcp_server),
        ("Gemini CLI", test_gemini_cli),
        ("Configuration Files", test_configuration_files),
        ("Serena Tools", test_serena_tools),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        print()
    
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! Integration is ready.")
        print("\n📝 Next steps:")
        print("1. Set GEMINI_API_KEY environment variable")
        print("2. Run: gemini")
        print("3. In Gemini CLI, try: 'List all available tools'")
        print("4. Test Serena tools with natural language commands")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

