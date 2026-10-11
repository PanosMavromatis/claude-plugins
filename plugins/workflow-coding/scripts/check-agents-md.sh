#!/usr/bin/env bash
# Verify AGENTS.md and AGENTS.override.md (root + every component) are in
# sync with docs/agents/ sources. Exits 0 on sync, non-zero on drift.
# Intended for pre-commit hooks or CI.
#
# CLAUDE.md is not checked — it is an @import dispatcher, not a generated
# artifact, so drift detection doesn't apply.
#
# Reuses scripts/build-agents-md.sh via DST_DIR to avoid duplicating
# generation logic, and walks the build output to determine the expected
# set of files automatically (monorepo components included).
#
# Consumers normally invoke /agents-docs-check rather than this script.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="${SCRIPT_DIR}/build-agents-md.sh"

if [ ! -x "$BUILD" ]; then
  echo "error: ${BUILD} not found or not executable" >&2
  exit 2
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Regenerate everything into TMP_DIR.
DST_DIR="$TMP_DIR" "$BUILD" > /dev/null

# Walk the build output and compare each file to its committed counterpart.
problems=0
while IFS= read -r generated_path; do
  rel="${generated_path#"$TMP_DIR"/}"
  committed="${ROOT}/${rel}"

  if [ ! -f "$committed" ]; then
    if [ "$problems" -eq 0 ]; then
      echo "Agent docs are out of sync with docs/agents/ sources." >&2
      echo >&2
    fi
    problems=1
    echo "missing: ${rel} (run /agents-docs-build to generate)" >&2
    continue
  fi

  if ! diff -q "$generated_path" "$committed" > /dev/null 2>&1; then
    if [ "$problems" -eq 0 ]; then
      echo "Agent docs are out of sync with docs/agents/ sources." >&2
      echo >&2
    fi
    problems=1
    echo "--- drift in ${rel} (expected vs. actual) ---" >&2
    diff -u "$generated_path" "$committed" >&2 || true
    echo >&2
  fi
done < <(find "$TMP_DIR" -type f | sort)

if [ "$problems" -ne 0 ]; then
  echo "Fix: run /agents-docs-build and commit the results." >&2
  exit 1
fi

echo "Agent docs are in sync with docs/agents/"
