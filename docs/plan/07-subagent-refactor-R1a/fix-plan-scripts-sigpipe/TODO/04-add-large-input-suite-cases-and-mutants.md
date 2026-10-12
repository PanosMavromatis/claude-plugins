# 04 — Add large-input suite cases and mutants

**Goal**: [ ]

- [ ] Measure first: does the unfixed script fail on every run against a >64 KB plan, or only sometimes? A case that catches the bug intermittently is not a test; choose the size from the measurement
  > **Note:** A side agent's suggestion, taken up (2026-10-12): a plan just over 64 KB may pass on broken code most of the time, so measure with a much larger plan (around 1 MB) and run it several times. The installed 0.10.0 `close-revision.sh` is byte-identical to the pre-fix script, so measure the old code there, with the fixed working tree as the control. By theory a file well past the pipe buffer fails every run, but 50 clean `cat | awk` runs contradict that (perhaps SIGPIPE is ignored in the harness's shells), so the measurement decides.
- [ ] A close-revision case closes a plan larger than 64 KB, both the close and its `--check`
- [ ] Mutants that put back `exit` at the five sites, and `--mutants` catches each, including `:365`'s silent one (it needs a directory list larger than the pipe buffer)
- [ ] A large-input case in the suite of each script that goal 02 changes
- [ ] `dev/close-revision/README.md` describes the new cases
