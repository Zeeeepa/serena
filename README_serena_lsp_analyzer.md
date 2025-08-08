# Comprehensive Serena LSP Error Analysis Tool

A powerful tool for analyzing entire codebases using **Serena** and **SolidLSP** to extract all LSP errors and diagnostics. This tool provides comprehensive error analysis across all programming languages supported by Serena.

## 🚀 Features

- **Real LSP Integration**: Uses Serena and SolidLSP for accurate error detection
- **Comprehensive Analysis**: Analyzes ALL source files without limitations
- **Multi-Language Support**: Python, TypeScript/JavaScript, Java, C#, C++, Rust, Go, PHP, Ruby, Kotlin, Dart
- **Parallel Processing**: Efficient batch processing with configurable workers
- **Advanced Error Categorization**: Detailed error analysis and statistics
- **Progress Tracking**: Real-time progress with ETA calculations
- **Flexible Output**: Both text and JSON output formats
- **Repository Support**: Works with both local and remote Git repositories

## 📋 Requirements

- Python 3.8+
- Serena and SolidLSP installed
- Git (for remote repository cloning)

## 🔧 Installation

1. Clone the Serena repository:
```bash
git clone https://github.com/Zeeeepa/serena.git
cd serena
```

2. Install Serena and dependencies:
```bash
pip install -e .
```

3. The analyzer tool is ready to use!

## 📊 Usage

### Basic Usage

```bash
# Analyze a local repository
python serena_lsp_analyzer.py /path/to/repo

# Analyze a remote repository
python serena_lsp_analyzer.py https://github.com/user/repo.git

# Analyze current directory
python serena_lsp_analyzer.py .
```

### Advanced Usage

```bash
# Filter by severity level
python serena_lsp_analyzer.py /path/to/repo --severity ERROR

# Override language detection
python serena_lsp_analyzer.py /path/to/repo --language python

# Verbose output with progress tracking
python serena_lsp_analyzer.py /path/to/repo --verbose

# JSON output format
python serena_lsp_analyzer.py /path/to/repo --output json

# Performance tuning for large repositories
python serena_lsp_analyzer.py /path/to/repo --timeout 900 --max-workers 8
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `repository` | Repository URL or local path | Required |
| `--severity` | Filter by severity (ERROR, WARNING, INFO, HINT) | All |
| `--language` | Override language detection | Auto-detect |
| `--timeout` | LSP operation timeout in seconds | 600 |
| `--max-workers` | Maximum parallel workers | 4 |
| `--output` | Output format (text, json) | text |
| `--verbose` | Enable verbose logging | False |

## 📈 Output Format

### Text Output
```
ERRORS: ['42']
1. 'line 15, col 8' 'main.py' 'Undefined variable: foo' 'severity: ERROR, code: reportUndefinedVariable'
2. 'line 23, col 12' 'utils.py' 'Unused import: os' 'severity: WARNING, code: reportUnusedImport'
...

SERENA LSP DIAGNOSTIC SUMMARY
============================================================
Diagnostics by Severity:
  ERROR: 15
  WARNING: 27
Files with Most Errors:
  1. main.py: 8 errors
  2. utils.py: 5 errors
============================================================
```

### JSON Output
```json
{
  "total_files": 150,
  "processed_files": 148,
  "failed_files": 2,
  "total_diagnostics": 42,
  "diagnostics_by_severity": {
    "ERROR": 15,
    "WARNING": 27
  },
  "diagnostics": [
    {
      "file_path": "main.py",
      "line": 15,
      "column": 8,
      "severity": "ERROR",
      "message": "Undefined variable: foo",
      "code": "reportUndefinedVariable",
      "source": "lsp"
    }
  ],
  "performance_stats": {
    "total_time": 45.2,
    "analysis_time": 38.1
  }
}
```

## 🎯 Supported Languages

The tool supports all languages available in Serena:

- **Python** - Full LSP support with Pyright
- **TypeScript/JavaScript** - Complete type checking and analysis
- **Java** - Comprehensive Java language server integration
- **C#** - Microsoft C# language server support
- **C++** - Advanced C++ analysis capabilities
- **Rust** - Rust analyzer integration
- **Go** - Go language server support
- **PHP** - PHP language server integration
- **Ruby** - Ruby LSP support
- **Kotlin** - Kotlin language server
- **Dart** - Dart analysis server

## ⚡ Performance Tips

### For Large Repositories (1000+ files):
- Increase timeout: `--timeout 900`
- Reduce workers: `--max-workers 2`
- Filter by severity: `--severity ERROR`

### For Maximum Speed:
- Use more workers: `--max-workers 8`
- Focus on errors: `--severity ERROR`
- Disable verbose output

### For Detailed Analysis:
- Enable verbose mode: `--verbose`
- Use JSON output: `--output json`
- Include all severities (default)

## 🔍 How It Works

1. **Repository Setup**: Clones remote repositories or uses local paths
2. **Language Detection**: Automatically detects the primary programming language
3. **Project Configuration**: Sets up Serena project with appropriate settings
4. **LSP Server Initialization**: Starts the appropriate language server
5. **Comprehensive Analysis**: Processes ALL source files using real LSP integration
6. **Result Formatting**: Generates detailed reports with statistics

## 🛠️ Architecture

The tool is built using:

- **Serena**: Provides project management and LSP integration
- **SolidLSP**: Handles language server protocol communication
- **ThreadPoolExecutor**: Enables parallel file processing
- **Batch Processing**: Optimizes LSP server efficiency
- **Retry Mechanisms**: Handles transient failures gracefully

## 📝 Examples

### Analyze Python Project
```bash
python serena_lsp_analyzer.py https://github.com/python/cpython --language python --severity ERROR --verbose
```

### Analyze TypeScript Project
```bash
python serena_lsp_analyzer.py https://github.com/microsoft/vscode --language typescript --output json
```

### Analyze Local Rust Project
```bash
python serena_lsp_analyzer.py ./my-rust-project --language rust --max-workers 6
```

## 🐛 Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure Serena is properly installed with `pip install -e .`
2. **Language Server Not Found**: Check that required language servers are installed
3. **Timeout Issues**: Increase timeout for large repositories
4. **Memory Issues**: Reduce max-workers for very large codebases

### Debug Mode:
```bash
python serena_lsp_analyzer.py /path/to/repo --verbose
```

## 🤝 Contributing

This tool is part of the Serena project. Contributions are welcome!

## 📄 License

This tool follows the same license as the Serena project.

---

**Built with ❤️ using Serena and SolidLSP**
