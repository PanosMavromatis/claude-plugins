#!/usr/bin/env bash
# Thin wrapper: delegates to the canonical benchmark script in the main repo.
# The plugin invokes this script; the heavy lifting lives in benchmarks/run_benchmark.py
# so it stays co-located with the tokalign codebase and evolves with its interfaces.

set -euo pipefail

# Locate the project root (walk up until we find pyproject.toml)
dir="$(cd "$(dirname "$0")" && pwd)"
while [ ! -f "$dir/pyproject.toml" ]; do
  parent="$(dirname "$dir")"
  if [ "$parent" = "$dir" ]; then
    echo "ERROR: could not locate project root (no pyproject.toml found)" >&2
    exit 1
  fi
  dir="$parent"
done

exec uv run python "$dir/benchmarks/run_benchmark.py" "$@"
