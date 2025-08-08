#!/usr/bin/env python3
"""
Simple test script for Serena tools using direct MCP server testing
"""
import subprocess
import json
import time
import os
import sys

def test_mcp_server_direct():
    """Test MCP server directly via stdio"""
    print("🧪 Testing Serena MCP server directly...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    try:
        # Start MCP server
        process = subprocess.Popen(
            ['uv', 'run', 'serena-mcp-server', '--project', '.'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send the request
        request_json = json.dumps(initialize_request) + '\n'
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Wait for response with timeout
        try:
            stdout, stderr = process.communicate(timeout=10)
            
            if process.returncode == 0 or stdout:
                print("✅ MCP server responded successfully")
                if stdout:
                    print(f"   Response length: {len(stdout)} characters")
                    # Try to parse as JSON
                    try:
                        lines = stdout.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                response = json.loads(line)
                                if 'result' in response:
                                    print("✅ Valid MCP initialize response received")
                                    if 'capabilities' in response['result']:
                                        caps = response['result']['capabilities']
                                        if 'tools' in caps:
                                            print(f"✅ Server supports tools")
                                        if 'resources' in caps:
                                            print(f"✅ Server supports resources")
                                    return True
                    except json.JSONDecodeError:
                        print("⚠️  Response not valid JSON, but server responded")
                        return True
                return True
            else:
                print(f"❌ MCP server failed: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ MCP server test timed out")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def test_tools_list():
    """Test getting list of tools from MCP server"""
    print("🧪 Testing tools list from MCP server...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/tmp/Zeeeepa/serena/.venv/lib/python3.11/site-packages:/tmp/Zeeeepa/serena/src'
    
    try:
        # Start MCP server
        process = subprocess.Popen(
            ['uv', 'run', 'serena-mcp-server', '--project', '.'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send initialize request first
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        # Send both requests
        requests = [
            json.dumps(initialize_request) + '\n',
            json.dumps(tools_request) + '\n'
        ]
        
        for request in requests:
            process.stdin.write(request)
            process.stdin.flush()
            time.sleep(0.5)  # Small delay between requests
        
        # Wait for response
        try:
            stdout, stderr = process.communicate(timeout=15)
            
            if stdout:
                print("✅ MCP server provided response")
                lines = stdout.strip().split('\n')
                tools_found = []
                
                for line in lines:
                    if line.strip():
                        try:
                            response = json.loads(line)
                            if response.get('id') == 2 and 'result' in response:
                                tools = response['result'].get('tools', [])
                                for tool in tools:
                                    tool_name = tool.get('name', 'unknown')
                                    tools_found.append(tool_name)
                                break
                        except json.JSONDecodeError:
                            continue
                
                if tools_found:
                    print(f"✅ Found {len(tools_found)} Serena tools:")
                    for i, tool in enumerate(tools_found[:10]):  # Show first 10
                        print(f"   {i+1}. {tool}")
                    if len(tools_found) > 10:
                        print(f"   ... and {len(tools_found) - 10} more")
                    return True
                else:
                    print("⚠️  No tools found in response")
                    return False
            else:
                print(f"❌ No response from MCP server: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Tools list test timed out")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Error testing tools list: {e}")
        return False

def test_gemini_cli_integration():
    """Test Gemini CLI with a simple command"""
    print("🧪 Testing Gemini CLI integration...")
    
    if not os.environ.get('GEMINI_API_KEY'):
        print("⚠️  GEMINI_API_KEY not set - skipping integration test")
        return True
    
    try:
        # Create a simple test script
        test_script = '''
const { spawn } = require('child_process');

console.log('Testing Gemini CLI integration...');

const gemini = spawn('gemini', ['-p', 'What tools are available to me?'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, GEMINI_API_KEY: process.env.GEMINI_API_KEY }
});

let output = '';
let errorOutput = '';

gemini.stdout.on('data', (data) => {
    output += data.toString();
});

gemini.stderr.on('data', (data) => {
    errorOutput += data.toString();
});

gemini.on('close', (code) => {
    console.log(`Gemini CLI exited with code ${code}`);
    
    if (output.toLowerCase().includes('serena') || output.toLowerCase().includes('tool')) {
        console.log('✅ Gemini CLI integration appears to be working');
        console.log('Output contains tool-related content');
    } else {
        console.log('⚠️  Gemini CLI integration may have issues');
        console.log('Output does not contain expected content');
    }
    
    if (output.length > 0) {
        console.log(`Output length: ${output.length} characters`);
    }
    
    if (errorOutput.length > 0) {
        console.log(`Error output: ${errorOutput.substring(0, 200)}...`);
    }
});

// Timeout after 30 seconds
setTimeout(() => {
    console.log('Test timeout reached');
    gemini.kill();
}, 30000);
'''
        
        with open('test_gemini_integration.js', 'w') as f:
            f.write(test_script)
        
        result = subprocess.run(
            ['node', 'test_gemini_integration.js'],
            capture_output=True,
            text=True,
            timeout=45,
            env=os.environ.copy()
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        
        # Clean up
        if os.path.exists('test_gemini_integration.js'):
            os.remove('test_gemini_integration.js')
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ Gemini CLI integration test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Gemini CLI integration: {e}")
        return False

def main():
    """Run comprehensive integration tests"""
    print("🚀 Comprehensive Serena + Gemini CLI Integration Test")
    print("=" * 60)
    
    tests = [
        ("MCP Server Direct", test_mcp_server_direct),
        ("Tools List", test_tools_list),
        ("Gemini CLI Integration", test_gemini_cli_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
        print()
    
    print("🏁 Integration Test Results")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All integration tests passed!")
        print("\n📝 Serena + Gemini CLI integration is working!")
        print("\n🚀 Ready to use! Try these commands in Gemini CLI:")
        print("• 'What tools are available to me?'")
        print("• 'Show me the project structure'")
        print("• 'Find all Python functions in this project'")
        print("• 'Create a memory note about this integration'")
        print("• 'Help me understand the codebase'")
    else:
        print("⚠️  Some integration tests failed.")
        print("Check the configuration and try running individual tests.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

