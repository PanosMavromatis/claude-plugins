# 02 — A suite under dev/memory-check passes

**Goal**: [x]
> **Done:** `dev/memory-check/` tests the script on seven fixture repositories with 29 exact cases and kills all 26 mutants; the root README lists it as the eighth suite sharing `plan-rules.sh`.
> **Q:** Should `dev/memory-check/` follow `dev/check-plan-index/`'s pattern: five fixture repositories (a revisions root with an open and a closed revision, a legacy root, two open revisions, none open, no root plan), cases with exact sizes, the sibling's static checks, with the script's awk comparisons rewritten so a `>` never reads as a redirect, and about 20 mutants (A); or be lighter, with cases and static checks but no mutants (B)?
> **A:** A: every plan script's suite has mutants, and "writes nothing" and "exit status never depends on a size" are guarantees only a mutant shows the checks can catch.

- [x] `dev/memory-check/` builds fixtures for each layout (per-goal, single-file, a legacy root, no plan) and checks the script's report on each
  > **Note:** `suite.py` builds seven repositories: a revisions root with an open and a closed revision, a legacy root, two open revisions, none open, a broken index, no root plan, and the DO model. It runs 29 cases, twice under each Bash found (3.2 and Homebrew's), in about 20 s, and checks a measured report line for line against sizes it computes from the fixture's own bytes. Its static checks required the script's two awk comparisons to be turned around (`th < t`), with no change in behaviour.
- [x] The suite checks that the script writes nothing, and that its exit status does not depend on any file's size
  > **Note:** After every run, `git status --porcelain`, untracked files included, and `HEAD` must be as they were; m02–m04 exit 0 with a file on each side of the threshold. All 26 mutants are killed, each by the rule it breaks: `mc06-warnings-gate` by an exit of 1, and `mc26-writes`, a `touch`, only by the untouched-fixture check.
