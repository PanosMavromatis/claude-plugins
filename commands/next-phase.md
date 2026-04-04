---
description: "Advance an algorithm to the next implementation phase"
---

# /next-phase

Advance an algorithm to the next implementation phase.

## Behavior

1. Accept algorithm name as argument.
2. Run `/phase-check` first. If current phase is failing (tests fail or formalization not approved), stop and fix.
3. **Handle stale artifacts.** `/phase-check` reports the *effective* phase after
   timestamp analysis. If the effective phase is earlier than the file-existence phase
   (i.e., artifacts are stale), `/next-phase` targets the first stale artifact for
   regeneration — not the next missing file. For example, if `_python.py` and
   `_cython.pyx` both exist but `FORMALIZATION.md` was modified after `_python.py`,
   the effective phase is 0 and `/next-phase` invokes `algorithm-prototype` to
   regenerate `_python.py` from the updated formalization.
4. Route to the appropriate skill based on the effective phase:
   - Phase 0 → Phase 1: invoke `algorithm-prototype` skill.
   - Phase 1 → Phase 2: invoke `cython-translation` skill.
   - Phase 2 → Phase 3: invoke `gpu-parallelization` skill.
   - Phase 3 (no stale artifacts): "This algorithm is fully implemented across all backends."
