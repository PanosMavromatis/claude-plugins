# 01a — Make section_line and pointer_line read to EOF

**Goal**: [ ]
> **Note:** Found during goal 03, and independently by a side agent. close-revision.sh:277 and :282 pipe `src` into `section_line /dev/stdin` and `pointer_line /dev/stdin`, whose awks (plan-rules.sh:520 and :524) print the first match and `exit`. Goals 01 and 02 counted them safe because they take a file argument, but there that argument is the pipe; the suite's t02 and t03, which expect "awk failed reading /dev/stdin", show the same thing. A legacy close of a root plan larger than the pipe buffer can therefore kill `cat`, or `git show` under `--check`.

- [ ] Give both awks goal 01's guard (`got { next }` … `got = 1`), so each still prints only the first match but reads to EOF
- [ ] Their file-argument callers, propose-revision.sh:235 and :237, behave as before: the close-revision and propose-revision suites pass
- [ ] `--mutants` still kills every mutant in both suites; re-anchor any whose patch context is the edited lines, as goal 01 did
