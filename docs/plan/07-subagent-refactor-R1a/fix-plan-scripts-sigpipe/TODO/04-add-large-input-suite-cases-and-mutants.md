# 04 — Add large-input suite cases and mutants

**Goal**: [ ]

- [ ] Measure first: does the unfixed script fail on every run against a >64 KB plan, or only sometimes? A case that catches the bug intermittently is not a test; choose the size from the measurement
  > **Note:** A side agent's suggestion, taken up (2026-10-12): a plan just over 64 KB may pass on broken code most of the time, so measure with a much larger plan (around 1 MB) and run it several times. The installed 0.10.0 `close-revision.sh` is byte-identical to the pre-fix script, so measure the old code there, with the fixed working tree as the control. By theory a file well past the pipe buffer fails every run, but 50 clean `cat | awk` runs contradict that (perhaps SIGPIPE is ignored in the harness's shells), so the measurement decides.
- [ ] A close-revision case closes a plan larger than 64 KB, both the close and its `--check`
  > **Note:** To reach goal 01a's two sites the large file must be a legacy root plan, since only extract calls section_line and pointer_line.
- [ ] Mutants that put back `exit` at the seven sites (close-revision.sh's five, and section_line and pointer_line in lib/plan-rules.sh), and `--mutants` catches each, including `:365`'s silent one (it needs a directory list larger than the pipe buffer)
- [ ] A large-input case in the suite of each script that goal 02 changes
  > **Note:** Goal 02 changed no script (see its goal file), so this subgoal has nothing to cover. Expect `[-]` when goal 04 runs.
- [ ] `dev/close-revision/README.md` describes the new cases
