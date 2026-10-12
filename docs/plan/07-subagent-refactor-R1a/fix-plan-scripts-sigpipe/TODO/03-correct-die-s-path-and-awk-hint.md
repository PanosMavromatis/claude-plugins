# 03 — Correct die's PATH and awk hint

**Goal**: [~]
> **Q:** The new `die` branches for statuses 141 and 3 have no suite case. Pin them with two close-revision cases using a `cat` stub that kills itself with SIGPIPE, as a goal 03 subgoal (A), add that to goal 04 instead (B), or rely on the scratchpad runs (C)?
> **A:** A.
> **Q:** close-revision.sh:277 and :282 pipe `src` into `section_line /dev/stdin` and `pointer_line /dev/stdin`, which stop at the first match, so goals 01 and 02 missed two early-exit readers. Fix it in plan-rules.sh as a new goal 01a (A), as a goal 03 subgoal (B), or in close-revision.sh's callers (C)?
> **A:** A.

- [x] Read `die` (`lib/plan-rules.sh:34-41`) and the failures that reach it
  > **Note:** `die` is at plan-rules.sh:25-42, and its hint at :30-40 blames PATH for any failing status of awk, find, sort or git. The R1 close hit it twice per failure. The writer: `cat … || die "cat failed reading X"` ran at 141 when SIGPIPE killed cat, with no hint since cat is not in the list (under `--check`, `git show` at 141 would get "the git first on PATH is …"). The reader: the pipeline then failed with die's own status 3, so the outer `|| die "awk failed reading the status of X"` printed "the awk first on PATH is /usr/bin/awk, and it exited with status 3; check PATH, or that awk". The suites assert hints only for statuses 127, 2, 128 and 126, so new branches for 141 and 3 leave them alone. Only 141 gets a branch, not every status above 128: git exits 129 on its own usage errors.
- [x] Reword the hint so that a writer killed by SIGPIPE (status 141) is not blamed on PATH or awk
  > **Note:** die now checks the status before the tool. 141 gets a SIGPIPE hint, 3 gets a hint that the cause is reported above, and neither names a binary or PATH; every other status keeps its old hint. Tried in the scratchpad with stubs on PATH: a `cat` that kills itself with SIGPIPE (the close) and a `git` that does so on `show` (`--check`). Before, the close blamed awk for status 3 and the check also blamed git and PATH for 141; after, both print the two new hints.
- [x] A close-revision suite case pins each new hint, with a `cat` stub on PATH that kills itself with SIGPIPE: one case for status 141, one for status 3
  > **Note:** t04 and t05 run on the revisions-index fixture, where stamp's `|| die` at close-revision.sh:199 prints the status-3 hint; on a legacy root plan the first src is :277, which has no outer die. Both pass with the new die and fail against the installed 0.10.0 script's old die, so each pins its hint.
- [ ] Every suite of a script that sources `lib/plan-rules.sh` still passes
