"""
Data models for the upgraded analytics system.
"""

from enum import IntEnum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DiagnosticSeverity(IntEnum):
    """Diagnostic severity levels from LSP."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class Position(BaseModel):
    """Position in a text document."""
    line: int = Field(..., description="Line position (zero-based)")
    character: int = Field(..., description="Character position (zero-based)")


class Range(BaseModel):
    """Range in a text document."""
    start: Position
    end: Position


class RuntimeError(BaseModel):
    """Runtime error detected by SolidLSP."""
    file_path: str = Field(..., description="Relative path to the file")
    severity: DiagnosticSeverity = Field(..., description="Error severity level")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    source: Optional[str] = Field(None, description="Source of the diagnostic")
    range: Range = Field(..., description="Location of the error in the file")
    line_content: Optional[str] = Field(None, description="Content of the line with the error")


class FileErrorSummary(BaseModel):
    """Summary of errors for a single file."""
    file_path: str
    total_errors: int = 0
    errors: int = 0
    warnings: int = 0
    information: int = 0
    hints: int = 0
    runtime_errors: List[RuntimeError] = Field(default_factory=list)


class LanguageErrorSummary(BaseModel):
    """Summary of errors for a programming language."""
    language: str
    total_files: int = 0
    files_with_errors: int = 0
    total_errors: int = 0
    errors: int = 0
    warnings: int = 0
    information: int = 0
    hints: int = 0


class LineMetrics(BaseModel):
    """Line-based code metrics."""
    loc: int = Field(..., description="Lines of code")
    lloc: int = Field(..., description="Logical lines of code")
    sloc: int = Field(..., description="Source lines of code")
    comments: int = Field(..., description="Comment lines")
    comment_density: float = Field(..., description="Comment density percentage")


class ComplexityMetrics(BaseModel):
    """Code complexity metrics."""
    average_cyclomatic_complexity: float = Field(..., description="Average cyclomatic complexity")
    complexity_rank: str = Field(..., description="Complexity rank (A-F)")
    functions_analyzed: int = Field(..., description="Number of functions analyzed")


class HalsteadMetrics(BaseModel):
    """Halstead complexity metrics."""
    total_volume: int = Field(..., description="Total Halstead volume")
    average_volume: int = Field(..., description="Average Halstead volume per function")
    functions_analyzed: int = Field(..., description="Number of functions analyzed")


class MaintainabilityMetrics(BaseModel):
    """Code maintainability metrics."""
    average_index: int = Field(..., description="Average maintainability index")
    maintainability_rank: str = Field(..., description="Maintainability rank (A-F)")
    functions_analyzed: int = Field(..., description="Number of functions analyzed")


class InheritanceMetrics(BaseModel):
    """Inheritance-related metrics."""
    average_depth: float = Field(..., description="Average depth of inheritance")
    classes_analyzed: int = Field(..., description="Number of classes analyzed")


class RuntimeErrorSummary(BaseModel):
    """Summary of runtime errors detected by SolidLSP."""
    total_files_analyzed: int = 0
    files_with_errors: int = 0
    total_errors: int = 0
    errors: int = 0
    warnings: int = 0
    information: int = 0
    hints: int = 0
    languages_analyzed: List[str] = Field(default_factory=list)
    language_summaries: Dict[str, LanguageErrorSummary] = Field(default_factory=dict)
    file_summaries: List[FileErrorSummary] = Field(default_factory=list)


class RepositoryAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="GitHub repository URL (e.g., 'owner/repo')")
    include_runtime_errors: bool = Field(True, description="Whether to include runtime error analysis")
    languages: Optional[List[str]] = Field(None, description="Specific languages to analyze (if None, auto-detect)")
    max_files: Optional[int] = Field(None, description="Maximum number of files to analyze")


class RepositoryAnalysisResponse(BaseModel):
    """Complete repository analysis response."""
    repo_url: str
    description: str
    analysis_timestamp: str
    
    # Basic repository metrics
    num_files: int
    num_functions: int
    num_classes: int
    
    # Traditional code metrics
    line_metrics: LineMetrics
    complexity_metrics: ComplexityMetrics
    halstead_metrics: HalsteadMetrics
    maintainability_metrics: MaintainabilityMetrics
    inheritance_metrics: InheritanceMetrics
    
    # Runtime error analysis (new)
    runtime_error_summary: RuntimeErrorSummary
    
    # Git activity metrics
    monthly_commits: Dict[str, int] = Field(default_factory=dict)
    
    # Analysis metadata
    analysis_duration_seconds: float
    languages_detected: List[str] = Field(default_factory=list)
    analysis_errors: List[str] = Field(default_factory=list)


class AnalysisError(BaseModel):
    """Error that occurred during analysis."""
    component: str = Field(..., description="Component where error occurred")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    file_path: Optional[str] = Field(None, description="File path if applicable")

