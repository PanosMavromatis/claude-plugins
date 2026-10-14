# 02 — check-agents-md.sh keeps its in-sync check and gains two lints

**Goal**: [x]
> **Done:** `check-agents-md.sh` keeps its in-sync check for the pair and lints every hand-authored `AGENTS.md` outside `docs/agents/`, warning on stderr, never changing the exit status. Goal 04's suite makes the fixtures tests.
> **Note:** The in-sync check needed no change for the pair: it builds into a temporary directory and compares what the build produced, which since goal 01 is the `AGENTS.override.md` files only. `/agents-docs-check` is its one caller, and shows its output verbatim.
> **Q:** Should the lints read every `AGENTS.md` that `git ls-files --cached --others --exclude-standard` lists outside `docs/agents/` (the root's and every component's, guides excluded); warn on one over 200 lines and on each line matching `20\d\d-\d\d-\d\d`, with up to five line numbers; print each finding on stderr as `warning: <path>: …`, count them in the last line, keep exit 0 unless the pair has drifted, and run even when it has (A), or differently (B)?
> **A:** A: §4.3 makes `<component>/AGENTS.md` files the source of truth for components, guides are loaded by one subagent each and may carry history, and the exit code keeps its meaning while the warnings stay visible.

- [x] After a build, the check reports the pair in sync. It fails, naming the file, when an `AGENTS.override.md` differs from its guide or is missing
  > **Note:** On fixtures built by goal 01's build, the check reported the pair in sync (exit 0); a hand edit of `ui/AGENTS.override.md` failed it with that file's diff, and a deleted `AGENTS.override.md` with `missing: AGENTS.override.md`, both exit 1. The comparison is the old code unchanged.
- [x] It warns without failing on an `AGENTS.md` over 200 lines and on one with a dated sentence (`20\d\d-\d\d-\d\d`), at the root and in a component
  > **Note:** A 201-line root `AGENTS.md` with seven dated lines, a dated component `ui/AGENTS.md` and a new, untracked `svc/AGENTS.md` gave four warnings on stderr and "(4 warnings)" on the last line, exit 0; exactly 200 lines gave none. A dated guide under `docs/agents/` and a gitignored `vendor/AGENTS.md` were not linted. With drift too, the warnings print and the run exits 1.
