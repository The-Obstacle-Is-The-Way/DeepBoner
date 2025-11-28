"""Test runner script that writes output to file and handles timeouts.

This script runs tests with proper timeout handling and writes output to a file
to help debug hanging tests.
"""

import subprocess
import sys
from datetime import datetime

# Test output file
OUTPUT_FILE = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def run_tests_with_timeout():
    """Run tests with timeout and write output to file."""
    print(f"Running tests - output will be written to {OUTPUT_FILE}")

    # Base pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "-p",
        "no:logfire",
        "-m",
        "huggingface or (integration and not openai)",
        "--timeout=300",  # 5 minute timeout per test
        "tests/integration/",
    ]

    # Check if pytest-timeout is available
    try:
        import pytest_timeout  # noqa: F401

        print("Using pytest-timeout plugin")
    except ImportError:
        print("WARNING: pytest-timeout not installed, installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-timeout"], check=False)
        cmd.insert(-1, "--timeout=300")

    # Run tests and capture output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Test Run: {datetime.now().isoformat()}\n")
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write("=" * 80 + "\n\n")

        # Run pytest
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stream output to both file and console
        for line in process.stdout:
            print(line, end="")
            f.write(line)
            f.flush()

        process.wait()
        return_code = process.returncode

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Exit code: {return_code}\n")
        f.write(f"Completed: {datetime.now().isoformat()}\n")

    print(f"\nTest output written to: {OUTPUT_FILE}")
    return return_code


if __name__ == "__main__":
    exit_code = run_tests_with_timeout()
    sys.exit(exit_code)
