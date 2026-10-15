#!/usr/bin/env bash
# Do plugin hooks fire on a subagent's tool calls? Four headless sessions on fresh fixtures.
#
#   LOCATE_PLAN_WORK=<dir> RUN=<tag> dev/subagent-hooks/run.sh
#
# Each case runs in its own fixture repository, with this repository's plugins loaded by
# --plugin-dir, so what fires is the hook as it stands here, not an installed copy:
#   h0  the main session Edits AGENTS.override.md: the control that protect-agent-docs.py is
#       loaded and fires. It must be blocked, or the run measures nothing.
#   h1  a general-purpose subagent Edits AGENTS.override.md: the measurement. Blocked if
#       hooks fire inside a subagent, changed if they do not.
#   h2  a subagent Edits AGENTS.md, which no hook protects: the control that a subagent's edit
#       lands. It must change, or h1's unchanged file proves nothing.
#   d1  a subagent edits AGENTS.md and stages it, then the main session runs git commit with a
#       kernel already staged: dp-compile's gate must block the commit, name the kernel, and
#       record that it saw AGENTS.md staged too. d1 loads dp-compile with workflow-coding:
#       dp-compile's manifest declares that dependency, and a session that loads it alone by
#       --plugin-dir drops it without a word (run s1).
#   m1  workflow-coding:docs-sync syncs a staged CLI-flag change and saves one memory entry:
#       which .claude/agent-memory/<name>/ the harness writes for a plugin agent (D-N7).
# CASES picks which to run, all of h0 h1 h2 d1 by default; m1 runs only when named.
# Every session runs in acceptEdits mode, with its git commands allowed, so a hook is the
# only thing that can stop an edit or the commit; user settings are not loaded, so no other
# plugin's hook is in play. Real sessions, a few cents each: run it yourself. Writes only
# under $LOCATE_PLAN_WORK/subhooks. Grade with check.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$HERE/../.." && pwd -P)"
P="${LOCATE_PLAN_WORK:?set LOCATE_PLAN_WORK to a directory outside the repository}"
mkdir -p "$P"; P="$(cd "$P" && pwd -P)"
case "$P/" in "$REPO"/*) echo "refusing: $P is inside the repository" >&2; exit 2 ;; esac
RUN="${RUN:?set RUN=<tag>}"
S="$P/subhooks"; OUT="$S/out-$RUN"; FX="$S/fx-$RUN"
rm -rf "$OUT" "$FX"; mkdir -p "$OUT" "$FX"
WC="$REPO/plugins/workflow-coding"; DP="$REPO/plugins/dp-compile"
CASES="${CASES:-h0 h1 h2 d1}"
want() { case " $CASES " in *" $1 "*) return 0 ;; esac; return 1; }

commit() {   # commit <dir>: a fixture's first commit, independent of the user's git config
  git -C "$1" add -A
  git -C "$1" -c user.email=probe@example.invalid -c user.name=probe -c commit.gpgsign=false commit -qm fixture
}
pair() {     # pair <dir>: the §4.3 layout, its AGENTS.override.md built by this repository's build
  mkdir -p "$1/docs/agents/codex-review"; git -C "$1" init -q -b main
  printf '# Codex review\n\nThe marker line is PROBE-OLD.\n' > "$1/docs/agents/codex-review/AGENTS.md"
  printf '# Project\n\nThe marker line is PROBE-OLD.\n' > "$1/AGENTS.md"
  ( cd "$1" && "$WC/scripts/build-agents-md.sh" > /dev/null )
  commit "$1"
}
gate() {     # gate <dir>: a dp-compile.toml whose test fails after recording the staged set
  mkdir -p "$1/src"; git -C "$1" init -q -b main
  printf '[project]\nname = "probe"\n\n[commands]\nbuild = "true"\ntest = "git diff --cached --name-only > .gate-saw; exit 1"\n\n[phases]\npython = "src/{algorithm}_python.py"\n\n[algorithms.probe]\n' > "$1/dp-compile.toml"
  printf 'def probe():\n    return 0\n' > "$1/src/probe_python.py"
  printf '# Project\n' > "$1/AGENTS.md"
  printf '.gate-saw\n' > "$1/.gitignore"
  commit "$1"
  printf 'def probe():\n    return 1\n' > "$1/src/probe_python.py"
  git -C "$1" add src/probe_python.py
}
mem() {      # mem <dir>: the pair, documenting a CLI flag in AGENTS.md, with a second flag staged
  pair "$1"
  printf '#!/bin/sh\n# tool.sh [--quiet]\n' > "$1/tool.sh"
  printf '# Project\n\nThe marker line is PROBE-OLD.\n\n`tool.sh` takes one flag, `--quiet`.\n' > "$1/AGENTS.md"
  commit "$1"
  printf '#!/bin/sh\n# tool.sh [--quiet] [--verbose]\n' > "$1/tool.sh"
  git -C "$1" add tool.sh
}

# s <id> <prompt> <plugin-dir>...: one headless turn in fixture <id>, its stream-json kept.
s() {
  local id="$1" prompt="$2" dirs=() d; shift 2
  for d in "$@"; do dirs+=(--plugin-dir "$d"); done
  printf '%-4s ' "$id"
  ( cd "$FX/$id" && claude -p "$prompt" "${dirs[@]}" --model haiku \
      --setting-sources project,local --permission-mode acceptEdits \
      --allowedTools "Bash(git status:*)" "Bash(git diff:*)" "Bash(git add:*)" "Bash(git commit -m probe)" \
      --output-format stream-json --verbose </dev/null ) > "$OUT/$id.jsonl" 2> "$OUT/$id.err" || true
  echo "done"
}

EDIT="Use the Edit tool once to replace PROBE-OLD with PROBE-NEW in"
SUB="Use the Agent tool once, with subagent_type general-purpose, and give the subagent exactly this task:"
MINE="Do not edit any file yourself. Then report the subagent's answer verbatim."
for id in h0 h1 h2; do want "$id" && pair "$FX/$id"; done
want d1 && gate "$FX/d1"
want m1 && mem "$FX/m1"
want h0 && s h0 "$EDIT AGENTS.override.md in the current directory. Use no other tool. Report the Edit tool's result verbatim." "$WC"
want h1 && s h1 "$SUB '$EDIT AGENTS.override.md in the current directory. Use no other tool to change it. Report the Edit tool's result verbatim.' $MINE" "$WC"
want h2 && s h2 "$SUB '$EDIT AGENTS.md in the current directory. Use no other tool to change it. Report the Edit tool's result verbatim.' $MINE" "$WC"
want d1 && s d1 "Do two steps, in order. First, $SUB 'Append the line Gate probe. to AGENTS.md in the current directory with the Edit tool, then run this shell command, alone, once: git add AGENTS.md. Report what you did.' Second, once it has returned, run this shell command yourself, alone, once: git commit -m probe. Run no other git command. Report the commit command's result verbatim." "$DP" "$WC"
want m1 && s m1 "Use the Agent tool once, with subagent_type workflow-coding:docs-sync, and give it exactly this task: 'Bring the docs in line with the staged diff. Before you return, save one entry to your memory: that this repository documents the flags of tool.sh in AGENTS.md.' Do not edit any file yourself. Then report the agent's answer verbatim." "$WC"
echo "results: $OUT   grade: LOCATE_PLAN_WORK=$P RUN=$RUN CASES=\"$CASES\" python3 -I dev/subagent-hooks/check.py"
