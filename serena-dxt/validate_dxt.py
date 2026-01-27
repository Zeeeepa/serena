#!/usr/bin/env python3
"""
Comprehensive validation script for Serena DXT extension.
This script validates all imports, tools, and configurations before packaging.
"""

import sys
import os
import subprocess
from pathlib import Path

def validate_imports():
    """Validate all required Serena imports."""
    print("=== VALIDATING IMPORTS ===")
    
    # Add lib directory to Python path
    lib_path = Path(__file__).parent / "server" / "lib"
    sys.path.insert(0, str(lib_path))
    
    imports_to_test = [
        ("serena.mcp", "SerenaMCPFactorySingleProcess"),
        ("serena.util.logging", "MemoryLogHandler"),
        ("serena.constants", "DEFAULT_CONTEXT"),
        ("serena.constants", "DEFAULT_MODES"),
        ("serena.agent", "SerenaAgent"),
        ("serena.project", "Project"),
        ("serena.tools.tools_base", "ToolRegistry"),
    ]
    
    failed_imports = []
    
    for module, item in imports_to_test:
        try:
            exec(f"from {module} import {item}")
            print(f"✅ {module}.{item}")
        except ImportError as e:
            print(f"❌ {module}.{item}: {e}")
            failed_imports.append((module, item, str(e)))
    
    return len(failed_imports) == 0, failed_imports

def validate_tools():
    """Validate tool availability and manifest consistency."""
    print("\n=== VALIDATING TOOLS ===")
    
    try:
        from serena.tools.tools_base import ToolRegistry
        
        registry = ToolRegistry()
        default_enabled_tools = set(registry.get_tool_names_default_enabled())
        all_tool_classes = registry.get_all_tool_classes()
        
        print(f"Total tool classes available: {len(all_tool_classes)}")
        print(f"Default enabled tools: {len(default_enabled_tools)}")
        
        # Tools defined in our manifest
        manifest_tools = [
            'read_file', 'create_text_file', 'list_dir', 'find_file', 'replace_regex',
            'delete_lines', 'replace_lines', 'insert_at_line', 'search_for_pattern',
            'restart_language_server', 'get_symbols_overview', 'find_symbol',
            'find_referencing_symbols', 'replace_symbol_body', 'insert_after_symbol',
            'insert_before_symbol', 'write_memory', 'read_memory', 'list_memories',
            'delete_memory', 'execute_shell_command', 'activate_project', 'remove_project',
            'switch_modes', 'get_current_config', 'check_onboarding_performed',
            'onboarding', 'think_about_collected_information', 'think_about_task_adherence',
            'think_about_whether_you_are_done', 'summarize_changes', 'prepare_for_new_conversation',
            'initial_instructions'
        ]
        
        # Validate all manifest tools
        invalid_tools = []
        for tool in manifest_tools:
            if not registry.is_valid_tool_name(tool):
                invalid_tools.append(tool)
        
        if invalid_tools:
            print(f"❌ Invalid tools in manifest: {invalid_tools}")
            return False, invalid_tools
        else:
            print(f"✅ All {len(manifest_tools)} manifest tools are valid")
            
        # Check for tools not in default enabled
        non_default_tools = [tool for tool in manifest_tools if tool not in default_enabled_tools]
        if non_default_tools:
            print(f"ℹ️  Tools in manifest but not default enabled: {non_default_tools}")
        
        return True, []
        
    except Exception as e:
        print(f"❌ Error validating tools: {e}")
        return False, [str(e)]

def validate_mcp_server():
    """Validate that the MCP server entry point works."""
    print("\n=== VALIDATING MCP SERVER ===")
    
    try:
        server_path = Path(__file__).parent / "server" / "serena_mcp.py"
        lib_path = Path(__file__).parent / "server" / "lib"
        
        # Test that the server can be imported and shows help
        env = os.environ.copy()
        env["PYTHONPATH"] = str(lib_path)
        
        result = subprocess.run(
            [sys.executable, str(server_path), "--help"],
            cwd=server_path.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and "Serena MCP Server" in result.stdout:
            print("✅ MCP server entry point works correctly")
            return True, []
        else:
            print(f"❌ MCP server failed: {result.stderr}")
            return False, [result.stderr]
            
    except Exception as e:
        print(f"❌ Error validating MCP server: {e}")
        return False, [str(e)]

def validate_manifest():
    """Validate the manifest.json file."""
    print("\n=== VALIDATING MANIFEST ===")
    
    try:
        result = subprocess.run(
            ["dxt", "validate", "manifest.json"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and "Manifest is valid!" in result.stdout:
            print("✅ Manifest validation passed")
            return True, []
        else:
            print(f"❌ Manifest validation failed: {result.stderr}")
            return False, [result.stderr]
            
    except Exception as e:
        print(f"❌ Error validating manifest: {e}")
        return False, [str(e)]

def main():
    """Run all validations."""
    print("🔍 SERENA DXT VALIDATION")
    print("=" * 50)
    
    all_passed = True
    all_errors = []
    
    # Run all validations
    validations = [
        ("Imports", validate_imports),
        ("Tools", validate_tools),
        ("MCP Server", validate_mcp_server),
        ("Manifest", validate_manifest),
    ]
    
    for name, validation_func in validations:
        try:
            passed, errors = validation_func()
            if not passed:
                all_passed = False
                all_errors.extend(errors)
        except Exception as e:
            print(f"❌ {name} validation crashed: {e}")
            all_passed = False
            all_errors.append(f"{name}: {e}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Serena DXT extension is ready for packaging")
        return 0
    else:
        print("💥 VALIDATION FAILURES DETECTED!")
        print("❌ Fix the following issues before packaging:")
        for error in all_errors:
            print(f"   - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

