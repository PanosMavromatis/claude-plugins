#!/usr/bin/env bash
# Pre-commit hook: compile Cython extensions and run the test suite.
# Runs before git commit commands. Exit 0 = allow, exit 2 = block.

set -uo pipefail

# Build any Cython extensions before testing
uv run python setup.py build_ext --inplace 2>/dev/null

# Run the full test suite (parametrized across backends)
if uv run pytest tests/ -x --tb=short; then
  echo "All tests passed."
  exit 0
else
  echo "Tests failed — commit blocked." >&2
  exit 2
fi
