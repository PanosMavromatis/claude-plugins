# 02 — Reword any pointer a session searched around

**Goal**: [x]
> **Done:** No pointer needed rewording: run r12 had no session search the plugin's directory, and `dev/command-phrasing` passes its check, 35 cases and 13 mutants, so the five pointers stand as `fix/command-phrasing` left them.

- [x] Each pointer a session read or searched around from the shell is reworded so the session `Read`s it, and its scenario passes on a rerun; if the run shows none was, a Note here says so with the run's tag, and no pointer changes
  > **Note:** None was: in run r12 (goal 01) no session read or searched the plugin's directory from the shell, which `check.py` now fails, and every session that commits `Read` `smart-commit.md` before its first commit. No pointer changes.
- [x] `dev/command-phrasing/check.py` passes, its cases and mutants included
  > **Note:** On `5183f85`: `check.py` 0 failing (11 commands ok, 5 skipped as granting no `git`), `suite.py` 35 of 35 cases passing, `--mutants` 13 of 13 killed.
