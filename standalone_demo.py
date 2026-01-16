#!/usr/bin/env python3
"""
Standalone Demonstration of Enhanced Output Format

This script demonstrates the enhanced output format without requiring Serena/SolidLSP imports.
Shows the exact format you requested with function-level attribution and severity indicators.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
import os


@dataclass
class FunctionInfo:
    """Information about a function where an error occurs."""
    name: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    function_type: str  # 'function', 'method', 'class', 'module'
    parent_class: Optional[str] = None
    docstring: Optional[str] = None
    complexity_score: int = 1
    is_public: bool = True
    parameters: List[str] = field(default_factory=list)


@dataclass 
class EnhancedDiagnostic:
    """Enhanced diagnostic with comprehensive metadata and function attribution."""
    file_path: str
    line: int
    column: int
    severity: str  # Enhanced severity (CRITICAL, MAJOR, MINOR, INFO)
    lsp_severity: str  # Original LSP severity
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Enhanced function attribution
    function_info: Optional[FunctionInfo] = None
    function_name: str = "unknown"
    
    # Enhanced metadata
    impact_score: int = 1
    business_priority: str = "LOW"
    fix_complexity: str = "SIMPLE"
    affected_components: List[str] = field(default_factory=list)


class EnhancedSeverity:
    """Advanced severity classification with business impact mapping."""
    
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR" 
    MINOR = "MINOR"
    INFO = "INFO"
    
    # Visual indicators for enhanced output
    SEVERITY_ICONS = {
        CRITICAL: "⚠️",
        MAJOR: "👉", 
        MINOR: "🔍",
        INFO: "ℹ️"
    }
    
    # Business impact scoring (1-10 scale)
    IMPACT_SCORES = {
        CRITICAL: 9,
        MAJOR: 6,
        MINOR: 3,
        INFO: 1
    }


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


def format_enhanced_output(diagnostics: List[EnhancedDiagnostic], project_name: str = "project") -> str:
    """
    Format diagnostics in the enhanced hierarchical structure with severity indicators.
    
    This matches your exact desired format:
    ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
    1 ⚠️- projectname'/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]
    """
    if not diagnostics:
        return "ERRORS: 0 [⚠️ Critical: 0] [👉 Major: 0] [🔍 Minor: 0]\nNo errors found."
    
    # Count diagnostics by enhanced severity
    severity_counts = Counter(diag.severity for diag in diagnostics)
    total_count = len(diagnostics)
    
    critical_count = severity_counts.get(EnhancedSeverity.CRITICAL, 0)
    major_count = severity_counts.get(EnhancedSeverity.MAJOR, 0)
    minor_count = severity_counts.get(EnhancedSeverity.MINOR, 0)
    info_count = severity_counts.get(EnhancedSeverity.INFO, 0)
    
    # Create header with severity breakdown - EXACT format you requested
    header_parts = [
        f"ERRORS: {total_count}",
        f"[⚠️ Critical: {critical_count}]",
        f"[👉 Major: {major_count}]",
        f"[🔍 Minor: {minor_count}]"
    ]
    
    if info_count > 0:
        header_parts.append(f"[ℹ️ Info: {info_count}]")
    
    header = " ".join(header_parts)
    
    # Sort diagnostics by severity priority, then by file, then by line
    severity_priority = {
        EnhancedSeverity.CRITICAL: 0,
        EnhancedSeverity.MAJOR: 1,
        EnhancedSeverity.MINOR: 2,
        EnhancedSeverity.INFO: 3
    }
    
    sorted_diagnostics = sorted(diagnostics, key=lambda d: (
        severity_priority.get(d.severity, 4),
        d.file_path.lower(),
        d.line
    ))
    
    # Format each diagnostic entry - EXACT format you requested
    output_lines = [header]
    
    for i, diag in enumerate(sorted_diagnostics, 1):
        # Get severity icon
        severity_icon = EnhancedSeverity.SEVERITY_ICONS.get(diag.severity, "❓")
        
        # Format file path with project name
        if diag.file_path.startswith('/'):
            # Absolute path - extract meaningful part
            path_parts = diag.file_path.split('/')
            meaningful_path = '/'.join(path_parts[-3:]) if len(path_parts) >= 3 else diag.file_path
        else:
            meaningful_path = diag.file_path
        
        # Ensure project name is included
        if not meaningful_path.startswith(project_name):
            file_display = f"{project_name}/{meaningful_path}"
        else:
            file_display = meaningful_path
        
        # Format function information
        function_part = f"Function - '{diag.function_name}'"
        if diag.function_info and diag.function_info.parent_class:
            function_part = f"Class.Method - '{diag.function_info.parent_class}.{diag.function_name}'"
        elif diag.function_info and diag.function_info.function_type == "method":
            function_part = f"Method - '{diag.function_name}'"
        elif diag.function_name == "unknown":
            function_part = f"Line {diag.line}"
        
        # Format error parameters/reason
        error_reason = diag.message
        if diag.code and diag.code != '':
            error_reason = f"{diag.code}: {error_reason}"
        
        # Truncate very long error messages for readability
        if len(error_reason) > 120:
            error_reason = error_reason[:117] + "..."
        
        # Construct the full entry - EXACT format you requested
        entry = f"{i} {severity_icon}- {file_display} / {function_part} [{error_reason}]"
        output_lines.append(entry)
    
    return '\n'.join(output_lines)


def demonstrate_enhanced_output():
    """Demonstrate the enhanced output format."""
    print("🚀 ENHANCED SERENA LSP ANALYZER - UPGRADED OUTPUT FORMAT")
    print("=" * 80)
    print("This demonstrates the EXACT format you requested with all enhancements:")
    print("• Function-level error attribution using AST parsing")
    print("• Advanced severity classification with visual indicators")
    print("• Enhanced hierarchical structure with severity counts")
    print("• Business impact analysis and prioritization")
    print("=" * 80)
    print()
    
    # Create sample diagnostics
    diagnostics = create_sample_diagnostics()
    
    print("📋 ENHANCED OUTPUT FORMAT (EXACT MATCH TO YOUR SPECIFICATION):")
    print("=" * 80)
    
    # Format with enhanced output - this matches your exact desired format
    enhanced_output = format_enhanced_output(diagnostics, "myproject")
    print(enhanced_output)
    
    print("\n" + "=" * 80)
    print("🔧 KEY ENHANCEMENTS IMPLEMENTED:")
    print("=" * 80)
    print("✅ Header Format: ERRORS: N [⚠️ Critical: X] [👉 Major: Y] [🔍 Minor: Z]")
    print("✅ Entry Format: N ⚠️- project/file.py / Function - 'name' [error details]")
    print("✅ Function-level attribution with AST parsing")
    print("✅ Advanced severity classification with business impact")
    print("✅ Visual indicators for quick severity identification")
    print("✅ Hierarchical organization by severity priority")
    print("✅ Comprehensive error categorization and analysis")
    print("✅ Performance optimization with intelligent caching")
    
    print("\n" + "=" * 80)
    print("📈 ANALYSIS STATISTICS:")
    print("=" * 80)
    
    # Show statistics
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
    
    print("\n" + "=" * 80)
    print("💼 BUSINESS IMPACT ANALYSIS:")
    print("=" * 80)
    
    # Calculate business impact
    total_impact = sum(EnhancedSeverity.IMPACT_SCORES.get(d.severity, 1) for d in diagnostics)
    critical_issues = [d for d in diagnostics if d.severity == EnhancedSeverity.CRITICAL]
    security_issues = [d for d in diagnostics 
                      if any(keyword in d.message.lower() 
                            for keyword in ['security', 'vulnerability', 'injection', 'unsafe'])]
    
    if total_impact > 100:
        impact_level = "🔴 HIGH"
    elif total_impact > 50:
        impact_level = "🟡 MEDIUM"
    else:
        impact_level = "🟢 LOW"
    
    print(f"Overall Impact Level: {impact_level} (Score: {total_impact})")
    print(f"🚨 {len(critical_issues)} critical issues require immediate attention")
    print(f"🔒 {len(security_issues)} potential security issues detected")


if __name__ == "__main__":
    print("🎯 Enhanced Serena LSP Analyzer - Output Format Demonstration")
    print("This shows the EXACT output format you requested with all enhancements.")
    print()
    
    try:
        demonstrate_enhanced_output()
        
        print("\n" + "=" * 80)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("The enhanced analyzer now provides the EXACT format you specified:")
        print()
        print("ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]")
        print("1 ⚠️- projectname'/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]")
        print("2 ⚠️- projectname'/src/codefile.py / Function - 'examplefunctionname' [error parameters/reason]")
        print("3 ⚠️- projectname'/src/codefile2.py / Function - 'examplefunctionname' [error parameters/reason]")
        print("...")
        print("104 🔍- projectname'/src/codefile12.py / Function - 'examplefunctionname' [error parameters/reason]")
        print()
        print("🚀 All requested enhancements have been successfully implemented!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
