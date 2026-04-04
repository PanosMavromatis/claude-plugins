# Phase detection — shared reference

This document is the single source of truth for effective-phase calculation. Both `/phase-check` and `/next-phase` include it via `@references/phase-detection.md`.

## Step 1 — File existence

Check which files are present in `src/tokalign/algorithms/<name>/`:

| Files present                                                         | Nominal phase |
| --------------------------------------------------------------------- | ------------- |
| `FORMALIZATION.md` only                                               | Phase 0       |
| `FORMALIZATION.md` + `_python.py`                                     | Phase 1       |
| `FORMALIZATION.md` + `_python.py` + `_cython.pyx`                    | Phase 2       |
| `FORMALIZATION.md` + `_python.py` + `_cython.pyx` + `_numba.py`      | Phase 3       |

## Step 2 — Staleness check

In the dependency chain:

```
FORMALIZATION.md → _python.py → _cython.pyx → _numba.py
```

A file is **stale** if its prerequisite has a strictly newer modification time. Check timestamps with `stat -f %m` (macOS) or `stat -c %Y` (Linux) and compare numerically. Staleness is **transitive**: if `_python.py` is stale, then `_cython.pyx` and `_numba.py` are also stale regardless of their own timestamps.

Staleness rules (evaluate in order; stop at the first stale file):
1. `_python.py` is stale if `mtime(FORMALIZATION.md) > mtime(_python.py)`.
2. `_cython.pyx` is stale if `mtime(_python.py) > mtime(_cython.pyx)`, or if `_python.py` is stale.
3. `_numba.py` is stale if `mtime(_cython.pyx) > mtime(_numba.py)`, or if `_cython.pyx` is stale.

## Effective phase

The **effective phase** is the nominal phase minus the stale files:

> Effective phase = the phase just before the first stale file in the chain.

Examples:
- `FORMALIZATION.md` updated after `_python.py` was written → `_python.py` stale → effective phase **0** (even if `_cython.pyx` also exists).
- `_python.py` updated after `_cython.pyx` was written → `_cython.pyx` stale → effective phase **1**.
- All files present, no staleness → effective phase **3**.

## Phase-specific validation

- **Phase 0**: Verify `FORMALIZATION.md` is non-empty. Ask the user whether it has been reviewed and approved.
- **Phases 1–3**: Run the tests for all **non-stale** backends only. A stale backend's tests are not run — its source may be inconsistent with its prerequisite.
