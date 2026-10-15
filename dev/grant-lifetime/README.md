# How long an allowed-tools grant lasts

The skills docs (code.claude.com/docs/en/skills.md, "Pre-approve tools for a skill") say an
`allowed-tools` grant applies "during the turn that invokes the skill" and "clears when you
send your next message", and that a command file accepts the same frontmatter. They do not
say whether that holds for a plugin's command files, or whether a `claude -p --continue` or
`--resume` turn counts as the next message. This measures it. The plugin's "Scoped
`allowed-tools`" convention rests on the answer: a command that confirms before it writes
does the write in the turn after the user's reply.

`plugin/` is a one-command fixture. `/grant-probe:probe <n>` grants one harmless write,
`Bash(touch probe-*)`, and runs `touch probe-<n>`. The grant ends in a bare `*`, not `:*`:
`:*` is a trailing ` *`, space included, so `Bash(touch probe-:*)` would never match
`touch probe-1` (run g1 found this). Claude runs each `touch`, with its Bash
tool, in the session's working directory; what is measured is whether that tool call needs
permission. Every session runs in the default permission mode, set explicitly: in auto or
acceptEdits mode the write could pass with no grant at all.

## The scripted probe: headless, a few cents

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository
RUN=g1 dev/grant-lifetime/run.sh                    # four real sessions, on haiku
RUN=g1 python3 -I dev/grant-lifetime/check.py       # grades them; read-only
```

| Case | Turn | Must |
|---|---|---|
| g0 | a fresh session asks for `touch probe-0`, invoking no command | be denied: the control that the write needs the grant |
| g1 | `/grant-probe:probe 1` | run: the turn that invokes the command |
| g2 | the next message, resuming g1's session, asks for `touch probe-2` with no command | the measurement: denied if the grant clears with the next message, run if it lasts |
| g3 | the message after that invokes `/grant-probe:probe 3` again | run: re-invoking re-applies the grant |

If g0 runs, something else allows the write (a settings rule, a sandbox) and the run is void.
Every session runs in one fixture directory, `$LOCATE_PLAN_WORK/grant/fx-<run>`, outside this
repository, so the repository's settings do not load; the probe files land there.

## The interactive check: once, by hand

A headless denial and an interactive prompt may not be the same mechanism, so confirm one
live session agrees. You type the prompts and watch for permission prompts; Claude runs each
`touch` in the directory you start it in:

```bash
mkdir -p /tmp/grant-probe-live
cd /tmp/grant-probe-live
claude --plugin-dir <this repository>/dev/grant-lifetime/plugin --model haiku --permission-mode default
```

The directory's trust prompt comes first: accept it, since the directory is empty. Then type
`/grant-probe` and check that the autocomplete offers `/grant-probe:probe`; if it does not, the
session was started without `--plugin-dir`. Type each step below to Claude as a message, not
as a `!` command: a `!` command runs in your own shell, where no permission is checked. Answer
No to every permission prompt, so no rule is saved.

0. The control. It must prompt; with no prompt, something else allows the write, and the
   steps below mean nothing: stop.
   ```
   Run this shell command, alone, once, and nothing else: touch probe-0
   ```
1. It should run with no prompt.
   ```
   /grant-probe:probe 1
   ```
2. The measurement. A prompt here means the grant cleared with this message; no prompt means
   it lasted.
   ```
   Run this shell command, alone, once, and nothing else: touch probe-2
   ```
3. It should run with no prompt.
   ```
   /grant-probe:probe 3
   ```

## Does a grant reach a subagent? Headless, a few cents

R2's `docs-sync` agent is spawned by commands that grant writes: `/agents-docs-update` grants
`Edit` and `git add`, and `/smart-commit` grants `git commit` and `git push` too. The docs do
not say whether a command's grant reaches a subagent it spawns. If it does not, the agent's
writes are denied headless and prompt interactively; if it does, a subagent could commit under
`/smart-commit` with nothing but its instructions to stop it.

```bash
A="a0 a1 a2 a2f a3 a3f a4 a5 a5f"
CASES="$A" RUN=a1 dev/grant-lifetime/run.sh                        # nine sessions, on haiku
CASES="$A" RUN=a1 python3 -I dev/grant-lifetime/check.py
CASES="k1 k2" RUN=k1 dev/grant-lifetime/run.sh                     # the guard: two sessions
CASES="k1 k2" RUN=k1 python3 -I dev/grant-lifetime/check.py
```

`/grant-probe:spawn <task>` hands its task to a `general-purpose` subagent, and
`/grant-probe:direct <task>` does it in the main session; both grant `Edit`,
`Bash(git add:*)` and `Bash(git commit:*)`. The stand-in is `general-purpose`, not
`docs-sync`, which would refuse a commit because its body says so: what is measured is
whether anything else would stop it.

| Case | Turn | Must |
|---|---|---|
| a0 | no command: a subagent edits `AGENTS.md` and stages it | be denied: the control that the write needs a grant |
| a1 | `/grant-probe:direct`: the main session makes that edit and stages it | run: the control that the grant covers these tools |
| a2 | `/grant-probe:spawn`: a subagent makes it | the measurement: run if the grant reaches the subagent |
| a3 | `/grant-probe:spawn`: a subagent runs `git commit` with a change staged | the measurement: does a grant for a write the subagent must never make reach it too? |
| a4 | `/grant-probe:direct`: the main session commits | land: the control that the commit grant works |
| a5 | `/grant-probe:relay`: a subagent reads a file, then the main session commits once it returns | the measurement: `/smart-commit`'s shape, where the commit may fall in a later turn |
| a2f, a3f, a5f | a2, a3 and a5 with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | the same, with the subagent in the foreground, inside the command's turn |
| k1 | a3 with `workflow-coding` loaded and `WORKFLOW_CODING_GUARDED_AGENTS=general-purpose` | be blocked by its `guard-agent-git.py`, which the grant alone would pass |
| k2 | a4, loaded the same way | land: the main session's commit carries no `agent_type`, so the guard leaves it alone |

The `Agent` tool starts a subagent in the background by default, and the main session ends
its turn and resumes in a new one on the hand-back. A grant lasts one turn, so a denial in a
background case alone could mean the grant expired rather than never passed down: the
foreground twins tell the two apart. `check.py` reports each subagent case's mode, from an
"Async agent launched" result, and its turns, from its `init` records, and a twin that ran
in the wrong mode is void.

Each a-case runs in its own git fixture under `$LOCATE_PLAN_WORK/grant/fx-<run>/`, with
`--setting-sources project,local`, so no allow rule in the user's settings can pass a write.
`check.py` grades each write, ran, denied, not tried or tried with no effect, for the actor
the case names, from the fixture's files, index and commit count and from the stream-json.

## Results

Run `g1`, 2026-10-14, $0.02: void. g0 was denied, but so were g1 and g3: the probe then
granted `Bash(touch probe-:*)`, which never matches `touch probe-1`.

Run `run2`, 2026-10-14, $0.02, after the fix: g0 denied, g1 ran, g2 denied, g3 ran, all four
in the default permission mode, g1 to g3 one session. **The grant clears with the next
message.** g2's denial gave the same reason as g0's: the write needed approval, as if no grant
had been given.

Interactive, 2026-10-14, haiku, default permission mode: step 0 prompted, 1 ran with no
prompt, 2 prompted, 3 ran with no prompt. A live session agrees.

Run `a1`, 2026-10-14, haiku, Claude Code 2.1.300, $0.04: a0 denied (the subagent's `Edit` got
`Claude requested permissions to write to …`, its `git add` `This command requires
approval`), a1 and a4 ran. **A command's grant reaches the subagents it spawns.** Under
`/grant-probe:spawn` a subagent's `Edit` and `git add` ran (a2, a2f), and so did its
`git commit` (a3, a3f). a3's subagent ran in the background: the main session ended its turn
and resumed on the hand-back, and the commit landed, so the grant was still in force for a
background subagent; a background hand-back is not the next message that clears it. a2 and
a5, meant as background cases, ran in the foreground by the model's choice, so a command
cannot count on either mode; the main session's commit after a foreground hand-back ran (a5,
a5f). Not yet measured: the main session's own commit in the turn that resumes after a
background hand-back. The first grade crashed on a record whose `message` is a string, which
the synthetic streams lacked; `check.py` now skips such records.

Run `k1`, 2026-10-14, haiku, $0.01: **`guard-agent-git.py` holds where the grant would not.**
With `workflow-coding` loaded and `WORKFLOW_CODING_GUARDED_AGENTS=general-purpose`, the
subagent's `git commit -m probe` under `/grant-probe:spawn` came back `PreToolUse:Bash hook
error: […/guard-agent-git.py]: Blocked: general-purpose may not run `git commit`…` and no
commit was made (k1); the main session's commit under `/grant-probe:direct`, loaded the same
way, landed (k2).
