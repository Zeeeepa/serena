"""
FastAPI application for repository analytics with SolidLSP integration.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import RepositoryAnalysisRequest, RepositoryAnalysisResponse
from .analyzer import RepositoryAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analytics.log')
    ]
)

logger = logging.getLogger(__name__)

# Global analyzer instance
analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global analyzer
    logger.info("Starting up analytics application")
    analyzer = RepositoryAnalyzer()
    yield
    logger.info("Shutting down analytics application")


# Create FastAPI app
app = FastAPI(
    title="Repository Analytics API",
    description="Advanced repository analysis with traditional metrics and runtime error detection using SolidLSP",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Repository Analytics API",
        "version": "2.0.0",
        "features": [
            "Traditional code metrics (cyclomatic complexity, Halstead metrics, maintainability index)",
            "Runtime error detection using SolidLSP",
            "Multi-language support",
            "Git commit analysis",
            "Comprehensive error reporting"
        ],
        "supported_languages": [
            "Python", "TypeScript/JavaScript", "Java", "C#", "Go", 
            "Rust", "PHP", "Clojure", "Elixir", "C/C++"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-01-01T00:00:00Z"}


@app.post("/analyze", response_model=RepositoryAnalysisResponse)
async def analyze_repository(request: RepositoryAnalysisRequest) -> RepositoryAnalysisResponse:
    """
    Analyze a repository for code quality metrics and runtime errors.
    
    This endpoint performs comprehensive analysis including:
    - Traditional code metrics (complexity, maintainability, etc.)
    - Runtime error detection using SolidLSP
    - Git commit history analysis
    - Multi-language support
    
    Args:
        request: Repository analysis request
        
    Returns:
        Complete analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Received analysis request for repository: {request.repo_url}")
        
        if not analyzer:
            raise HTTPException(status_code=500, detail="Analyzer not initialized")
        
        # Validate repository URL
        if not request.repo_url or not request.repo_url.strip():
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        # Perform analysis
        result = analyzer.analyze_repository(request)
        
        logger.info(f"Analysis completed for {request.repo_url}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze_async")
async def analyze_repository_async(request: RepositoryAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start asynchronous repository analysis.
    
    This endpoint starts analysis in the background and returns immediately.
    Use this for large repositories that might take a long time to analyze.
    
    Args:
        request: Repository analysis request
        background_tasks: FastAPI background tasks
        
    Returns:
        Analysis job information
    """
    def run_analysis():
        try:
            logger.info(f"Starting background analysis for {request.repo_url}")
            result = analyzer.analyze_repository(request)
            logger.info(f"Background analysis completed for {request.repo_url}")
            # In a real implementation, you might store results in a database
            # or send them to a message queue
        except Exception as e:
            logger.error(f"Background analysis failed for {request.repo_url}: {e}")
    
    background_tasks.add_task(run_analysis)
    
    return {
        "message": "Analysis started",
        "repo_url": request.repo_url,
        "status": "processing"
    }


@app.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages."""
    return {
        "supported_languages": {
            "python": {
                "name": "Python",
                "extensions": [".py", ".pyw", ".pyi"],
                "solidlsp_support": True
            },
            "typescript": {
                "name": "TypeScript",
                "extensions": [".ts", ".tsx"],
                "solidlsp_support": True
            },
            "javascript": {
                "name": "JavaScript", 
                "extensions": [".js", ".jsx", ".mjs", ".cjs"],
                "solidlsp_support": True
            },
            "java": {
                "name": "Java",
                "extensions": [".java"],
                "solidlsp_support": True
            },
            "csharp": {
                "name": "C#",
                "extensions": [".cs", ".csx"],
                "solidlsp_support": True
            },
            "go": {
                "name": "Go",
                "extensions": [".go"],
                "solidlsp_support": True
            },
            "rust": {
                "name": "Rust",
                "extensions": [".rs"],
                "solidlsp_support": True
            },
            "php": {
                "name": "PHP",
                "extensions": [".php", ".phtml"],
                "solidlsp_support": True
            },
            "clojure": {
                "name": "Clojure",
                "extensions": [".clj", ".cljs", ".cljc"],
                "solidlsp_support": True
            },
            "elixir": {
                "name": "Elixir",
                "extensions": [".ex", ".exs"],
                "solidlsp_support": True
            }
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Repository Analytics API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

