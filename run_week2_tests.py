#!/usr/bin/env python3
"""
Week 2 Test Runner

Runs all existing tests but with Week 2 EnhancedChatService to generate
comprehensive Phoenix tracing logs across all test scenarios.

This script modifies the import paths to use Week 2 enhanced components
while running the full test suite.
"""

import sys
from pathlib import Path

# Add both Week 1 and Week 2 solutions to path
week1_path = Path(__file__).parent / "week_1" / "solution"
week2_path = Path(__file__).parent / "week_2" / "solution"

sys.path.insert(0, str(week2_path))  # Week 2 first (higher priority)
sys.path.insert(0, str(week1_path))  # Week 1 as fallback

# Import Week 2 enhanced components

print("🔍 Week 2 Enhanced Test Runner")
print("=" * 50)
print(f"✅ Week 2 path: {week2_path}")
print(f"✅ Week 1 path: {week1_path}")
print("✅ Enhanced tracing enabled")
print("=" * 50)

# Now run pytest with all tests
if __name__ == "__main__":
    import subprocess

    # Run all tests except the slow LLM judge test
    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "-v",
        "-k",
        "not test_robustness_llm_judge",
        "--tb=short",  # Shorter traceback for cleaner output
    ]

    print(f"🚀 Running command: {' '.join(cmd)}")
    print("📊 This will generate comprehensive Phoenix traces!")
    print("🔍 Check your Phoenix dashboard during test execution")
    print("=" * 50)

    # Execute the tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    print("=" * 50)
    if result.returncode == 0:
        print("✅ All tests completed successfully!")
    else:
        print(f"⚠️  Tests completed with return code: {result.returncode}")

    print("🔍 Check Phoenix dashboard for comprehensive trace data!")
