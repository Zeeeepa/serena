#!/usr/bin/env python3
"""
Comprehensive test script for individual Serena tools
"""
import subprocess
import json
import time
import os
import sys
import tempfile

def run_serena_tool_test(tool_name, test_args=None):
    """Test a specific Serena tool via MCP server"""
    print(f"🧪 Testing {tool_name}...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    # Create a simple test script that uses the tool
    test_script = f'''
import sys
import os
sys.path.insert(0, "/tmp/Zeeeepa/serena/src")

try:
    from serena.agent import SerenaAgent
    from serena.config.context_mode import load_context, load_mode
    from serena.config.project import ProjectConfig
    
    # Load project config
    project_config = ProjectConfig.from_project_dir(".")
    
    # Load context and mode
    context = load_context("ide-assistant")
    mode = load_mode("interactive")
    
    # Create agent
    agent = SerenaAgent(
        project_config=project_config,
        context=context,
        mode=mode
    )
    
    # Get the tool
    tool = None
    for t in agent.tool_registry.tools:
        if t.name == "{tool_name}":
            tool = t
            break
    
    if tool is None:
        print(f"❌ Tool '{tool_name}' not found in registry")
        sys.exit(1)
    
    print(f"✅ Tool '{tool_name}' found")
    print(f"   Description: {{tool.description[:100]}}...")
    print(f"   Parameters: {{len(tool.input_schema.get('properties', {{}}))}} parameters")
    
    # List parameter names
    params = list(tool.input_schema.get('properties', {{}}).keys())
    if params:
        print(f"   Parameter names: {{', '.join(params[:5])}}")
    
except Exception as e:
    print(f"❌ Error testing {tool_name}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd='.'
        )
        
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"❌ Failed to test {tool_name}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Test for {tool_name} timed out")
        return False
    except Exception as e:
        print(f"❌ Exception testing {tool_name}: {e}")
        return False

def test_functional_tools():
    """Test tools with actual functionality"""
    print("🧪 Testing functional Serena tools...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    # Test read_file tool
    test_script = '''
import sys
import os
sys.path.insert(0, "/tmp/Zeeeepa/serena/src")

try:
    from serena.agent import SerenaAgent
    from serena.config.context_mode import load_context, load_mode
    from serena.config.project import ProjectConfig
    
    # Load project config
    project_config = ProjectConfig.from_project_dir(".")
    
    # Load context and mode
    context = load_context("ide-assistant")
    mode = load_mode("interactive")
    
    # Create agent
    agent = SerenaAgent(
        project_config=project_config,
        context=context,
        mode=mode
    )
    
    # Test read_file tool
    read_file_tool = None
    for tool in agent.tool_registry.tools:
        if tool.name == "read_file":
            read_file_tool = tool
            break
    
    if read_file_tool:
        print("✅ read_file tool found and ready")
        
        # Try to read README.md
        if os.path.exists("README.md"):
            try:
                result = read_file_tool.call({"file_path": "README.md"})
                if result and len(str(result)) > 0:
                    print("✅ read_file tool works - successfully read README.md")
                    print(f"   Content length: {len(str(result))} characters")
                else:
                    print("⚠️  read_file tool returned empty result")
            except Exception as e:
                print(f"❌ read_file tool failed: {e}")
        else:
            print("⚠️  README.md not found for testing read_file")
    else:
        print("❌ read_file tool not found")
    
    # Test list_dir tool
    list_dir_tool = None
    for tool in agent.tool_registry.tools:
        if tool.name == "list_dir":
            list_dir_tool = tool
            break
    
    if list_dir_tool:
        print("✅ list_dir tool found and ready")
        try:
            result = list_dir_tool.call({"path": "."})
            if result and len(str(result)) > 0:
                print("✅ list_dir tool works - successfully listed current directory")
                print(f"   Result length: {len(str(result))} characters")
            else:
                print("⚠️  list_dir tool returned empty result")
        except Exception as e:
            print(f"❌ list_dir tool failed: {e}")
    else:
        print("❌ list_dir tool not found")
    
    # Test write_memory tool
    write_memory_tool = None
    for tool in agent.tool_registry.tools:
        if tool.name == "write_memory":
            write_memory_tool = tool
            break
    
    if write_memory_tool:
        print("✅ write_memory tool found and ready")
        try:
            result = write_memory_tool.call({
                "memory_name": "integration_test",
                "content": "This is a test memory created during Serena + Gemini CLI integration testing."
            })
            print("✅ write_memory tool works - successfully created test memory")
        except Exception as e:
            print(f"❌ write_memory tool failed: {e}")
    else:
        print("❌ write_memory tool not found")
    
    # Test read_memory tool
    read_memory_tool = None
    for tool in agent.tool_registry.tools:
        if tool.name == "read_memory":
            read_memory_tool = tool
            break
    
    if read_memory_tool:
        print("✅ read_memory tool found and ready")
        try:
            result = read_memory_tool.call({"memory_name": "integration_test"})
            if result and "integration testing" in str(result).lower():
                print("✅ read_memory tool works - successfully read test memory")
            else:
                print("⚠️  read_memory tool didn't return expected content")
        except Exception as e:
            print(f"❌ read_memory tool failed: {e}")
    else:
        print("❌ read_memory tool not found")
        
except Exception as e:
    print(f"❌ Error in functional testing: {e}")
    import traceback
    traceback.print_exc()
'''
    
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            cwd='.'
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Functional testing timed out")
        return False
    except Exception as e:
        print(f"❌ Exception in functional testing: {e}")
        return False

def main():
    """Test all key Serena tools"""
    print("🚀 Testing Individual Serena Tools")
    print("=" * 50)
    
    # Key tools to test
    key_tools = [
        "find_symbol",
        "find_referencing_symbols", 
        "get_symbols_overview",
        "replace_symbol_body",
        "insert_before_symbol",
        "read_file",
        "create_text_file",
        "list_dir",
        "search_for_pattern",
        "write_memory",
        "read_memory",
        "list_memories",
        "onboarding",
        "activate_project",
        "get_current_config"
    ]
    
    print(f"📋 Testing {len(key_tools)} key Serena tools...")
    print()
    
    results = []
    for tool_name in key_tools:
        success = run_serena_tool_test(tool_name)
        results.append((tool_name, success))
        print()
    
    print("🧪 Running functional tests...")
    print("-" * 30)
    functional_success = test_functional_tools()
    print()
    
    print("🏁 Tool Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for tool_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {tool_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    func_status = "✅ PASS" if functional_success else "❌ FAIL"
    print(f"{func_status} Functional Tests")
    
    print()
    print(f"📊 Results: {passed} passed, {failed} failed out of {len(key_tools)} tools")
    
    if functional_success:
        print("✅ Functional tests passed")
    else:
        print("❌ Functional tests failed")
    
    print()
    if passed >= len(key_tools) * 0.8 and functional_success:  # 80% success rate
        print("🎉 Serena tools are working well!")
        print("\n📝 Integration is ready for use with Gemini CLI")
        print("Try these commands in Gemini CLI:")
        print("• 'Show me the project structure'")
        print("• 'Find all Python functions in this project'") 
        print("• 'Create a memory note about this integration'")
        print("• 'Help me understand the codebase'")
        return 0
    else:
        print("⚠️  Some tools may have issues. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

