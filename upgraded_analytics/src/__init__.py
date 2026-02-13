"""
Repository Analytics with SolidLSP Integration

A comprehensive repository analysis tool that combines traditional code quality metrics
with runtime error detection using Serena's SolidLSP implementation.
"""

__version__ = "2.0.0"
__author__ = "Repository Analytics Team"
__description__ = "Advanced repository analysis with SolidLSP integration"

from .models import (
    RepositoryAnalysisRequest,
    RepositoryAnalysisResponse,
    RuntimeError,
    DiagnosticSeverity,
)

from .analyzer import RepositoryAnalyzer
from .solidlsp_integration import SolidLSPAnalyzer
from .language_detection import detect_repository_languages, get_primary_language

__all__ = [
    "RepositoryAnalysisRequest",
    "RepositoryAnalysisResponse", 
    "RuntimeError",
    "DiagnosticSeverity",
    "RepositoryAnalyzer",
    "SolidLSPAnalyzer",
    "detect_repository_languages",
    "get_primary_language",
]

