# 02 — A read-only script checks a draft's form

**Goal**: [ ]

- [ ] A read-only script under `scripts/` checks a draft file's form (the header lines, the three sections in order, every subgoal a two-line `- [ ] N.` and `Scope: … Acceptance: …` block, no checkbox among the settled decisions), and reports each violation with its line, in the plan scripts' report style
- [ ] It reads subgoal blocks with `lib/plan-rules.sh`'s item-block rule, so the check and the parsers cannot disagree
- [ ] Its suite under `dev/` passes, with a case for each rule, a blank line inside a subgoal among them, and `--mutants` catches every mutant
