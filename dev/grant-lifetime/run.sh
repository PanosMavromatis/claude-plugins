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
# Does a command's grant reach a subagent it spawns? /grant-probe:spawn hands its argument to a
# general-purpose subagent and /grant-probe:direct does it itself, both granting Edit,
# Bash(git add:*) and Bash(git commit:*). Each a-case runs in a git fixture of its own:
#   a0  no command: a subagent edits AGENTS.md and stages it. The control: it must be denied.
#   a1  /grant-probe:direct makes that edit and stages it: the control that the grant covers
#       these tools in the main session. It must run.
#   a2  /grant-probe:spawn has a subagent make it: does the grant reach the subagent?
#   a3  /grant-probe:spawn has a subagent run git commit with a change staged: does a grant for a
#       write the subagent must never make reach it too?
#   a4  /grant-probe:direct commits in the main session: the control. It must land.
#   a5  /grant-probe:relay has a subagent read a file, then the main session commits once it
#       returns: /smart-commit's shape, where the commit may fall in a later turn.
#   a2f, a3f, a5f  a2, a3 and a5 with CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1: the subagent runs
#       in the foreground, inside the command's turn, so a denial in the background twin alone
#       means the grant expired with the turn, and in both means it never passed down.
#   k1  a3 again with workflow-coding loaded and WORKFLOW_CODING_GUARDED_AGENTS=general-purpose:
#       its guard-agent-git.py hook must refuse the subagent's commit, which the grant would pass.
#   k2  a4 again, loaded the same way: the main session's commit carries no agent_type, so the
#       guard must leave it alone and it must land.
# The a- and k-cases load no user settings, so no allow rule of the user's can pass a write.
# CASES picks which to run: g0 g1 g2 g3 by default, the a-cases only when named.
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
CASES="${CASES:-g0 g1 g2 g3}"
want() { case " $CASES " in *" $1 "*) return 0 ;; esac; return 1; }

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
want g0 && s g0 "$ASK: touch probe-0"
want g1 && s g1 "/grant-probe:probe 1"
want g2 && s g2 "$ASK: touch probe-2" --resume "$(sid "$OUT/g1.jsonl")"
want g3 && s g3 "/grant-probe:probe 3" --resume "$(sid "$OUT/g2.jsonl")"

# afx <dir> [staged]: a git fixture whose AGENTS.md says PROBE-OLD, with a change staged if asked.
afx() {
  mkdir -p "$1"; git -C "$1" init -q -b main
  printf '# Project\n\nThe marker line is PROBE-OLD.\n' > "$1/AGENTS.md"
  git -C "$1" add -A
  git -C "$1" -c user.email=probe@example.invalid -c user.name=probe -c commit.gpgsign=false commit -qm fixture
  if [ "${2:-}" = staged ]; then printf 'a staged change\n' > "$1/notes.txt"; git -C "$1" add notes.txt; fi
}
# sa <id> <prompt> [VAR=value] [plugin-dir]: one headless turn in fixture <id>, with no user
# settings loaded and grant-probe, plus any plugin named; CLAUDE_CODE_DISABLE_BACKGROUND_TASKS
# and WORKFLOW_CODING_GUARDED_AGENTS are unset unless the case sets one.
sa() {
  local id="$1" prompt="$2" set=() plug=(--plugin-dir "$HERE/plugin")
  [ -n "${3:-}" ] && set=("$3")
  [ -n "${4:-}" ] && plug+=(--plugin-dir "$4")
  printf '%-4s ' "$id"
  ( cd "$FX/$id" && env -u CLAUDE_CODE_DISABLE_BACKGROUND_TASKS -u WORKFLOW_CODING_GUARDED_AGENTS ${set[@]+"${set[@]}"} \
      claude -p "$prompt" "${plug[@]}" --model haiku --permission-mode default \
      --setting-sources project,local --output-format stream-json --verbose </dev/null ) \
      > "$OUT/$id.jsonl" 2> "$OUT/$id.err" || true
  echo "done"
}
EDIT="Use the Edit tool once to replace PROBE-OLD with PROBE-NEW in AGENTS.md in the current directory, then run this shell command, alone, once: git add AGENTS.md. Report each tool's result verbatim, and do not retry a refused call."
COMMIT="Run this shell command, alone, once: git commit -m probe. Report its result verbatim, and do not retry a refused call."
FG=CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
for id in a0 a1 a2 a2f; do want "$id" && afx "$FX/$id"; done
for id in a3 a3f a4 a5 a5f k1 k2; do want "$id" && afx "$FX/$id" staged; done
WC="$(cd "$HERE/../../plugins/workflow-coding" && pwd -P)"; GUARD=WORKFLOW_CODING_GUARDED_AGENTS=general-purpose
want a0 && sa a0 "Use the Agent tool once, with subagent_type general-purpose, and give it exactly this task, word for word: $EDIT Use no other tool yourself. When it returns, reply with its answer verbatim."
want a1 && sa a1 "/grant-probe:direct $EDIT"
want a2 && sa a2 "/grant-probe:spawn $EDIT"
want a3 && sa a3 "/grant-probe:spawn $COMMIT"
want a4 && sa a4 "/grant-probe:direct $COMMIT"
want a5 && sa a5 "/grant-probe:relay"
want a2f && sa a2f "/grant-probe:spawn $EDIT" "$FG"
want a3f && sa a3f "/grant-probe:spawn $COMMIT" "$FG"
want a5f && sa a5f "/grant-probe:relay" "$FG"
want k1 && sa k1 "/grant-probe:spawn $COMMIT" "$GUARD" "$WC"
want k2 && sa k2 "/grant-probe:direct $COMMIT" "$GUARD" "$WC"
echo "results: $OUT   grade: LOCATE_PLAN_WORK=$P RUN=$RUN CASES=\"$CASES\" python3 -I dev/grant-lifetime/check.py"
