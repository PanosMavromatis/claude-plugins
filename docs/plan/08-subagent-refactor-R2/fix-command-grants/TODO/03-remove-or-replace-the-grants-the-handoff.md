# 03 — Remove or replace the grants the handoff lists

**Goal**: [x]
> **Note:** `new-branch.md` never names `Glob` or `Grep`; `step.md` and `hitl-step.md` say to use them "if your session has them"; `smart-commit.md`'s own text runs neither `find` nor `cat` (the docs-update skill it invokes does, under its own grants) and never names its `Glob` and `Grep`. The permissions docs class `Grep`, like file reads, as read-only, needing no approval inside the working directory.
> **Q:** `Glob` and `Grep` need no approval inside the working directory, and the commands never search outside it. Should `/step` and `/hitl-step` lose those grants too, though their text uses the tools when present (A), or keep them there (B)?
> **A:** A: removed from all four commands, `smart-commit.md` included; a grant that changes nothing is dead weight. The text that says to use the tools if present stays.
> **Q:** `/smart-merge`'s `gh` path writes the PR body to `/tmp`, then `rm`s it, which always prompts. Should it write the body where no cleanup is needed and drop the `rm` (A), or keep the `rm` and fix only the e2e harness's allow rule (B)?
> **A:** A: as `/master-plan`'s reply, the body goes to the session's scratchpad, or else `/tmp/pr-body-<repository>-<branch>.md`, read first if left from an earlier run, and is never deleted. Goal 04 drops `run.sh`'s and `check.py`'s `rm` allowance.
> **Done:** Every grant the handoff listed is gone, along with `smart-commit.md`'s `Glob` and `Grep`. The `gh` path now writes its body where no cleanup is needed, so no `rm` is left to prompt.

- [x] `Glob` and `Grep` are gone from `new-branch.md`, `step.md` and `hitl-step.md`, and `Bash(find:*)` and `Bash(cat:*)` from `smart-commit.md`, unless the command's text runs them
  > **Note:** `Glob` and `Grep` are gone from `new-branch.md`, `step.md`, `hitl-step.md` and `smart-commit.md`, and `Bash(find:*)` and `Bash(cat:*)` from `smart-commit.md`; no other grant changed. `step.md` and `hitl-step.md` still say to use the tools if present, which needs no grant inside the repository.
- [x] A `gh`-path merge no longer ends in a refused `rm` of its body file
  > **Note:** The `gh` fallback writes the body to the scratchpad's `pr-body.md`, or else `/tmp/pr-body-<repository>-<flattened-branch>.md`, reading a leftover first, and never deletes it. The `rm` is gone, and so is its place in the Guidelines' list of gates. The e2e `gh` stub copies any `--body-file` path, so only goal 04's allowance changes.
- [x] `dev/command-phrasing` passes, and the Step 1 sections of `/step` and `/hitl-step` stay byte-identical apart from the filename
  > **Note:** `check.py` passes all 16 commands. The Step 1 sections, extracted and substituted in one `python3 -I` script, are identical.
