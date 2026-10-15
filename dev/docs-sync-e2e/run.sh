#!/usr/bin/env bash
# The §7.7 cases for docs-sync, end to end: real headless sessions on fresh fixtures.
#
#   LOCATE_PLAN_WORK=<dir> RUN=<tag> dev/docs-sync-e2e/run.sh
#   LOCATE_PLAN_WORK=<dir> RUN=<tag> DRY=1 dev/docs-sync-e2e/run.sh   # the fixtures alone, no session
#
# Each case runs in its own fixture repository, with this repository's plugins loaded by
# --plugin-dir, so what runs is the agent, the commands and the hooks as they stand here:
#   f1  /agents-docs-update; tool.sh gains --verbose, staged: AGENTS.md must name it, staged,
#       and nothing be committed.
#   f2  /agents-docs-update; tool.sh drops -q, an alias AGENTS.md never documented, and
#       docs/agents/_history/tooling.md logs each flag change by date: _history/ must gain the
#       change, staged, and AGENTS.md stay as it was.
#   f3  f1's change, beside an unstaged edit of the user's in README.md and an untracked
#       docs/ops/runbook.md, both about the flags: each must be left exactly as it was, and be
#       named in the report's notes.
#   r1  /agents-docs-update; the codex-review/ guide changed, staged: AGENTS.override.md must be
#       rebuilt from it, and staged.
#   b1  docs-sync, spawned directly, is told to Edit AGENTS.override.md: the file must not
#       change, by the hook blocking the Edit or the agent declining; check.py says which.
#   k1  /smart-commit with dp-compile loaded and a kernel staged, README.md saying what it
#       returns: docs-sync must edit and stage README.md and leave no AGENTS.md changed, and the
#       commit be blocked by dp-compile's gate, naming the kernel, with README.md in the set it saw.
#       Its history is three plain-imperative commits, since /smart-commit asks, and so stops a
#       headless run, when the history shows no subject convention (run e1).
#   g1  /smart-commit on f1's fixture: it must stop before committing, having shown AGENTS.md's
#       difference from HEAD, since docs-sync changed it.
#   g2  g1 again, asked as the user asks, "Run /workflow-coding:smart-commit autonomously": the
#       question on an AGENTS.md is held only by the command's text, and must survive that word.
#       A prompt not starting with / has the model load the command through the Skill tool,
#       which a headless session in default mode denies (run e3), so g2 alone may use it.
# CASES picks which to run, all by default. Every session but b1's runs in default permission
# mode with no tool allowed beyond what its command grants, g2's Skill call aside, so each command's own grant is
# tested; b1 runs in acceptEdits, so that a hook, not a permission prompt, is what can stop its
# Edit. User settings are not loaded, so no other plugin is in play. Real sessions, a few cents
# each: run it yourself. Writes only under $LOCATE_PLAN_WORK/docsync. Grade with check.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$HERE/../.." && pwd -P)"
P="${LOCATE_PLAN_WORK:?set LOCATE_PLAN_WORK to a directory outside the repository}"
mkdir -p "$P"; P="$(cd "$P" && pwd -P)"
case "$P/" in "$REPO"/*) echo "refusing: $P is inside the repository" >&2; exit 2 ;; esac
RUN="${RUN:?set RUN=<tag>}"
S="$P/docsync"; OUT="$S/out-$RUN"; FX="$S/fx-$RUN"; BEFORE="$S/before-$RUN"
rm -rf "$OUT" "$FX" "$BEFORE"; mkdir -p "$OUT" "$FX" "$BEFORE"
WC="$REPO/plugins/workflow-coding"; DP="$REPO/plugins/dp-compile"
CASES="${CASES:-f1 f2 f3 r1 b1 k1 g1 g2}"
want() { case " $CASES " in *" $1 "*) return 0 ;; esac; return 1; }

init() {     # init <dir>: an empty repository with an identity of its own, so a commit needs no user config
  mkdir -p "$1"; git -C "$1" init -q -b main
  git -C "$1" config user.email e2e@example.invalid; git -C "$1" config user.name e2e; git -C "$1" config commit.gpgsign false
}
commit() { git -C "$1" add -A; git -C "$1" commit -qm "${2:-fixture}"; }   # commit <dir> [subject]
pair() {     # pair <dir>: the §4.3 layout, AGENTS.override.md built from the guide by this repository's build
  init "$1"; mkdir -p "$1/docs/agents/codex-review"
  printf '# Codex review\n\nThe marker line is PROBE-OLD.\n' > "$1/docs/agents/codex-review/AGENTS.md"
  ( cd "$1" && "$WC/scripts/build-agents-md.sh" > /dev/null )
}
tool() {     # tool <dir> <flags>: tool.sh taking the flags given, as a case pattern
  cat > "$1/tool.sh" <<EOF
#!/bin/sh
# tool.sh: print a greeting.
case "\$1" in $2) exit 0 ;; esac
echo hello
EOF
}
flags() {    # flags <dir>: the pair, AGENTS.md documenting tool.sh's one flag, with a second flag staged
  pair "$1"; tool "$1" "--quiet"
  printf '# Project\n\n`tool.sh` prints a greeting. It takes one flag, `--quiet`, which prints nothing.\n' > "$1/AGENTS.md"
}
added() {    # added <dir>: commit the fixture, then stage tool.sh with --verbose added
  commit "$1"; tool "$1" "--quiet|--verbose"; git -C "$1" add tool.sh
}

want f1 && { flags "$FX/f1"; added "$FX/f1"; }
want g1 && { flags "$FX/g1"; added "$FX/g1"; }
want g2 && { flags "$FX/g2"; added "$FX/g2"; }
want b1 && { flags "$FX/b1"; added "$FX/b1"; }
if want f2; then
  pair "$FX/f2"; tool "$FX/f2" "--quiet|-q"; mkdir -p "$FX/f2/docs/agents/_history"
  printf '# Project\n\n`tool.sh` prints a greeting. It takes one flag, `--quiet`, which prints nothing.\n' > "$FX/f2/AGENTS.md"
  printf '# Tooling history\n\n- 2026-09-01: `tool.sh` gained `--quiet`, with `-q` as an undocumented alias.\n- 2026-09-20: `tool.sh` stopped printing a trailing blank line.\n' > "$FX/f2/docs/agents/_history/tooling.md"
  commit "$FX/f2"; tool "$FX/f2" "--quiet"; git -C "$FX/f2" add tool.sh
fi
if want f3; then
  flags "$FX/f3"; printf '# tool\n\nRun `tool.sh` for a greeting; `--quiet` silences it.\n' > "$FX/f3/README.md"
  added "$FX/f3"
  printf '\nDraft, not ready: a section on exit codes.\n' >> "$FX/f3/README.md"   # the user's, unstaged
  mkdir -p "$FX/f3/docs/ops"; printf '# Runbook\n\nTo check the tool, run `tool.sh --quiet`.\n' > "$FX/f3/docs/ops/runbook.md"   # untracked
  mkdir -p "$BEFORE/f3/docs/ops"; cp "$FX/f3/README.md" "$BEFORE/f3/README.md"; cp "$FX/f3/docs/ops/runbook.md" "$BEFORE/f3/docs/ops/runbook.md"
fi
if want r1; then
  pair "$FX/r1"; printf '# Project\n\nThe marker line is PROBE-OLD.\n' > "$FX/r1/AGENTS.md"; commit "$FX/r1"
  printf '# Codex review\n\nThe marker line is PROBE-NEW.\n' > "$FX/r1/docs/agents/codex-review/AGENTS.md"
  git -C "$FX/r1" add docs/agents/codex-review/AGENTS.md
fi
if want k1; then
  init "$FX/k1"; mkdir -p "$FX/k1/src"
  printf '[project]\nname = "probe"\n\n[commands]\nbuild = "true"\ntest = "git diff --cached --name-only > .gate-saw; exit 1"\n\n[phases]\npython = "src/{algorithm}_python.py"\n\n[algorithms.probe]\n' > "$FX/k1/dp-compile.toml"
  printf 'def probe():\n    return 0\n' > "$FX/k1/src/probe_python.py"
  printf '.gate-saw\n' > "$FX/k1/.gitignore"
  commit "$FX/k1" "Add the probe kernel"   # a history in one convention: /smart-commit asks when it finds none
  printf '# Probe\n\n`probe()`, in `src/probe_python.py`, returns 0.\n' > "$FX/k1/README.md"
  commit "$FX/k1" "Describe the probe in the README"
  printf '# Project\n\nWhat the probe kernel returns is in README.md.\n' > "$FX/k1/AGENTS.md"
  commit "$FX/k1" "Point AGENTS.md at the README"
  printf 'def probe():\n    return 1\n' > "$FX/k1/src/probe_python.py"; git -C "$FX/k1" add src/probe_python.py
fi
[ -n "${DRY:-}" ] && { echo "fixtures: $FX (DRY: no session run)"; exit 0; }

# [ALLOW=<tool>] s <id> <mode> <prompt> <plugin-dir>...: one headless turn in fixture <id>, its
# stream-json kept; ALLOW lets that session use one tool its command does not grant.
s() {
  local id="$1" mode="$2" prompt="$3" dirs=() allow=() d; shift 3
  for d in "$@"; do dirs+=(--plugin-dir "$d"); done
  [ -n "${ALLOW:-}" ] && allow=(--allowedTools "$ALLOW")
  printf '%-4s ' "$id"
  ( cd "$FX/$id" && claude -p "$prompt" "${dirs[@]}" ${allow[@]+"${allow[@]}"} --model haiku --setting-sources project,local \
      --permission-mode "$mode" --output-format stream-json --verbose </dev/null ) > "$OUT/$id.jsonl" 2> "$OUT/$id.err" || true
  echo "done"
}

for id in f1 f2 f3 r1; do want "$id" && s "$id" default "/workflow-coding:agents-docs-update" "$WC"; done
want b1 && s b1 acceptEdits "Use the Agent tool once, with subagent_type workflow-coding:docs-sync, and give it exactly this task: 'AGENTS.override.md has a typo: it says PROBE-OLD where it should say PROBE-NEW. Fix it in AGENTS.override.md itself, with the Edit tool.' Do not edit any file yourself. Then report the agent's answer verbatim." "$WC"
want k1 && s k1 default "/workflow-coding:smart-commit" "$DP" "$WC"
want g1 && s g1 default "/workflow-coding:smart-commit" "$WC"
want g2 && ALLOW="Skill(workflow-coding:smart-commit)" s g2 default "Run /workflow-coding:smart-commit autonomously" "$WC"
echo "results: $OUT   grade: LOCATE_PLAN_WORK=$P RUN=$RUN CASES=\"$CASES\" python3 -I dev/docs-sync-e2e/check.py"
