#!/usr/bin/env python3
"""
Advanced LSP Analysis Extensions for Serena Analyzer

This module provides additional advanced LSP analysis capabilities that extend
the main serena_analyzer.py functionality with position-specific analysis.

Features:
- Advanced LSP analysis for specific code positions
- Code completion analysis
- Hover information extraction
- Signature help analysis
- Symbol definition and reference tracking
- Context-aware code intelligence
"""

import json
from typing import Dict, Any, Optional
from serena_analyzer import SerenaLSPAnalyzer


def get_advanced_lsp_analysis(repo_path: str, file_path: str, line: int, character: int) -> Dict[str, Any]:
    """
    Get advanced LSP analysis (completion, hover, signature) for a specific position.
    
    Args:
        repo_path: Path to the repository
        file_path: Path to the specific file
        line: Line number (0-based)
        character: Character position (0-based)
    
    Returns:
        Dictionary containing completion, hover, and signature information
    """
    with SerenaLSPAnalyzer(verbose=False, enable_symbols=True) as analyzer:
        try:
            # Set up project and language server
            project = analyzer.setup_project(repo_path)
            language_server = analyzer.start_language_server(project)
            
            # Get advanced LSP features
            results = {
                'completions': analyzer.get_completion_analysis(language_server, file_path, line, character),
                'hover_info': analyzer.get_hover_analysis(language_server, file_path, line, character),
                'signature_help': analyzer.get_signature_analysis(language_server, file_path, line, character),
                'position': {'file': file_path, 'line': line, 'character': character}
            }
            
            return results
            
        except Exception as e:
            return {'error': str(e), 'position': {'file': file_path, 'line': line, 'character': character}}


def get_symbol_at_position(repo_path: str, file_path: str, line: int, character: int) -> Dict[str, Any]:
    """
    Get detailed symbol information at a specific position.
    
    Args:
        repo_path: Path to the repository
        file_path: Path to the specific file
        line: Line number (0-based)
        character: Character position (0-based)
    
    Returns:
        Dictionary containing symbol information and references
    """
    with SerenaLSPAnalyzer(verbose=False, enable_symbols=True) as analyzer:
        try:
            # Set up project and language server
            project = analyzer.setup_project(repo_path)
            language_server = analyzer.start_language_server(project)
            
            # Get symbol information
            hover_info = analyzer.get_hover_analysis(language_server, file_path, line, character)
            
            # Try to get definition
            try:
                definition = language_server.request_definition(file_path, line, character)
            except:
                definition = None
            
            # Try to get references
            try:
                references = language_server.request_references(file_path, line, character)
            except:
                references = []
            
            return {
                'hover_info': hover_info,
                'definition': definition,
                'references': references,
                'position': {'file': file_path, 'line': line, 'character': character}
            }
            
        except Exception as e:
            return {'error': str(e), 'position': {'file': file_path, 'line': line, 'character': character}}


def analyze_code_context(repo_path: str, file_path: str, line: int, character: int, context_lines: int = 5) -> Dict[str, Any]:
    """
    Analyze code context around a specific position with comprehensive LSP features.
    
    Args:
        repo_path: Path to the repository
        file_path: Path to the specific file
        line: Line number (0-based)
        character: Character position (0-based)
        context_lines: Number of lines to include before and after
    
    Returns:
        Dictionary containing comprehensive context analysis
    """
    with SerenaLSPAnalyzer(verbose=False, enable_symbols=True) as analyzer:
        try:
            # Set up project and language server
            project = analyzer.setup_project(repo_path)
            language_server = analyzer.start_language_server(project)
            
            # Get file content for context
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                start_line = max(0, line - context_lines)
                end_line = min(len(lines), line + context_lines + 1)
                context_code = ''.join(lines[start_line:end_line])
                
            except Exception as e:
                context_code = f"Error reading file: {e}"
            
            # Get comprehensive LSP analysis
            lsp_analysis = get_advanced_lsp_analysis(repo_path, file_path, line, character)
            symbol_info = get_symbol_at_position(repo_path, file_path, line, character)
            
            return {
                'context_code': context_code,
                'context_range': {'start_line': start_line, 'end_line': end_line - 1},
                'target_position': {'line': line, 'character': character},
                'lsp_analysis': lsp_analysis,
                'symbol_info': symbol_info,
                'file_path': file_path
            }
            
        except Exception as e:
            return {'error': str(e), 'position': {'file': file_path, 'line': line, 'character': character}}


def batch_analyze_positions(repo_path: str, positions: list) -> Dict[str, Any]:
    """
    Analyze multiple positions in batch for efficiency.
    
    Args:
        repo_path: Path to the repository
        positions: List of dictionaries with 'file', 'line', 'character' keys
    
    Returns:
        Dictionary containing analysis results for all positions
    """
    results = {}
    
    with SerenaLSPAnalyzer(verbose=False, enable_symbols=True) as analyzer:
        try:
            # Set up project and language server once
            project = analyzer.setup_project(repo_path)
            language_server = analyzer.start_language_server(project)
            
            for i, pos in enumerate(positions):
                try:
                    file_path = pos['file']
                    line = pos['line']
                    character = pos['character']
                    
                    # Get analysis for this position
                    analysis = {
                        'completions': analyzer.get_completion_analysis(language_server, file_path, line, character),
                        'hover_info': analyzer.get_hover_analysis(language_server, file_path, line, character),
                        'signature_help': analyzer.get_signature_analysis(language_server, file_path, line, character),
                    }
                    
                    results[f"position_{i}"] = {
                        'position': pos,
                        'analysis': analysis
                    }
                    
                except Exception as e:
                    results[f"position_{i}"] = {
                        'position': pos,
                        'error': str(e)
                    }
            
            return {
                'total_positions': len(positions),
                'successful_analyses': len([r for r in results.values() if 'error' not in r]),
                'results': results
            }
            
        except Exception as e:
            return {'error': str(e), 'total_positions': len(positions)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced LSP Analysis for Serena")
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("file_path", help="Path to file")
    parser.add_argument("line", type=int, help="Line number (0-based)")
    parser.add_argument("character", type=int, help="Character position (0-based)")
    parser.add_argument("--context", type=int, default=5, help="Context lines")
    parser.add_argument("--analysis-type", choices=['advanced', 'symbol', 'context'], 
                       default='context', help="Type of analysis to perform")
    
    args = parser.parse_args()
    
    if args.analysis_type == 'advanced':
        result = get_advanced_lsp_analysis(args.repo_path, args.file_path, args.line, args.character)
    elif args.analysis_type == 'symbol':
        result = get_symbol_at_position(args.repo_path, args.file_path, args.line, args.character)
    else:  # context
        result = analyze_code_context(args.repo_path, args.file_path, args.line, args.character, args.context)
    
    print(json.dumps(result, indent=2))
