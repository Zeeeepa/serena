# Serena LSP Error Analyzer

A comprehensive script that retrieves **ALL LSP errors** from any codebase using Serena's solidlsp integration. Supports both GitHub repositories and local codebases with automatic language detection and multi-language server support.

## Features

- 🌐 **Multi-Language Support**: Python, TypeScript/JavaScript, Java, C#, Rust, Go, Ruby, C++, PHP, Dart, Kotlin, Clojure, Elixir, Terraform
- 🔗 **GitHub Integration**: Direct analysis of GitHub repositories via URL
- 🏠 **Local Analysis**: Analyze local codebases and directories
- 🚀 **Concurrent Processing**: Multiple language servers running simultaneously for maximum efficiency
- 📊 **Comprehensive Error Classification**: Critical (Errors), Major (Warnings), Minor (Info/Hints)
- 🎯 **Symbol Context**: Shows function/class context for each error
- 📈 **Detailed Statistics**: Complete analysis metrics and timing

## Installation

1. **Prerequisites**: Ensure you have Serena installed and configured
2. **Place the script**: Copy `serena_analyzer.py` to your Serena root directory
3. **Make executable**: `chmod +x serena_analyzer.py`

## Usage

### Basic Usage

```bash
# Analyze a GitHub repository
python serena_analyzer.py https://github.com/user/repo

# Analyze local project
python serena_analyzer.py /path/to/project

# Analyze current directory
python serena_analyzer.py .
```

### Advanced Options

```bash
# Verbose output with detailed logging
python serena_analyzer.py -v https://github.com/user/repo

# Save results to file
python serena_analyzer.py -o results.txt /path/to/project

# Combined options
python serena_analyzer.py -v -o analysis_report.txt https://github.com/user/repo
```

## Output Format

The analyzer produces output in the exact format requested:

```
ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
1 ⚠️- project/src/file.py / Function - 'function_name' [Undefined variable 'x']
2 ⚠️- project/src/file.py / Class - 'MyClass' [Missing return type annotation]
3 👉- project/src/utils.py / Function - 'helper' [Unused variable 'temp']
4 👉- project/src/main.py / Function - 'main' [Line too long (120 > 88 characters)]
5 🔍- project/src/config.py / Variable - 'DEBUG' [Consider using constant naming]
...
104 🔍- project/tests/test_utils.py / Function - 'test_helper' [Missing docstring]
```

### Error Classification

- **⚠️ Critical**: LSP Error severity (syntax errors, undefined variables, type errors)
- **👉 Major**: LSP Warning severity (style issues, potential problems, deprecations)
- **🔍 Minor**: LSP Information/Hint severity (suggestions, optimizations, style preferences)

## How It Works

### 1. Project Initialization
- Detects if input is GitHub URL or local path
- Clones GitHub repositories to temporary directory
- Initializes Serena project with automatic language detection

### 2. Language Server Management
- Automatically detects all languages in the codebase
- Starts appropriate language servers concurrently
- Handles server lifecycle and error recovery

### 3. Comprehensive Error Collection
- Discovers all source files using Serena's file discovery
- Groups files by language for efficient processing
- Sends `textDocument/didOpen` to trigger diagnostic generation
- Requests diagnostics from all language servers using `textDocument/diagnostic`
- Aggregates errors from all servers with deduplication

### 4. Symbol Context Resolution
- Uses LSP `textDocument/documentSymbol` to find function/class context
- Maps error locations to containing symbols
- Provides meaningful context for each error

### 5. Output Formatting
- Classifies errors by LSP severity levels
- Sorts by severity and location
- Formats according to specified output format

## Supported Languages & Servers

| Language | LSP Server | File Extensions |
|----------|------------|-----------------|
| Python | Pyright | `.py`, `.pyi` |
| TypeScript/JavaScript | TypeScript Language Server | `.ts`, `.tsx`, `.js`, `.jsx` |
| Java | Eclipse JDT LS | `.java` |
| C# | OmniSharp | `.cs` |
| Rust | rust-analyzer | `.rs` |
| Go | gopls | `.go` |
| Ruby | Solargraph | `.rb` |
| C++ | clangd | `.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp` |
| PHP | Intelephense | `.php` |
| Dart | Dart Language Server | `.dart` |
| Kotlin | Kotlin Language Server | `.kt`, `.kts` |
| Clojure | clojure-lsp | `.clj`, `.cljs`, `.cljc` |
| Elixir | Elixir LS | `.ex`, `.exs` |
| Terraform | terraform-ls | `.tf`, `.tfvars` |

## Architecture

### Core Components

1. **SerenaAnalyzer**: Main orchestration class
2. **Project Integration**: Uses Serena's Project class for file discovery and language detection
3. **Language Server Management**: Concurrent server initialization and lifecycle management
4. **Diagnostic Collection**: Multi-threaded error collection with timeout handling
5. **Symbol Resolution**: Context-aware error reporting with function/class information
6. **Output Formatting**: Structured error classification and formatting

