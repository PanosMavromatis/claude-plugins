#!/usr/bin/env bash
# Propose moves that file merged branch plans into revision directories.
#
# Branch plans are never deleted, so docs/plan/ gains one flat directory per
# merged branch. Which revision directory each belongs to is not a judgement:
# /new-branch writes the plan's "> **Branch:** <name>" backlink beneath a
# specific "## Subgoals — revision <label>" heading in the master plan, so the
# revision is already recorded at creation time. This script reads it back.
#
# READ-ONLY. It prints proposed `git mv` commands and a report; it never
# moves, stages or commits anything. Consumers normally invoke /file-plans,
# which runs this, confirms, and executes.
#
# Two cases cannot be derived and are reported as skipped, never guessed:
#   - no backlink in the master plan (a standalone branch, or one created
#     without /new-branch)
#   - a "## Subgoals" heading carrying no revision number (predates the
#     convention)
# Both leave the plan flat. A plan filed into the wrong revision is worse
# than one never filed, because the error becomes invisible once it is filed.
#
# Exit: 0 = proposals printed, or nothing to do. 2 = error.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PLAN_DIR="docs/plan"
[ -d "$PLAN_DIR" ] || { echo "nothing to do: no ${PLAN_DIR}/ in this repo"; exit 0; }

MASTER=""
for f in "${PLAN_DIR}/DO.md" "${PLAN_DIR}/TODO.md"; do
  [ -f "$f" ] && { MASTER="$f"; break; }
done
[ -n "$MASTER" ] || { echo "nothing to do: no master plan at ${PLAN_DIR}/DO.md or TODO.md"; exit 0; }

# branch name -> revision number, from each backlink's enclosing heading.
# The ^[[:space:]]* anchor is load-bearing: without it, prose that merely
# mentions the backlink syntax matches too, and the master plan's own
# explanation of this mechanism does exactly that.
MAP="$(awk '
  /^## Subgoals/                       { heading = $0 }
  /^[[:space:]]*> \*\*Branch:\*\*/     {
    rev = "none"
    if (match(heading, /revision[ ]+[^ :]+/))
      { rev = substr(heading, RSTART, RLENGTH); sub(/revision[ ]+/, "", rev) }
    print $NF "\t" rev
  }
' "$MASTER" | sort -u)"

proposals=0
skipped=0

for dir in "${PLAN_DIR}"/*/; do
  dir="${dir%/}"
  name="$(basename "$dir")"

  # A plan directory holds a plan file. Directories that only contain other
  # directories are containers (a revision's own directory) and are already filed.
  plan=""
  for f in "${dir}/DO.md" "${dir}/TODO.md"; do
    [ -f "$f" ] && { plan="$f"; break; }
  done
  [ -n "$plan" ] || continue

  status="$(grep -m1 '^\*\*Status\*\*:' "$plan" 2>/dev/null | sed 's/^\*\*Status\*\*:[[:space:]]*//' || true)"
  case "$status" in
    merged*) ;;
    *) continue ;;   # active, unstamped, or anything else: still in flight
  esac

  # Match the directory name against a backlinked branch, flattened the same
  # way /new-branch flattens it.
  rev=""
  branch=""
  while IFS=$'\t' read -r b r; do
    [ -n "$b" ] || continue
    [ "${b//\//-}" = "$name" ] || continue
    branch="$b"; rev="$r"; break
  done <<< "$MAP"

  if [ -z "$branch" ]; then
    printf 'skip  %-38s no backlink in %s — cannot derive a revision\n' "$name" "$MASTER"
    skipped=$((skipped + 1))
    continue
  fi
  if [ "$rev" = "none" ]; then
    printf 'skip  %-38s backlink found, but its heading carries no revision label\n' "$name"
    skipped=$((skipped + 1))
    continue
  fi

  printf 'git mv %s %s/%s/%s\n' "$dir" "$PLAN_DIR" "$rev" "$name"
  proposals=$((proposals + 1))
done

echo
if [ "$proposals" -eq 0 ] && [ "$skipped" -eq 0 ]; then
  echo "nothing to do: no merged plans sitting flat under ${PLAN_DIR}/"
else
  echo "${proposals} to file, ${skipped} skipped"
fi
