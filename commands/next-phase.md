---
description: "Advance an algorithm to the next implementation phase"
---

# /next-phase

Advance an algorithm to the next implementation phase.

## Behavior

1. Accept algorithm name as argument.
2. Run `/phase-check` first. If current phase is failing (tests fail or formalization not approved), stop and fix.
3. If Phase 0 → Phase 1: invoke `algorithm-prototype` skill.
4. If Phase 1 → Phase 2: invoke `cython-translation` skill.
5. If Phase 2 → Phase 3: invoke `gpu-parallelization` skill.
6. If Phase 3: "This algorithm is fully implemented across all backends."
