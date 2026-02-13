# Repository Analytics with SolidLSP Integration

Advanced repository analysis tool that combines traditional code quality metrics with runtime error detection using Serena's SolidLSP implementation.

## Features

### 🔍 Traditional Code Metrics
- **Cyclomatic Complexity**: Measure code complexity and maintainability
- **Halstead Metrics**: Analyze code volume and difficulty
- **Maintainability Index**: Overall code maintainability score
- **Line Metrics**: LOC, LLOC, SLOC, and comment density
- **Inheritance Depth**: Object-oriented design complexity

### 🚨 Runtime Error Detection (NEW)
- **SolidLSP Integration**: Leverage Serena's powerful language server protocol implementation
- **Multi-language Support**: Python, TypeScript/JavaScript, Java, C#, Go, Rust, PHP, Clojure, Elixir
- **Comprehensive Diagnostics**: Errors, warnings, information, and hints
- **File-level Analysis**: Detailed error reporting with line numbers and context

### 📈 Git Activity Analysis
- **Commit History**: Monthly commit patterns over the last 12 months
- **Repository Statistics**: File counts, language distribution

### 🌐 Multi-language Support
Supports analysis of repositories containing multiple programming languages with automatic language detection.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd upgraded_analytics
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Serena** (for SolidLSP support):
   ```bash
   pip install serena-agent
   ```

## Usage

### Command Line Interface

The tool supports the exact command format you requested:

```bash
# Basic analysis
python api.py --repo Zeeeepa/graph-sitter

# Analysis with options
python api.py --repo owner/repo --no-runtime-errors --output results.json

# Full GitHub URL
python api.py --repo https://github.com/microsoft/vscode
```

#### CLI Options

- `--repo`: Repository to analyze (required)
- `--no-runtime-errors`: Skip SolidLSP runtime error analysis (faster)
- `--max-files N`: Limit analysis to N files
- `--languages python java`: Analyze only specific languages
- `--output file.json`: Save results to JSON file
- `--verbose`: Enable detailed logging

### FastAPI Server Mode

Start the API server:

```bash
# Default server (localhost:8000)
python api.py --server

# Custom host and port
python api.py --server --host 0.0.0.0 --port 8080
```

#### API Endpoints

- `GET /`: API information and supported features
- `GET /health`: Health check endpoint
- `POST /analyze`: Synchronous repository analysis
- `POST /analyze_async`: Asynchronous analysis (background processing)
- `GET /languages`: List of supported programming languages

#### Example API Usage

```bash
# Analyze a repository
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "Zeeeepa/graph-sitter",
    "include_runtime_errors": true,
    "max_files": 100
  }'
```

## Output Format

The tool provides comprehensive analysis results in JSON format:

```json
{
  "repo_url": "owner/repo",
  "description": "Repository description",
  "analysis_timestamp": "2025-01-01T12:00:00",
  "num_files": 150,
  "num_functions": 45,
  "num_classes": 12,
  "line_metrics": {
    "loc": 5000,
    "lloc": 3500,
    "sloc": 4200,
    "comments": 800,
    "comment_density": 16.0
  },
  "complexity_metrics": {
    "average_cyclomatic_complexity": 3.2,
    "complexity_rank": "B",
    "functions_analyzed": 45
  },
  "runtime_error_summary": {
    "total_files_analyzed": 120,
    "files_with_errors": 8,
    "total_errors": 23,
    "errors": 5,
    "warnings": 12,
    "information": 4,
    "hints": 2,
    "language_summaries": {
      "python": {
        "language": "python",
        "total_files": 80,
        "files_with_errors": 5,
        "total_errors": 15
      }
    },
    "file_summaries": [
      {
        "file_path": "src/main.py",
        "total_errors": 3,
        "runtime_errors": [
          {
            "file_path": "src/main.py",
            "severity": 1,
            "message": "Undefined variable 'x'",
            "range": {
              "start": {"line": 10, "character": 5},
              "end": {"line": 10, "character": 6}
            },
            "line_content": "    print(x)"
          }
        ]
      }
    ]
  },
  "monthly_commits": {
    "2024-01": 15,
    "2024-02": 23,
    "2024-03": 18
  },
  "analysis_duration_seconds": 45.2,
  "languages_detected": ["python", "typescript", "javascript"],
  "analysis_errors": []
}
```

## Architecture

### Components

1. **Language Detection** (`language_detection.py`): Automatically detects programming languages in repositories
2. **SolidLSP Integration** (`solidlsp_integration.py`): Interfaces with Serena's language servers for runtime error detection
3. **Repository Handler** (`repository_handler.py`): Manages repository cloning and Git operations
4. **Analyzer** (`analyzer.py`): Orchestrates all analysis components
5. **API** (`api.py`): FastAPI server and CLI interface
6. **Models** (`models.py`): Pydantic data models for requests and responses

### SolidLSP Integration

The tool leverages Serena's SolidLSP implementation to provide advanced runtime error detection:

- **Language Server Management**: Automatically initializes appropriate language servers
- **Diagnostic Collection**: Gathers comprehensive diagnostic information
- **Error Classification**: Categorizes issues by severity (Error, Warning, Information, Hint)
- **Multi-language Support**: Handles multiple programming languages in a single repository

## Supported Languages

### Full SolidLSP Support
- Python (.py, .pyw, .pyi)
- TypeScript (.ts, .tsx)
- JavaScript (.js, .jsx, .mjs, .cjs)
- Java (.java)
- C# (.cs, .csx)
- Go (.go)
- Rust (.rs)
- PHP (.php, .phtml)
- Clojure (.clj, .cljs, .cljc)
- Elixir (.ex, .exs)

### Traditional Metrics Only
- C/C++ (.c, .cpp, .h, .hpp)
- Ruby (.rb)
- Kotlin (.kt)
- Swift (.swift)
- And many more...

## Performance Considerations

- **Shallow Cloning**: Uses `git clone --depth 1` for faster repository cloning
- **File Limiting**: Supports `--max-files` option to limit analysis scope
- **Language Filtering**: Can analyze specific languages only
- **Async Processing**: Server mode supports background analysis for large repositories

## Error Handling

The tool provides comprehensive error handling and reporting:

- **Component-level Errors**: Tracks errors by analysis component
- **Graceful Degradation**: Continues analysis even if some components fail
- **Detailed Logging**: Verbose logging for debugging
- **Error Aggregation**: Collects and reports all analysis errors

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Project Structure

```
upgraded_analytics/
├── src/
│   ├── models.py              # Data models
│   ├── language_detection.py  # Language detection
│   ├── solidlsp_integration.py # SolidLSP interface
│   ├── repository_handler.py  # Git operations
│   ├── analyzer.py            # Main analyzer
│   └── api.py                 # FastAPI server
├── tests/                     # Test files
├── api.py                     # Main CLI/server script
├── cli.py                     # Alternative CLI script
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Serena**: For the powerful SolidLSP implementation
- **Codegen SDK**: For traditional code analysis capabilities
- **FastAPI**: For the modern API framework

