#!/usr/bin/env bash
# How long a command's allowed-tools grant lasts: four headless sessions on a fixture.
#
#   LOCATE_PLAN_WORK=<dir> RUN=<tag> dev/grant-lifetime/run.sh
#
# The fixture plugin's /grant-probe:probe <n> grants one write, Bash(touch probe-*), and
# runs `touch probe-<n>`. Each case is judged by whether its touch ran or was denied:
#   g0  a fresh session asks for `touch probe-0` and invokes no command: the control that the
#       write is not allowed without the grant. It must be denied, or the run measures nothing.
#   g1  /grant-probe:probe 1, the turn that invokes the command: it must run.
#   g2  the next message, resuming g1's session, asks for `touch probe-2` and invokes no
#       command: denied if the grant clears with the next message, run if it lasts.
#   g3  the message after that invokes /grant-probe:probe 3 again: re-applied, it must run.
# Each session runs in --permission-mode default, whatever defaultMode the settings name: in
# auto or acceptEdits mode the write could pass with no grant, and the run would measure nothing.
# Real sessions, a few cents each: run it yourself. Writes only under $LOCATE_PLAN_WORK/grant.
# Grade with check.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$HERE/../.." && pwd -P)"
P="${LOCATE_PLAN_WORK:?set LOCATE_PLAN_WORK to a directory outside the repository}"
mkdir -p "$P"; P="$(cd "$P" && pwd -P)"
case "$P/" in "$REPO"/*) echo "refusing: $P is inside the repository" >&2; exit 2 ;; esac
RUN="${RUN:?set RUN=<tag>}"
G="$P/grant"; OUT="$G/out-$RUN"; FX="$G/fx-$RUN"
rm -rf "$OUT" "$FX"; mkdir -p "$OUT" "$FX"

# s <id> <prompt> [claude options]: one headless turn in the fixture, its stream-json kept.
s() {
  local id="$1" prompt="$2"; shift 2
  printf '%-4s ' "$id"
  ( cd "$FX" && claude -p "$prompt" --plugin-dir "$HERE/plugin" --model haiku --permission-mode default "$@" \
      --output-format stream-json --verbose </dev/null ) > "$OUT/$id.jsonl" 2> "$OUT/$id.err" || true
  echo "done"
}
# The session a turn ran in, from its stream-json, so the next turn resumes exactly it.
sid() {
  python3 -I -c 'import json,sys
for l in open(sys.argv[1]):
    try: d = json.loads(l)
    except ValueError: continue
    if d.get("session_id"): print(d["session_id"]); break' "$1"
}

ASK="Run this shell command, alone, once, and nothing else"
s g0 "$ASK: touch probe-0"
s g1 "/grant-probe:probe 1"
s g2 "$ASK: touch probe-2" --resume "$(sid "$OUT/g1.jsonl")"
s g3 "/grant-probe:probe 3" --resume "$(sid "$OUT/g2.jsonl")"
echo "results: $OUT   grade: LOCATE_PLAN_WORK=$P RUN=$RUN python3 -I dev/grant-lifetime/check.py"
