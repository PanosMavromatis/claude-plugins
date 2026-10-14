# 04 — An e2e run of e1, e3 and e4 has no permission denial

**Goal**: [~]

- [x] `run.sh` and `check.py` no longer allow or excuse the body file's `rm`, so a denial of it fails the run
  > **Note:** `run.sh` drops `Bash(rm /tmp/pr-body-:*)` and keeps `--add-dir /tmp`, which the body file itself now needs, since a headless session has no scratchpad. `check.py`'s excuse is gone, and with it `common()`'s `gates`, which nothing else used, so any denial fails a session. The README says where the body goes instead of the `r4` gate.
- [ ] A run of e1, e3 and e4, run by the user, has no permission denial, and the e2e README logs it
