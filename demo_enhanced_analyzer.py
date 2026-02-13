#!/usr/bin/env python3
"""
Demonstration of Enhanced Serena LSP Analyzer

This script demonstrates the enhanced capabilities of the upgraded Serena analyzer,
showing the new output format with function-level attribution and advanced severity classification.
"""

import sys
import os
from typing import List

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_serena_analyzer import (
    EnhancedDiagnostic, 
    EnhancedSeverity, 
    FunctionInfo
)
from enhanced_output_formatter import EnhancedOutputFormatter


def create_sample_diagnostics() -> List[EnhancedDiagnostic]:
    """Create sample diagnostics to demonstrate the enhanced output format."""
    
    # Sample function info
    func1 = FunctionInfo(
        name="process_user_data",
        line_start=45,
        line_end=78,
        column_start=1,
        column_end=20,
        function_type="function",
        parameters=["user_data", "options"],
        complexity_score=7,
        is_public=True
    )
    
    func2 = FunctionInfo(
        name="validate_input",
        line_start=12,
        line_end=25,
        column_start=1,
        column_end=15,
        function_type="method",
        parent_class="UserValidator",
        parameters=["input_data"],
        complexity_score=3,
        is_public=True
    )
    
    func3 = FunctionInfo(
        name="main",
        line_start=120,
        line_end=150,
        column_start=1,
        column_end=10,
        function_type="function",
        parameters=[],
        complexity_score=5,
        is_public=True
    )
    
    # Create sample diagnostics with different severities
    diagnostics = [
        # Critical security issue
        EnhancedDiagnostic(
            file_path="src/auth/security.py",
            line=67,
            column=15,
            severity=EnhancedSeverity.CRITICAL,
            lsp_severity="ERROR",
            message="Potential SQL injection vulnerability detected in user input handling",
            code="security-sql-injection",
            source="pylint",
            function_info=func1,
            function_name="process_user_data",
            impact_score=9,
            business_priority="HIGH"
        ),
        
        # Critical null pointer issue
        EnhancedDiagnostic(
            file_path="src/core/main.py",
            line=135,
            column=8,
            severity=EnhancedSeverity.CRITICAL,
            lsp_severity="ERROR", 
            message="Potential null pointer dereference in main execution path",
            code="null-pointer-dereference",
            source="static-analyzer",
            function_info=func3,
            function_name="main",
            impact_score=9,
            business_priority="HIGH"
        ),
        
        # Major performance issue
        EnhancedDiagnostic(
            file_path="src/utils/data_processor.py",
            line=89,
            column=12,
            severity=EnhancedSeverity.MAJOR,
            lsp_severity="WARNING",
            message="Inefficient database query detected - consider using batch operations",
            code="performance-inefficient-query",
            source="performance-analyzer",
            function_info=func1,
            function_name="process_user_data",
            impact_score=6,
            business_priority="MEDIUM"
        ),
        
        # Major deprecated API usage
        EnhancedDiagnostic(
            file_path="src/api/client.py",
            line=23,
            column=5,
            severity=EnhancedSeverity.MAJOR,
            lsp_severity="WARNING",
            message="Usage of deprecated API method 'old_authenticate()' - will be removed in v2.0",
            code="deprecated-api-usage",
            source="deprecation-checker",
            function_name="authenticate_user",
            impact_score=6,
            business_priority="MEDIUM"
        ),
        
        # Minor style issues
        EnhancedDiagnostic(
            file_path="src/models/user.py",
            line=18,
            column=1,
            severity=EnhancedSeverity.MINOR,
            lsp_severity="INFO",
            message="Missing docstring for public method",
            code="missing-docstring",
            source="pydocstyle",
            function_info=func2,
            function_name="validate_input",
            impact_score=2,
            business_priority="LOW"
        ),
        
        # Minor formatting issue
        EnhancedDiagnostic(
            file_path="src/utils/helpers.py",
            line=45,
            column=80,
            severity=EnhancedSeverity.MINOR,
            lsp_severity="INFO",
            message="Line too long (85 > 79 characters)",
            code="line-too-long",
            source="flake8",
            function_name="format_output",
            impact_score=1,
            business_priority="LOW"
        ),
        
        # Info level hint
        EnhancedDiagnostic(
            file_path="src/config/settings.py",
            line=12,
            column=1,
            severity=EnhancedSeverity.INFO,
            lsp_severity="HINT",
            message="Consider using environment variables for configuration",
            code="config-suggestion",
            source="best-practices",
            function_name="load_config",
            impact_score=1,
            business_priority="LOW"
        ),
        
        # Additional critical issue for demonstration
        EnhancedDiagnostic(
            file_path="src/auth/permissions.py",
            line=78,
            column=20,
            severity=EnhancedSeverity.CRITICAL,
            lsp_severity="ERROR",
            message="Unsafe deserialization of user input - potential remote code execution",
            code="security-unsafe-deserialization",
            source="security-scanner",
            function_name="deserialize_permissions",
            impact_score=10,
            business_priority="CRITICAL"
        ),
        
        # More major issues
        EnhancedDiagnostic(
            file_path="src/database/connection.py",
            line=156,
            column=25,
            severity=EnhancedSeverity.MAJOR,
            lsp_severity="WARNING",
            message="Database connection not properly closed - potential memory leak",
            code="resource-leak",
            source="resource-analyzer",
            function_name="execute_query",
            impact_score=7,
            business_priority="HIGH"
        ),
        
        # Function with multiple errors
        EnhancedDiagnostic(
            file_path="src/auth/security.py",
            line=72,
            column=10,
            severity=EnhancedSeverity.MAJOR,
            lsp_severity="WARNING",
            message="Weak password hashing algorithm detected - use bcrypt or Argon2",
            code="security-weak-hash",
            source="security-scanner",
            function_info=func1,
            function_name="process_user_data",
            impact_score=8,
            business_priority="HIGH"
        )
    ]
    
    return diagnostics


