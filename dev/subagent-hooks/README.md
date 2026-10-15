# Do hooks fire inside a subagent?

R2 subgoal 8 moves `/agents-docs-update`'s work into a subagent, `docs-sync`. Two things
it relies on are tested here before the agent is built, as the subgoal asks:

- that `workflow-coding`'s `protect-agent-docs.py`, a `PreToolUse` hook on
  `Write|Edit|MultiEdit`, fires on an `Edit` a subagent makes. If it does not, an agent
  could rewrite a generated `AGENTS.override.md` unchecked, and `/agents-docs-update` must
  re-run `check-agents-md.sh` after the agent returns (§8 of the design);
- that `dp-compile`'s gate, a `PreToolUse` hook on `Bash` that reads the staged set when a
  `git commit` runs, still sees the docs a subagent has staged before the main session
  commits.

## The probe: headless, a few cents

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite               # outside this repository
RUN=s1 dev/subagent-hooks/run.sh                    # four real sessions, on haiku
RUN=s1 python3 -I dev/subagent-hooks/check.py       # grades them; read-only
CASES=m1 RUN=m1 dev/subagent-hooks/run.sh           # docs-sync's memory directory: one session
CASES=m1 RUN=m1 python3 -I dev/subagent-hooks/check.py
CASES=i1 RUN=i1 dev/subagent-hooks/run.sh           # what a hook's input says about who called
CASES=i1 RUN=i1 python3 -I dev/subagent-hooks/check.py
```

| Case | Who acts | Must |
|---|---|---|
| h0 | the main session `Edit`s `AGENTS.override.md` | be blocked: the control that the hook is loaded and fires |
| h1 | a `general-purpose` subagent `Edit`s `AGENTS.override.md` | the measurement: blocked if hooks fire inside a subagent, edited if not |
| h2 | a subagent `Edit`s `AGENTS.md`, which no hook protects | be edited: the control that a subagent's edit lands |
| d1 | a subagent edits and stages `AGENTS.md`; the main session runs `git commit` with a kernel staged | be blocked by the gate, which names the kernel and records both files staged |
| m1 | `workflow-coding:docs-sync` syncs a staged CLI-flag change and saves one memory entry; run only when `CASES` names it | write an agent-memory directory: which name a plugin agent gets there (D-N7) |
| i1 | with `inputs-plugin` loaded, whose `PreToolUse` hook on `Bash` logs every input to `.hook-inputs.jsonl`, the main session, `workflow-coding:docs-sync` and a `general-purpose` subagent each run `git`; run only when `CASES` names it | show a call from each, and what identifies it: `agent_type`, `agent_id`, or neither |

h1 counts only between its controls. If h0 is not blocked, the hook never loaded; if h2 does
not land, a subagent cannot edit, and an unchanged file in h1 proves nothing. h1 counts only
if the subagent itself attempted the `Edit`, which `check.py` reads from the tool calls that
carry a `parent_tool_use_id` in the stream-json, or, if the stream holds none, from the
session's subagent transcripts under `~/.claude/projects`.

Each case runs in a fresh fixture repository under `$LOCATE_PLAN_WORK/subhooks/fx-<run>`,
outside this repository, with this repository's plugin loaded by `--plugin-dir`, so what
fires is the hook as it stands here, not an installed copy. d1 loads `dp-compile` together
with `workflow-coding`, as a consumer does: `dp-compile`'s manifest declares `workflow-coding`
a dependency, and a session that loads it alone by `--plugin-dir` drops it without a word,
which voided d1 in run s1. `check.py` reads each session's `init` record and reports a case
whose plugin did not load as exactly that. The h-cases use the §4.3 layout,
whose `AGENTS.override.md` this repository's build writes. d1's `dp-compile.toml` lists one
algorithm whose kernel is staged before the session starts, and its `[commands].test` writes
`git diff --cached --name-only` to `.gate-saw` and fails: the gate prints the kernel's name
only when it blocks, and `.gate-saw` is the staged set exactly as the gate saw it.

Every session runs in `acceptEdits` mode, with `git status`, `git diff`, `git add` and
`git commit -m probe` allowed (runs s1 and s2 allowed only `git add AGENTS.md` and the commit),
so a hook is the only thing that can stop an edit or the commit, and with
`--setting-sources project,local`, so no plugin enabled in the user's settings adds a hook
of its own.

## Results

Run `s1`, 2026-10-14, haiku, Claude Code 2.1.300, $0.02: h0 blocked, h1 blocked, h2 edited;
d1 void. `dp-compile` never loaded: its manifest declares `workflow-coding` a dependency, d1
loaded it alone, and the session dropped it with nothing on stderr, so the commit landed with
no gate. d1 now loads both plugins, and `check.py` checks each session's plugin list.

Run `s2`, 2026-10-14, $0.02, after the fix: all four pass.

- **`protect-agent-docs.py` fires on a subagent's `Edit`.** The subagent's own `Edit` of
  `AGENTS.override.md` came back `PreToolUse:Edit hook error: [...protect-agent-docs.py]:
  Blocked: …`, and the file kept its text, between a blocked main-session `Edit` and a
  subagent's `Edit` of `AGENTS.md` that landed. s1's h-cases agree.
- **`dp-compile`'s gate sees the docs a subagent stages.** The main session's `git commit`
  was blocked, naming `src/probe_python.py`, and `.gate-saw` lists `AGENTS.md` and the
  kernel; both stayed staged, and nothing was committed.

In both runs the `Agent` tool started the subagent in the background, and the main session
acted only on its hand-back: in d1 the commit came after the subagent's `git add`, the
ordering §5.3 of the design asks about.

Run `m1`, 2026-10-14, haiku with `docs-sync` on sonnet, $0.05: **a plugin agent's
`memory: project` directory is `.claude/agent-memory/<plugin>-<agent>/`**, here
`.claude/agent-memory/workflow-coding-docs-sync/`, holding a `MEMORY.md` index and one entry
file. `docs-sync` read its guide (absent), ran `git status` and `git diff --cached` alone,
changed the one `AGENTS.md` line the staged flag made false, ran no build, staged the doc and
its memory together, and returned its four output lines.

Run `i1`, 2026-10-14, $0.04: **a subagent's call carries `agent_id` and `agent_type` in a
`PreToolUse` hook's input, and a plugin agent's `agent_type` is its namespaced name.** The
main session's `git status` came with neither field; `docs-sync`'s four calls (`git diff
--cached`, `git status`, `git add AGENTS.md`, `git status --short`) with
`agent_type: workflow-coding:docs-sync`; the `general-purpose` subagent's with
`agent_type: general-purpose`. Every input also carries `session_id`, `transcript_path`,
`cwd`, `permission_mode`, `prompt_id`, `effort`, `tool_name`, `tool_input` and
`tool_use_id`.