### Error Collection Strategy

The analyzer uses a **pull-based diagnostic collection** approach:

1. **File Discovery**: Uses `Project.gather_source_files()` to find all source files
2. **Language Detection**: Maps file extensions to appropriate language servers
3. **Server Initialization**: Starts all required language servers concurrently
4. **File Processing**: For each file:
   - Opens the file in the appropriate language server (`textDocument/didOpen`)
   - Requests diagnostics (`textDocument/diagnostic`)
   - Extracts symbol context (`textDocument/documentSymbol`)
5. **Aggregation**: Combines errors from all servers with deduplication
6. **Classification**: Maps LSP severity levels to user-friendly categories

### Performance Optimizations

- **Concurrent Processing**: Multiple language servers run simultaneously
- **Threaded File Processing**: Files processed in parallel within each language
- **Efficient File Grouping**: Files grouped by language to minimize server switching
- **Timeout Management**: Prevents hanging on unresponsive servers or files
- **Resource Cleanup**: Proper cleanup of servers and temporary files

## Error Handling

The analyzer includes comprehensive error handling:

- **Server Startup Failures**: Continues with available servers if some fail to start
- **File Processing Errors**: Skips problematic files and continues analysis
- **Timeout Management**: Prevents hanging on unresponsive operations
- **Resource Cleanup**: Ensures proper cleanup even on failures
- **GitHub Clone Failures**: Handles network issues and repository access problems

## Troubleshooting

### Common Issues

1. **Language Server Not Found**
   ```
   ❌ Error starting python language server: Language server binary not found
   ```
   **Solution**: Install the required language server (e.g., `npm install -g pyright`)

2. **Permission Denied**
   ```
   ❌ Error: Permission denied accessing /path/to/project
   ```
   **Solution**: Check file permissions and run with appropriate privileges

3. **GitHub Clone Timeout**
   ```
   ❌ Git clone timed out after 5 minutes
   ```
   **Solution**: Check network connection or try with a smaller repository

4. **No Source Files Found**
   ```
   ⚠️ Found 0 source files to analyze
   ```
   **Solution**: Ensure the project contains supported source files and check ignore patterns

### Debug Mode

Use the `-v` flag for detailed debugging information:

```bash
python serena_analyzer.py -v /path/to/project
```

This provides:
- Detailed language server startup logs
- File processing progress
- Error details and stack traces
- LSP communication tracing

## Examples

### Analyzing Popular Repositories

```bash
# Analyze a Python project
python serena_analyzer.py https://github.com/psf/requests

# Analyze a TypeScript project  
python serena_analyzer.py https://github.com/microsoft/vscode

# Analyze a multi-language project
python serena_analyzer.py https://github.com/microsoft/playwright
```

### Sample Output

```
🚀 Serena LSP Error Analyzer
==================================================
📂 Target: https://github.com/user/example-project

🔄 Cloning https://github.com/user/example-project to /tmp/serena_analyzer_xyz
✅ Successfully cloned to /tmp/serena_analyzer_xyz/example-project
🔍 Initializing Serena project at /tmp/serena_analyzer_xyz/example-project
✅ Project initialized: example-project
📝 Detected language: python
🌐 Detected languages: ['python', 'typescript']
🚀 Creating python language server
🔧 Starting python language server...
✅ python language server started successfully
🚀 Creating typescript language server
🔧 Starting typescript language server...
✅ typescript language server started successfully
🎯 Successfully started 2/2 language servers
📄 Found 45 source files to analyze
🔍 Analyzing 32 python files...
🔍 Analyzing 13 typescript files...
📊 Processed 50/45 files...
✅ Analysis complete: 23 errors found in 45 files

✅ Analysis completed in 12.34 seconds
📊 Languages analyzed: python, typescript
📄 Files processed: 45

ERRORS: 23 [⚠️ Critical: 8] [👉 Major: 12] [🔍 Minor: 3]
1 ⚠️- src/main.py / Function - 'process_data' [Undefined variable 'result']
2 ⚠️- src/utils.py / Class - 'DataProcessor' [Missing required argument 'config']
3 ⚠️- frontend/app.ts / Function - 'handleClick' [Property 'value' does not exist on type 'EventTarget']
...
23 🔍- tests/test_utils.py / Function - 'test_processor' [Consider using more descriptive variable names]
```

## Integration

The analyzer can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Serena LSP Analysis
  run: |
    python serena_analyzer.py . -o lsp_errors.txt
    if [ -s lsp_errors.txt ]; then
      echo "LSP errors found:"
      cat lsp_errors.txt
      exit 1
    fi
```

## Contributing

To extend the analyzer:

1. **Add Language Support**: Extend the `language_patterns` and `extension_map` dictionaries
2. **Improve Symbol Context**: Enhance the `get_symbol_context` method for better context resolution
3. **Add Output Formats**: Extend the `format_output` method for additional output formats
4. **Performance Optimization**: Improve concurrent processing and caching strategies

## License

This script is part of the Serena project and follows the same license terms.