def demonstrate_enhanced_output():
    """Demonstrate the enhanced output format."""
    print("🚀 ENHANCED SERENA LSP ANALYZER DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create sample diagnostics
    diagnostics = create_sample_diagnostics()
    
    # Initialize formatter
    formatter = EnhancedOutputFormatter(verbose=True)
    
    print("📋 ENHANCED OUTPUT FORMAT (Matching Desired Structure):")
    print("=" * 80)
    
    # Format with enhanced output
    enhanced_output = formatter.format_enhanced_output(diagnostics, "myproject")
    print(enhanced_output)
    
    print("\n" + "=" * 80)
    print("📊 COMPACT SUMMARY FORMAT:")
    print("=" * 80)
    
    # Show compact format
    compact_output = formatter.format_compact_output(diagnostics)
    print(compact_output)
    
    print("\n" + "=" * 80)
    print("🔧 ENHANCED FEATURES DEMONSTRATED:")
    print("=" * 80)
    print("✅ Function-level error attribution with AST parsing")
    print("✅ Advanced severity classification (⚠️ Critical, 👉 Major, 🔍 Minor)")
    print("✅ Enhanced output format matching desired structure")
    print("✅ Business impact analysis and prioritization")
    print("✅ Comprehensive error categorization and analysis")
    print("✅ Visual indicators for quick severity identification")
    print("✅ Function complexity and context awareness")
    print("✅ Detailed summary with actionable insights")
    
    print("\n" + "=" * 80)
    print("📈 ANALYSIS STATISTICS:")
    print("=" * 80)
    
    # Show statistics
    from collections import Counter
    severity_counts = Counter(d.severity for d in diagnostics)
    function_counts = Counter(d.function_name for d in diagnostics if d.function_name != "unknown")
    
    print(f"Total Diagnostics: {len(diagnostics)}")
    print(f"Functions Analyzed: {len(function_counts)}")
    print(f"Files Analyzed: {len(set(d.file_path for d in diagnostics))}")
    print()
    print("Severity Distribution:")
    for severity, count in severity_counts.items():
        icon = EnhancedSeverity.SEVERITY_ICONS.get(severity, "❓")
        print(f"  {icon} {severity}: {count}")
    
    print()
    print("Functions with Most Errors:")
    for func_name, count in function_counts.most_common(5):
        print(f"  🔧 {func_name}: {count} errors")


def demonstrate_json_output():
    """Demonstrate the enhanced JSON output format."""
    print("\n" + "=" * 80)
    print("📄 ENHANCED JSON OUTPUT FORMAT:")
    print("=" * 80)
    
    diagnostics = create_sample_diagnostics()
    formatter = EnhancedOutputFormatter()
    
    # Generate JSON output
    json_output = formatter.format_json_output(
        diagnostics, 
        "myproject",
        performance_stats={
            "analysis_time": 45.2,
            "files_processed": 150,
            "functions_analyzed": 89,
            "symbols_resolved": 234
        }
    )
    
    import json
    print(json.dumps(json_output, indent=2, default=str))


if __name__ == "__main__":
    print("🎯 Enhanced Serena LSP Analyzer - Demonstration")
    print("This demo shows the upgraded capabilities with function-level attribution")
    print("and advanced severity classification matching your desired output format.")
    print()
    
    try:
        demonstrate_enhanced_output()
        demonstrate_json_output()
        
        print("\n" + "=" * 80)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("The enhanced analyzer now provides:")
        print("• Function-level error attribution using AST parsing")
        print("• Advanced severity classification with visual indicators")
        print("• Enhanced output format: ERRORS: N [⚠️ Critical: X] [👉 Major: Y] [🔍 Minor: Z]")
        print("• Structured entries: N ⚠️- project/file.py / Function - 'name' [error details]")
        print("• Comprehensive business impact analysis")
        print("• Performance optimization with intelligent caching")
        print("• Multi-language support with language-specific optimizations")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
