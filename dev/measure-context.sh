#!/usr/bin/env bash
# Measure what a Claude Code session, and each workflow-claude command, loads into
# context in a consuming repository.
#
# The subagent refactor exists to shrink these numbers, so it is judged against them
# rather than against impressions: run this before a revision and after it.
#
# READ-ONLY. Reads files and prints a report; writes nothing and runs no git command
# that changes state. Pass the target as an argument rather than running this from
# inside it: a Claude Code session whose shell moves into a repository loads that
# repository's CLAUDE.md as a side effect.
#
# Tokens are bytes / 4 — a usable approximation for English Markdown, and the one the
# refactor plan's baseline uses. Treat them as relative, not as a tokenizer's count.
#
# Usage: measure-context.sh [--plugin <dir>] [<repo>]
#   <repo>    the consuming repository (default: the current git toplevel)
#   --plugin  the workflow-claude directory whose commands to measure
#             (default: plugins/workflow-claude beside this script's repository)
# Exit:  0 = report printed. 2 = usage error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="${SCRIPT_DIR}/../plugins/workflow-claude"
REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --plugin) [ $# -ge 2 ] || { echo "usage: $(basename "$0") [--plugin <dir>] [<repo>]" >&2; exit 2; }
              PLUGIN="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *)  [ -z "$REPO" ] || { echo "error: one repository only" >&2; exit 2; }
        REPO="$1"; shift ;;
  esac
done
[ -n "$REPO" ] || REPO="$(git rev-parse --show-toplevel)"
[ -d "$REPO" ]        || { echo "error: no such directory: $REPO" >&2; exit 2; }
[ -d "$PLUGIN/commands" ] || { echo "error: no commands/ under --plugin $PLUGIN" >&2; exit 2; }
REPO="$(cd "$REPO" && pwd)"; PLUGIN="$(cd "$PLUGIN" && pwd)"

bytes()  { wc -c < "$1" | tr -d '[:space:]'; }
lines()  { wc -l < "$1" | tr -d '[:space:]'; }
fmt()    { awk -v n="$1" 'BEGIN{s=sprintf("%d",n); r=""; while(length(s)>3){r=","substr(s,length(s)-2)r; s=substr(s,1,length(s)-3)} print s r}'; }
tok()    { fmt $(( $1 / 4 )); }
rel()    { case "$1" in "$REPO"/*) echo "${1#"$REPO"/}";; "$PLUGIN"/*) echo "<plugin>/${1#"$PLUGIN"/}";; *) echo "$1";; esac; }
row()    { printf "  %10s %9s  %s\n" "$(fmt "$2")" "$(tok "$2")" "$1"; }
head2()  { printf "\n%s\n  %10s %9s  %s\n" "$1" "bytes" "≈tokens" "file"; }
sum()    { local t=0 f; for f in "$@"; do t=$(( t + $(bytes "$f") )); done; echo "$t"; }

# @imports in one file, resolved to existing paths. Mirrors what Claude Code expands:
# @path tokens outside fenced code blocks and inline code spans, relative to the
# importing file, ~/ meaning home.
imports_of() {
  local f="$1" d; d="$(dirname "$f")"
  awk '
    /^[[:space:]]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    { gsub(/`[^`]*`/, "")
      line = $0
      while (match(line, /(^|[[:space:](])@[^[:space:])]+/)) {
        tok = substr(line, RSTART, RLENGTH); sub(/^[[:space:](]*@/, "", tok)
        sub(/[.,;:!?]+$/, "", tok); print tok
        line = substr(line, RSTART + RLENGTH)
      } }' "$f" |
  while IFS= read -r p; do
    case "$p" in "~/"*) p="$HOME/${p#\~/}";; /*) ;; *) p="$d/$p";; esac
    [ -f "$p" ] && (cd "$(dirname "$p")" && echo "$(pwd)/$(basename "$p")")
  done
}

# Depth-first expansion, at most five hops, each file once.
SEEN=""
expand() {
  local f="$1" depth="$2" i
  case " $SEEN " in *" $f "*) return;; esac
  SEEN="$SEEN $f"; echo "$depth $f"
  [ "$depth" -ge 5 ] && return
  local kids=(); while IFS= read -r i; do kids+=("$i"); done < <(imports_of "$f")
  for i in "${kids[@]+"${kids[@]}"}"; do expand "$i" $(( depth + 1 )); done
}

echo "measure-context — $(basename "$REPO")$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null | sed 's/^/ at /')"
echo "plugin commands from $(basename "$(dirname "$PLUGIN")")/$(basename "$PLUGIN")$(sed -n "s/.*\"version\": *\"\([^\"]*\)\".*/ at \1/p" "$PLUGIN/.claude-plugin/plugin.json" 2>/dev/null)"

# ---------------------------------------------------------------------------
# 1. Session start: the project instruction files and their transitive imports.
#    AGENTS.md is read natively only when none of the three CLAUDE files exists.
#    .claude/rules/*.md load at start unless they carry a paths: frontmatter key.
#    User-level ~/.claude/CLAUDE.md is the user's, not the repository's: not counted.
# ---------------------------------------------------------------------------
head2 "1. Session start"
ROOTS=()
for f in CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md; do [ -f "$REPO/$f" ] && ROOTS+=("$REPO/$f"); done
if [ ${#ROOTS[@]} -eq 0 ] && [ -f "$REPO/AGENTS.md" ]; then ROOTS=("$REPO/AGENTS.md"); fi
if [ -d "$REPO/.claude/rules" ]; then
  while IFS= read -r f; do
    awk 'NR==1 && !/^---/ {exit 1} NR>1 && /^---/ {exit 1} /^paths:/ {exit 0}' "$f" && continue
    ROOTS+=("$f")
  done < <(find "$REPO/.claude/rules" -name '*.md' | sort)
fi
START=0
for r in "${ROOTS[@]+"${ROOTS[@]}"}"; do
  while read -r depth f; do
    pad=""; [ "$depth" -gt 0 ] && pad="$(printf '%*s' $(( depth * 2 )) '')└ "
    row "${pad}$(rel "$f")" "$(bytes "$f")"; START=$(( START + $(bytes "$f") ))
  done < <(expand "$r" 0)
done
[ ${#ROOTS[@]} -gt 0 ] || echo "  (no project instruction file)"
row "TOTAL at session start" "$START"
[ -f "$REPO/CLAUDE.local.md" ] && [ -f "$REPO/AGENTS.md" ] && echo "  note: CLAUDE.local.md present, so AGENTS.md is not read natively"

# ---------------------------------------------------------------------------
# 4. Plans (measured before the commands, which reuse the numbers).
#    Branch plans: DO.md / TODO.md below docs/plan/; archives: _DO.md / _TODO.md;
#    the master plan: docs/plan/DO.md or TODO.md.
#    A DO.md / TODO.md below docs/plan/ that carries a "## Subgoals" heading is an
#    older master plan that was moved, not a branch plan: counted apart, so it does
#    not skew the branch-plan median.
# ---------------------------------------------------------------------------
PLAN_DIR="$REPO/docs/plan"
MASTER=""; for f in DO TODO; do [ -f "$PLAN_DIR/$f.md" ] && { MASTER="$PLAN_DIR/$f.md"; break; }; done
BRANCH_PLANS=(); ARCHIVES=(); OLD_MASTERS=()
if [ -d "$PLAN_DIR" ]; then
  while IFS= read -r f; do
    if grep -q "^## Subgoals" "$f"; then OLD_MASTERS+=("$f"); else BRANCH_PLANS+=("$f"); fi
  done < <(find "$PLAN_DIR" -mindepth 2 \( -name DO.md -o -name TODO.md \) | sort)
  while IFS= read -r f; do ARCHIVES+=("$f"); done < <(find "$PLAN_DIR" \( -name _DO.md -o -name _TODO.md \) | sort)
fi
NB=${#BRANCH_PLANS[@]}
PLAN_MED=0; PLAN_MAX=0; PLAN_MIN=0; PLAN_MAX_F=""
if [ "$NB" -gt 0 ]; then
  SIZES="$(for f in "${BRANCH_PLANS[@]}"; do echo "$(bytes "$f") $f"; done | sort -n)"
  PLAN_MIN=$(echo "$SIZES" | head -1 | cut -d' ' -f1)
  PLAN_MAX=$(echo "$SIZES" | tail -1 | cut -d' ' -f1); PLAN_MAX_F=$(echo "$SIZES" | tail -1 | cut -d' ' -f2-)
  PLAN_MED=$(echo "$SIZES" | awk '{a[NR]=$1} END{print (NR%2)? a[(NR+1)/2] : int((a[NR/2]+a[NR/2+1])/2)}')
fi

# ---------------------------------------------------------------------------
# 2. Per command: the command file plus what its steps read whole.
#    "Reads whole" is a property of the command's prose, which a script cannot parse,
#    so it is stated here. Keep this table in step with the commands: a command that
#    stops reading a file whole must be taken off it, or the report overstates.
# ---------------------------------------------------------------------------
AGENT_DOCS=(); while IFS= read -r f; do AGENT_DOCS+=("$f"); done < <(
  { [ -f "$REPO/README.md" ] && echo "$REPO/README.md"
    for d in docs/agents docs/ops docs/git; do [ -d "$REPO/$d" ] && find "$REPO/$d" -type f -name '*.md'; done; } | sort)
SYNC_READS=0; [ ${#AGENT_DOCS[@]} -gt 0 ] && SYNC_READS=$(sum "${AGENT_DOCS[@]}")
cmd() { local f="$PLUGIN/commands/$1.md"; [ -f "$f" ] && bytes "$f" || echo 0; }

printf '\n2. Per command (≈tokens)\n  %-20s %7s %15s  %s\n' "command" "own" "per call" "also reads whole"
crow() { # name own_bytes reads_label reads_lo reads_hi
  local lo=$(( $2 + $4 )) hi=$(( $2 + $5 )) range
  if [ "$lo" -eq "$hi" ]; then range="$(tok "$lo")"; else range="$(tok "$lo")-$(tok "$hi")"; fi
  printf '  %-20s %7s %15s  %s\n' "$1" "$(tok "$2")" "$range" "$3"
}
PLAN_LABEL="branch plan (median-max)"
crow "/hitl-step"          "$(cmd hitl-step)"          "$PLAN_LABEL" "$PLAN_MED" "$PLAN_MAX"
crow "/step"               "$(cmd step)"               "$PLAN_LABEL" "$PLAN_MED" "$PLAN_MAX"
crow "/smart-merge"        "$(cmd smart-merge)"        "$PLAN_LABEL + branch doc" "$PLAN_MED" "$PLAN_MAX"
crow "/agents-docs-update" "$(cmd agents-docs-update)" "README + docs/{agents,ops,git}" "$SYNC_READS" "$SYNC_READS"
crow "/smart-commit"       "$(( $(cmd smart-commit) + $(cmd agents-docs-update) ))" "as /agents-docs-update, same ctx" "$SYNC_READS" "$SYNC_READS"
OTHERS=""; for f in "$PLUGIN"/commands/*.md; do
  n="$(basename "$f" .md)"
  case "$n" in hitl-step|step|smart-merge|agents-docs-update|smart-commit) continue;; esac
  OTHERS="$OTHERS /$n $(tok "$(bytes "$f")"),"
done
echo "  others, own text only:${OTHERS%,}"
echo "  (/smart-merge's branch doc is per-branch and not included; /smart-commit's own column adds /agents-docs-update's text)"

# ---------------------------------------------------------------------------
# 3. docs/agents/**
# ---------------------------------------------------------------------------
head2 "3. docs/agents/**"
if [ -d "$REPO/docs/agents" ]; then
  AG=(); while IFS= read -r f; do AG+=("$f"); done < <(find "$REPO/docs/agents" -type f -name '*.md' | sort)
  for f in "${AG[@]+"${AG[@]}"}"; do row "$(rel "$f")" "$(bytes "$f")"; done
  row "TOTAL (${#AG[@]} files)" "$(sum "${AG[@]+"${AG[@]}"}")"
else
  echo "  (no docs/agents/)"
fi

# ---------------------------------------------------------------------------
# 4. Plans, reported.
# ---------------------------------------------------------------------------
head2 "4. Branch plans and archives"
if [ "$NB" -gt 0 ]; then
  row "branch plans: $NB, smallest" "$PLAN_MIN"
  row "branch plans: median" "$PLAN_MED"
  row "branch plans: largest — $(rel "$PLAN_MAX_F")" "$PLAN_MAX"
  # A log entry starts its line; a marker quoted inside a sentence ("its `> **Done:**`
  # line is ...") is prose about the convention, not an entry, and is not counted.
  printf '  inline log entries across branch plans: %s Note, %s Q, %s A, %s Done\n' \
    $(for k in Note Q A Done; do cat "${BRANCH_PLANS[@]}" | grep -cE "^[[:space:]]*> \*\*$k:\*\*" || true; done)
else
  echo "  (no branch plans)"
fi
if [ ${#ARCHIVES[@]} -gt 0 ]; then
  BIG="$(for f in "${ARCHIVES[@]}"; do echo "$(bytes "$f") $f"; done | sort -n | tail -1)"
  row "revision archives: ${#ARCHIVES[@]}, largest — $(rel "${BIG#* }")" "${BIG%% *}"
fi

# ---------------------------------------------------------------------------
# 5. The master plan.
# ---------------------------------------------------------------------------
head2 "5. Master plan"
if [ -n "$MASTER" ]; then
  row "$(rel "$MASTER") ($(lines "$MASTER") lines)" "$(bytes "$MASTER")"
  [ "$(lines "$MASTER")" -gt 2000 ] && echo "  warning: over 2000 lines — a whole-file Read truncates"
  for f in "${OLD_MASTERS[@]+"${OLD_MASTERS[@]}"}"; do row "older, moved: $(rel "$f") ($(lines "$f") lines)" "$(bytes "$f")"; done
else
  echo "  (no master plan at docs/plan/DO.md or TODO.md)"
fi
exit 0
