# 01 — Build the docs-classifier agent

**Goal**: [ ]

- [ ] `plugins/workflow-coding/agents/docs-classifier.md` carries §4.1's row: model `sonnet`, a `color`, and tools `Read, Grep, Glob, Bash(find:*)`, none of which writes.
- [ ] Its description takes §4.1's form in under 400 characters and says not to use it outside `/agents-docs-migrate`; its body opens with "When to invoke", then the guide, return and must-not paragraphs, in under 3,000 characters.
- [ ] Given a legacy `CLAUDE.md`, the dispatcher layout's `docs/agents/{core,claude,codex}.md`, or an oversized `AGENTS.md`, it returns one row per section, or per paragraph inside a "Current state"-shaped section, each with one destination: `AGENTS.md`, `docs/agents/<guide>/AGENTS.md`, `docs/agents/_history/<area>.md`, or dropped as duplicated by a named ADR or plan; it flags every row it is unsure of.
- [ ] It passes `validate-agent.sh` and the `plugin-dev:plugin-validator` agent.
