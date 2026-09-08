# dp-compile

Development toolkit for the tokalign package: guides algorithm implementation through formalization → prototype → Cython → GPU phases with test equivalence enforcement, benchmarking, and packaging.

## Overview

This Claude Code plugin supports the full lifecycle of a dynamic-programming algorithm in
any repository that carries a `dp-compile.toml` manifest. Every algorithm progresses
through five stages — a formalization, then four executable backends:

| # | Phase key | What it is |
|---|---|---|
| 0 | `formalization` | Language-agnostic pseudocode; understanding and adaptation |
| 1 | `python` | Pure Python; correctness. The reference every later phase is checked against |
| 2 | `cython` | Typed memoryviews; single-threaded performance |
| 3 | `cpu_parallel` | `@njit(parallel=True)` with `prange`; parallel correctness, no GPU required |
| 4 | `cuda` | `@cuda.jit`; scale |

**The filenames are the repository's, not the plugin's** — each phase is a path template in
the manifest. Phases 3 and 4 are both Numba, and neither is called `numba`: that names the
library, and a name shared by two phases cannot distinguish them.

The plugin ensures the agent follows this sequence without skipping phases, losing test
coverage, or introducing behavioral differences between backends. **Staleness is decided by
recorded provenance, not by modification time**: each derived artifact carries a
`derived-from` header naming its source and that source's SHA-256, and is stale when the
recorded hash no longer matches. That survives `git checkout`, which resets every mtime,
and it records the *direction* of each edge — so a formalization recovered from an
implementation is marked stale by a change to the kernel, rather than the reverse. The full
rule is `commands/references/phase-detection.md`.

## Skills

| Skill                    | Purpose                                                  |
| ------------------------ | -------------------------------------------------------- |
| `algorithm-formalize`    | Phase 0: pseudocode formalization from source material   |
| `algorithm-prototype`    | Phase 1: pure Python implementation + tests              |
| `cython-translation`     | Phase 2: Cython translation with equivalence check       |
| `cpu-parallelization`    | Phase 3: `@njit(parallel=True)` with `prange`            |
| `gpu-parallelization`    | Phase 4: Numba CUDA parallelization                      |
| `benchmarking`           | Compare performance across backends                      |

## Commands

| Command          | Description                                        |
| ---------------- | -------------------------------------------------- |
| `/new-algorithm` | Scaffold a new algorithm and start Phase 0 (formalization) |
| `/phase-check`   | Report phase and staleness status for one algorithm (or all); exits without suggesting next steps |
| `/next-phase`    | Advance one algorithm to the next phase; requires an explicit name argument (asks if missing) |
| `/benchmark`     | Run cross-backend benchmarks for an algorithm      |

## Hooks

- **pre-commit**: Runs the full test suite before each commit, ensuring no existing backend is broken. Cython extensions are recompiled only when a `.pyx` file is staged.

## Typical Workflow

```
/dp-compile:new-algorithm
  → produce FORMALIZATION.md → human reviews and approves

/dp-compile:next-phase needleman_wunsch
  → implement in pure Python from formalization → all tests pass

/dp-compile:next-phase needleman_wunsch
  → Cython translation → same tests pass automatically

/dp-compile:next-phase needleman_wunsch
  → Numba CPU-parallel (prange) → same tests pass, on any machine

/dp-compile:next-phase needleman_wunsch
  → Numba CUDA → same tests pass, or skip loudly if no GPU

/dp-compile:benchmark needleman_wunsch
  → see performance comparison across backends
```

### Updating a formalization mid-lifecycle

If the formalization is edited after later phases already exist, `/phase-check` reports the
phase-1 file as **stale** and everything below it as **blocked**, and `/next-phase`
regenerates the stale artifact rather than patching it:

```
# Edit the formalization after the Cython backend already exists
/dp-compile:phase-check needleman_wunsch
  → python: stale (formalization changed) — cython: blocked

/dp-compile:next-phase needleman_wunsch
  → regenerates the python phase from the updated formalization → tests pass

/dp-compile:next-phase needleman_wunsch
  → the cython phase is now stale in its own right → regenerated → tests pass
```

**Stale and blocked are different states, and the difference is what makes this
converge.** A blocked artifact's own recorded source has not changed yet, so it is not
regenerated speculatively; it becomes stale the moment its source actually is. Each
artifact is rebuilt exactly once, when the thing it was derived from really moves.

## Key Architectural Patterns

### Encode-at-the-boundary

`tokalign` uses multi-character string tokens as symbols. The `Alphabet` class encodes strings to integer indices at the entry point of every `align()` function. All DP computation uses integer arrays. Results are decoded back to strings at the exit. This pattern makes Phase 1 → 2 → 3 translations mechanical.

### Backend boundary (Cython and GPU)

Compiled backends split into a thin Python wrapper (handles encode/decode) and a compiled inner function (pure integer/float computation). The Cython/Numba code never imports or touches the `Alphabet` class.

### Test equivalence

Tests are parametrized across backends via `conftest.py`. Adding a new backend automatically runs the full existing test suite against it. If any test fails, the new backend is wrong — not the tests.

## Development

### Smoke test

After modifying the plugin, verify all components have valid syntax and load correctly:

```bash
./dev/smoke-test.sh
```

When adding a new skill, command, or other component, update the `expected` array in `dev/smoke-test.sh` so the smoke test covers it.

## Directory Structure

```
dp-compile/
├── .claude-plugin/
│   └── plugin.json
├── dev/
│   └── smoke-test.sh             # Verify all plugin components load
├── skills/
│   ├── algorithm-formalize/       # Phase 0 skill
│   ├── algorithm-prototype/       # Phase 1 skill
│   ├── cython-translation/        # Phase 2 skill
│   ├── cpu-parallelization/       # Phase 3 skill
│   ├── gpu-parallelization/       # Phase 4 skill
│   └── benchmarking/              # Cross-backend benchmarking
├── commands/
│   ├── new-algorithm.md
│   ├── phase-check.md
│   ├── next-phase.md
│   ├── benchmark.md
│   └── references/               # @-included fragments, not commands
│       ├── manifest.md           # The dp-compile.toml contract
│       └── phase-detection.md    # Nominal phase, staleness, and the target
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── pre-commit-check.py
└── README.md
```

## Decisions

Architectural decisions for this plugin and the `tokalign` package are recorded together in the parent repository at [`docs/decisions/adr/`](../docs/decisions/adr/) (available when using the nested co-location layout). The shared log is intentional: this plugin exists to enforce the package's architecture, so decisions about the algorithm lifecycle (ADRs 0004–0014) simultaneously define what the package must do and what this plugin must guide. Keeping them in one place avoids cross-repository duplication and makes the relationship between package decisions and plugin skills explicit.

## Naming

`tok` is a placeholder prefix that will be replaced before publication. The `package-release` skill includes a rename checklist for when the time comes.
