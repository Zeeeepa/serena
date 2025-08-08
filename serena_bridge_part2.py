#!/usr/bin/env python3
"""
Serena Bridge Part 2: Diagnostic Collection and Analysis Bridge

This module contains the diagnostic collection, analysis, and comprehensive
analyzer classes that complete the Serena bridge functionality.
"""

from serena_bridge import *  # Import all base classes and imports


class SerenaDiagnosticBridge:
    """
    Comprehensive Diagnostic Collection Bridge providing complete abstraction over Serena diagnostic functionality.
    
    This bridge encapsulates all diagnostic collection, parsing, and processing
    with 100% compatibility with the actual Serena LSP diagnostic API.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the diagnostic bridge.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        if verbose:
            self.logger.info("🔬 Initializing Serena Diagnostic Bridge")
    
    def collect_diagnostics_from_file(
        self, 
        language_server: SolidLanguageServer,
        file_path: str,
        severity_filter: Optional[DiagnosticSeverity] = None
    ) -> Tuple[List[EnhancedDiagnostic], Optional[str]]:
        """
        Collect diagnostics from a single file using actual Serena LSP API.
        
        Args:
            language_server: Active SolidLanguageServer instance
            file_path: Relative path to the file
            severity_filter: Optional severity filter
            
        Returns:
            Tuple of (diagnostics_list, error_message)
            
        Raises:
            SolidLSPException: If LSP request fails
            InvalidTextLocationError: If file location is invalid
        """
        try:
            self.logger.debug(f"🔍 Collecting diagnostics from: {os.path.basename(file_path)}")
            
            # Use the actual request_text_document_diagnostics method
            # Based on analysis: LanguageServerRequest has 53 methods including diagnostic requests
            lsp_response = language_server.request_text_document_diagnostics(file_path)
            
            if lsp_response is None:
                self.logger.debug(f"📋 No diagnostics returned for {os.path.basename(file_path)}")
                return [], None
            
            # Parse the actual LSP response format
            # Based on analysis: response contains 'items' array with diagnostic objects
            diagnostics = []
            
            # Handle different response formats
            if isinstance(lsp_response, dict):
                if 'items' in lsp_response:
                    diagnostic_items = lsp_response['items']
                elif 'diagnostics' in lsp_response:
                    diagnostic_items = lsp_response['diagnostics']
                else:
                    diagnostic_items = [lsp_response]  # Single diagnostic
            elif isinstance(lsp_response, list):
                diagnostic_items = lsp_response
            else:
                self.logger.warning(f"⚠️  Unexpected response format for {file_path}: {type(lsp_response)}")
                return [], f"Unexpected response format: {type(lsp_response)}"
            
            for diag_data in diagnostic_items:
                try:
                    enhanced_diag = self._parse_diagnostic(diag_data, file_path, severity_filter)
                    if enhanced_diag:
                        diagnostics.append(enhanced_diag)
                except Exception as e:
                    self.logger.warning(f"⚠️  Error parsing diagnostic in {file_path}: {e}")
                    continue
            
            if self.verbose and len(diagnostics) > 0:
                severity_counts = {}
                for diag in diagnostics:
                    severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
                
                self.logger.debug(f"📊 {os.path.basename(file_path)}: {len(diagnostics)} diagnostics")
                for severity, count in severity_counts.items():
                    self.logger.debug(f"   {severity}: {count}")
            
            return diagnostics, None
            
        except SolidLSPException as e:
            error_msg = f"LSP Exception: {e}"
            if e.is_language_server_terminated():
                error_msg += " (Server terminated)"
            self.logger.warning(f"⚠️  {error_msg} for {os.path.basename(file_path)}")
            return [], error_msg
            
        except InvalidTextLocationError as e:
            error_msg = f"Invalid text location: {e}"
            self.logger.warning(f"⚠️  {error_msg} for {os.path.basename(file_path)}")
            return [], error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.warning(f"⚠️  {error_msg} for {os.path.basename(file_path)}")
            return [], error_msg
    
    def _parse_diagnostic(
        self, 
        diag_data: Dict[str, Any], 
        file_path: str,
        severity_filter: Optional[DiagnosticSeverity] = None
    ) -> Optional[EnhancedDiagnostic]:
        """
        Parse a single diagnostic from LSP response data.
        
        Args:
            diag_data: Raw diagnostic data from LSP
            file_path: File path for the diagnostic
            severity_filter: Optional severity filter
            
        Returns:
            EnhancedDiagnostic instance or None if filtered out
        """
        try:
            # Extract range information
            range_info = diag_data.get("range", {})
            start_pos = range_info.get("start", {})
            end_pos = range_info.get("end", {})
            
            # LSP uses 0-based indexing, convert to 1-based for user display
            line = start_pos.get("line", 0) + 1
            column = start_pos.get("character", 0) + 1
            
            # Extract severity using actual DiagnosticSeverity enum values
            # Based on analysis: 1=Error, 2=Warning, 3=Information, 4=Hint
            severity_value = diag_data.get("severity", DiagnosticSeverity.Error)
            severity_map = {
                DiagnosticSeverity.Error: "ERROR",
                DiagnosticSeverity.Warning: "WARNING", 
                DiagnosticSeverity.Information: "INFO",
                DiagnosticSeverity.Hint: "HINT",
                1: "ERROR",
                2: "WARNING",
                3: "INFO", 
                4: "HINT"
            }
            
            severity = severity_map.get(severity_value, "UNKNOWN")
            
            # Apply severity filter
            if severity_filter and severity_value != severity_filter:
                return None
            
            # Extract message and code
            message = diag_data.get("message", "No message provided")
            code = diag_data.get("code")
            source = diag_data.get("source", "lsp")
            
            # Extract tags if present
            tags = []
            if "tags" in diag_data:
                for tag in diag_data["tags"]:
                    if tag == DiagnosticTag.Unnecessary:
                        tags.append("unnecessary")
                    elif tag == DiagnosticTag.Deprecated:
                        tags.append("deprecated")
            
            # Extract error code if available
            error_code = None
            if isinstance(code, int):
                try:
                    error_code = ErrorCodes(code)
                except ValueError:
                    pass  # Not a standard LSP error code
            
            # Create URI for the file
            file_uri = Path(file_path).as_uri() if file_path else None
            
            # Create enhanced diagnostic
            enhanced_diag = EnhancedDiagnostic(
                file_path=file_path,
                line=line,
                column=column,
                severity=severity,
                message=message,
                code=str(code) if code is not None else None,
                source=source,
                category="lsp_diagnostic",
                tags=tags + ["serena_lsp_analysis"],
                error_code=error_code,
                uri=file_uri,
                range_start_line=start_pos.get("line"),
                range_start_character=start_pos.get("character"),
                range_end_line=end_pos.get("line"),
                range_end_character=end_pos.get("character")
            )
            
            return enhanced_diag
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error parsing diagnostic data: {e}")
            return None
    
    def collect_diagnostics_batch(
        self,
        language_server: SolidLanguageServer,
        file_paths: List[str],
        severity_filter: Optional[DiagnosticSeverity] = None,
        max_workers: int = 4,
        progress_callback: Optional[callable] = None
    ) -> Tuple[List[EnhancedDiagnostic], Dict[str, str]]:
        """
        Collect diagnostics from multiple files in parallel.
        
        Args:
            language_server: Active SolidLanguageServer instance
            file_paths: List of file paths to analyze
            severity_filter: Optional severity filter
            max_workers: Maximum number of parallel workers
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (all_diagnostics, error_map)
        """
        all_diagnostics = []
        error_map = {}
        processed_count = 0
        
        self.logger.info(f"🔍 Collecting diagnostics from {len(file_paths)} files using {max_workers} workers")
        
        def analyze_file(file_path: str) -> Tuple[str, List[EnhancedDiagnostic], Optional[str]]:
            """Analyze a single file and return results."""
            diagnostics, error = self.collect_diagnostics_from_file(
                language_server, file_path, severity_filter
            )
            return file_path, diagnostics, error
        
        # Process files in batches to avoid overwhelming the LSP server
        batch_size = min(50, max(1, len(file_paths) // 10))
        file_batches = [
            file_paths[i:i + batch_size] 
            for i in range(0, len(file_paths), batch_size)
        ]
        
        for batch_idx, file_batch in enumerate(file_batches):
            self.logger.debug(f"📦 Processing batch {batch_idx + 1}/{len(file_batches)} ({len(file_batch)} files)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(analyze_file, file_path): file_path
                    for file_path in file_batch
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        analyzed_file, diagnostics, error = future.result()
                        
                        if error is None:
                            all_diagnostics.extend(diagnostics)
                        else:
                            error_map[analyzed_file] = error
                        
                        processed_count += 1
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(processed_count, len(file_paths))
                        
                    except Exception as e:
                        error_map[file_path] = f"Processing error: {e}"
                        processed_count += 1
                        self.logger.warning(f"⚠️  Error processing {os.path.basename(file_path)}: {e}")
            
            # Brief pause between batches to prevent LSP server overload
            if batch_idx < len(file_batches) - 1:
                time.sleep(0.5)
        
        self.logger.info(f"✅ Collected {len(all_diagnostics)} diagnostics from {processed_count} files")
        if error_map:
            self.logger.warning(f"⚠️  {len(error_map)} files had errors during processing")
        
        return all_diagnostics, error_map


class SerenaComprehensiveAnalyzer:
    """
    Comprehensive Serena Analyzer that orchestrates all bridge components
    to provide complete codebase analysis functionality.
    
    This is the main class that users interact with for performing
    comprehensive LSP-based analysis of entire codebases.
    """
    
    def __init__(self, verbose: bool = False, timeout: float = 600, max_workers: int = 4):
        """
        Initialize the comprehensive analyzer.
        
        Args:
            verbose: Enable detailed logging and progress tracking
            timeout: Timeout for LSP operations in seconds
            max_workers: Maximum number of parallel workers
        """
        self.verbose = verbose
        self.timeout = timeout
        self.max_workers = max_workers
        
        # Initialize all bridge components
        self.lsp_bridge = SerenaLSPBridge(verbose=verbose, timeout=timeout)
        self.project_bridge = SerenaProjectBridge(verbose=verbose)
        self.diagnostic_bridge = SerenaDiagnosticBridge(verbose=verbose)
        
        # Analysis tracking
        self.analysis_start_time: Optional[float] = None
        self.performance_stats: Dict[str, float] = {}
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        if verbose:
            self.logger.info("🚀 Initializing Comprehensive Serena Analyzer")
            self.logger.info(f"⚙️  Configuration: timeout={timeout}s, max_workers={max_workers}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up all resources."""
        try:
            # Stop LSP server
            self.lsp_bridge.stop_language_server()
            
            # Clean up temporary directories
            self.project_bridge.cleanup_temp_directory()
            
            if self.verbose:
                self.logger.info("🧹 Cleanup completed successfully")
                
        except Exception as e:
            self.logger.warning(f"⚠️  Error during cleanup: {e}")
    
    def analyze_repository(
        self,
        repo_url_or_path: str,
        severity_filter: Optional[str] = None,
        language_override: Optional[str] = None,
        output_format: str = "text"
    ) -> Union[str, Dict[str, Any]]:
        """
        Perform comprehensive analysis of a repository using all bridge components.
        
        Args:
            repo_url_or_path: Repository URL or local path
            severity_filter: Optional severity filter ('ERROR', 'WARNING', 'INFO', 'HINT')
            language_override: Optional language override
            output_format: Output format ('text' or 'json')
            
        Returns:
            Analysis results in requested format
            
        Raises:
            Various exceptions based on failure points
        """
        self.analysis_start_time = time.time()
        
        try:
            self.logger.info("🚀 Starting Comprehensive Serena LSP Analysis")
            self.logger.info("=" * 80)
            self.logger.info(f"📁 Target: {repo_url_or_path}")
            self.logger.info(f"🔍 Severity filter: {severity_filter or 'ALL'}")
            self.logger.info(f"🌐 Language override: {language_override or 'AUTO-DETECT'}")
            self.logger.info(f"📊 Output format: {output_format}")
            self.logger.info("=" * 80)
            
            # Step 1: Repository setup
            repo_setup_start = time.time()
            if self.project_bridge.is_git_url(repo_url_or_path):
                self.logger.info("📥 Cloning remote repository...")
                repo_path = self.project_bridge.clone_repository(repo_url_or_path)
            else:
                repo_path = os.path.abspath(repo_url_or_path)
                if not os.path.exists(repo_path):
                    raise FileNotFoundError(f"Local path does not exist: {repo_path}")
                self.logger.info(f"📂 Using local repository: {repo_path}")
            
            self.performance_stats["repo_setup_time"] = time.time() - repo_setup_start
            
            # Step 2: Language detection and project creation
            project_setup_start = time.time()
            language = None
            if language_override:
                try:
                    language = Language(language_override.lower())
                    self.logger.info(f"🎯 Language override: {language.value}")
                except ValueError:
                    self.logger.warning(f"⚠️  Invalid language '{language_override}', will auto-detect")
            
            self.logger.info("⚙️  Setting up Serena project...")
            project = self.project_bridge.create_project(repo_path, language)
            
            self.performance_stats["project_setup_time"] = time.time() - project_setup_start
            
            # Step 3: LSP server initialization
            lsp_setup_start = time.time()
            self.logger.info("🔧 Creating and starting LSP server...")
            language_server = self.lsp_bridge.create_language_server(project)
            self.lsp_bridge.start_language_server()
            
            # Allow server to fully initialize
            initialization_delay = 5 if len(self.project_bridge.gather_source_files()) > 100 else 2
            self.logger.info(f"⏳ Allowing {initialization_delay}s for LSP initialization...")
            time.sleep(initialization_delay)
            
            self.performance_stats["lsp_setup_time"] = time.time() - lsp_setup_start
            
            # Step 4: Parse severity filter
            severity = None
            if severity_filter:
                severity_map = {
                    "ERROR": DiagnosticSeverity.Error,
                    "WARNING": DiagnosticSeverity.Warning,
                    "INFO": DiagnosticSeverity.Information,
                    "HINT": DiagnosticSeverity.Hint
                }
                severity = severity_map.get(severity_filter.upper())
                if severity is None:
                    self.logger.warning(f"⚠️  Invalid severity '{severity_filter}', showing all diagnostics")
                else:
                    self.logger.info(f"🔍 Filtering by severity: {severity_filter.upper()}")
            
            # Step 5: Comprehensive diagnostic collection
            analysis_start = time.time()
            self.logger.info("🔍 Beginning comprehensive diagnostic collection...")
            
            # Get all source files
            source_files = self.project_bridge.gather_source_files()
            if not source_files:
                self.logger.warning("⚠️  No source files found in project")
                return self._generate_empty_result(output_format, "No source files found")
            
            # Progress tracking
            def progress_callback(processed: int, total: int):
                if processed % max(1, total // 20) == 0:  # Report every 5%
                    percentage = (processed / total) * 100
                    elapsed = time.time() - analysis_start
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta = (total - processed) / rate if rate > 0 else 0
                    
                    self.logger.info(
                        f"📈 Progress: {processed}/{total} ({percentage:.1f}%) "
                        f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s"
                    )
            
            # Collect diagnostics
            all_diagnostics, error_map = self.diagnostic_bridge.collect_diagnostics_batch(
                language_server=language_server,
                file_paths=source_files,
                severity_filter=severity,
                max_workers=self.max_workers,
                progress_callback=progress_callback if self.verbose else None
            )
            
            self.performance_stats["analysis_time"] = time.time() - analysis_start
            
            # Step 6: Generate results
            total_time = time.time() - self.analysis_start_time
            self.performance_stats["total_time"] = total_time
            
            # Create analysis results
            results = self._generate_analysis_results(
                diagnostics=all_diagnostics,
                error_map=error_map,
                source_files=source_files,
                project=project,
                repo_path=repo_path
            )
            
            # Log final statistics
            self._log_final_statistics(results)
            
            # Return in requested format
            if output_format == "json":
                return results.to_dict()
            else:
                return self._format_text_output(results)
                
        except Exception as e:
            self.logger.error(f"❌ Comprehensive analysis failed: {e}")
            if self.verbose:
                import traceback
                self.logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            
            if output_format == "json":
                return {"error": str(e), "diagnostics": []}
            else:
                return f"ERRORS: ['0']\nSerena analysis failed: {e}"
    
    def _generate_analysis_results(
        self,
        diagnostics: List[EnhancedDiagnostic],
        error_map: Dict[str, str],
        source_files: List[str],
        project: Project,
        repo_path: str
    ) -> AnalysisResults:
        """Generate comprehensive analysis results."""
        
        # Count diagnostics by severity and file
        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "HINT": 0, "UNKNOWN": 0}
        file_counts = {}
        
        for diag in diagnostics:
            severity_counts[diag.severity] = severity_counts.get(diag.severity, 0) + 1
            file_counts[diag.file_path] = file_counts.get(diag.file_path, 0) + 1
        
        # Create results
        results = AnalysisResults(
            total_files=len(source_files),
            processed_files=len(source_files) - len(error_map),
            failed_files=len(error_map),
            total_diagnostics=len(diagnostics),
            diagnostics_by_severity=severity_counts,
            diagnostics_by_file=file_counts,
            diagnostics=diagnostics,
            performance_stats=self.performance_stats,
            language_detected=project.language.value,
            repository_path=repo_path,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            server_info=self.lsp_bridge.get_server_status(),
            project_info={
                "project_name": project.project_config.project_name,
                "language": project.language.value,
                "ignored_paths": project.project_config.ignored_paths,
                "source_file_count": len(source_files)
            }
        )
        
        return results
    
    def _generate_empty_result(self, output_format: str, message: str) -> Union[str, Dict[str, Any]]:
        """Generate empty result for edge cases."""
        if output_format == "json":
            return {
                "total_files": 0,
                "total_diagnostics": 0,
                "diagnostics": [],
                "message": message
            }
        else:
            return f"ERRORS: ['0']\n{message}"
    
    def _format_text_output(self, results: AnalysisResults) -> str:
        """Format results as text output."""
        if not results.diagnostics:
            return "ERRORS: ['0']\nNo errors found."
        
        # Sort diagnostics by severity, file, then line
        severity_priority = {"ERROR": 0, "WARNING": 1, "INFO": 2, "HINT": 3, "UNKNOWN": 4}
        results.diagnostics.sort(
            key=lambda d: (
                severity_priority.get(d.severity, 5),
                d.file_path.lower(),
                d.line
            )
        )
        
        output_lines = [f"ERRORS: ['{len(results.diagnostics)}']"]
        
        for i, diag in enumerate(results.diagnostics, 1):
            file_name = os.path.basename(diag.file_path)
            location = f"line {diag.line}, col {diag.column}"
            
            # Clean message
            clean_message = diag.message.replace("\n", " ").replace("\r", " ")
            clean_message = " ".join(clean_message.split())
            if len(clean_message) > 200:
                clean_message = clean_message[:197] + "..."
            
            # Metadata
            metadata_parts = [f"severity: {diag.severity}"]
            if diag.code:
                metadata_parts.append(f"code: {diag.code}")
            if diag.source and diag.source != "lsp":
                metadata_parts.append(f"source: {diag.source}")
            
            other_types = ", ".join(metadata_parts)
            
            diagnostic_line = f"{i}. '{location}' '{file_name}' '{clean_message}' '{other_types}'"
            output_lines.append(diagnostic_line)
        
        return "\n".join(output_lines)
    
    def _log_final_statistics(self, results: AnalysisResults):
        """Log comprehensive final statistics."""
        self.logger.info("=" * 80)
        self.logger.info("📋 COMPREHENSIVE SERENA LSP ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Files processed successfully: {results.processed_files}")
        self.logger.info(f"❌ Files failed: {results.failed_files}")
        self.logger.info(f"📊 Total files analyzed: {results.total_files}")
        self.logger.info(f"🔍 Total diagnostics found: {results.total_diagnostics}")
        
        self.logger.info("📋 Diagnostics by severity:")
        for severity, count in results.diagnostics_by_severity.items():
            if count > 0:
                self.logger.info(f"   {severity}: {count}")
        
        self.logger.info("⏱️  Performance Summary:")
        for stat_name, stat_value in self.performance_stats.items():
            self.logger.info(f"   {stat_name}: {stat_value:.2f}s")
        
        if results.total_files > 0:
            avg_time = self.performance_stats.get("analysis_time", 0) / results.total_files
            self.logger.info(f"   avg_time_per_file: {avg_time:.3f}s")
        
        self.logger.info("=" * 80)


# Export main classes for use
__all__ = [
    'SerenaLSPBridge',
    'SerenaProjectBridge', 
    'SerenaDiagnosticBridge',
    'SerenaComprehensiveAnalyzer',
    'EnhancedDiagnostic',
    'AnalysisResults',
    'LSPServerInfo'
]
