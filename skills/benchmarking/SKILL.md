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

**Read what the command emitted; do not assume a shape.** A harness may print a table, write
files, or both, and what it writes is the repository's choice. Present whatever it produced
— reproduce a printed table directly in the response, and name the path of any file or plot
it reports so the user can open it.

Then say three things about the numbers:

- **Each crossover, named by the pair it lies between.** With four backends there are three
  transitions — `python → cython`, `cython → cpu_parallel`, `cpu_parallel → cuda` — and each
  has its own crossover input size, or none. **A crossover that does not exist within the
  sizes measured is a result, not a gap**: it says the faster backend never repays its
  overhead at this scale, which is exactly what a reader needs in order to decide which
  backend to ship.
- **Scaling.** Does each backend show the complexity the formalization claims? A backend
  whose curve has the wrong slope is a more interesting finding than one that is merely
  slow, because slope is a property of the algorithm and constants are properties of the
  machine.
- **Anomalies**, with the usual cause named where there is one. `cython` slower than
  `python` suggests missing type declarations or an object-mode fallback; `cpu_parallel`
  slower than `cython` at every size suggests thread overhead exceeding the work, or
  oversubscription against a threaded BLAS; `cuda` slower end-to-end while its kernel is
  fast suggests host/device copies inside the launch loop.

### 3. Report the machine, and say what the numbers are a claim about

**A crossover is a property of the machine, not of the algorithm.** The `cython →
cpu_parallel` crossover moves with core count; the `cpu_parallel → cuda` crossover moves
with the device. The same kernels on a laptop and on a workstation will disagree about
which backend to use at a given size, and both measurements are correct.

So a benchmark report states the machine it came from: core count, the thread count used,
the GPU if one was present, and which backends were excluded and why. Without those a
number is not reproducible and is not comparable to the next one.

This matters beyond tidiness because of where a benchmark result tends to end up. "Cython
wins below 500" is a true local observation that becomes false the moment it is written into
a README as a fact about the algorithm — the same shape as any measurement promoted from
*here, today* to *always*. Report the conditions with the number so that the promotion is
visibly unsupported.

### 4. Interpret briefly

Two or three sentences: which backend is fastest at each scale, whether the speedup repays
the compilation or transfer overhead, and any red flag from the anomalies above.

Do **not** suggest optimizations or code changes unless the user asks. A measurement is not
a mandate.

## Methodology — what a good harness does

The plugin owns no harness, and these notes are not instructions to build one. They are
what to check when reading a repository's results, and what to apply if the repository asks
for a harness as a piece of work in its own right.

### Inputs go through the repository's encoder

Generate inputs by sampling the symbols the encoder actually knows, read from the
`[project].encoder` documents — never by generating arbitrary values. Arbitrary values fail
at the encoding boundary and measure the error path. Seed the generator, so a surprising
result can be re-examined rather than re-rolled.

Make the input representative in the dimension the algorithm is sensitive to: an alphabet of
two symbols, a model with three states, or sequences that are all the same length can each
produce a curve that no real workload will reproduce.

### Timing

- `time.perf_counter()`, never `time.time()`.
- **Discard a warm-up iteration**, and see the compilation note below.
- Several timed repeats per (backend, size) pair, and report the spread as well as the
  centre. A single number hides the variance that makes a GPU result unreliable.
- Reduce the repeat count at large sizes rather than dropping the size: the pure-Python
  backend at a size the compiled ones find easy can take minutes, and its cost is the point
  of the comparison.

### Compilation is not execution, and it is now two different costs

**This applies to phase 3 exactly as it does to phase 4**, which is easy to miss because the
CPU-parallel phase looks like ordinary Python:

- `@njit(parallel=True)` compiles on first call, per signature. A benchmark that includes it
  attributes the compiler's work to the kernel.
- `@cuda.jit` compiles to PTX on first launch, and is typically slower still.
- `cache=True` moves that cost to the first run *of the process ever*, not of the session.
  So a harness measuring "compilation overhead" gets a different answer depending on whether
  a cache file happens to exist — which means the cache state belongs in the report, or the
  cache should be off for that particular measurement.

A warm-up per (backend, signature) discards all three. One warm-up for the whole run does
not, because a new input dtype or dimensionality triggers a fresh compilation.

### Thread count is a parameter, not an ambient fact

A `cpu_parallel` number without a thread count is not interpretable. Fix it explicitly —
`NUMBA_NUM_THREADS`, or the repository's own control — and report it. Sweeping it is often
more informative than sweeping the input size, since it separates "this decomposition
scales" from "this machine is wide".

Beware oversubscription: a threaded BLAS, or a caller already inside a parallel region, will
make a correct parallel kernel look slower than the serial one. That reads like a bad
decomposition and is not.

## Output

Where results are written, and in what format, belongs to the repository. Read what the
command prints and follow it to whatever it names. Do not assume a file exists because a
previous repository wrote one.

## What NOT to do

- Don't benchmark stale or blocked backends — the comparison is meaningless.
- Don't benchmark a single backend — there is nothing to compare.
- Don't invent a benchmark command, or offer to build a harness, when `[commands].benchmark`
  is absent.
- Don't generate inputs that bypass the encoder.
- Don't use `time.time()`.
- Don't report a timing that includes a first compilation.
- Don't report a `cpu_parallel` or `cuda` number without the thread count or device.
- Don't state a crossover as a property of the algorithm.
- Don't suggest code optimizations unless the user asks.

## Gotchas

- **The compiled backends must be built first.** Run `[commands].build`; a missing extension
  is a stale or absent backend, which the staleness gate above should already have caught.
- **The first call compiles.** Phase 3 and phase 4 both, and phase 4 more slowly.
- **A parallel float sum is reassociated**, so `cpu_parallel` and `cython` can differ in the
  last bits. That is a correctness note the equivalence suite owns, but it surfaces here as
  a puzzling "the backends disagree" during a benchmark run.
- **GPU timing needs a synchronise.** A kernel launch is asynchronous, so a timer stopped
  without waiting for the device measures the launch and not the work.
- **Variance is the GPU's tell.** Thermal throttling, another process on the device, or a
  transfer contending for bandwidth all show up as spread rather than as a wrong mean.
- **A profiling flag can cost an order of magnitude.** Memory profiling in particular is
  usually not free; do not leave it on for a timing run, and do not compare a profiled
  number with an unprofiled one.
- **Plots are files.** A harness that opens an interactive window has no useful behaviour in
  a non-interactive session; if one does, that is worth reporting rather than working
  around.
