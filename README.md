# tokalign-dev

Development toolkit for the tokalign package: guides algorithm implementation through formalization → prototype → Cython → GPU phases with test equivalence enforcement, benchmarking, and packaging.

## Overview

This Claude Code plugin supports the full lifecycle of sequence-alignment algorithm development in the `tokalign` package. Every algorithm progresses through four phases, starting with a formalization and then producing three executable backends:

0. **Formalize** (`FORMALIZATION.md`) — Language-agnostic pseudocode, understanding & adaptation focus
1. **Prototype** (`_python.py`) — Pure Python, correctness focus
2. **Compile** (`_cython.pyx`) — Cython with typed memoryviews, performance focus
3. **Parallelize** (`_numba.py`) — Numba CUDA kernels, scalability focus

The plugin ensures the agent follows this sequence without skipping phases, losing test coverage, or introducing behavioral differences between backends. Phase advancement uses `make`-like timestamp logic: a backend is considered **stale** if its prerequisite file has a newer modification time, even if the file exists. Staleness propagates transitively — updating `FORMALIZATION.md` marks `_python.py`, `_cython.pyx`, and `_numba.py` all stale in sequence.

## Skills

| Skill                    | Purpose                                                  |
| ------------------------ | -------------------------------------------------------- |
| `algorithm-formalize`    | Guide Phase 0: pseudocode formalization from source material |
| `algorithm-prototype`    | Guide Phase 1: pure Python implementation + tests        |
| `cython-translation`     | Guide Phase 2: Cython translation with equivalence check |
| `gpu-parallelization`    | Guide Phase 3: Numba CUDA parallelization                |
| `scoring-matrix`         | Create and manage scoring matrices for custom alphabets  |
| `benchmarking`           | Compare performance across backends                      |
| `alignment-viz`          | Visualize alignment results                              |
| `package-release`        | PyPI packaging and release workflow                      |

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
/tokalign-dev:new-algorithm
  → produce FORMALIZATION.md → human reviews and approves

/tokalign-dev:next-phase needleman_wunsch
  → implement in pure Python from formalization → all tests pass

/tokalign-dev:next-phase needleman_wunsch
  → Cython translation → same tests pass automatically

/tokalign-dev:next-phase needleman_wunsch
  → Numba GPU → same tests pass (or skip if no GPU)

/tokalign-dev:benchmark needleman_wunsch
  → see performance comparison across backends
```

### Updating a formalization mid-lifecycle

If `FORMALIZATION.md` is edited after `_python.py` (or later backends) already exist,
`/phase-check` will report the **effective phase** as 0 and flag the downstream files as
stale. Running `/next-phase` will regenerate `_python.py` from the updated formalization —
not patch it — and cascade from there:

```
# Edit FORMALIZATION.md after Cython backend already exists
/tokalign-dev:phase-check needleman_wunsch
  → Phase 0 (effective) — _python.py and _cython.pyx are stale

/tokalign-dev:next-phase needleman_wunsch
  → regenerates _python.py from updated formalization → tests pass

/tokalign-dev:next-phase needleman_wunsch
  → regenerates _cython.pyx from updated _python.py → tests pass
```

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
tokalign-dev/
├── .claude-plugin/
│   └── plugin.json
├── dev/
│   └── smoke-test.sh             # Verify all plugin components load
├── skills/
│   ├── algorithm-formalize/       # Phase 0 skill
│   ├── algorithm-prototype/       # Phase 1 skill
│   ├── cython-translation/        # Phase 2 skill
│   ├── gpu-parallelization/       # Phase 3 skill
│   ├── scoring-matrix/            # Scoring matrix generation
│   ├── benchmarking/              # Cross-backend benchmarking
│   ├── alignment-viz/             # Visualization
│   └── package-release/           # PyPI packaging
├── commands/
│   ├── new-algorithm.md
│   ├── phase-check.md
│   ├── next-phase.md
│   ├── benchmark.md
│   └── references/
│       └── phase-detection.md    # Shared phase/staleness logic (@-included by phase-check and next-phase)
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── pre-commit-check.sh
└── README.md
```

## Decisions

Architectural decisions for this plugin and the `tokalign` package are recorded together in the parent repository at [`docs/decisions/adr/`](../docs/decisions/adr/) (available when using the nested co-location layout). The shared log is intentional: this plugin exists to enforce the package's architecture, so decisions about the algorithm lifecycle (ADRs 0004–0014) simultaneously define what the package must do and what this plugin must guide. Keeping them in one place avoids cross-repository duplication and makes the relationship between package decisions and plugin skills explicit.

## Naming

`tok` is a placeholder prefix that will be replaced before publication. The `package-release` skill includes a rename checklist for when the time comes.
