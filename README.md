# tokalign-dev

Development toolkit for the tokalign package: guides algorithm implementation through prototype → Cython → GPU phases with test equivalence enforcement, benchmarking, and packaging.

## Overview

This Claude Code plugin supports the full lifecycle of sequence-alignment algorithm development in the `tokalign` package. Every algorithm progresses through three phases:

1. **Prototype** (`_python.py`) — Pure Python, correctness focus
2. **Compile** (`_cython.pyx`) — Cython with typed memoryviews, performance focus
3. **Parallelize** (`_numba.py`) — Numba CUDA kernels, scalability focus

The plugin ensures the agent follows this sequence without skipping phases, losing test coverage, or introducing behavioral differences between backends.

## Skills

| Skill                    | Purpose                                                  |
| ------------------------ | -------------------------------------------------------- |
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
| `/new-algorithm` | Scaffold a new algorithm and start Phase 1         |
| `/phase-check`   | Validate whether the current phase is complete     |
| `/next-phase`    | Advance an algorithm to the next implementation phase |
| `/benchmark`     | Run cross-backend benchmarks for an algorithm      |

## Hooks

- **pre-commit**: Compiles Cython extensions and runs the full test suite before each commit, ensuring no existing backend is broken.

## Typical Workflow

```
/tokalign-dev:new-algorithm
  → implement in pure Python → all tests pass

/tokalign-dev:next-phase needleman_wunsch
  → Cython translation → same tests pass automatically

/tokalign-dev:next-phase needleman_wunsch
  → Numba GPU → same tests pass (or skip if no GPU)

/tokalign-dev:benchmark needleman_wunsch
  → see performance comparison across backends
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
│   └── benchmark.md
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── pre-commit-check.sh
└── README.md
```

## Naming

`tok` is a placeholder prefix that will be replaced before publication. The `package-release` skill includes a rename checklist for when the time comes.
