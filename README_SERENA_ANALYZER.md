# Comprehensive Serena LSP Error Analysis Tool

A unified analyzer that combines all Serena capabilities into a single comprehensive tool for complete codebase analysis with ALL LSP server errors, symbol overviews, and advanced code intelligence features.

## Features

- **Complete LSP Error Reporting**: Get all errors from language servers across your entire codebase
- **Comprehensive Symbol Analysis**: Advanced symbol mapping and code intelligence
- **Runtime Error Collection**: Capture and analyze runtime errors during execution
- **Multi-Language Support**: Python, TypeScript, Java, C#, C++, Rust, Go, PHP, Ruby, Kotlin, Dart
- **Real-time Analysis**: Background processing with live error detection
- **Enhanced LSP Protocol**: Full integration with ProcessLaunchInfo, LSPError, MessageType handling
- **Detailed Reporting**: JSON and text output with comprehensive metrics
- **Performance Tracking**: Detailed timing and performance statistics

## Installation

Ensure you have Serena and SolidLSP properly installed:

```bash
# From the serena repository root
pip install -e .
```

## Usage

### Basic Usage

```bash
# Analyze a local repository
python serena_analyzer.py /path/to/your/repo

# Analyze a remote repository
python serena_analyzer.py https://github.com/user/repo.git

# Analyze current directory
python serena_analyzer.py .
```

### Advanced Options

```bash
# Filter by severity level
python serena_analyzer.py /path/to/repo --severity ERROR

# Override language detection
python serena_analyzer.py /path/to/repo --language python

# Enable verbose logging
python serena_analyzer.py /path/to/repo --verbose

# Enable symbol analysis
python serena_analyzer.py /path/to/repo --symbols

# Enable runtime error collection
python serena_analyzer.py /path/to/repo --runtime-errors

# Adjust performance settings
python serena_analyzer.py /path/to/repo --timeout 300 --max-workers 8
```

### Complete Example

```bash
python serena_analyzer.py https://github.com/user/repo.git \
    --severity ERROR \
    --language python \
    --verbose \
    --symbols \
    --runtime-errors \
    --timeout 600 \
    --max-workers 4
```

## Output Format

The analyzer provides comprehensive error reporting in the following format:

```
ERRORS: 15 [⚠️ Critical: 8] [👉 Major: 5] [🔥 Runtime: 2]

1 ⚠️- src/main.py / line 42, col 15 - 'Undefined variable: user_data' [severity: ERROR, code: E0602, source: pylsp]
2 👉- src/utils.py / line 18, col 8 - 'Unused import: json' [severity: WARNING, code: W0611, source: pylsp]
3 🔥- src/api.py / line 95, col 12 - '[RUNTIME] AttributeError: NoneType object has no attribute get' [severity: ERROR, source: runtime]
...
```

## Programmatic Usage

You can also use the analyzer programmatically:

```python
from serena_analyzer import SerenaLSPAnalyzer, create_enhanced_serena_integration

# Using the main analyzer class
with SerenaLSPAnalyzer(verbose=True, enable_runtime_errors=True) as analyzer:
    result = analyzer.analyze_repository("/path/to/repo")
    print(result)

# Using the enhanced integration
integration = create_enhanced_serena_integration("/path/to/repo")
errors = integration.get_all_errors()
runtime_errors = integration.get_runtime_errors()
analysis = integration.get_comprehensive_analysis()
integration.shutdown()

# Simple function for quick analysis
from serena_analyzer import get_comprehensive_errors
errors = get_comprehensive_errors("/path/to/repo", include_runtime=True)
```

## Configuration

The analyzer supports various configuration options:

- **Timeout**: LSP operation timeout (default: 600 seconds)
- **Max Workers**: Parallel processing workers (default: 4)
- **Severity Filter**: ERROR, WARNING, INFO, HINT
- **Language Override**: Force specific language detection
- **Symbol Analysis**: Enable comprehensive symbol mapping
- **Runtime Errors**: Capture runtime execution errors

## Error Categories

The analyzer categorizes errors into several types:

- **Static Analysis**: Syntax, import, type errors from LSP
- **Runtime Errors**: Errors captured during execution
- **Linting**: Code style and quality issues
- **Security**: Security vulnerabilities
- **Performance**: Performance-related issues

## LSP Protocol Integration

Full integration with LSP protocol features:

- **ProcessLaunchInfo**: Proper server process management
- **LSPError**: Comprehensive error handling
- **MessageType**: Enhanced message categorization
- **Position & Range**: Precise error location tracking
- **Location**: URI-based file references
- **MarkupContent**: Rich error descriptions
- **CompletionItem**: Code completion integration
- **SymbolInformation**: Advanced symbol analysis

## Performance

The analyzer is optimized for large codebases:

- **Parallel Processing**: Multi-threaded file analysis
- **Efficient LSP Communication**: Optimized server interactions
- **Memory Management**: Controlled resource usage
- **Progress Tracking**: Real-time analysis progress
- **Caching**: Intelligent result caching

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Serena and SolidLSP are properly installed
2. **Language Server Timeout**: Increase timeout with `--timeout` option
3. **Memory Issues**: Reduce `--max-workers` for large repositories
4. **Permission Errors**: Ensure read access to repository files

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
python serena_analyzer.py /path/to/repo --verbose
```

## Contributing

This analyzer is part of the Serena project. Contributions are welcome!

## License

Same as the Serena project license.
