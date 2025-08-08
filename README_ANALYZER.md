# 🚀 Comprehensive Serena LSP Error Analysis Tool

A powerful standalone tool that analyzes entire codebases using Serena and SolidLSP to extract all LSP errors and diagnostics. This tool provides deep, real-time analysis of code quality issues across multiple programming languages.

## ✨ Features

### 🎯 **Universal Repository Support**
- **Local Repositories**: Analyze any local codebase directory
- **Remote Git Repositories**: Clone and analyze repositories from GitHub, GitLab, etc.
- **Automatic Detection**: Smart detection of repository type and structure

### 🌐 **Multi-Language Analysis**
Supports all languages available in Serena:
- **Python** (with Pyright LSP)
- **TypeScript/JavaScript** (with TypeScript LSP)
- **Java** (with Eclipse JDT LS)
- **C#** (with C# LSP)
- **C++** (with Clangd)
- **Rust** (with rust-analyzer)
- **Go** (with gopls)
- **PHP** (with Intelephense)
- **Ruby** (with Solargraph)
- **Kotlin** (with Kotlin LSP)
- **Dart** (with Dart LSP)

### 🔍 **Real LSP Integration**
- **Authentic Analysis**: Uses actual language servers for accurate error detection
- **Comprehensive Diagnostics**: Extracts errors, warnings, info, and hints
- **Enhanced Metadata**: Includes LSP error codes, sources, and categories
- **Server Management**: Robust LSP server lifecycle management with retry mechanisms

### ⚡ **High-Performance Processing**
- **Parallel Processing**: Configurable worker threads for efficient analysis
- **Batch Processing**: Adaptive batch sizing for optimal LSP server utilization
- **Progress Tracking**: Real-time progress reporting with ETA calculations
- **Memory Efficient**: Handles large codebases without memory issues

### 🛡️ **Enterprise-Ready Reliability**
- **Error Recovery**: Comprehensive error handling and retry mechanisms
- **Resource Management**: Proper cleanup of servers and temporary directories
- **Timeout Handling**: Configurable timeouts for different repository sizes
- **Graceful Degradation**: Continues analysis even when individual files fail

### 📊 **Flexible Output Formats**
- **Text Format**: Human-readable output with detailed error listings
- **JSON Format**: Structured data for integration with other tools
- **Statistical Analysis**: Comprehensive breakdowns by severity and file
- **Performance Metrics**: Detailed timing and processing statistics

## 🚀 Installation

### Prerequisites
1. **Serena and SolidLSP**: Must be installed and available
   ```bash
   # From the serena repository root
   pip install -e .
   ```

2. **Language Servers**: Install the language servers for languages you want to analyze
   ```bash
   # Python (Pyright)
   npm install -g pyright
   
   # TypeScript
   npm install -g typescript typescript-language-server
   
   # Java (Eclipse JDT LS) - automatically managed by Serena
   # C++ (Clangd)
   # Install clangd via your system package manager
   
   # Rust (rust-analyzer)
   rustup component add rust-analyzer
   
   # Go (gopls)
   go install golang.org/x/tools/gopls@latest
   ```

### Setup
1. **Download the analyzer**:
   ```bash
   # Copy serena_lsp_analyzer.py to your desired location
   chmod +x serena_lsp_analyzer.py
   ```

2. **Verify installation**:
   ```bash
   python serena_lsp_analyzer.py --help
   ```

## 📖 Usage

### Basic Usage

```bash
# Analyze a local repository
python serena_lsp_analyzer.py /path/to/your/project

# Analyze a remote repository
python serena_lsp_analyzer.py https://github.com/user/repo.git

# Analyze current directory
python serena_lsp_analyzer.py .
```

### Advanced Usage

