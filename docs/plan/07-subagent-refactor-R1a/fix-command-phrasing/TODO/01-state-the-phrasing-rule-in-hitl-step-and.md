# 01 — State the phrasing rule in /hitl-step and /step

**Goal**: [x]
> **Done:** `/hitl-step` and `/step` state the phrasing rule at the head of Step 3, where their sessions work, and grant `git show` and `git ls-files`, read-only; Step 1 stays in lockstep.
> **Q:** Two of the `git -C` denials used subcommands the step commands do not grant even plainly, `git show` (e5) and `git ls-files` (e4-step): grant both, read-only, in `/hitl-step` and `/step` (A), or state the rule only, naming the granted subcommands (B)?
> **A:** A.

- [x] `commands/hitl-step.md` states the rule where its session does its work, not only where it runs its scripts: `git` as `git <subcommand>` from the repository, never `git -C <path>`, and every command alone, never chained or piped, with the reason, that `allowed-tools` matches only the plain, single command
  > **Note:** Step 3 opens with **Phrase each command so `allowed-tools` matches it**: `git <subcommand>`, never `git -C`, and every command alone, with the reason. As answered above, `allowed-tools` also grants `git show` and `git ls-files`, read-only, since e5 and e4-step reached for them in plain checks; dropping the `-C` alone would not have let either through.
- [x] `commands/step.md` states the same rule where its session does its work
  > **Note:** `step.md` gains the same paragraph, word for word, at the head of its Step 3, and the same two grants.
- [x] Step 1 stays byte-identical between the two: the lockstep diff comes out empty
  > **Note:** Step 1 is untouched in both; the lockstep check of `CLAUDE.md:200` comes out empty, 65 lines each.
