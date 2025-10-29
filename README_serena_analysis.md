# 🚀 Comprehensive Serena LSP Error Analysis Tool

A powerful, production-ready tool that analyzes **entire codebases** using Serena and SolidLSP to extract all LSP errors and diagnostics. This tool provides comprehensive error analysis without any file count limitations, using real LSP integration for accurate error detection.

## ✨ Features

- **🔍 Comprehensive Analysis**: Analyzes ALL source files in a repository without limitations
- **🌐 Multi-Language Support**: Auto-detects and supports Python, TypeScript, JavaScript, Java, C#, C++, Rust, Go, PHP, Ruby
- **📡 Real LSP Integration**: Uses Serena and SolidLSP for accurate, production-grade error detection
- **⚡ High Performance**: Parallel processing with adaptive batch sizing for optimal LSP server efficiency
- **🔄 Robust Error Handling**: Retry mechanisms for transient failures with exponential backoff
- **📊 Advanced Analytics**: Error categorization, deduplication, and statistical analysis
- **🎯 Flexible Filtering**: Filter by severity levels (ERROR, WARNING, INFO, HINT)
- **📈 Progress Tracking**: Real-time progress with ETA calculations and performance metrics
- **🌍 Repository Support**: Works with both local repositories and remote Git URLs
- **📋 Multiple Output Formats**: Text and JSON output formats for different use cases

## 🛠️ Installation

### Prerequisites

Ensure you have Serena and SolidLSP installed:

```bash
# Install Serena and SolidLSP dependencies
pip install -e .  # From the Serena repository root
```

### Quick Start

```bash
# Make the script executable
chmod +x serena_analysis.py

# Analyze a local repository
./serena_analysis.py /path/to/your/repo

# Analyze a remote repository
./serena_analysis.py https://github.com/user/repo.git

# Analyze with verbose output and error filtering
./serena_analysis.py . --severity ERROR --verbose
```

## 📖 Usage

### Basic Usage

```bash
python serena_analysis.py <repo_url_or_path> [options]
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `repository` | Repository URL or local path to analyze | Required |
| `--severity` | Filter by severity: ERROR, WARNING, INFO, HINT | All |
| `--language` | Override language detection (python, javascript, etc.) | Auto-detect |
| `--timeout` | Timeout for LSP operations in seconds | 600 |
| `--max-workers` | Maximum parallel workers | 4 |
| `--output` | Output format: text, json | text |
| `--verbose, -v` | Enable verbose logging and progress tracking | False |

### 🎯 Examples

#### Basic Analysis
```bash
# Analyze current directory
./serena_analysis.py .

# Analyze a specific repository
./serena_analysis.py /path/to/project
```

#### Advanced Analysis
```bash
# Focus on critical errors only
./serena_analysis.py https://github.com/user/repo.git --severity ERROR

# Verbose analysis with custom settings
./serena_analysis.py . --verbose --timeout 900 --max-workers 8

# Override language detection
./serena_analysis.py /path/to/project --language python --verbose

# JSON output for programmatic processing
./serena_analysis.py . --output json > analysis_results.json
```

#### Large Repository Optimization
```bash
# For very large repositories (5000+ files)
./serena_analysis.py https://github.com/large/repo.git \
  --timeout 1200 \
  --max-workers 2 \
  --severity ERROR \
  --verbose
```

## 📊 Output Format

### Text Output
```
ERRORS: ['42']
1. 'line 15, col 8' 'main.py' 'Undefined variable: user_data' 'severity: ERROR, code: reportUndefinedVariable, source: pylsp'
2. 'line 23, col 12' 'utils.py' 'Missing import statement' 'severity: ERROR, code: reportMissingImports, source: pylsp'
...

[ENHANCED DIAGNOSTIC SUMMARY - when verbose or >50 errors]
Top Error Categories:
  1. ERROR reportMissingImports: 15 occurrences
  2. WARNING unusedVariable: 8 occurrences
Files with Most Errors:
  1. main.py: 12 errors
  2. utils.py: 6 errors
