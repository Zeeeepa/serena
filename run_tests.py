#!/usr/bin/env python3
"""
Comprehensive Test Runner for Serena Orchestrator
Runs all test suites with proper configuration and reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, env=None):
    """Run a command and return the result"""
    print(f"🔄 Running: {' '.join(cmd)}")
    
    # Merge environment variables
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=full_env,
            cwd=Path(__file__).parent
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "pytest-mock",
        "psutil",
        "aiohttp",
        "pyyaml"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed")
    return True


def run_unit_tests(verbose=False):
    """Run unit tests"""
    print("\n🧪 Running Unit Tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "test/orchestration/test_sub_agent_manager.py",
        "test/mcp_tools/test_mcp_manager.py", 
        "test/monitoring/test_health_monitor.py",
        "-m", "not integration and not performance",
        "--cov=src/serena",
        "--cov-report=term-missing",
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_integration_tests(api_key=None, verbose=False):
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️  No GEMINI_API_KEY provided. Skipping integration tests.")
        print("   Set GEMINI_API_KEY environment variable or use --api-key option")
        return True
    
    cmd = [
        "python", "-m", "pytest",
        "test/integration/test_full_system.py",
        "-m", "integration",
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    env = {"GEMINI_API_KEY": api_key}
    return run_command(cmd, env=env)


def run_performance_tests(verbose=False):
    """Run performance tests"""
    print("\n⚡ Running Performance Tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "test/",
        "-m", "performance",
        "--tb=short",
        "--durations=10"
    ]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_coverage_report():
    """Generate coverage report"""
    print("\n📊 Generating Coverage Report...")
    
    cmd = [
        "python", "-m", "pytest",
        "test/",
        "-m", "not integration",  # Skip integration for coverage
        "--cov=src/serena",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "--cov-fail-under=70",
        "-q"
    ]
    
    success = run_command(cmd)
    
    if success:
        print("✅ Coverage report generated:")
        print("   📄 HTML: htmlcov/index.html")
        print("   📄 XML: coverage.xml")
    
    return success


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or function"""
    print(f"\n🎯 Running Specific Test: {test_path}")
    
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_all_tests(api_key=None, verbose=False, skip_integration=False):
    """Run all test suites"""
    print("🚀 Running All Tests...")
    
    success = True
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    # Run unit tests
    if not run_unit_tests(verbose=verbose):
        print("❌ Unit tests failed")
        success = False
    else:
        print("✅ Unit tests passed")
    
    # Run integration tests if API key provided
    if not skip_integration:
        if not run_integration_tests(api_key=api_key, verbose=verbose):
            print("❌ Integration tests failed")
            success = False
        else:
            print("✅ Integration tests passed")
    
    # Generate coverage report
    if not run_coverage_report():
        print("⚠️  Coverage report generation failed")
    
    return success


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for Serena Orchestrator"
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--api-key",
        help="Gemini API key for integration tests"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--skip-integration",
        action="store_true",
        help="Skip integration tests"
    )
    
    parser.add_argument(
        "--test",
        help="Run specific test file or function"
    )
    
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Only generate coverage report"
    )
    
    args = parser.parse_args()
    
    # Set up environment
    os.environ["TESTING"] = "true"
    os.environ["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    if args.api_key:
        os.environ["GEMINI_API_KEY"] = args.api_key
    
    success = True
    
    try:
        if args.coverage_only:
            success = run_coverage_report()
        elif args.test:
            success = run_specific_test(args.test, verbose=args.verbose)
        elif args.type == "unit":
            success = run_unit_tests(verbose=args.verbose)
        elif args.type == "integration":
            success = run_integration_tests(api_key=args.api_key, verbose=args.verbose)
        elif args.type == "performance":
            success = run_performance_tests(verbose=args.verbose)
        elif args.type == "all":
            success = run_all_tests(
                api_key=args.api_key,
                verbose=args.verbose,
                skip_integration=args.skip_integration
            )
        
        if success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n💥 Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
