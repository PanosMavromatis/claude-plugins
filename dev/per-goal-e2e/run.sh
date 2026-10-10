#!/usr/bin/env bash
# The per-goal end-to-end sessions: the real commands, headless, on fresh fixtures.
#
#   LOCATE_PLAN_WORK=<dir> RUN=<tag> dev/per-goal-e2e/run.sh [scenario...]   (default: all)
#
# Rebuilds the fixtures (build.py), then runs each scenario's sessions in order, each in
# its fixture repository, with only the working tree's plugin copy loaded (--plugin-dir).
# Sessions write stream-json (every tool call, and the result with its permission
# denials) to $LOCATE_PLAN_WORK/e2e/out-$RUN/. Grade with check.py. Run it yourself: it
# starts real sessions, which cost money. Writes only under $LOCATE_PLAN_WORK/e2e.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$HERE/../.." && pwd -P)"
P="${LOCATE_PLAN_WORK:?set LOCATE_PLAN_WORK to a directory outside the repository}"
mkdir -p "$P"; P="$(cd "$P" && pwd -P)"
case "$P/" in "$REPO"/*) echo "refusing: $P is inside the repository" >&2; exit 2 ;; esac
RUN="${RUN:?set RUN=<tag>}"
E="$P/e2e"; OUT="$E/out-$RUN"

python3 -I "$HERE/build.py"
PLUGIN="$(printf '%s' "e2e/plugin" | shasum | cut -c1-8)"; PLUGIN="$E/p/$PLUGIN/workflow-claude"
mkdir -p "$OUT"

# id | fixture | prompt. Each scenario's sessions run in order, on the state the one
# before left; a scenario is all lines whose id starts with its name.
SESSIONS=(
  'e1|r1|/workflow-claude:new-branch feat/plan-dirs. Purpose: subgoal 2 of revision 07-rev, the plan directory structure. Scope: (1) Create notes/structure.txt containing the word structure. (2) Create notes/layout.txt containing the word layout. Context: none. This branch executes subgoal 2, "Plan directory structure", in docs/plan/07-rev/_TODO.md.'
  'e1-step|r1|/workflow-claude:hitl-step 2'
  'e3|r3|/workflow-claude:new-branch fix/do-tasks. Purpose: subgoal 2 of revision 07-rev. Scope: (1) Create a.txt containing the letter a. (2) Create b.txt containing the letter b. Context: none. This branch executes subgoal 2, "Plan directory structure", in docs/plan/07-rev/_DO.md.'
  'e3-step|r3|/workflow-claude:step 2'
  'e4|r4|/workflow-claude:new-branch feat/legacy-notes. Purpose: the legacy notes subgoal. Scope: (1) Create notes/legacy.txt containing the word legacy. Context: none. This branch executes the subgoal "Write the legacy notes" in docs/plan/TODO.md.'
  'e4-step|r4|/workflow-claude:hitl-step 1'
  'e5|r5|/workflow-claude:hitl-step 1'
)

want=" ${*:-e1 e3 e4 e5} "
for s in "${SESSIONS[@]}"; do
  IFS='|' read -r id fx prompt <<< "$s"
  case "$want" in *" ${id%%-*} "*) ;; *) continue ;; esac
  printf '%-8s %-3s ' "$id" "$fx"
  ( cd "$E/$fx" && claude -p "$prompt" --plugin-dir "$PLUGIN" --output-format stream-json --verbose </dev/null ) \
    > "$OUT/$id.jsonl" 2> "$OUT/$id.err" || true
  python3 -I -c 'import json,sys
r=None
for l in open(sys.argv[1]):
    try: d=json.loads(l)
    except Exception: continue
    if d.get("type")=="result": r=d
if not r: print("no result line"); sys.exit()
print("turns", r.get("num_turns","?"), "|", "%.0f s" % (r.get("duration_ms",0)/1000), "|", "error" if r.get("is_error") else "ok",
      "| denials", len(r.get("permission_denials") or []), "| $%.2f" % (r.get("total_cost_usd") or 0))' "$OUT/$id.jsonl"
done
echo "results: $OUT   grade: LOCATE_PLAN_WORK=$P RUN=$RUN python3 -I dev/per-goal-e2e/check.py"
