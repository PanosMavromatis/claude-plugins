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
3. For Phase 0: check that `FORMALIZATION.md` exists and is non-empty; ask the user whether the formalization has been reviewed and approved.
4. For Phases 1–3: run the tests for all existing backends.
5. Report: which phase, test/review status, and what's needed to advance.