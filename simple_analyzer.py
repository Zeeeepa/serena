#!/usr/bin/env python3
"""
Simplified Serena LSP Error Analysis Tool
"""

import sys
import os
import tempfile
import subprocess
import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

# Fix Python path to avoid conflicts
sys.path = [p for p in sys.path if not p.startswith('/usr/local/lib/python3.13')]
sys.path.insert(0, '/tmp/Zeeeepa/serena/serena_env/lib/python3.11/site-packages')
sys.path.insert(0, '/tmp/Zeeeepa/serena/src')

# Now import Serena components
try:
    from serena.config.serena_config import ProjectConfig
    from serena.project import Project
    from solidlsp.ls_config import Language
    from solidlsp.ls_types import DiagnosticsSeverity
    print("✅ Successfully imported Serena and SolidLSP components")
except ImportError as e:
    print(f"❌ Failed to import Serena/SolidLSP: {e}")
    sys.exit(1)

@dataclass
class SimpleDiagnostic:
    """Simple diagnostic structure"""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: Optional[str] = None
    source: Optional[str] = None

def clone_repository(repo_url: str) -> str:
    """Clone a Git repository to a temporary directory."""
    print(f"📥 Cloning repository: {repo_url}")
    
    temp_dir = tempfile.mkdtemp(prefix="serena_analysis_")
    repo_name = os.path.basename(repo_url.rstrip("/").replace(".git", ""))
    clone_path = os.path.join(temp_dir, repo_name)
    
    try:
        cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        print(f"✅ Repository cloned to: {clone_path}")
        return clone_path
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 300 seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to clone repository: {e}")

def detect_language(repo_path: str) -> Language:
    """Detect the primary programming language of the repository."""
    print("🔍 Detecting repository language...")
    
    # Language detection based on file extensions
    language_indicators = {
        Language.PYTHON: [".py", "requirements.txt", "setup.py", "pyproject.toml"],
        Language.TYPESCRIPT: [".ts", ".tsx", ".js", ".jsx", "tsconfig.json", "package.json"],
        Language.JAVA: [".java", "pom.xml", "build.gradle"],
        Language.CSHARP: [".cs", ".csproj", ".sln"],
        Language.CPP: [".cpp", ".cc", ".cxx", ".h", ".hpp", "CMakeLists.txt"],
        Language.RUST: [".rs", "Cargo.toml"],
        Language.GO: [".go", "go.mod"],
    }
    
    file_counts = {lang: 0 for lang in language_indicators.keys()}
    
    # Walk through the repository and count file types
    for root, dirs, files in os.walk(repo_path):
        # Skip common ignore directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "target", "build", "dist", "vendor"]]
        
        for file in files:
            file_lower = file.lower()
            for lang, indicators in language_indicators.items():
                if any(file_lower.endswith(ext) or file_lower == indicator for ext in indicators for indicator in [ext] if ext.startswith(".")):
                    file_counts[lang] += 1
                elif any(file_lower == indicator for indicator in indicators if not indicator.startswith(".")):
                    file_counts[lang] += 5  # Weight config files higher
    
    # Find the language with the most files
    detected_lang = max(file_counts, key=file_counts.get)
    
    if file_counts[detected_lang] == 0:
        print("⚠️  Could not detect language, defaulting to Python")
        detected_lang = Language.PYTHON
    
    print(f"✅ Detected language: {detected_lang.value}")
    return detected_lang

def setup_project(repo_path: str, language: Language) -> Project:
    """Set up a Serena project for the repository."""
    print(f"⚙️  Setting up project for {repo_path} with language {language.value}")
    
    # Create project configuration
    project_config = ProjectConfig(
        project_name=os.path.basename(repo_path),
        language=language,
        ignored_paths=[
            ".git/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/target/**",
            "**/build/**",
            "**/.venv/**",
            "**/venv/**",
            "**/dist/**",
            "**/vendor/**",
        ],
        ignore_all_files_in_gitignore=True,
    )
    
    # Create and return project
    project = Project(repo_path, project_config)
    return project

