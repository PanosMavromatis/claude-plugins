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
GHBIN="$(printf '%s' "e2e/gh" | shasum | cut -c1-8)"; GHBIN="$E/bin/$GHBIN"
mkdir -p "$OUT"

# id | fixture | prompt. Each scenario's sessions run in order, on the state the one
# before left; a scenario is all lines whose id starts with its name.
SESSIONS=(
  'e1|r1|/workflow-claude:new-branch feat/plan-dirs. Purpose: subgoal 2 of revision 07-rev, the plan directory structure. Scope: (1) Create notes/structure.txt containing the word structure. (2) Create notes/layout.txt containing the word layout. Context: none. This branch executes subgoal 2, "Plan directory structure", in docs/plan/07-rev/_TODO.md.'
  'e1-step|r1|/workflow-claude:hitl-step 2'
  'e1-merge|r1m|/workflow-claude:smart-merge'
  'e3|r3|/workflow-claude:new-branch fix/do-tasks. Purpose: subgoal 2 of revision 07-rev. Scope: (1) Create a.txt containing the letter a. (2) Create b.txt containing the letter b. Context: none. This branch executes subgoal 2, "Plan directory structure", in docs/plan/07-rev/_DO.md.'
  'e3-step|r3|/workflow-claude:step 2'
  'e3-merge|r3m|/workflow-claude:smart-merge'
  'e4|r4|/workflow-claude:new-branch feat/legacy-notes. Purpose: the legacy notes subgoal. Scope: (1) Create notes/legacy.txt containing the word legacy. Context: none. This branch executes the subgoal "Write the legacy notes" in docs/plan/TODO.md.'
  'e4-step|r4|/workflow-claude:hitl-step 1'
  'e4-merge|r4m|/workflow-claude:smart-merge'
  'e5|r5|/workflow-claude:hitl-step 1'
)

want=" ${*:-e1 e3 e4 e5} "
for s in "${SESSIONS[@]}"; do
  IFS='|' read -r id fx prompt <<< "$s"
  case "$want" in *" ${id%%-*} "*) ;; *) continue ;; esac
  printf '%-8s %-3s ' "$id" "$fx"
  extra=()
  case "$fx" in
    *m) # A merge session runs in a fresh clone of its scenario's fixture, on the branch the
        # step session left, so the fixture itself stays as check.py grades it. gh is the
        # stub build.py wrote; MCP is off, so no session can reach a real repository; and
        # the gates /smart-merge leaves to the harness are opened for these sessions only.
        # The step session left its work uncommitted, as the fixture's CLAUDE.md tells it to,
        # and a clone carries only commits: copy the working tree over and commit it, as a
        # user would before merging. Then the clone matches its CLAUDE.md, with a local main
        # and no remote, and refs/e2e/pre marks the tip check.py compares the merge against.
        src="$E/${fx%m}"; dst="$E/$fx"; br="$(git -C "$src" branch --show-current)"; rm -rf "$dst"
        git clone -q -b "$br" "$src" "$dst"
        for kv in user.email=e2e@example.invalid user.name=e2e commit.gpgsign=false; do git -C "$dst" config "${kv%%=*}" "${kv#*=}"; done
        rsync -a --delete --exclude .git "$src/" "$dst/"
        git -C "$dst" add -A
        git -C "$dst" diff --cached --quiet || git -C "$dst" commit -q -m "The step session's work"
        git -C "$dst" branch --no-track main origin/main
        git -C "$dst" update-ref refs/e2e/pre HEAD
        git -C "$dst" remote remove origin
        : > "$OUT/$id.gh"
        # --strict-mcp-config should load no server at all, which check.py measures; the
        # GitHub server's tools are denied as well, so a server that loads anyway is inert.
        extra=(--strict-mcp-config --disallowedTools mcp__plugin_github_github --add-dir /tmp
               --allowedTools "Bash(git rm:*)" "Bash(gh pr merge:*)" "Bash(rm /tmp/pr-body-:*)") ;;
  esac
  ( cd "$E/$fx" && PATH="$GHBIN:$PATH" GH_LOG="$OUT/$id.gh" \
      claude -p "$prompt" --plugin-dir "$PLUGIN" ${extra[@]+"${extra[@]}"} --output-format stream-json --verbose </dev/null ) \
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
