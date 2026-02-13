"""
Language detection utilities for repository analysis.
"""

import os
from pathlib import Path
from typing import Dict, Set
from collections import defaultdict

# Language file extensions mapping
LANGUAGE_EXTENSIONS = {
    'python': {'.py', '.pyw', '.pyi'},
    'javascript': {'.js', '.jsx', '.mjs', '.cjs'},
    'typescript': {'.ts', '.tsx', '.d.ts'},
    'java': {'.java'},
    'csharp': {'.cs', '.csx'},
    'go': {'.go'},
    'rust': {'.rs'},
    'php': {'.php', '.phtml', '.php3', '.php4', '.php5', '.phps'},
    'ruby': {'.rb', '.rbw'},
    'cpp': {'.cpp', '.cxx', '.cc', '.c++', '.hpp', '.hxx', '.hh', '.h++'},
    'c': {'.c', '.h'},
    'kotlin': {'.kt', '.kts'},
    'dart': {'.dart'},
    'elixir': {'.ex', '.exs'},
    'clojure': {'.clj', '.cljs', '.cljc', '.edn'},
    'scala': {'.scala', '.sc'},
    'swift': {'.swift'},
    'r': {'.r', '.R'},
    'matlab': {'.m'},
    'perl': {'.pl', '.pm', '.t', '.pod'},
    'shell': {'.sh', '.bash', '.zsh', '.fish'},
    'powershell': {'.ps1', '.psm1', '.psd1'},
    'lua': {'.lua'},
    'haskell': {'.hs', '.lhs'},
    'erlang': {'.erl', '.hrl'},
    'f#': {'.fs', '.fsi', '.fsx'},
    'vb.net': {'.vb'},
    'objective-c': {'.m', '.mm'},
    'assembly': {'.asm', '.s'},
    'sql': {'.sql'},
    'html': {'.html', '.htm', '.xhtml'},
    'css': {'.css', '.scss', '.sass', '.less'},
    'xml': {'.xml', '.xsd', '.xsl', '.xslt'},
    'json': {'.json'},
    'yaml': {'.yaml', '.yml'},
    'toml': {'.toml'},
    'ini': {'.ini', '.cfg', '.conf'},
    'dockerfile': {'dockerfile', '.dockerfile'},
    'makefile': {'makefile', '.makefile', 'gnumakefile'},
}

# Common directories to ignore
IGNORE_DIRECTORIES = {
    '.git', '.svn', '.hg', '.bzr',  # Version control
    'node_modules', 'bower_components',  # JavaScript
    '__pycache__', '.pytest_cache', 'venv', 'env', '.env',  # Python
    'target', 'build', 'dist', 'out',  # Build outputs
    '.gradle', '.maven',  # Java build tools
    'bin', 'obj',  # .NET
    'vendor',  # Various package managers
    '.idea', '.vscode', '.vs',  # IDEs
    'coverage', '.coverage', '.nyc_output',  # Coverage reports
    'logs', 'log',  # Log directories
    'tmp', 'temp', 'cache',  # Temporary directories
}

# Files to ignore
IGNORE_FILES = {
    '.gitignore', '.gitattributes', '.gitmodules',
    '.dockerignore', '.eslintignore', '.prettierignore',
    'package-lock.json', 'yarn.lock', 'composer.lock',
    'Pipfile.lock', 'poetry.lock',
    '.DS_Store', 'Thumbs.db',
}


def get_file_language(file_path: str) -> str:
    """
    Determine the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or 'unknown' if not recognized
    """
    file_name = os.path.basename(file_path).lower()
    file_ext = Path(file_path).suffix.lower()
    
    # Special cases for files without extensions
    if file_name in {'dockerfile', 'makefile', 'gnumakefile'}:
        if 'dockerfile' in file_name:
            return 'dockerfile'
        elif 'makefile' in file_name:
            return 'makefile'
    
    # Check extensions
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if file_ext in extensions or file_name in extensions:
            return language
    
    return 'unknown'


def should_ignore_path(path: str) -> bool:
    """
    Check if a path should be ignored during analysis.
    
    Args:
        path: File or directory path
        
    Returns:
        True if the path should be ignored
    """
    path_parts = Path(path).parts
    file_name = os.path.basename(path).lower()
    
    # Check if any part of the path is in ignore directories
    for part in path_parts:
        if part.lower() in IGNORE_DIRECTORIES:
            return True
    
    # Check if file should be ignored
    if file_name in IGNORE_FILES:
        return True
    
    # Ignore hidden files and directories (starting with .)
    if any(part.startswith('.') and part not in {'.', '..'} for part in path_parts):
        # Allow some common config files
        allowed_hidden = {'.env.example', '.env.template', '.gitkeep'}
        if file_name not in allowed_hidden:
            return True
    
    return False


def count_lines_in_file(file_path: str) -> int:
    """
    Count the number of lines in a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of lines in the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def detect_repository_languages(repo_path: str, min_files: int = 1, min_lines: int = 10) -> Dict[str, Dict[str, int]]:
    """
    Detect programming languages used in a repository.
    
    Args:
        repo_path: Path to the repository root
        min_files: Minimum number of files required to consider a language
        min_lines: Minimum total lines required to consider a language
        
    Returns:
        Dictionary mapping language names to statistics:
        {
            'language_name': {
                'files': number_of_files,
                'lines': total_lines,
                'percentage': percentage_of_total_lines
            }
        }
    """
    language_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    total_lines = 0
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip ignored files
            if should_ignore_path(file_path):
                continue
            
            # Determine language
            language = get_file_language(file_path)
            if language == 'unknown':
                continue
            
            # Count lines
            line_count = count_lines_in_file(file_path)
            if line_count == 0:
                continue
            
            # Update statistics
            language_stats[language]['files'] += 1
            language_stats[language]['lines'] += line_count
            total_lines += line_count
    
    # Filter languages by minimum requirements and calculate percentages
    filtered_stats = {}
    for language, stats in language_stats.items():
        if stats['files'] >= min_files and stats['lines'] >= min_lines:
            percentage = (stats['lines'] / total_lines * 100) if total_lines > 0 else 0
            filtered_stats[language] = {
                'files': stats['files'],
                'lines': stats['lines'],
                'percentage': round(percentage, 2)
            }
    
    # Sort by percentage (descending)
    return dict(sorted(filtered_stats.items(), key=lambda x: x[1]['percentage'], reverse=True))


def get_primary_language(repo_path: str) -> str:
    """
    Get the primary programming language of a repository.
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        Primary language name or 'unknown' if none detected
    """
    languages = detect_repository_languages(repo_path)
    if not languages:
        return 'unknown'
    
    # Return the language with the highest percentage
    return max(languages.keys(), key=lambda lang: languages[lang]['percentage'])


def get_supported_languages_for_solidlsp() -> Set[str]:
    """
    Get the list of languages supported by SolidLSP.
    
    Returns:
        Set of supported language names
    """
    return {
        'python', 'typescript', 'javascript', 'java', 'csharp', 
        'go', 'rust', 'php', 'clojure', 'elixir', 'cpp', 'c'
    }


def filter_supported_languages(detected_languages: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    """
    Filter detected languages to only include those supported by SolidLSP.
    
    Args:
        detected_languages: Dictionary of detected languages with statistics
        
    Returns:
        Filtered dictionary containing only supported languages
    """
    supported = get_supported_languages_for_solidlsp()
    return {lang: stats for lang, stats in detected_languages.items() if lang in supported}

