---
description: "Validate whether the current phase of an algorithm is complete"
---

# /phase-check

Check whether an algorithm has completed its current phase.

## Behavior

1. Accept algorithm name as argument (or prompt for it).
2. Determine current phase by checking which files exist in `src/tokalign/algorithms/<name>/`:
   - Only `FORMALIZATION.md` → Phase 0
   - `FORMALIZATION.md` + `_python.py` → Phase 1
   - `FORMALIZATION.md` + `_python.py` + `_cython.pyx` → Phase 2
   - All four files → Phase 3
3. **Check for stale artifacts** using `make`-like timestamp logic. In the dependency
   chain `FORMALIZATION.md` → `_python.py` → `_cython.pyx` → `_numba.py`, a file is
   **stale** if its prerequisite has a more recent modification time. Check timestamps
   with `stat -f %m` (macOS) or `stat -c %Y` (Linux) and compare numerically.
   - `_python.py` is stale if `FORMALIZATION.md` is newer
   - `_cython.pyx` is stale if `_python.py` is newer (or transitively, if `_python.py`
     is itself stale)
   - `_numba.py` is stale if `_cython.pyx` is newer (or transitively stale)

   If any file is stale, report the **effective phase** as the phase just before the
   first stale file, not the phase implied by file existence alone. For example, if
   `_python.py` and `_cython.pyx` both exist but `FORMALIZATION.md` is newer than
   `_python.py`, the effective phase is **Phase 0** (the formalization has been updated
   and the Python backend needs to be regenerated).
4. For Phase 0: check that `FORMALIZATION.md` exists and is non-empty; ask the user whether the formalization has been reviewed and approved.
5. For Phases 1–3: run the tests for all **non-stale** backends only.
6. Report: which phase (noting any stale artifacts and why), test/review status, and
   what's needed to advance. If artifacts are stale, explain which file was modified
   and which downstream files need regeneration.