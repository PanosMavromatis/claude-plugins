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

## Results

Run `g1`, 2026-10-14, $0.02: void. g0 was denied, but so were g1 and g3: the probe then
granted `Bash(touch probe-:*)`, which never matches `touch probe-1`.

Run `run2`, 2026-10-14, $0.02, after the fix: g0 denied, g1 ran, g2 denied, g3 ran, all four
in the default permission mode, g1 to g3 one session. **The grant clears with the next
message.** g2's denial gave the same reason as g0's: the write needed approval, as if no grant
had been given.

Interactive, 2026-10-14, haiku, default permission mode: step 0 prompted, 1 ran with no
prompt, 2 prompted, 3 ran with no prompt. A live session agrees.
