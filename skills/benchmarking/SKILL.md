---
name: benchmarking
description: >
  TRIGGER: when the user says "benchmark", "compare backends", "how fast is",
  "performance comparison", "profile", "timing", or "throughput" for a specific
  algorithm; when the user runs /benchmark; when the user asks about crossover
  points between Python/Cython/GPU backends; when the user wants to see scaling
  behavior across sequence lengths.
  Do NOT trigger for correctness testing (use pytest), memory-only profiling
  without timing, or general "is this fast enough" questions unrelated to
  backend comparison.
---

# Benchmarking Skill

Compare wall-clock performance across available backends (Python, Cython, Numba)
for a single algorithm, producing a markdown table and scaling plot.

## When to trigger

When the user wants to compare backend performance for a specific algorithm — via
`/benchmark <algorithm>`, or natural language like "benchmark needleman-wunsch",
"how much faster is the Cython backend", "compare Python vs Cython performance".

Do **not** trigger for:
- Correctness testing — that's `pytest`
- Memory-only profiling without timing context
- Questions about performance that don't involve cross-backend comparison

## Prerequisites — verify before running

### 1. Resolve the algorithm name

Accept natural language names and normalise to `snake_case`:
- Strip whitespace, lowercase, replace hyphens/spaces with underscores
- Examples: `"Needleman-Wunsch"` -> `needleman_wunsch`, `"smith waterman"` -> `smith_waterman`

If the name doesn't match a directory under `src/tokalign/algorithms/`:
- Edit distance <= 3: ask "Did you mean `<candidate>`?"
- No close match: list available algorithms and ask again

**An algorithm name is required.** If none is provided, ask. Do not default to "all".

### 2. Run phase-check for staleness

Before benchmarking, run the equivalent of `/phase-check <algorithm>` to determine:
- Which backends exist (Python, Cython, Numba)
- Whether any backend is **stale** (prerequisite has a newer mtime)

If any backend is stale, **stop and report**:
> "Cannot benchmark `<algorithm>`: `<file>` is stale (its prerequisite `<prereq>`
> was modified more recently). Run `/next-phase <algorithm>` to regenerate stale
> backends before benchmarking."

**Rationale**: comparing backends that implement different versions of the algorithm
produces meaningless results.

### 3. At least two non-stale backends must exist

If only one backend is available (typically just `_python.py`), there is nothing to
compare. Report:
> "Only the Python backend exists for `<algorithm>`. Benchmarking requires at least
> two backends to compare. Run `/next-phase <algorithm>` to add a Cython backend."

## What to do

### 1. Invoke the benchmark script

The canonical benchmark script lives in the main `tokalign` repo at
`benchmarks/run_benchmark.py`, co-located with the codebase it tests. The plugin
provides a thin shell wrapper that locates the project root and delegates:

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/benchmarking/scripts/run-benchmark.sh" \
    <algorithm_name> [--memory]
```

Or invoke the script directly from the project root:

```bash
uv run python benchmarks/run_benchmark.py <algorithm_name> [--memory]
```

- `<algorithm_name>` is the snake_case algorithm name (required positional arg)
- `--memory` enables memory profiling (optional, off by default — adds significant
  overhead and requires `memory-profiler`)

The script will:
1. Auto-discover available backends via `get_available_backends()`
2. Benchmark each backend across sequence lengths: 10, 50, 100, 500, 1000, 5000
3. Run each configuration multiple times for statistical rigor (mean +/- std)
4. Save results to `benchmarks/results/<algorithm>/`

### 2. Review and present the output

The script produces:
- **`results.md`**: a markdown table with timing results per backend per sequence length
- **`scaling.png`**: a log-log scaling plot showing how each backend scales
- **`results.json`**: raw data for programmatic consumption

If `--memory` was used, additional columns/plots for peak memory are included.

Present the markdown table directly in the response. Mention the plot file path so
the user can open it. Highlight:
- **Crossover points**: at what sequence length does Cython beat Python? GPU beat Cython?
- **Scaling behavior**: does each backend show the expected O(mn) complexity?
- **Anomalies**: unexpected slowdowns, high variance, non-monotonic scaling

### 3. Interpret results (briefly)

Offer a 2-3 sentence interpretation:
- Which backend is fastest at each scale
- Whether the speedup justifies the compilation/GPU overhead
- Any red flags (e.g., Cython slower than Python suggests a GIL issue or
  missing type declarations)

Do **not** suggest optimizations or code changes unless the user asks.

## Benchmark methodology

### Sequence generation

Generate benchmark sequences by sampling from the alphabet's symbol list:

```python
import random
seq = [random.choice(alphabet.symbols) for _ in range(length)]
```

**Never** generate random strings — they won't be in the alphabet and will fail at
encoding. Use a fixed random seed for reproducibility.

### Timing

- Use `time.perf_counter()` for wall-clock measurements
- Run a warmup iteration (discarded) before timed runs
- Default: 5 timed iterations per (backend, length) pair
- Report mean and standard deviation

### Memory profiling (optional, `--memory` flag)

- Uses `memory_profiler.memory_usage()` to measure peak RSS during alignment
- Adds ~10x overhead — only enable when investigating memory scaling
- Reports peak memory in MiB

### Scoring setup

Use a simple identity scoring matrix for benchmarks (match=1, mismatch=-1,
gap_open=-2, gap_extend=-0.5). The goal is to compare backend speed, not to
produce meaningful alignments. Both sequences use the same alphabet and length.

## Output files

All output is saved under `benchmarks/results/<algorithm>/`:

```
benchmarks/results/needleman_wunsch/
├── results.md       # Markdown table
├── results.json     # Raw timing data
└── scaling.png      # Log-log scaling plot
```

If `--memory` is used, the same files include memory data (extra columns in the
table, second y-axis or separate subplot in the plot).

## What NOT to do

- Don't benchmark stale backends — the comparison is meaningless
- Don't benchmark a single backend — there's nothing to compare
- Don't generate random strings for sequences — sample from `alphabet.symbols`
- Don't use `time.time()` — use `time.perf_counter()` for precision
- Don't suggest code optimizations unless the user asks
- Don't run benchmarks with unrealistically small alphabets (use >= 4 symbols)
- Don't skip the warmup iteration — first-run JIT/import overhead skews results
- Don't display plots interactively (`plt.show()`) — save to file only

## Gotchas

- Cython backends must be compiled before benchmarking — if the `.so` is missing,
  run `uv run python setup.py build_ext --inplace` first
- The first call to a Numba backend triggers JIT compilation — always discard the
  warmup run
- Large sequence lengths (>5000) can take minutes with the pure Python backend —
  the script adjusts iteration count automatically (fewer reps for longer sequences)
- `memory-profiler` is not in the default dev dependencies — it must be installed
  separately (`uv pip install memory-profiler`) before using `--memory`
- matplotlib uses the `Agg` backend (headless) — plots are saved to files, never
  displayed interactively
