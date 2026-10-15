# 03 — Add the version check and the @AGENTS.md shim

**Goal**: [ ]

- [ ] The destructive step comes last and asks first: only after the user confirms are each target's `CLAUDE.md` and `docs/agents/[<path>/]{core,claude,codex}.md` deleted, and a declined confirmation deletes nothing and leaves every written file in place.
- [ ] After the delete, `build-agents-md.sh` rebuilds each `AGENTS.override.md` from its `docs/agents/[<path>/]codex-review/AGENTS.md`, which it refuses to do while a `core.md` or `codex.md` of the old layout is there (goal 02, Q9).
- [ ] A run that stops after `apply` resumes: given the saved reply, the command runs `verify` again and offers the destructive step without classifying again, and if the reply is gone, it says how to undo the move and start again.
  > **Note:** A side agent found that, as goal 02 left it, a second run cannot reach the delete: uncommitted, the clean-tree preflight stops it; committed, it classifies afresh and `apply` refuses as having run (`a07`, `a08`). `verify` with the saved reply needs neither a commit nor a fresh table.
- [ ] The command reads the Claude Code version and, below 2.1.277, writes the two-line `@AGENTS.md` shim as `CLAUDE.md` instead of deleting it.
- [ ] Beside a `CLAUDE.local.md`, it says that file switches native `AGENTS.md` off for its owner, offers the shim or `/config` → `claude-md-and-agents-md`, and says which it did.
- [ ] The version comparison and the shim decision are rules, covered by goal 02's suite.
- [ ] `protect-agent-docs.py` lets the command write the shim from the main session, and still blocks a subagent's write of `CLAUDE.md`.
