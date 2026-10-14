# 03 — /master-plan runs the form check and judges fidelity from the trace

**Goal**: [ ]

- [ ] `commands/master-plan.md` step 3 runs the script on the draft in place of reading the form itself, and judges fidelity from the trace rather than by re-reading the spec: an unresolved tag becomes a question for the user, and a doubtful subgoal is checked by reading only the section its tag names
- [ ] Once the plan is written, `/master-plan` runs the script with `--plan` on it, so the review's edits reach the user checked, and runs it again after the user approves the commit, immediately before `git add`, whether or not an edit was mentioned: a hand edit or a formatter's save made outside the session reaches the commit checked, and a failure there stops the commit. A dry run, which commits nothing, runs it once on the file it wrote
- [ ] The command's `allowed-tools` grants the script and nothing wider, and its text leads to no `git -C` and no shell read outside the repository
