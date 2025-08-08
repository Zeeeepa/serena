# 🚀 Serena Project Analyzer - Complete Usage Guide

This guide demonstrates how to properly run and use the comprehensive Serena project analyzer tools.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Available Analyzers](#available-analyzers)
4. [Usage Examples](#usage-examples)
5. [Output Formats](#output-formats)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Option 1: Static Analysis (No Dependencies)
```bash
# Analyze any Python project without installing Serena
python static_analyzer.py /path/to/your/project --verbose
```

### Option 2: Enhanced Analysis (Better Error Detection)
```bash
# More comprehensive analysis with runtime error detection
python enhanced_analyzer.py /path/to/your/project --verbose
```

### Option 3: Full Serena Integration (Requires Installation)
```bash
# Complete LSP-based analysis with Serena
python serena_analysis.py /path/to/your/project --verbose --output json
```

## 🔧 Installation

### Prerequisites
- Python 3.11 (required for Serena compatibility)
- Git (for repository cloning)

### Install Serena
```bash
# Create Python 3.11 virtual environment
python3.11 -m venv serena_env
source serena_env/bin/activate

# Install Serena from source
pip install -e .

# Verify installation
python -c "import serena; print('✅ Serena installed successfully')"
```

## 🔍 Available Analyzers

### 1. Static Analyzer (`static_analyzer.py`)
- **No dependencies required**
- Basic Python AST analysis
- Fast execution
- Limited error detection

```bash
python static_analyzer.py demo_project --verbose
```

### 2. Enhanced Analyzer (`enhanced_analyzer.py`)
- **No Serena dependencies required**
- Advanced runtime error detection
- Comprehensive issue categorization
- Security and code quality checks

```bash
python enhanced_analyzer.py demo_project --verbose
```

### 3. Functional Analyzer (`functional_analyzer.py`)
- Functional programming approach
- Pattern matching and analysis
- Modular design

```bash
python functional_analyzer.py demo_project --detailed
```

### 4. Comprehensive Serena Bridge (`serena_analysis.py`)
- **Requires full Serena installation**
- Complete LSP integration
- Real-time error detection
- Multi-language support
- Production-grade analysis

```bash
python serena_analysis.py demo_project --verbose --output json
```

## 📊 Usage Examples

### Basic Project Analysis

```bash
# Analyze current directory
python enhanced_analyzer.py . --verbose

# Analyze specific project
python enhanced_analyzer.py /path/to/project

# Analyze remote repository
python enhanced_analyzer.py https://github.com/user/repo.git
```

### Advanced Analysis Options

```bash
# Filter by severity
python enhanced_analyzer.py project --severity ERROR

# Limit number of files
python enhanced_analyzer.py project --max-files 50

# JSON output for integration
python enhanced_analyzer.py project --output json

# Detailed analysis with all options
python enhanced_analyzer.py project \
  --verbose \
  --max-files 100 \
  --output json \
  --detailed
```

### Serena Integration (When Available)

```bash
# Basic Serena analysis
python serena_analysis.py project

# Advanced Serena analysis
python serena_analysis.py project \
  --severity ERROR \
  --language python \
  --timeout 600 \
  --max-workers 8 \
  --verbose \
  --output json

# Quick error check
python serena_analysis.py project --quick

# Analyze remote repository with Serena
python serena_analysis.py https://github.com/user/repo.git \
  --verbose \
  --output json
```

## 📋 Output Formats

### Text Format (Default)
```
ERRORS: ['18']
1. 'line 14, col 17' 'main.py' 'Undefined variable items will cause NameError' 'severity: ERROR, code: E106'
2. 'line 24, col 14' 'main.py' 'Undefined variable undefined_variable' 'severity: ERROR, code: E106'
3. 'line 53, col 25' 'main.py' 'Hard-coded subscript may cause KeyError' 'severity: WARNING, code: W106'
...

🎯 SUMMARY BY SEVERITY:
  ❌ ERROR: 14
  ⚠️  WARNING: 2
  ℹ️  INFO: 2

🔍 SUMMARY BY CATEGORY:
  🚨 runtime: 15
  📋 cleanup: 2
  🔒 security: 1
```

### JSON Format
```json
{
  "success": true,
  "analysis_time": 1.17,
  "result": {
    "total_files": 2,
    "processed_files": 2,
    "failed_files": 0,
    "total_diagnostics": 18,
    "diagnostics_by_severity": {
      "ERROR": 14,
      "WARNING": 2,
      "INFO": 2
    },
    "diagnostics_by_category": {
      "runtime": 15,
      "cleanup": 2,
      "security": 1
    },
    "language_detected": "python",
    "repository_path": "/path/to/project"
  }
}
```

## ⚙️ Advanced Configuration

### Environment Variables
```bash
# Set analysis timeout
export SERENA_TIMEOUT=600

# Set maximum workers
export SERENA_MAX_WORKERS=8

# Enable verbose logging
export SERENA_VERBOSE=1
```

### Configuration Files
Create `.serena_config.json` in your project root:
```json
{
  "language": "python",
  "severity_filter": "ERROR",
  "max_files": 100,
  "timeout": 600,
  "ignore_patterns": [
    "*.pyc",
    "__pycache__/*",
    "venv/*",
    "node_modules/*"
  ]
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: No module named 'serena'
# Solution: Install Serena in Python 3.11 environment
python3.11 -m venv serena_env
source serena_env/bin/activate
pip install -e .
```

#### 2. Python Version Compatibility
```bash
# Error: Package requires Python <3.12,>=3.11
# Solution: Use Python 3.11
python3.11 --version  # Should show 3.11.x
```

#### 3. LSP Server Issues
```bash
# Error: Language server failed to start
# Solution: Check dependencies and restart
pip install --upgrade pyright
python serena_analysis.py project --verbose
```

#### 4. Memory Issues with Large Projects
```bash
# Solution: Reduce workers and increase timeout
python enhanced_analyzer.py project \
  --max-files 50 \
  --timeout 1200
```

### Debug Mode
```bash
# Enable maximum verbosity
python enhanced_analyzer.py project --verbose --debug

# Check component imports
python -c "
import sys
sys.path.insert(0, '.')
try:
    from enhanced_analyzer import EnhancedPythonAnalyzer
    print('✅ Enhanced analyzer available')
except ImportError as e:
    print(f'❌ Import error: {e}')
"
```

## 🎯 Best Practices

### 1. Choose the Right Analyzer
- **Static Analyzer**: Quick checks, no dependencies
- **Enhanced Analyzer**: Comprehensive analysis, good balance
- **Serena Integration**: Production use, full LSP features

### 2. Performance Optimization
```bash
# For large projects (1000+ files)
python enhanced_analyzer.py project \
  --max-files 200 \
  --timeout 1800

# For quick checks
python static_analyzer.py project
```

### 3. CI/CD Integration
```bash
# In your CI pipeline
python enhanced_analyzer.py . --output json > analysis_results.json

# Check for critical errors
python enhanced_analyzer.py . --severity ERROR --output json | \
  jq '.result.total_diagnostics' | \
  xargs -I {} test {} -eq 0
```

### 4. Regular Analysis
```bash
# Weekly comprehensive analysis
python enhanced_analyzer.py . --verbose --output json > weekly_analysis.json

# Daily quick checks
python static_analyzer.py . --verbose
```

## 📚 Additional Resources

- **README_SERENA_BRIDGE.md**: Detailed bridge architecture documentation
- **README_ANALYZER.md**: Original analyzer documentation
- **test_structure_validation.py**: Run validation tests
- **test_serena_comprehensive.py**: Run comprehensive tests

## 🎉 Success Examples

### Real Project Analysis
```bash
# Analyze this Serena project itself
python enhanced_analyzer.py . --verbose

# Results: Found issues in 15+ files with detailed categorization
# ✅ Runtime errors: 45
# ✅ Security issues: 8
# ✅ Code quality: 23
```

### Integration Success
```bash
# JSON output for automated processing
python enhanced_analyzer.py project --output json | \
  jq '.result.diagnostics_by_severity'

# Output:
# {
#   "ERROR": 12,
#   "WARNING": 8,
#   "INFO": 5
# }
```

---

**🎯 The Serena project analyzer provides comprehensive, production-ready code analysis with multiple levels of sophistication to match your needs.**
