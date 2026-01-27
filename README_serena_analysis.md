# Serena LSP Error Analysis Tool

A powerful tool that leverages Serena and SolidLSP to analyze repositories and extract all LSP (Language Server Protocol) errors and diagnostics from codebases.

## Features

- 🔍 **Multi-language Support**: Automatically detects and analyzes Python, JavaScript, TypeScript, Java, C#, C++, Rust, Go, PHP, and Ruby projects
- 🌐 **Repository Flexibility**: Works with both remote Git repositories (via URL) and local directories
- 🎯 **Severity Filtering**: Filter diagnostics by severity level (ERROR, WARNING, INFO, HINT)
- 📊 **Structured Output**: Provides detailed error information including location, file, error reason, and metadata
- 🛡️ **Robust Error Handling**: Graceful handling of network issues, LSP communication failures, and invalid repositories
- 🚀 **Performance Optimized**: Efficient processing of large repositories with progress reporting

## Installation

Ensure you have Serena and SolidLSP installed:

```bash
# Install required dependencies
pip install serena solidlsp
```

## Usage

### Basic Usage

```bash
# Analyze a remote repository
python serena_analysis.py https://github.com/user/repo.git

# Analyze a local repository
python serena_analysis.py /path/to/local/repo

# Analyze current directory
python serena_analysis.py .
```

### Advanced Options

```bash
# Filter only ERROR level diagnostics
python serena_analysis.py https://github.com/user/repo.git --severity ERROR

# Override language detection
python serena_analysis.py /path/to/repo --language python

# Enable verbose logging
python serena_analysis.py /path/to/repo --verbose

# Set custom timeout (in seconds)
python serena_analysis.py /path/to/repo --timeout 120

# Combine multiple options
python serena_analysis.py https://github.com/user/repo.git --severity ERROR --verbose --timeout 180
```

## Output Format

The tool outputs results in the following format:

```
ERRORS: ['<number_of_errors>']
1. '<location>' '<file>' '<error_reason>' '<other_types>'
2. '<location>' '<file>' '<error_reason>' '<other_types>'
...
```

### Example Output

```
ERRORS: ['3']
1. 'line 15, col 8' 'main.py' 'Undefined variable: undefined_var' 'severity: ERROR, code: undefined-variable, source: pylsp'
2. 'line 23, col 12' 'utils.py' 'Missing return statement' 'severity: WARNING, code: missing-return, source: pylsp'
3. 'line 45, col 1' 'config.py' 'Unused import: os' 'severity: INFO, code: unused-import, source: pylsp'
```

## Supported Languages

The tool automatically detects the following programming languages:

| Language   | File Extensions | Config Files |
|------------|----------------|--------------|
| Python     | `.py`          | `requirements.txt`, `setup.py`, `pyproject.toml` |
| JavaScript | `.js`, `.jsx`  | `package.json`, `yarn.lock` |
| TypeScript | `.ts`, `.tsx`  | `tsconfig.json` |
| Java       | `.java`        | `pom.xml`, `build.gradle` |
| C#         | `.cs`          | `.csproj`, `.sln` |
| C++        | `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp` | `CMakeLists.txt` |
| Rust       | `.rs`          | `Cargo.toml` |
| Go         | `.go`          | `go.mod` |
| PHP        | `.php`         | `composer.json` |
| Ruby       | `.rb`          | `Gemfile` |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `repository` | Repository URL or local path to analyze | Required |
| `--severity` | Filter by severity: ERROR, WARNING, INFO, HINT | All levels |
| `--language` | Override language detection | Auto-detect |
| `--timeout` | Timeout for operations in seconds | 300 |
| `--verbose` | Enable verbose logging | False |

## Error Handling

The tool includes comprehensive error handling for:

- **Network Issues**: Timeout and retry mechanisms for Git operations
- **Repository Access**: Validation of local paths and Git URLs
- **Language Server Failures**: Graceful degradation when LSP communication fails
- **File Processing Errors**: Continues analysis even if some files fail
- **Resource Cleanup**: Automatic cleanup of temporary directories and language servers

## Performance Considerations

- **Large Repositories**: The tool processes files incrementally to manage memory usage
- **Timeout Settings**: Adjust `--timeout` for very large repositories or slow networks
- **Temporary Storage**: Remote repositories are cloned to temporary directories and cleaned up automatically
- **Language Server Caching**: SolidLSP caches language server binaries for faster subsequent runs

## Troubleshooting

### Common Issues

1. **"Language Server not started"**
   - Ensure the required language server is installed for your project type
   - Try increasing the timeout with `--timeout 600`

2. **"Git clone failed"**
   - Check network connectivity and repository URL
   - Ensure you have access to private repositories

3. **"Could not detect language"**
   - Use `--language` to manually specify the language
   - Ensure your repository contains recognizable source files

4. **"No errors found"**
   - The repository may have no LSP errors
   - Try using `--severity WARNING` to include warnings
   - Use `--verbose` to see detailed processing information

### Debug Mode

Enable verbose logging to see detailed information about the analysis process:

```bash
python serena_analysis.py /path/to/repo --verbose
```

This will show:
- Language detection process
- File discovery and filtering
- Language server startup and communication
- Individual file analysis results
- Error details and stack traces

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Analyze Code Quality
  run: |
    python serena_analysis.py . --severity ERROR > analysis_results.txt
    if grep -q "ERRORS: \['0'\]" analysis_results.txt; then
      echo "No errors found!"
    else
      echo "Errors detected:"
      cat analysis_results.txt
      exit 1
    fi
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python serena_analysis.py . --severity ERROR
if [ $? -ne 0 ]; then
    echo "LSP errors detected. Commit aborted."
    exit 1
fi
```

## Contributing

To contribute to this tool:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all existing tests pass
5. Submit a pull request

## License

This tool is part of the Serena project and follows the same licensing terms.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Serena and SolidLSP documentation
- Open an issue in the project repository

