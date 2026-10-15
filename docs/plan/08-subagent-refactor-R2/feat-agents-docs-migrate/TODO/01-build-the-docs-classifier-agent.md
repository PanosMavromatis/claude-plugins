# 01 — Build the docs-classifier agent

**Goal**: [~]
> **Q:** Which tools does `docs-classifier` get, given that `guard-agent-git.py` refuses `find` for every `workflow-coding:` agent?
> **A:** A: `Read, Grep, Glob`, with no `Bash`. `Glob` does what `find` would, subagents keep `Grep` and `Glob` in native builds, and the guard stays as it is.
> **Q:** What shape does a row of the destination table take?
> **A:** A: one row per line range, `| <file>:<start>-<end> | <destination> | <a few words on what it is> | sure / unsure: <why> |`, its destination one of `AGENTS.md` or `<component>/AGENTS.md`, `docs/agents/<guide>/AGENTS.md`, `docs/agents/_history/<area>.md`, or `drop: <path>[:<line>]` naming the file that already carries it. Every non-blank line of each source falls in exactly one row, which goal 02's script checks; a row with the wrong number of columns fails it closed.
> **Q:** Is a `codex.md` classified, or moved whole by rule?
> **A:** A: moved whole by rule. The command moves each `docs/agents/[<path>/]codex.md` unchanged to `docs/agents/[<path>/]codex-review/AGENTS.md`, as §4.3's "as-is" says, and the classifier never gets it as a source; the coverage check counts it as one row. The classifier may still route a `core.md` or `claude.md` paragraph to `codex-review/` when only the reviewer needs it.
> **Q:** How does the classifier choose guide names?
> **A:** A: freely from the guides with a reader, `codex-review`, `docs-sync` and `pr-drafter`, and any `docs/agents/<guide>/` already on disk; any other name, `kernel` or `release` among them, is allowed but flagged `unsure`, naming who would read it, so Checkpoint 1 decides it.
> **Q:** Where does text go that is obsolete rather than duplicated, such as a dispatcher layout's description of itself?
> **A:** A: a sixth destination form, `drop: obsolete — <why>`, always flagged `unsure`, so Checkpoint 1 puts each one to the user and Checkpoint 2 shows it in full with its reason. The coverage script counts a `drop` row as accounted for only if it carries a reason: a path for a duplicate, prose for an obsolete one.

- [x] `plugins/workflow-coding/agents/docs-classifier.md` carries §4.1's row, but for its tools: model `sonnet`, a `color`, and tools `Read, Grep, Glob`, with no `Bash`, none of which writes.
  > **Note:** §4.1's row gives `Bash(find:*)`, but `guard-agent-git.py:162` refuses `find`, as every command off its allowlist, for each `workflow-coding:` agent, and `Glob` does the same job: native builds dropped `Grep` and `Glob` from the main session at 2.1.117, not from subagents (plugin `CLAUDE.md:114`).
- [ ] Its description takes §4.1's form in under 400 characters and says not to use it outside `/agents-docs-migrate`; its body opens with "When to invoke", then the guide, return and must-not paragraphs, in under 3,000 characters.
- [ ] Given a legacy `CLAUDE.md`, the dispatcher layout's `docs/agents/{core,claude,codex}.md`, or an oversized `AGENTS.md`, it returns one row per section, or per paragraph inside a "Current state"-shaped section, each with one destination: `AGENTS.md`, `docs/agents/<guide>/AGENTS.md`, `docs/agents/_history/<area>.md`, or dropped as duplicated by a named ADR or plan; it flags every row it is unsure of.
- [ ] It passes `validate-agent.sh` and the `plugin-dev:plugin-validator` agent.
