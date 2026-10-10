#!/usr/bin/env bash
# Goal-10 trial runner: runs cases headless (claude -p) against one arm.
#
#   LOCATE_PLAN_WORK=<dir> ARM=baseline|haiku|sonnet RUN=<tag> run.sh <case>... | all
#
# Needs the fixtures (suite.py builds both) and the arms (build-arms.py). Results go to
# $LOCATE_PLAN_WORK/out-$ARM-$RUN/: per case, claude's JSON, its stderr, and a .case line.
# Writes only under $LOCATE_PLAN_WORK. Each case checks its fixture branch out first and
# restores the tree afterwards. Run it yourself: it starts real sessions, which cost money.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$HERE/../../.." && pwd -P)"
P="${LOCATE_PLAN_WORK:?set LOCATE_PLAN_WORK to the work directory suite.py built}"; P="$(cd "$P" && pwd -P)"
case "$P/" in "$REPO"/*) echo "refusing: $P is inside the repository" >&2; exit 2 ;; esac
ARM="${ARM:?set ARM=baseline, haiku or sonnet}"; RUN="${RUN:?set RUN=<tag>}"
OUT="$P/out-$ARM-$RUN"

h() { printf '%s' "$1" | shasum | cut -c1-8; }   # as build-arms.py and build-fixtures.sh
arm_dir() { printf '%s/p/%s/workflow-claude' "$P" "$(h "arm/$ARM/$1")"; }
[ -d "$(arm_dir '')" ] || { echo "no arm at $(arm_dir ''): run build-arms.py" >&2; exit 1; }
for r in fx fx-diag; do [ -d "$P/$r" ] || { echo "no fixture $P/$r: run suite.py" >&2; exit 1; }; done
mkdir -p "$OUT"

# id | repo | branch | runner | arguments | fault   (runner: probe = /probe-resolver;
# hitl, step = the command itself). Faults all use c03's fixture: chmod = the plan
# unreadable; awk = a failing awk first on PATH; f03, f04, f05 = the arm's fault copy.
CASES=(
  "c01|fx|case/r1-valid|probe|TODO.md docs/plan/some-plan"
  "c02|fx|case/r1-bad|probe|TODO.md docs/plan/nope"
  "c03|fx|case/r2-flat|probe|TODO.md"
  "c04|fx|case/r2-moved|probe|TODO.md"
  "c05|fx|case/r2-dup|probe|TODO.md"
  "c06|fx|case/r3-legacy|probe|TODO.md"
  "c07|fx|case/r3-rev-one|probe|TODO.md"
  "c08|fx|case/r3-rev-two|probe|TODO.md"
  "c09|fx|case/r3-rev-none|probe|TODO.md"
  "c10|fx|case/r4-one|probe|TODO.md"
  "c11|fx|case/r4-several|probe|TODO.md"
  "c12|fx|case/r4-merged-only|probe|TODO.md"
  "c13|fx|case/r5-root|probe|TODO.md"
  "c14|fx|case/none|probe|TODO.md"
  "c15|fx|case/do-model|probe|DO.md"
  "c16|fx|case/blocked|probe|TODO.md"
  "c17|fx|case/closed|probe|TODO.md"
  "c18|fx|case/cmd-hitl|hitl|"
  "c19|fx|case/cmd-hitl-master|hitl|"
  "c20|fx|case/cmd-step|step|"
  "e01|fx-diag|d/e01|probe|TODO.md docs/plan/nope"
  "e02|fx-diag|d/e02|probe|TODO.md docs/plan/d2"
  "e02b|fx-diag|d/e02b|probe|TODO.md d2b"
  "e03|fx-diag|d/e03|probe|TODO.md $P"
  "e04|fx-diag|d/e04|probe|TODO.md"
  "e05|fx-diag|d/e05|probe|TODO.md"
  "e06|fx-diag|d/e06|probe|TODO.md"
  "e07|fx-diag|d/e07|probe|TODO.md"
  "e07b|fx-diag|d/e07b|probe|TODO.md"
  "e08|fx-diag|d/e08|probe|TODO.md"
  "e08b|fx-diag|d/e08b|probe|TODO.md"
  "e09|fx-diag|d/e09|probe|TODO.md"
  "e10|fx-diag|d/e10|probe|TODO.md"
  "e11|fx-diag|d/e11|probe|TODO.md"
  "e13|nogit||probe|TODO.md"
  "e14|fx-diag|d/e14|probe|TODO.md docs/plan/TODO.md"
  "f01|fx|case/r2-flat|probe|TODO.md|chmod"
  "f02|fx|case/r2-flat|probe|TODO.md|awk"
  "f03|fx|case/r2-flat|probe|TODO.md|f03"
  "f04|fx|case/r2-flat|probe|TODO.md|f04"
  "f05|fx|case/r2-flat|probe|TODO.md|f05"
  # goal 12: a cut-short report through the real commands, which run the shipped Step 1
  "t-hitl|fx|case/cmd-hitl|hitl||f03"
  "t-step|fx|case/cmd-step|step||f03"
)

run_case() {
  local id="$1" repo="$2" br="$3" kind="$4" args="$5" fault="${6:-}" prompt dir="$P/$2" env=() wc
  wc="$(arm_dir '')"
  case "$kind" in
    probe) prompt="/workflow-claude:probe-resolver $args" ;;
    hitl)  prompt="/workflow-claude:hitl-step" ;;
    step)  prompt="/workflow-claude:step" ;;
  esac
  if [ -n "$br" ]; then
    git -C "$dir" checkout -q "$br"
    [ -z "$(git -C "$dir" status --porcelain)" ] || { echo "$id: fixture tree dirty on $br" >&2; exit 1; }
  else
    env=(GIT_CEILING_DIRECTORIES="$P")   # e13: outside any repository
  fi
  case "$fault" in
    chmod) chmod 000 "$dir/docs/plan/case-r2-flat/TODO.md"; trap 'chmod 644 "$P/fx/docs/plan/case-r2-flat/TODO.md"' EXIT ;;
    awk)   env=(PATH="$P/bin/$(h awk-127):$PATH") ;;
    f0?)   wc="$(arm_dir "$fault")" ;;
  esac
  printf '%s %-24s ' "$id" "${br:-(no repo)}"
  ( cd "$dir" && env ${env[@]+"${env[@]}"} claude -p "$prompt" --plugin-dir "$wc" --output-format json </dev/null ) \
    > "$OUT/$id.json" 2> "$OUT/$id.err" || true
  if [ "$fault" = chmod ]; then chmod 644 "$dir/docs/plan/case-r2-flat/TODO.md"; trap - EXIT; fi
  printf '%s|%s|%s|%s|%s\n' "$id" "$repo" "$br" "$kind" "$args" > "$OUT/$id.case"
  python3 -I -c 'import json,sys
try: d=json.load(open(sys.argv[1])); print("turns", d.get("num_turns","?"), "|", "%.1f s" % (d.get("duration_ms",0)/1000), "|", "error" if d.get("is_error") else "ok", "| denials", len(d.get("permission_denials") or []))
except Exception as e: print("unparseable output:", e)' "$OUT/$id.json"
  if [ -n "$br" ]; then git -C "$dir" checkout -q -- . 2>/dev/null || true; fi
}

[ $# -gt 0 ] || { echo "name the cases to run, or 'all'" >&2; exit 2; }
want=" $* "
for c in "${CASES[@]}"; do
  IFS='|' read -r id repo br kind args fault <<< "$c"
  if [ "$*" = all ] || [[ "$want" == *" $id "* ]]; then run_case "$id" "$repo" "$br" "$kind" "$args" "$fault"; fi
done
for r in fx fx-diag; do git -C "$P/$r" checkout -q main; done
echo "results: $OUT"
