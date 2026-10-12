# 01a — Make section_line and pointer_line read to EOF

**Goal**: [x]
> **Done:** section_line and pointer_line read to EOF, so close-revision.sh:277 and :282 no longer stop early on src's pipe; both suites and both mutant sets pass.
> **Note:** Found during goal 03, and independently by a side agent. close-revision.sh:277 and :282 pipe `src` into `section_line /dev/stdin` and `pointer_line /dev/stdin`, whose awks (plan-rules.sh:520 and :524) print the first match and `exit`. Goals 01 and 02 counted them safe because they take a file argument, but there that argument is the pipe; the suite's t02 and t03, which expect "awk failed reading /dev/stdin", show the same thing. A legacy close of a root plan larger than the pipe buffer can therefore kill `cat`, or `git show` under `--check`.

- [x] Give both awks goal 01's guard (`got { next }` … `got = 1`), so each still prints only the first match but reads to EOF
  > **Note:** Both awks now start with `got { next }` and set `got = 1` where they exited, and the comment above them says why. Tried in the scratchpad first: close-revision 60 of 60 and propose-revision 0 failing against the draft, and given three matching headings the section matcher still prints only the first (line 2, the subtitled one).
- [x] Their file-argument callers, propose-revision.sh:235 and :237, behave as before: the close-revision and propose-revision suites pass
  > **Note:** Both pass against the repo copy: close-revision 60 of 60, and propose-revision 0 failing, including its l01–l15 cases, which read a legacy root plan through those two callers.
- [x] `--mutants` still kills every mutant in both suites; re-anchor any whose patch context is the edited lines, as goal 01 did
  > **Note:** The edit made 12 patches stale and let none survive: close-revision's l01–l03 and propose-revision's v01–v08 and v10, whose context was the edited lines. Each was re-anchored by applying its own mutation to the new text and taking `diff -u`; then close-revision killed 40 of 40 and propose-revision 36 of 36, none stale. v08 (the label through `-v` rather than ENVIRON) is still killed by l11's `a\tb` label.
