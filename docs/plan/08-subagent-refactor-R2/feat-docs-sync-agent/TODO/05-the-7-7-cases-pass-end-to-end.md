# 05 — The §7.7 cases pass end to end

**Goal**: [ ]
> **Note:** Its runs use `--permission-mode default`, not `acceptEdits`: goal 01's probe pre-approved edits to isolate the hooks, so it says nothing about whether `docs-sync` may write under a user's normal settings.

- [ ] A staged change to a CLI flag edits `AGENTS.md` and commits nothing, and a staged diff of pure history edits `_history/` and leaves `AGENTS.md` alone
- [ ] A `codex-review/` change rebuilds `AGENTS.override.md`, and an `Edit` of `AGENTS.override.md` from inside the agent is blocked by the hook
- [ ] `/smart-commit` with a kernel staged runs `docs-sync` and then the `dp-compile` gate, whose output names the kernel
  > **Note:** The gate names the kernel only when it blocks: a passing run prints a count and "suite passed". So this case, like goal 01's d1, uses a manifest whose `test` writes `git diff --cached --name-only` to `.gate-saw` and fails: the blocked commit's message names the kernel, and `.gate-saw` shows the docs `docs-sync` staged were there when the gate ran. Naming kernels on a pass would change `dp-compile`, which R2 leaves to R4.