def analyze_with_basic_lsp(project: Project) -> List[SimpleDiagnostic]:
    """Analyze the project using basic LSP functionality."""
    print("🔍 Starting basic LSP analysis...")
    
    diagnostics = []
    
    try:
        # Get source files
        source_files = project.gather_source_files()
        print(f"📊 Found {len(source_files)} source files to analyze")
        
        if len(source_files) == 0:
            print("⚠️  No source files found")
            return diagnostics
        
        # Try to create a language server
        try:
            language_server = project.create_language_server(
                log_level=30,  # WARNING level
                ls_timeout=60,
                trace_lsp_communication=False,
            )
            
            if language_server:
                print("🔧 Language server created successfully")
                
                # Start the server
                language_server.start()
                print("🚀 Language server started")
                
                # Give it time to initialize
                time.sleep(5)
                
                if language_server.is_running():
                    print("✅ Language server is running")
                    
                    # Analyze a subset of files to avoid timeout
                    max_files = min(10, len(source_files))
                    print(f"🔍 Analyzing first {max_files} files...")
                    
                    for i, file_path in enumerate(source_files[:max_files]):
                        try:
                            print(f"📄 Analyzing {os.path.basename(file_path)} ({i+1}/{max_files})")
                            
                            # Get diagnostics for this file
                            file_diagnostics = language_server.request_text_document_diagnostics(file_path)
                            
                            for diag in file_diagnostics:
                                range_info = diag.get("range", {})
                                start_pos = range_info.get("start", {})
                                line = start_pos.get("line", 0) + 1
                                column = start_pos.get("character", 0) + 1
                                
                                severity_map = {
                                    1: "ERROR",
                                    2: "WARNING", 
                                    3: "INFO",
                                    4: "HINT"
                                }
                                
                                severity = severity_map.get(diag.get("severity", 1), "ERROR")
                                
                                diagnostic = SimpleDiagnostic(
                                    file_path=file_path,
                                    line=line,
                                    column=column,
                                    severity=severity,
                                    message=diag.get("message", "No message"),
                                    code=str(diag.get("code", "")),
                                    source=diag.get("source", "lsp")
                                )
                                diagnostics.append(diagnostic)
                            
                            if len(file_diagnostics) > 0:
                                print(f"  ✅ Found {len(file_diagnostics)} diagnostics")
                            
                        except Exception as e:
                            print(f"  ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
                            continue
                    
                    # Stop the language server
                    language_server.stop()
                    print("🛑 Language server stopped")
                    
                else:
                    print("❌ Language server failed to start")
            
            else:
                print("❌ Failed to create language server")
        
        except Exception as e:
            print(f"❌ Language server error: {e}")
    
    except Exception as e:
        print(f"❌ Project analysis error: {e}")
    
    return diagnostics

def format_results(diagnostics: List[SimpleDiagnostic]) -> str:
    """Format diagnostics in the requested output format."""
    if not diagnostics:
        return "ERRORS: ['0']\nNo errors found."
    
    # Sort diagnostics by severity (ERROR first), then by file, then by line
    severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3}
    
    diagnostics.sort(key=lambda d: (
        severity_priority.get(d.severity, 4),
        d.file_path.lower(),
        d.line,
    ))
    
    # Generate output
    error_count = len(diagnostics)
    output_lines = [f"ERRORS: ['{error_count}']"]
    
    # Add each formatted diagnostic
    for i, diag in enumerate(diagnostics, 1):
        file_name = os.path.basename(diag.file_path)
        location = f"line {diag.line}, col {diag.column}"
        
        # Clean message
        clean_message = diag.message.replace("\n", " ").replace("\r", " ")
        clean_message = " ".join(clean_message.split())
        
        if len(clean_message) > 200:
            clean_message = clean_message[:197] + "..."
        
        # Metadata
        metadata_parts = [f"severity: {diag.severity}"]
        if diag.code and diag.code != "":
            metadata_parts.append(f"code: {diag.code}")
        if diag.source and diag.source != "lsp":
            metadata_parts.append(f"source: {diag.source}")
        
        other_types = ", ".join(metadata_parts)
        
        diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
        output_lines.append(diagnostic_line)
    
    return "\n".join(output_lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simplified Serena LSP Error Analysis Tool")
    parser.add_argument("repository", help="Repository URL or local path to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    print("🚀 SIMPLIFIED SERENA LSP ERROR ANALYSIS TOOL")
    print("=" * 60)
    print(f"📁 Target: {args.repository}")
    print("=" * 60)
    
    try:
        # Handle repository
        if args.repository.startswith("http") or args.repository.endswith(".git"):
            repo_path = clone_repository(args.repository)
        else:
            repo_path = os.path.abspath(args.repository)
            if not os.path.exists(repo_path):
                raise FileNotFoundError(f"Local path does not exist: {repo_path}")
            print(f"📂 Using local repository: {repo_path}")
        
        # Detect language and setup project
        language = detect_language(repo_path)
        project = setup_project(repo_path, language)
        
        # Analyze with LSP
        diagnostics = analyze_with_basic_lsp(project)
        
        # Format and output results
        result = format_results(diagnostics)
        
        print("\n" + "=" * 60)
        print("📋 ANALYSIS RESULTS")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print(f"ERRORS: ['0']\nAnalysis failed: {e}")

if __name__ == "__main__":
    main()
