# 01 — Measure how long an allowed-tools grant lasts

**Goal**: [x]
> **Note:** The skills docs (code.claude.com/docs/en/skills.md, "Pre-approve tools for a skill") say an `allowed-tools` grant applies "during the turn that invokes the skill" and "clears when you send your next message"; a command file "accepts the same fields except `name` and `paths`". They do not say whether the rule holds for a plugin's command files, or whether a `claude -p --continue` turn counts as the next message.
> **Q:** How is the grant's lifetime measured: a scripted headless probe, a fixture plugin's `/probe` granting one harmless write, run as `claude -p` then `claude -p --continue` with a control that invokes `/probe` again, then one interactive run of it (A); the scripted probe alone (B); or an interactive run alone (C)?
> **A:** A: both. The scripted probe under `dev/grant-lifetime/` is the method the plugin's `CLAUDE.md` cites; the interactive run confirms that a live session prompts where a headless one is denied. The user runs both.
> **Done:** A command's grant lasts one turn: measured headless and interactively with `dev/grant-lifetime/`, and recorded beside the convention, which goal 02 revises by it.

- [x] Whether a command's `allowed-tools` grant still covers a tool call made after the user's next message is measured, by a method someone can repeat
  > **Note:** Run g1 (2026-10-14, $0.02) is void: g0 was denied as it should be, but g1 and g3 were denied too, since the probe's `Bash(touch probe-:*)` never matched `touch probe-1`. The permissions docs: "`:*` is an equivalent way to write a trailing wildcard … The space before a trailing `*` is part of the rule." The e2e harness's `Bash(rm /tmp/pr-body-:*)` has the same fault, which explains r4's "denied even when allowed".
  > **Note:** Run `run2` ($0.02): g0 denied, g1 ran, g2 denied, g3 ran, all in the default permission mode, with g1–g3 one session resumed by its id. The interactive check agreed: the control and the next message prompted, and both invocations ran without one. A command's grant clears with the user's next message.
- [x] The measurement and its method are recorded in the plugin's `CLAUDE.md`, beside the "Scoped `allowed-tools`" convention
  > **Note:** Recorded in the plugin's `CLAUDE.md` as "A grant lasts one turn, measured", beside the convention, with the `:*` trap added to its traps.