```

### JSON Output
```json
{
  "total_files": 150,
  "processed_files": 148,
  "failed_files": 2,
  "total_diagnostics": 42,
  "diagnostics_by_severity": {
    "ERROR": 25,
    "WARNING": 15,
    "INFO": 2
  },
  "diagnostics": [
    {
      "file_path": "src/main.py",
      "line": 15,
      "column": 8,
      "severity": "ERROR",
      "message": "Undefined variable: user_data",
      "code": "reportUndefinedVariable",
      "source": "pylsp"
    }
  ],
  "performance_stats": {
    "analysis_time": 45.2,
    "total_time": 52.1
  }
}
```

## 🏗️ Architecture

### Core Components

1. **SerenaLSPAnalyzer**: Main analyzer class with comprehensive error detection
2. **Project Setup**: Automatic language detection and Serena project configuration
3. **LSP Integration**: Real language server integration with health monitoring
4. **Diagnostic Collection**: Parallel processing with batch optimization
5. **Result Processing**: Advanced formatting and statistical analysis

### Processing Flow

```
Repository Input → Language Detection → Project Setup → LSP Server Start
     ↓
Batch Processing → Parallel Analysis → Error Collection → Deduplication
     ↓
Statistical Analysis → Output Formatting → Results Display
```

## ⚡ Performance Optimization

### Recommended Settings by Repository Size

| Repository Size | Max Workers | Timeout | Notes |
|----------------|-------------|---------|-------|
| < 100 files | 4 | 300s | Default settings |
| 100-1000 files | 6 | 600s | Standard analysis |
| 1000-5000 files | 4 | 900s | Balanced approach |
| > 5000 files | 2 | 1200s | Prevent LSP overload |

### Performance Tips

- **Use severity filtering** (`--severity ERROR`) to focus on critical issues
- **Enable verbose mode** (`--verbose`) for progress tracking on large repositories
- **Adjust worker count** based on your system's CPU cores and memory
- **Increase timeout** for very large repositories to prevent premature failures
- **Use batch processing** (automatically handled) for optimal LSP server efficiency

## 🔧 Troubleshooting

### Common Issues

#### Language Server Startup Failures
```bash
# Try with increased timeout and verbose logging
./serena_analysis.py . --timeout 900 --verbose
```

#### Memory Issues with Large Repositories
```bash
# Reduce worker count and use error filtering
./serena_analysis.py . --max-workers 2 --severity ERROR
```

#### Timeout Issues
```bash
# Increase timeout for large codebases
./serena_analysis.py . --timeout 1200
```

### Debug Mode
```bash
# Enable maximum verbosity for debugging
./serena_analysis.py . --verbose --timeout 1200 --max-workers 1
```

## 🤝 Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run LSP Analysis
  run: |
    python serena_analysis.py . --output json > lsp_analysis.json
    # Process results or fail build based on error count
```

### Programmatic Usage

```python
from serena_analysis import SerenaLSPAnalyzer

with SerenaLSPAnalyzer(verbose=True, timeout=600) as analyzer:
    results = analyzer.analyze_repository(
        "/path/to/repo",
        severity_filter="ERROR",
        output_format="json"
    )
    print(f"Found {results['total_diagnostics']} errors")
```

## 📈 Advanced Features

### Statistical Analysis
- **Error categorization** by type and severity
- **File-level error distribution** analysis
- **Performance metrics** and processing rates
- **Failure rate tracking** and retry statistics

### Error Deduplication
- **Location-based deduplication** prevents duplicate reports
- **Message similarity detection** for cleaner output
- **Cross-file error correlation** for better insights

### Batch Processing
- **Adaptive batch sizing** based on repository size
- **LSP server efficiency optimization** with controlled parallelism
- **Memory-efficient processing** for very large codebases

## 🔒 Security & Safety

- **Temporary directory cleanup** after analysis
- **Safe path handling** with validation
- **Resource cleanup** on interruption
- **No modification** of analyzed repositories

## 📝 License

This tool is part of the Serena project. Please refer to the main project license.

## 🙋‍♂️ Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Enable verbose mode for detailed logging
3. Report issues with full error logs and system information

---

**Happy analyzing! 🚀**
