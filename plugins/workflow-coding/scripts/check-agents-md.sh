#!/usr/bin/env bash
# Verify that every generated AGENTS.override.md (root and every component) matches the
# Codex reviewer's guide it is built from, and lint the hand-authored AGENTS.md files.
# Exits 0 when the pair is in sync, 1 on drift or a missing file, whatever the lints
# find. Intended for pre-commit hooks or CI.
#
# The in-sync check reuses scripts/build-agents-md.sh via DST_DIR, so it compares exactly
# what the build would write and has no generation logic of its own. AGENTS.md and
# CLAUDE.md are hand-authored, so neither is compared.
#
# The lints read every AGENTS.md git lists, tracked or new and not ignored, outside
# docs/agents/: the root's and every component's, not the guides, which one subagent each
# loads and which may carry history. Every agent loads an AGENTS.md at session start, so
# it should stay short and in the present tense. Each lint warns on stderr, and neither
# changes the exit status:
#   - more than 200 lines;
#   - a dated line (20\d\d-\d\d-\d\d): dated prose belongs in docs/agents/_history/.
#
# Consumers normally invoke /agents-docs-check rather than this script.

set -euo pipefail
set -f

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="${SCRIPT_DIR}/build-agents-md.sh"
MAX_LINES=200
NL='
'
TAB="$(printf '\t')"

if [ ! -x "$BUILD" ]; then
  echo "error: ${BUILD} not found or not executable" >&2
  exit 2
fi

# --- the lints, on the hand-authored AGENTS.md files ---------------------------------

warnings=0
warn() { echo "warning: $1" >&2; warnings=$((warnings + 1)); }

files="$(cd "$ROOT" && git ls-files --cached --others --exclude-standard -- 'AGENTS.md' '*/AGENTS.md')"
if [ -n "$files" ]; then files="$(printf '%s\n' "$files" | sort -u)"; fi

IFS="$NL"
for f in $files; do
  case "$f" in docs/agents/*) continue ;; esac
  p="${ROOT}/${f}"
  [ -f "$p" ] || continue
  n="$(awk 'END { print NR }' "$p")"
  if [ "$n" -gt "$MAX_LINES" ]; then
    warn "${f}: ${n} lines, over ${MAX_LINES}; every agent loads it at session start"
  fi
  dated="$(awk '/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/ { k++; if (k <= 5) s = s (s == "" ? "" : ", ") NR }
                END { if (k) print k "\t" s }' "$p")"
  if [ -n "$dated" ]; then
    k="${dated%%"$TAB"*}"; at="${dated#*"$TAB"}"
    if [ "$k" -eq 1 ]; then
      warn "${f}: line ${at} is dated; dated prose belongs in docs/agents/_history/"
    elif [ "$k" -le 5 ]; then
      warn "${f}: lines ${at} are dated; dated prose belongs in docs/agents/_history/"
    else
      warn "${f}: lines ${at} and $((k - 5)) more are dated; dated prose belongs in docs/agents/_history/"
    fi
  fi
done
unset IFS

# --- the in-sync check, on the generated pair ---------------------------------------

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

case "$warnings" in
  0) echo "Agent docs are in sync with docs/agents/" ;;
  1) echo "Agent docs are in sync with docs/agents/ (1 warning)" ;;
  *) echo "Agent docs are in sync with docs/agents/ (${warnings} warnings)" ;;
esac
