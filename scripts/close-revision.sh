#!/usr/bin/env bash
# Propose extracting a closed revision's section out of the master plan.
#
# The master plan accumulates every subgoal of every revision along with its
# "> **Done:**" annotation, and nothing ever removes any of it. Closing a
# revision moves its section into docs/plan/<label>/_DO.md, leaving a one-line
# pointer behind, so the master plan reads as an index of closed revisions
# plus whatever is currently open.
#
# The archive is named _DO.md, not DO.md, and that is load-bearing. Plan
# resolution globs docs/plan/**/DO.md and matches on filename, so an archive
# named DO.md would be indistinguishable from a branch plan — and unstamped,
# it would count as active and pollute the disambiguation prompt. The
# underscore keeps an archived revision out of resolution entirely, which is
# right: a finished revision should never be offered as somewhere to do work.
# It stays reachable by explicit path.
#
# READ-ONLY. Prints what it would do; extracts nothing. /close-revision runs
# this, confirms, and performs the write.
#
# Whether a revision is finished is the user's call, never inferred. This
# script refuses on unchecked items as a safety net, not as the decision.
#
# Usage: close-revision.sh <label>
# Exit:  0 = proposal printed. 1 = refused, with a reason. 2 = usage error.

set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $(basename "$0") <revision-label>   e.g. 03-subgoal-plan-management" >&2; exit 2; }
REV="$1"
# A revision is identified by its label, not by a position in a sequence. The
# numeric prefix convention (03-…) is for sorting and lives inside the label.
case "$REV" in
  ''|*/*|*' '*) echo "error: label must be non-empty and contain no spaces or slashes, got '${REV}'" >&2; exit 2 ;;
esac

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PLAN_DIR="docs/plan"
MASTER=""; ARCHIVE_NAME=""
for f in DO TODO; do
  if [ -f "${PLAN_DIR}/${f}.md" ]; then MASTER="${PLAN_DIR}/${f}.md"; ARCHIVE_NAME="_${f}.md"; break; fi
done
[ -n "$MASTER" ] || { echo "refused: no master plan at ${PLAN_DIR}/DO.md or TODO.md" >&2; exit 1; }

DEST_DIR="${PLAN_DIR}/${REV}"
DEST="${DEST_DIR}/${ARCHIVE_NAME}"

# Exact string comparison, not a regex: BSD grep does not support \| alternation
# in a basic regex (it silently matches nothing rather than erroring), and a
# label could contain regex metacharacters. awk compares literally.
START="$(awk -v h="## Subgoals — revision ${REV}" '
  $0 == h || index($0, h ":") == 1 { print NR; exit }
' "$MASTER")"
[ -n "$START" ] || { echo "refused: no '## Subgoals — revision ${REV}' section in ${MASTER}" >&2; exit 1; }

# The section runs to the next top-level heading, or end of file.
END="$(awk -v s="$START" 'NR > s && /^## /{print NR - 1; exit}' "$MASTER")"
# BSD wc pads its output with spaces; strip them or arithmetic and the report both break.
[ -n "$END" ] || END="$(wc -l < "$MASTER" | tr -d "[:space:]")"

OPEN="$(sed -n "${START},${END}p" "$MASTER" | grep -c '^- \[[ ~!]\]' || true)"
if [ "$OPEN" -gt 0 ]; then
  echo "refused: revision ${REV} still has ${OPEN} unfinished item(s):" >&2
  sed -n "${START},${END}p" "$MASTER" | grep '^- \[[ ~!]\]' | cut -c1-100 >&2
  echo "Close them, descope them, or move them to another revision first." >&2
  exit 1
fi

[ -e "$DEST" ] && { echo "refused: ${DEST} already exists — revision ${REV} looks closed already" >&2; exit 1; }

TITLE="$(sed -n "${START}p" "$MASTER")"
# "## Subgoals — revision 2: MCP-preferred GitHub access" -> "MCP-preferred GitHub access".
# A heading with no colon yields the whole line, so fall back to no subtitle.
SUBTITLE=""
case "$TITLE" in *": "*) SUBTITLE=" — ${TITLE#*: }" ;; esac
POINTER="- **Revision ${REV}**${SUBTITLE} — closed. See \`${DEST}\`."

cat <<REPORT
master plan : ${MASTER}
section     : lines ${START}-${END} ($(( END - START + 1 )) lines, ${OPEN} unfinished)
destination : ${DEST}
pointer     : ${POINTER}

--- section that would be extracted (first 12 lines) ---
$(sed -n "${START},${END}p" "$MASTER" | head -12)
$( [ $(( END - START + 1 )) -gt 12 ] && echo "... $(( END - START + 1 - 12 )) more lines" )
--- end ---

The extraction is a CUT, not a copy: the section must not survive in both
places, or the master plan keeps the growth this exists to stop and the two
copies drift.
REPORT
