#!/usr/bin/env python3
"""
Enhanced Output Formatter for Serena LSP Analysis

This module provides advanced output formatting capabilities for the enhanced Serena analyzer,
including the desired hierarchical structure with severity-based categorization and visual indicators.

Output Format:
ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
1 ⚠️- projectname'/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]
2 ⚠️- projectname'/src/codefile.py / Function - 'examplefunctionname' [error parameters/reason]
...
"""

import os
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from dataclasses import asdict

from enhanced_serena_analyzer import EnhancedDiagnostic, EnhancedSeverity, FunctionInfo


class EnhancedOutputFormatter:
    """
    Advanced output formatter for enhanced Serena LSP analysis results.
    
    Provides multiple output formats including the desired hierarchical structure
    with severity-based categorization and visual indicators.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def format_enhanced_output(self, diagnostics: List[EnhancedDiagnostic], 
                             project_name: str = "project") -> str:
        """
        Format diagnostics in the enhanced hierarchical structure with severity indicators.
        
        Args:
            diagnostics: List of enhanced diagnostics
            project_name: Name of the project for display
            
        Returns:
            Formatted output string matching the desired structure
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
        
        # Create header with severity breakdown
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
        
        # Format each diagnostic entry
        output_lines = [header, ""]
        
        for i, diag in enumerate(sorted_diagnostics, 1):
            formatted_entry = self._format_diagnostic_entry(i, diag, project_name)
            output_lines.append(formatted_entry)
        
        # Add comprehensive summary if verbose or many errors
        if self.verbose or total_count > 20:
            output_lines.extend(self._generate_summary_section(diagnostics, project_name))
        
        return '\n'.join(output_lines)
    
    def _format_diagnostic_entry(self, index: int, diag: EnhancedDiagnostic, 
                                project_name: str) -> str:
        """
        Format a single diagnostic entry in the desired structure.
        
        Format: 1 ⚠️- projectname'/src/codefile.py / Function - 'function_name' [error parameters/reason]
        """
        # Get severity icon
        severity_icon = EnhancedSeverity.SEVERITY_ICONS.get(diag.severity, "❓")
        
        # Format file path with project name
        if diag.file_path.startswith('/'):
            # Absolute path - extract meaningful part
            path_parts = diag.file_path.split('/')
            # Find project-like directory or use last few parts
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
        
        # Construct the full entry
        entry = f"{index} {severity_icon}- {file_display} / {function_part} [{error_reason}]"
        
        return entry
    
    def _generate_summary_section(self, diagnostics: List[EnhancedDiagnostic], 
                                project_name: str) -> List[str]:
        """Generate comprehensive summary section for detailed analysis."""
        summary_lines = ["", "=" * 80, "📋 ENHANCED SERENA LSP ANALYSIS SUMMARY", "=" * 80]
        
        # Severity breakdown with details
        severity_counts = Counter(diag.severity for diag in diagnostics)
        summary_lines.append("🎯 Severity Distribution:")
        for severity in [EnhancedSeverity.CRITICAL, EnhancedSeverity.MAJOR, 
                        EnhancedSeverity.MINOR, EnhancedSeverity.INFO]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                icon = EnhancedSeverity.SEVERITY_ICONS[severity]
                percentage = (count / len(diagnostics)) * 100
                summary_lines.append(f"   {icon} {severity}: {count} ({percentage:.1f}%)")
        
        # Function-level analysis
        function_errors = defaultdict(list)
        for diag in diagnostics:
            if diag.function_name != "unknown":
                function_errors[diag.function_name].append(diag)
        
        if function_errors:
            summary_lines.append("")
            summary_lines.append("🔧 Functions with Most Errors:")
            sorted_functions = sorted(function_errors.items(), 
                                    key=lambda x: len(x[1]), reverse=True)
            for i, (func_name, func_diags) in enumerate(sorted_functions[:10], 1):
                critical_count = sum(1 for d in func_diags if d.severity == EnhancedSeverity.CRITICAL)
                major_count = sum(1 for d in func_diags if d.severity == EnhancedSeverity.MAJOR)
                severity_info = ""
                if critical_count > 0:
                    severity_info += f" (⚠️{critical_count})"
                if major_count > 0:
                    severity_info += f" (👉{major_count})"
                
                summary_lines.append(f"   {i}. {func_name}: {len(func_diags)} errors{severity_info}")
        
        # File-level analysis
        file_errors = defaultdict(list)
        for diag in diagnostics:
            file_name = os.path.basename(diag.file_path)
            file_errors[file_name].append(diag)
        
        if file_errors:
            summary_lines.append("")
            summary_lines.append("📁 Files with Most Errors:")
            sorted_files = sorted(file_errors.items(), 
                                key=lambda x: len(x[1]), reverse=True)
            for i, (file_name, file_diags) in enumerate(sorted_files[:10], 1):
                critical_count = sum(1 for d in file_diags if d.severity == EnhancedSeverity.CRITICAL)
                severity_info = f" (⚠️{critical_count})" if critical_count > 0 else ""
                summary_lines.append(f"   {i}. {file_name}: {len(file_diags)} errors{severity_info}")
        
        # Error type analysis
        error_types = Counter()
        for diag in diagnostics:
            if diag.code and diag.code != '':
                error_types[diag.code] += 1
        
        if error_types:
            summary_lines.append("")
            summary_lines.append("🏷️  Most Common Error Types:")
            for i, (error_type, count) in enumerate(error_types.most_common(10), 1):
                summary_lines.append(f"   {i}. {error_type}: {count} occurrences")
        
        # Business impact analysis
        impact_analysis = self._analyze_business_impact(diagnostics)
        if impact_analysis:
            summary_lines.append("")
            summary_lines.append("💼 Business Impact Analysis:")
            summary_lines.extend(impact_analysis)
        
        summary_lines.append("=" * 80)
        return summary_lines
    
    def _analyze_business_impact(self, diagnostics: List[EnhancedDiagnostic]) -> List[str]:
        """Analyze business impact of the diagnostics."""
        impact_lines = []
        
        # Calculate total impact score
        total_impact = sum(EnhancedSeverity.IMPACT_SCORES.get(diag.severity, 1) 
                          for diag in diagnostics)
        
        # Categorize impact level
        if total_impact > 100:
            impact_level = "🔴 HIGH"
        elif total_impact > 50:
            impact_level = "🟡 MEDIUM"
        else:
            impact_level = "🟢 LOW"
        
        impact_lines.append(f"   Overall Impact Level: {impact_level} (Score: {total_impact})")
        
        # Critical issues requiring immediate attention
        critical_issues = [d for d in diagnostics if d.severity == EnhancedSeverity.CRITICAL]
        if critical_issues:
            impact_lines.append(f"   🚨 {len(critical_issues)} critical issues require immediate attention")
        
        # Security-related issues
        security_issues = [d for d in diagnostics 
                          if any(keyword in d.message.lower() 
                                for keyword in ['security', 'vulnerability', 'injection', 'unsafe'])]
        if security_issues:
            impact_lines.append(f"   🔒 {len(security_issues)} potential security issues detected")
        
        # Performance-related issues
        performance_issues = [d for d in diagnostics 
                            if any(keyword in d.message.lower() 
                                  for keyword in ['performance', 'slow', 'memory', 'timeout'])]
        if performance_issues:
            impact_lines.append(f"   ⚡ {len(performance_issues)} performance-related issues found")
        
        return impact_lines
    
    def format_json_output(self, diagnostics: List[EnhancedDiagnostic], 
                          project_name: str = "project",
                          performance_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format diagnostics as enhanced JSON output with comprehensive metadata.
        
        Args:
            diagnostics: List of enhanced diagnostics
            project_name: Name of the project
            performance_stats: Performance statistics
            
        Returns:
            Comprehensive JSON structure with enhanced analysis
        """
        # Count diagnostics by severity
        severity_counts = Counter(diag.severity for diag in diagnostics)
        
        # Analyze functions and files
        function_analysis = defaultdict(list)
        file_analysis = defaultdict(list)
        
        for diag in diagnostics:
            if diag.function_name != "unknown":
                function_analysis[diag.function_name].append(diag)
            file_analysis[os.path.basename(diag.file_path)].append(diag)
        
        # Convert diagnostics to dictionaries
        diagnostics_data = []
        for i, diag in enumerate(diagnostics, 1):
            diag_dict = asdict(diag)
            diag_dict['index'] = i
            diag_dict['severity_icon'] = EnhancedSeverity.SEVERITY_ICONS.get(diag.severity, "❓")
            diagnostics_data.append(diag_dict)
        
        # Build comprehensive JSON structure
        result = {
            "summary": {
                "total_errors": len(diagnostics),
                "project_name": project_name,
                "severity_breakdown": {
                    "critical": severity_counts.get(EnhancedSeverity.CRITICAL, 0),
                    "major": severity_counts.get(EnhancedSeverity.MAJOR, 0),
                    "minor": severity_counts.get(EnhancedSeverity.MINOR, 0),
                    "info": severity_counts.get(EnhancedSeverity.INFO, 0)
                },
                "business_impact": {
                    "total_score": sum(EnhancedSeverity.IMPACT_SCORES.get(diag.severity, 1) 
                                     for diag in diagnostics),
                    "impact_level": self._calculate_impact_level(diagnostics)
                }
            },
            "diagnostics": diagnostics_data,
            "analysis": {
                "functions_with_errors": {
                    func_name: {
                        "error_count": len(func_diags),
                        "severity_breakdown": Counter(d.severity for d in func_diags)
                    }
                    for func_name, func_diags in function_analysis.items()
                },
                "files_with_errors": {
                    file_name: {
                        "error_count": len(file_diags),
                        "severity_breakdown": Counter(d.severity for d in file_diags)
                    }
                    for file_name, file_diags in file_analysis.items()
                },
                "error_types": dict(Counter(diag.code for diag in diagnostics if diag.code))
            }
        }
        
        if performance_stats:
            result["performance"] = performance_stats
        
        return result
    
    def _calculate_impact_level(self, diagnostics: List[EnhancedDiagnostic]) -> str:
        """Calculate overall business impact level."""
        total_impact = sum(EnhancedSeverity.IMPACT_SCORES.get(diag.severity, 1) 
                          for diag in diagnostics)
        
        if total_impact > 100:
            return "HIGH"
        elif total_impact > 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    def format_compact_output(self, diagnostics: List[EnhancedDiagnostic]) -> str:
        """
        Format diagnostics in a compact summary format for quick overview.
        
        Returns:
            Compact summary string
        """
        if not diagnostics:
            return "✅ No errors found"
        
        severity_counts = Counter(diag.severity for diag in diagnostics)
        total = len(diagnostics)
        
        # Create compact summary
        parts = []
        if severity_counts.get(EnhancedSeverity.CRITICAL, 0) > 0:
            parts.append(f"⚠️{severity_counts[EnhancedSeverity.CRITICAL]}")
        if severity_counts.get(EnhancedSeverity.MAJOR, 0) > 0:
            parts.append(f"👉{severity_counts[EnhancedSeverity.MAJOR]}")
        if severity_counts.get(EnhancedSeverity.MINOR, 0) > 0:
            parts.append(f"🔍{severity_counts[EnhancedSeverity.MINOR]}")
        
        summary = f"🔍 {total} errors: {' '.join(parts)}"
        
        # Add top error types
        error_types = Counter(diag.code for diag in diagnostics if diag.code)
        if error_types:
            top_error = error_types.most_common(1)[0]
            summary += f" | Top: {top_error[0]} ({top_error[1]}x)"
        
        return summary
