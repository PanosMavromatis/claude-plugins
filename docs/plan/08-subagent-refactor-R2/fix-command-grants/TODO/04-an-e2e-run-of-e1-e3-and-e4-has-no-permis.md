# 04 — An e2e run of e1, e3 and e4 has no permission denial

**Goal**: [x]
> **Done:** The e2e harness no longer allows or excuses the body file's `rm`, and run `r15` of e1, e3 and e4 passed with no permission denial in any session, under the trimmed grants.

- [x] `run.sh` and `check.py` no longer allow or excuse the body file's `rm`, so a denial of it fails the run
  > **Note:** `run.sh` drops `Bash(rm /tmp/pr-body-:*)` and keeps `--add-dir /tmp`, which the body file itself now needs, since a headless session has no scratchpad. `check.py`'s excuse is gone, and with it `common()`'s `gates`, which nothing else used, so any denial fails a session. The README says where the body goes instead of the `r4` gate.
- [x] A run of e1, e3 and e4, run by the user, has no permission denial, and the e2e README logs it
  > **Note:** Run `r15`: every check passed, $5.36, with no denial in any of the nine sessions. Each merge session read its body file, found none, wrote `/tmp/pr-body-<repository>-<flattened-branch>.md`, passed it to `gh pr create`, and ran no `rm`. Logged in `dev/per-goal-e2e/README.md`.
