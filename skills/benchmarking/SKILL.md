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

Compare wall-clock performance across the backends a repository actually has — up to
four of them: pure Python, Cython, Numba CPU-parallel and Numba CUDA — for a single
algorithm, producing whatever table and plot the repository's own harness emits.

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

If the name doesn't match a key in the manifest's `[algorithms]` table:
- Edit distance <= 3: ask "Did you mean `<candidate>`?"
- No close match: list available algorithms and ask again

**An algorithm name is required.** If none is provided, ask. Do not default to "all".

### 2. Run phase-check for staleness

Before benchmarking, run the equivalent of `/phase-check <algorithm>` to determine:
- Which of the manifest's declared implementation phases exist.
- The state of each: `fresh`, `stale`, or `blocked`. **Staleness is decided by the
  provenance header each artifact carries, not by modification time** — the full rule is
  in `commands/references/phase-detection.md` and is not restated here, because two
  statements of one rule drift apart and this is the copy that would be missed.

If any implementation phase is **stale or blocked**, stop and report:
> "Cannot benchmark `<algorithm>`: `<file>` is `<stale|blocked>` (`<source>` has changed
> since it was generated). Run `/next-phase <algorithm>` to regenerate it before
> benchmarking."

**Rationale**: comparing backends that implement different versions of the algorithm
produces meaningless results. `blocked` gates for the same reason `stale` does — an
ancestor has changed, so the backend is about to be regenerated and any number measured
now describes code on its way out.

The formalization's state is **not** a gate: it is a document, it compiles to nothing, and
it contributes no timing.

### 3. At least two fresh backends must exist

If only one is available (typically just the pure-Python phase), there is nothing to
compare. Report:
> "Only the Python backend exists for `<algorithm>`. Benchmarking requires at least
> two backends to compare. Run `/next-phase <algorithm>` to add a Cython backend."

## What to do

### 1. Invoke the benchmark script

Take the command from the manifest's `[commands].benchmark`, substituting `{algorithm}`.

**That key is optional, and its absence is a real outcome rather than an edge case.** A
repository may have no benchmark infrastructure at all — one of this plugin's own
consumers does not. Where the key is missing, report that no benchmark command is
configured and stop. Do not invent a script path, and do not offer to build the harness:
that is a piece of work with its own decisions about timing methodology and output
format, not a side effect of asking for a measurement.

What the command measures, where it writes and what format it emits are the repository's
business. Read what it prints and follow it to whatever files it names. The methodology
notes further down describe what a *good* harness does, and are worth applying when
writing one — but they describe the repository's harness, not this skill's.

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

Output layout belongs to the repository. A harness typically emits some combination of a
table, machine-readable data, and a plot — for example:

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
  run the manifest's `[commands].build` first
- The first call to a Numba backend triggers JIT compilation — always discard the
  warmup run
- Large sequence lengths (>5000) can take minutes with the pure Python backend —
  the script adjusts iteration count automatically (fewer reps for longer sequences)
- `memory-profiler` is not in the default dev dependencies — it must be installed
  separately (`uv pip install memory-profiler`) before using `--memory`
- matplotlib uses the `Agg` backend (headless) — plots are saved to files, never
  displayed interactively
