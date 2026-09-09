#!/usr/bin/env bash
# Propose opening a new revision in the master plan.
#
# A revision is a milestone: its subgoals each spawn a branch, its branch plans
# are filed into its directory by /file-plans, and /close-revision archives it
# when it is finished. Until now revisions could be closed but never opened —
# one came into existence when someone typed a heading by hand.
#
# Revisions are identified by a LABEL, not a number. The label is the identity,
# the same rule branch plans already follow: it names the heading
# ("## Subgoals — revision 03-subgoal-plan-management") and the directory
# (docs/plan/03-subgoal-plan-management/). A leading ordinal is a sorting
# convention inside the label, not a separate identifier — so a listing and a
# heading each read without cross-referencing the other.
#
# READ-ONLY. Prints the section it would insert and where; writes nothing.
# /open-revision runs this, confirms, and performs the write.
#
# Usage: open-revision.sh <label>   e.g. 04-revision-lifecycle
# Exit:  0 = proposal printed. 1 = refused, with a reason. 2 = usage error.

set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $(basename "$0") <label>   e.g. 04-revision-lifecycle" >&2; exit 2; }
LABEL="$1"
case "$LABEL" in
  ''|*/*|*' '*) echo "error: label must be non-empty and contain no spaces or slashes, got '${LABEL}'" >&2; exit 2 ;;
  '#'*|-*)      echo "error: label must not start with '#' or '-', got '${LABEL}'" >&2; exit 2 ;;
esac

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PLAN_DIR="docs/plan"
MASTER=""
for f in DO TODO; do
  [ -f "${PLAN_DIR}/${f}.md" ] && { MASTER="${PLAN_DIR}/${f}.md"; break; }
done
[ -n "$MASTER" ] || { echo "refused: no master plan at ${PLAN_DIR}/DO.md or TODO.md" >&2; exit 1; }

HEADING="## Subgoals — revision ${LABEL}"

if grep -qF "$HEADING" "$MASTER"; then
  echo "refused: ${MASTER} already has a section for revision '${LABEL}'" >&2
  exit 1
fi
if [ -e "${PLAN_DIR}/${LABEL}" ]; then
  echo "refused: ${PLAN_DIR}/${LABEL} already exists — that revision has been opened before" >&2
  exit 1
fi
if grep -qF "revision ${LABEL} — closed" "$MASTER" 2>/dev/null; then
  echo "refused: revision '${LABEL}' appears under Closed revisions in ${MASTER}" >&2
  exit 1
fi

# The new section goes above the trailing sections, so open revisions stay
# together and the closed index and deferred notes remain at the bottom.
INSERT_BEFORE=""
for h in "## Closed revisions" "## Deferred"; do
  n="$(grep -n "^${h}\$" "$MASTER" | head -1 | cut -d: -f1 || true)"
  if [ -n "$n" ]; then INSERT_BEFORE="$h"; INSERT_AT="$n"; break; fi
done
if [ -z "$INSERT_BEFORE" ]; then
  INSERT_BEFORE="(end of file)"
  INSERT_AT="$(( $(wc -l < "$MASTER" | tr -d "[:space:]") + 1 ))"
fi

OPEN_COUNT="$(grep -c '^## Subgoals — revision ' "$MASTER" || true)"

cat <<REPORT
master plan  : ${MASTER}
label        : ${LABEL}
directory    : ${PLAN_DIR}/${LABEL}/   (created by /file-plans on the first filing)
insert at    : line ${INSERT_AT}, before "${INSERT_BEFORE}"
existing     : ${OPEN_COUNT} revision section(s) already in the master plan

--- section that would be inserted ---
${HEADING}

<One paragraph: what prompted this revision and what it covers. The commands
do not write this — it is the part a person has to mean.>

- [ ] <first subgoal>

--- end ---

Each subgoal spawns a branch. /new-branch adds a "> **Branch:**" backlink
beneath the one it executes, and that backlink is what later tells /file-plans
which revision a plan belongs to — so the label above becomes the directory
name without anyone choosing it twice.
REPORT
