#!/usr/bin/env bash
# Smoke test: validate plugin syntax AND check components are correctly placed.
# The validator only checks files it can find — a misplaced component is invisible
# to both the validator and Claude Code's loader. The placement check catches that.
# Does NOT verify runtime loading — no CLI diagnostic exists for that.
# Run from the plugin root: ./dev/smoke-test.sh

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Validating plugin at: $PLUGIN_DIR"
echo

# --- Step 1: Validate syntax, frontmatter, schemas ---

if claude plugin validate "$PLUGIN_DIR" 2>&1; then
  echo
  echo "Validation passed."
else
  echo
  echo "--- FAILED: fix the validation errors above ---"
  exit 1
fi

echo

# --- Step 2: Check expected components are correctly placed ---
# Update this list when adding new skills, commands, agents, or hooks.

expected=(
  "skills/algorithm-formalize/SKILL.md"
  "skills/algorithm-prototype/SKILL.md"
  "skills/cython-translation/SKILL.md"
  "skills/cpu-parallelization/SKILL.md"
  "skills/cpu-parallelization/references/decomposition-patterns.md"
  "skills/gpu-parallelization/SKILL.md"
  "skills/benchmarking/SKILL.md"
  "commands/new-algorithm.md"
  "commands/phase-check.md"
  "commands/next-phase.md"
  "commands/benchmark.md"
  "commands/references/manifest.md"
  "commands/references/phase-detection.md"
  "hooks/hooks.json"
  "hooks/scripts/pre-commit-check.py"
)
# Deliberately not listed yet. The check is `-s` (exists and non-empty), so listing a
# placeholder would fail rather than warn:
#   skills/gpu-parallelization/SKILL.md is a stub, and its references/ and examples/
#   hold zero-byte placeholders. Add the references and the example here when the
#   CUDA phase is written for real.

missing=0
echo "Checking component placement:"
for component in "${expected[@]}"; do
  if [ -s "$PLUGIN_DIR/$component" ]; then
    echo "  [ok] $component"
  else
    echo "  [MISSING] $component"
    missing=1
  fi
done

echo
if [ "$missing" -eq 1 ]; then
  echo "--- FAILED: some components are missing or empty ---"
  exit 1
else
  echo "All components found."
fi
