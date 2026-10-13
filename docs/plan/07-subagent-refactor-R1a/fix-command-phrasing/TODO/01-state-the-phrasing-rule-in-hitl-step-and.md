# 01 — State the phrasing rule in /hitl-step and /step

**Goal**: [ ]

- [ ] `commands/hitl-step.md` states the rule where its session does its work, not only where it runs its scripts: `git` as `git <subcommand>` from the repository, never `git -C <path>`, and every command alone, never chained or piped, with the reason, that `allowed-tools` matches only the plain, single command
- [ ] `commands/step.md` states the same rule where its session does its work
- [ ] Step 1 stays byte-identical between the two: the lockstep diff comes out empty
