"""
Main repository analyzer that orchestrates all analysis components.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
import math
import re

from codegen import Codebase
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression

from .models import (
    RepositoryAnalysisRequest, RepositoryAnalysisResponse,
    LineMetrics, ComplexityMetrics, HalsteadMetrics, 
    MaintainabilityMetrics, InheritanceMetrics, AnalysisError
)
from .repository_handler import RepositoryHandler
from .solidlsp_integration import SolidLSPAnalyzer
from .language_detection import detect_repository_languages

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Main analyzer that combines traditional metrics with SolidLSP runtime error detection."""
    
    def __init__(self):
        self.analysis_errors: List[AnalysisError] = []
    
    def _add_error(self, component: str, error_type: str, message: str, file_path: Optional[str] = None):
        """Add an analysis error to the error list."""
        error = AnalysisError(
            component=component,
            error_type=error_type,
            message=message,
            file_path=file_path
        )
        self.analysis_errors.append(error)
        logger.error(f"Analysis error in {component}: {message}")
    
    def calculate_cyclomatic_complexity(self, function) -> int:
        """Calculate cyclomatic complexity for a function."""
        def analyze_statement(statement):
            complexity = 0

            if isinstance(statement, IfBlockStatement):
                complexity += 1
                if hasattr(statement, "elif_statements"):
                    complexity += len(statement.elif_statements)

            elif isinstance(statement, (ForLoopStatement, WhileStatement)):
                complexity += 1

            elif isinstance(statement, TryCatchStatement):
                complexity += len(getattr(statement, "except_blocks", []))

            if hasattr(statement, "condition") and isinstance(statement.condition, str):
                complexity += statement.condition.count(" and ") + statement.condition.count(" or ")

            if hasattr(statement, "nested_code_blocks"):
                for block in statement.nested_code_blocks:
                    complexity += analyze_block(block)

            return complexity

        def analyze_block(block):
            if not block or not hasattr(block, "statements"):
                return 0
            return sum(analyze_statement(stmt) for stmt in block.statements)

        return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1
    
    def cc_rank(self, complexity: int) -> str:
        """Convert cyclomatic complexity to a letter rank."""
        if complexity < 0:
            return "F"

        ranks = [
            (1, 5, "A"),
            (6, 10, "B"),
            (11, 20, "C"),
            (21, 30, "D"),
            (31, 40, "E"),
            (41, float("inf"), "F"),
        ]
        for low, high, rank in ranks:
            if low <= complexity <= high:
                return rank
        return "F"
    
    def calculate_doi(self, cls) -> int:
        """Calculate the depth of inheritance for a given class."""
        return len(cls.superclasses) if hasattr(cls, 'superclasses') else 0
    
    def get_operators_and_operands(self, function):
        """Extract operators and operands from a function."""
        operators = []
        operands = []

        if not hasattr(function, 'code_block') or not hasattr(function.code_block, 'statements'):
            return operators, operands

        for statement in function.code_block.statements:
            # Handle function calls
            if hasattr(statement, 'function_calls'):
                for call in statement.function_calls:
                    operators.append(call.name)
                    for arg in call.args:
                        operands.append(arg.source)

            # Handle expressions
            if hasattr(statement, "expressions"):
                for expr in statement.expressions:
                    if isinstance(expr, BinaryExpression):
                        operators.extend([op.source for op in expr.operators])
                        operands.extend([elem.source for elem in expr.elements])
                    elif isinstance(expr, UnaryExpression):
                        operators.append(expr.ts_node.type)
                        operands.append(expr.argument.source)
                    elif isinstance(expr, ComparisonExpression):
                        operators.extend([op.source for op in expr.operators])
                        operands.extend([elem.source for elem in expr.elements])

            if hasattr(statement, "expression"):
                expr = statement.expression
                if isinstance(expr, BinaryExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
                elif isinstance(expr, UnaryExpression):
                    operators.append(expr.ts_node.type)
                    operands.append(expr.argument.source)
                elif isinstance(expr, ComparisonExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])

        return operators, operands
    
    def calculate_halstead_volume(self, operators, operands):
        """Calculate Halstead volume metrics."""
        n1 = len(set(operators))
        n2 = len(set(operands))
        N1 = len(operators)
        N2 = len(operands)
        N = N1 + N2
        n = n1 + n2

        if n > 0:
            volume = N * math.log2(n)
            return volume, N1, N2, n1, n2
        return 0, N1, N2, n1, n2
    
    def count_lines(self, source: str):
        """Count different types of lines in source code."""
        if not source.strip():
            return 0, 0, 0, 0

        lines = [line.strip() for line in source.splitlines()]
        loc = len(lines)
        sloc = len([line for line in lines if line])

        in_multiline = False
        comments = 0
        code_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            code_part = line
            if not in_multiline and "#" in line:
                comment_start = line.find("#")
                if not re.search(r'["\'].*#.*["\']', line[:comment_start]):
                    code_part = line[:comment_start].strip()
                    if line[comment_start:].strip():
                        comments += 1

            if ('"""' in line or "'''" in line) and not (
                line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0
            ):
                if in_multiline:
                    in_multiline = False
                    comments += 1
                else:
                    in_multiline = True
                    comments += 1
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        code_part = ""
            elif in_multiline:
                comments += 1
                code_part = ""
            elif line.strip().startswith("#"):
                comments += 1
                code_part = ""

            if code_part.strip():
                code_lines.append(code_part)

            i += 1

        lloc = 0
        continued_line = False
        for line in code_lines:
            if continued_line:
                if not any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                    continued_line = False
                continue

            lloc += len([stmt for stmt in line.split(";") if stmt.strip()])

            if any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                continued_line = True

        return loc, lloc, sloc, comments
    
    def calculate_maintainability_index(self, halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
        """Calculate the normalized maintainability index for a given function."""
        if loc <= 0:
            return 100

        try:
            raw_mi = (
                171
                - 5.2 * math.log(max(1, halstead_volume))
                - 0.23 * cyclomatic_complexity
                - 16.2 * math.log(max(1, loc))
            )
            normalized_mi = max(0, min(100, raw_mi * 100 / 171))
            return int(normalized_mi)
        except (ValueError, TypeError):
            return 0
    
    def get_maintainability_rank(self, mi_score: float) -> str:
        """Convert maintainability index score to a letter grade."""
        if mi_score >= 85:
            return "A"
        elif mi_score >= 65:
            return "B"
        elif mi_score >= 45:
            return "C"
        elif mi_score >= 25:
            return "D"
        else:
            return "F"
    
    def analyze_traditional_metrics(self, codebase: Codebase) -> tuple:
        """Analyze traditional code metrics using the codegen SDK."""
        try:
            num_files = len(codebase.files(extensions="*"))
            num_functions = len(codebase.functions)
            num_classes = len(codebase.classes)

            total_loc = total_lloc = total_sloc = total_comments = 0
            total_complexity = 0
            total_volume = 0
            total_mi = 0
            total_doi = 0

            # Analyze files for line metrics
            for file in codebase.files:
                try:
                    loc, lloc, sloc, comments = self.count_lines(file.source)
                    total_loc += loc
                    total_lloc += lloc
                    total_sloc += sloc
                    total_comments += comments
                except Exception as e:
                    self._add_error("line_analysis", "count_error", str(e), file.path)

            # Analyze functions and methods
            callables = codebase.functions + [m for c in codebase.classes for m in c.methods]
            num_callables = 0
            
            for func in callables:
                try:
                    if not hasattr(func, "code_block"):
                        continue

                    complexity = self.calculate_cyclomatic_complexity(func)
                    operators, operands = self.get_operators_and_operands(func)
                    volume, _, _, _, _ = self.calculate_halstead_volume(operators, operands)
                    loc = len(func.code_block.source.splitlines()) if hasattr(func.code_block, 'source') else 0
                    mi_score = self.calculate_maintainability_index(volume, complexity, loc)

                    total_complexity += complexity
                    total_volume += volume
                    total_mi += mi_score
                    num_callables += 1
                except Exception as e:
                    self._add_error("function_analysis", "metric_error", str(e), getattr(func, 'path', None))

            # Analyze classes for inheritance depth
            for cls in codebase.classes:
                try:
                    doi = self.calculate_doi(cls)
                    total_doi += doi
                except Exception as e:
                    self._add_error("class_analysis", "inheritance_error", str(e), getattr(cls, 'path', None))

            # Create metrics objects
            line_metrics = LineMetrics(
                loc=total_loc,
                lloc=total_lloc,
                sloc=total_sloc,
                comments=total_comments,
                comment_density=(total_comments / total_loc * 100) if total_loc > 0 else 0
            )

            avg_complexity = total_complexity / num_callables if num_callables > 0 else 0
            complexity_metrics = ComplexityMetrics(
                average_cyclomatic_complexity=avg_complexity,
                complexity_rank=self.cc_rank(avg_complexity),
                functions_analyzed=num_callables
            )

            halstead_metrics = HalsteadMetrics(
                total_volume=int(total_volume),
                average_volume=int(total_volume / num_callables) if num_callables > 0 else 0,
                functions_analyzed=num_callables
            )

            avg_mi = total_mi / num_callables if num_callables > 0 else 0
            maintainability_metrics = MaintainabilityMetrics(
                average_index=int(avg_mi),
                maintainability_rank=self.get_maintainability_rank(avg_mi),
                functions_analyzed=num_callables
            )

            inheritance_metrics = InheritanceMetrics(
                average_depth=total_doi / len(codebase.classes) if codebase.classes else 0,
                classes_analyzed=len(codebase.classes)
            )

            return (
                num_files, num_functions, num_classes,
                line_metrics, complexity_metrics, halstead_metrics,
                maintainability_metrics, inheritance_metrics
            )

        except Exception as e:
            self._add_error("traditional_metrics", "general_error", str(e))
            # Return default values
            return (
                0, 0, 0,
                LineMetrics(loc=0, lloc=0, sloc=0, comments=0, comment_density=0),
                ComplexityMetrics(average_cyclomatic_complexity=0, complexity_rank="F", functions_analyzed=0),
                HalsteadMetrics(total_volume=0, average_volume=0, functions_analyzed=0),
                MaintainabilityMetrics(average_index=0, maintainability_rank="F", functions_analyzed=0),
                InheritanceMetrics(average_depth=0, classes_analyzed=0)
            )
    
    def analyze_repository(self, request: RepositoryAnalysisRequest) -> RepositoryAnalysisResponse:
        """
        Perform complete repository analysis including traditional metrics and runtime errors.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Complete analysis response
        """
        start_time = time.time()
        self.analysis_errors.clear()
        
        logger.info(f"Starting analysis of repository: {request.repo_url}")
        
        with RepositoryHandler() as repo_handler:
            try:
                # Parse repository URL and get info
                owner, repo_name = repo_handler.parse_repo_url(request.repo_url)
                repo_info = repo_handler.get_github_repo_info(owner, repo_name)
                
                # Clone repository
                repo_path = repo_handler.clone_repository(request.repo_url)
                
                # Detect languages
                detected_languages = detect_repository_languages(repo_path)
                languages_list = list(detected_languages.keys())
                
                logger.info(f"Detected languages: {languages_list}")
                
                # Analyze traditional metrics using codegen SDK
                try:
                    codebase = Codebase.from_repo(request.repo_url)
                    (num_files, num_functions, num_classes, line_metrics, 
                     complexity_metrics, halstead_metrics, maintainability_metrics, 
                     inheritance_metrics) = self.analyze_traditional_metrics(codebase)
                except Exception as e:
                    self._add_error("codegen_sdk", "initialization_error", str(e))
                    # Use default values
                    num_files = num_functions = num_classes = 0
                    line_metrics = LineMetrics(loc=0, lloc=0, sloc=0, comments=0, comment_density=0)
                    complexity_metrics = ComplexityMetrics(average_cyclomatic_complexity=0, complexity_rank="F", functions_analyzed=0)
                    halstead_metrics = HalsteadMetrics(total_volume=0, average_volume=0, functions_analyzed=0)
                    maintainability_metrics = MaintainabilityMetrics(average_index=0, maintainability_rank="F", functions_analyzed=0)
                    inheritance_metrics = InheritanceMetrics(average_depth=0, classes_analyzed=0)
                
                # Analyze runtime errors using SolidLSP
                runtime_error_summary = None
                if request.include_runtime_errors:
                    try:
                        with SolidLSPAnalyzer() as lsp_analyzer:
                            runtime_error_summary = lsp_analyzer.analyze_repository(
                                repo_path, 
                                max_files=request.max_files
                            )
                    except Exception as e:
                        self._add_error("solidlsp", "analysis_error", str(e))
                        # Create empty summary
                        from .models import RuntimeErrorSummary
                        runtime_error_summary = RuntimeErrorSummary()
                else:
                    from .models import RuntimeErrorSummary
                    runtime_error_summary = RuntimeErrorSummary()
                
                # Get monthly commits
                monthly_commits = {}
                try:
                    monthly_commits = repo_handler.get_monthly_commits(repo_path, owner, repo_name)
                except Exception as e:
                    self._add_error("git_analysis", "commit_history_error", str(e))
                
                # Calculate analysis duration
                analysis_duration = time.time() - start_time
                
                # Create response
                response = RepositoryAnalysisResponse(
                    repo_url=request.repo_url,
                    description=repo_info.get('description', 'No description available'),
                    analysis_timestamp=datetime.now().isoformat(),
                    num_files=num_files,
                    num_functions=num_functions,
                    num_classes=num_classes,
                    line_metrics=line_metrics,
                    complexity_metrics=complexity_metrics,
                    halstead_metrics=halstead_metrics,
                    maintainability_metrics=maintainability_metrics,
                    inheritance_metrics=inheritance_metrics,
                    runtime_error_summary=runtime_error_summary,
                    monthly_commits=monthly_commits,
                    analysis_duration_seconds=round(analysis_duration, 2),
                    languages_detected=languages_list,
                    analysis_errors=[error.model_dump() for error in self.analysis_errors]
                )
                
                logger.info(f"Analysis completed in {analysis_duration:.2f} seconds")
                return response
                
            except Exception as e:
                self._add_error("general", "fatal_error", str(e))
                logger.error(f"Fatal error during analysis: {e}")
                
                # Return minimal response with error information
                analysis_duration = time.time() - start_time
                from .models import RuntimeErrorSummary
                
                return RepositoryAnalysisResponse(
                    repo_url=request.repo_url,
                    description="Analysis failed",
                    analysis_timestamp=datetime.now().isoformat(),
                    num_files=0,
                    num_functions=0,
                    num_classes=0,
                    line_metrics=LineMetrics(loc=0, lloc=0, sloc=0, comments=0, comment_density=0),
                    complexity_metrics=ComplexityMetrics(average_cyclomatic_complexity=0, complexity_rank="F", functions_analyzed=0),
                    halstead_metrics=HalsteadMetrics(total_volume=0, average_volume=0, functions_analyzed=0),
                    maintainability_metrics=MaintainabilityMetrics(average_index=0, maintainability_rank="F", functions_analyzed=0),
                    inheritance_metrics=InheritanceMetrics(average_depth=0, classes_analyzed=0),
                    runtime_error_summary=RuntimeErrorSummary(),
                    monthly_commits={},
                    analysis_duration_seconds=round(analysis_duration, 2),
                    languages_detected=[],
                    analysis_errors=[error.model_dump() for error in self.analysis_errors]
                )

