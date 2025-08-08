#!/usr/bin/env python3
"""
Demo LSP Error Analysis Tool

This is a demonstration version that shows how the serena_analysis.py tool would work
by simulating the analysis of the graph-sitter repository and showing the expected output format.
"""

import os
import subprocess
import tempfile
import sys
from pathlib import Path

def clone_repository(repo_url: str) -> str:
    """Clone a Git repository to a temporary directory."""
    print(f"🔄 Cloning repository: {repo_url}")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="demo_analysis_")
    repo_name = os.path.basename(repo_url.rstrip('/').replace('.git', ''))
    clone_path = os.path.join(temp_dir, repo_name)
    
    try:
        # Clone the repository
        cmd = ['git', 'clone', '--depth', '1', repo_url, clone_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
            
        print(f"✅ Repository cloned to: {clone_path}")
        return clone_path
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 300 seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to clone repository: {e}")

def analyze_repository_structure(repo_path: str):
    """Analyze the repository structure and detect language."""
    print(f"\n📁 Analyzing repository structure: {repo_path}")
    
    # Count different file types
    file_counts = {}
    total_files = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Skip .git and other hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.startswith('.'):
                continue
                
            total_files += 1
            ext = Path(file).suffix.lower()
            if ext:
                file_counts[ext] = file_counts.get(ext, 0) + 1
    
    print(f"📊 Found {total_files} files")
    print("🔍 File type distribution:")
    for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {ext}: {count} files")
    
    # Detect primary language
    language_indicators = {
        '.py': 'Python',
        '.js': 'JavaScript', 
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.rs': 'Rust',
        '.go': 'Go',
        '.php': 'PHP',
        '.rb': 'Ruby'
    }
    
    detected_language = "Unknown"
    max_count = 0
    for ext, count in file_counts.items():
        if ext in language_indicators and count > max_count:
            max_count = count
            detected_language = language_indicators[ext]
    
    print(f"🎯 Detected primary language: {detected_language}")
    return detected_language, file_counts

def simulate_lsp_analysis(repo_path: str, language: str):
    """Simulate LSP analysis and generate demo errors."""
    print(f"\n🔍 Simulating LSP analysis for {language} project...")
    
    # This would normally use Serena + SolidLSP to get real diagnostics
    # For demo purposes, we'll simulate some common errors based on the repository
    
    demo_errors = []
    
    # Look for actual files to make realistic examples
    source_files = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h', '.rs', '.go')):
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                source_files.append(rel_path)
                if len(source_files) >= 10:  # Limit for demo
                    break
        if len(source_files) >= 10:
            break
    
    # Generate realistic demo errors based on common patterns
    if language == "Python":
        demo_errors = [
            {
                'location': 'line 45, col 12',
                'file': source_files[0] if source_files else 'main.py',
                'error_reason': 'Undefined variable: undefined_var',
                'other_types': 'severity: ERROR, code: undefined-variable, source: pylsp'
            },
            {
                'location': 'line 23, col 8',
                'file': source_files[1] if len(source_files) > 1 else 'utils.py',
                'error_reason': 'Missing return statement in function',
                'other_types': 'severity: WARNING, code: missing-return, source: pylsp'
            },
            {
                'location': 'line 67, col 1',
                'file': source_files[2] if len(source_files) > 2 else 'config.py',
                'error_reason': 'Unused import: os',
                'other_types': 'severity: INFO, code: unused-import, source: pylsp'
            }
        ]
    elif language == "JavaScript" or language == "TypeScript":
        demo_errors = [
            {
                'location': 'line 34, col 15',
                'file': source_files[0] if source_files else 'index.js',
                'error_reason': 'Variable is used before being declared',
                'other_types': 'severity: ERROR, code: no-use-before-define, source: eslint'
            },
            {
                'location': 'line 89, col 22',
                'file': source_files[1] if len(source_files) > 1 else 'utils.js',
                'error_reason': 'Missing semicolon',
                'other_types': 'severity: WARNING, code: semi, source: eslint'
            }
        ]
    elif language == "C" or language == "C++":
        demo_errors = [
            {
                'location': 'line 156, col 9',
                'file': source_files[0] if source_files else 'main.c',
                'error_reason': 'Unused variable: temp',
                'other_types': 'severity: WARNING, code: unused-variable, source: clangd'
            },
            {
                'location': 'line 203, col 5',
                'file': source_files[1] if len(source_files) > 1 else 'parser.c',
                'error_reason': 'Potential memory leak',
                'other_types': 'severity: ERROR, code: memory-leak, source: clangd'
            },
            {
                'location': 'line 78, col 12',
                'file': source_files[2] if len(source_files) > 2 else 'tree.c',
                'error_reason': 'Implicit function declaration',
                'other_types': 'severity: ERROR, code: implicit-function-declaration, source: clangd'
            }
        ]
    else:
        # Generic errors for other languages
        demo_errors = [
            {
                'location': 'line 42, col 10',
                'file': source_files[0] if source_files else 'main.ext',
                'error_reason': 'Syntax error: unexpected token',
                'other_types': 'severity: ERROR, code: syntax-error, source: language-server'
            }
        ]
    
    return demo_errors

def format_output(errors):
    """Format the errors in the requested output format."""
    if not errors:
        return "ERRORS: ['0']\nNo errors found."
    
    error_count = len(errors)
    output_lines = [f"ERRORS: ['{error_count}']"]
    
    for i, error in enumerate(errors, 1):
        line = f"{i}. '{error['location']}' '{error['file']}' '{error['error_reason']}' '{error['other_types']}'"
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def main():
    """Main demo function."""
    repo_url = "https://github.com/Zeeeepa/graph-sitter"
    
    print("🚀 Serena LSP Error Analysis Tool - Demo Mode")
    print("=" * 60)
    print(f"📋 Analyzing repository: {repo_url}")
    print("⚠️  Note: This is a demonstration showing expected functionality")
    print("   The actual tool requires Serena and SolidLSP to be properly installed")
    print("=" * 60)
    
    try:
        # Clone the repository
        repo_path = clone_repository(repo_url)
        
        # Analyze repository structure
        language, file_counts = analyze_repository_structure(repo_path)
        
        # Simulate LSP analysis
        errors = simulate_lsp_analysis(repo_path, language)
        
        # Format and display results
        print(f"\n📋 Analysis Results:")
        print("=" * 40)
        result = format_output(errors)
        print(result)
        
        print("\n" + "=" * 60)
        print("✅ Demo analysis completed!")
        print("💡 The actual serena_analysis.py tool would:")
        print("   • Use real LSP servers for accurate diagnostics")
        print("   • Support all file types in the repository")
        print("   • Provide filtering by severity level")
        print("   • Handle large repositories efficiently")
        print("=" * 60)
        
        # Cleanup
        import shutil
        shutil.rmtree(os.path.dirname(repo_path), ignore_errors=True)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

