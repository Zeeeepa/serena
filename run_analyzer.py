#!/usr/bin/env python3
"""
Wrapper script to run the Serena LSP analyzer with proper environment isolation
"""

import sys
import os

# Remove global Python 3.13 packages from path to avoid conflicts
sys.path = [p for p in sys.path if not p.startswith('/usr/local/lib/python3.13')]

# Add virtual environment packages first
venv_path = '/tmp/Zeeeepa/serena/serena_env/lib/python3.11/site-packages'
src_path = '/tmp/Zeeeepa/serena/src'

if venv_path not in sys.path:
    sys.path.insert(0, venv_path)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now import and run the analyzer
if __name__ == "__main__":
    # Import the analyzer module
    import importlib.util
    spec = importlib.util.spec_from_file_location("serena_lsp_analyzer", "/tmp/Zeeeepa/serena/serena_lsp_analyzer.py")
    analyzer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer_module)
    
    # Run the main function
    analyzer_module.main()