```bash
# Filter by severity level
python serena_lsp_analyzer.py /path/to/project --severity ERROR

# Override language detection
python serena_lsp_analyzer.py /path/to/project --language python

# Enable verbose logging with progress tracking
python serena_lsp_analyzer.py /path/to/project --verbose

# Optimize for large repositories
python serena_lsp_analyzer.py /path/to/project --timeout 1200 --max-workers 8

# Output as JSON for integration
python serena_lsp_analyzer.py /path/to/project --output json
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `repository` | Repository URL or local path to analyze | Required |
| `--severity` | Filter by severity: ERROR, WARNING, INFO, HINT | All |
| `--language` | Override language detection | Auto-detect |
| `--timeout` | Timeout for LSP operations (seconds) | 600 |
| `--max-workers` | Number of parallel workers | 4 |
| `--output` | Output format: text, json | text |
| `--verbose` | Enable detailed logging and progress | False |

## 📊 Output Format

### Text Output
```
ERRORS: ['15']
1. 'line 42, col 10' 'main.py' 'Undefined variable: undefined_var' 'severity: ERROR, code: undefined-variable, source: pyright'
2. 'line 15, col 5' 'utils.py' 'Missing return statement' 'severity: WARNING, code: missing-return, source: pyright'
...

============================================================
SERENA LSP DIAGNOSTIC SUMMARY
============================================================
Diagnostics by Severity:
  ERROR: 8
  WARNING: 5
  INFO: 2

Files with Most Errors:
  1. main.py: 6 errors
  2. utils.py: 4 errors
  3. config.py: 3 errors
============================================================
```

### JSON Output
```json
{
  "total_files": 45,
  "processed_files": 43,
  "failed_files": 2,
  "total_diagnostics": 15,
  "diagnostics_by_severity": {
    "ERROR": 8,
    "WARNING": 5,
    "INFO": 2
  },
  "diagnostics": [
    {
      "file_path": "main.py",
      "line": 42,
      "column": 10,
      "severity": "ERROR",
      "message": "Undefined variable: undefined_var",
      "code": "undefined-variable",
      "source": "pyright",
      "category": "lsp_diagnostic",
      "tags": ["serena_lsp_analysis"]
    }
  ],
  "performance_stats": {
    "clone_time": 2.5,
    "setup_time": 1.2,
    "lsp_start_time": 8.3,
    "analysis_time": 45.7,
    "total_time": 57.7
  },
  "language_detected": "python",
  "repository_path": "/tmp/analyzed_repo",
  "analysis_timestamp": "2024-01-15 14:30:22"
}
```

## ⚡ Performance Optimization

### For Small Projects (< 100 files)
```bash
python serena_lsp_analyzer.py /path/to/project --max-workers 2 --timeout 300
```

### For Medium Projects (100-1000 files)
```bash
python serena_lsp_analyzer.py /path/to/project --max-workers 4 --timeout 600
```

### For Large Projects (1000+ files)
```bash
python serena_lsp_analyzer.py /path/to/project --max-workers 6 --timeout 1200 --verbose
```

### For Very Large Projects (5000+ files)
```bash
python serena_lsp_analyzer.py /path/to/project --max-workers 2 --timeout 1800 --verbose
```

## 🔧 Troubleshooting

### Common Issues

1. **Language Server Not Found**
   ```
   Error: Failed to start language server
   ```
   **Solution**: Install the required language server for your project's language.

2. **Timeout Errors**
   ```
   Error: LSP operation timed out
   ```
   **Solution**: Increase the timeout value with `--timeout 1200`.

3. **Memory Issues**
   ```
   Error: Out of memory
   ```
   **Solution**: Reduce the number of workers with `--max-workers 2`.

4. **Import Errors**
   ```
   Error: Failed to import Serena/SolidLSP modules
   ```
   **Solution**: Ensure Serena is properly installed with `pip install -e .`.

### Debug Mode
Enable verbose logging to see detailed information:
```bash
python serena_lsp_analyzer.py /path/to/project --verbose
```

## 🎯 Use Cases

### 1. **Code Quality Assessment**
Analyze entire codebases to identify and prioritize code quality issues.

### 2. **CI/CD Integration**
Integrate into continuous integration pipelines for automated code quality checks.

### 3. **Migration Analysis**
Assess code quality before major refactoring or migration projects.

### 4. **Technical Debt Analysis**
Quantify and categorize technical debt across large codebases.

### 5. **Code Review Preparation**
Pre-analyze code before reviews to focus on the most critical issues.

## 🤝 Contributing

This tool is part of the Serena project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This tool is licensed under the same license as the Serena project.

## 🙏 Acknowledgments

- **Serena Team**: For the excellent LSP integration framework
- **SolidLSP**: For robust language server protocol implementation
- **Language Server Community**: For creating and maintaining language servers

---

**Happy Analyzing! 🚀**

For more information about Serena, visit the main repository documentation.
