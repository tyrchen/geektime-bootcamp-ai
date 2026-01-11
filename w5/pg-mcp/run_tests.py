"""
Test Runner Script
==================

This script runs the test suite for the PostgreSQL MCP Server.

Usage:
    # Run all tests
    python -m pytest

    # Run specific test file
    python -m pytest tests/test_sql_validator.py

    # Run with coverage
    python -m pytest --cov=pg_mcp --cov-report=html

    # Run specific test
    python -m pytest tests/test_sql_validator.py::TestSQLValidator::test_validate_select_query
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the test suite."""
    project_root = Path(__file__).parent
    test_dir = project_root / "tests"

    if not test_dir.exists():
        print(f"Error: Test directory not found at {test_dir}")
        sys.exit(1)

    # Run pytest with default options
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
    ]

    print(f"Running tests in {test_dir}...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
