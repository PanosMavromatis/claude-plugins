---
name: cpu-parallelization
description: >
  TRIGGER: when advancing an algorithm to Phase 3, the `cpu_parallel` phase; when the user
  says "parallelize", "prange", "njit(parallel=True)", "multithread this kernel", "use all
  the cores", or asks to make a DP kernel parallel without a GPU. Also trigger when
  /next-phase resolves a target whose phase key is `cpu_parallel`.
  Do NOT trigger for the CUDA phase (that is gpu-parallelization), for the single-threaded
  Cython phase (cython-translation), or for benchmarking an existing parallel backend.
---

# cpu-parallelization

Guide the translation of a compiled single-threaded kernel into a Numba CPU-parallel
kernel: `@njit(parallel=True)` with `prange` over an axis the formalization says is
independent.

This phase exists because **a GPU is not required to find out whether a decomposition is
correct.** Race conditions, tie-break drift and reassociated reductions are properties of
concurrency, not of hardware, and every one of them can be found on a laptop. Phase 4
inherits a decomposition that has already been validated here, and is left with the
problems that really are hardware-specific.

## The manifest comes first

Every path, command and dependency below is resolved through the consumer's root
`dp-compile.toml`, whose contract is `commands/references/manifest.md`. This skill knows no
repository's layout and must not assume one: if there is no manifest, stop and say so
rather than resolving paths under a layout the repository does not have.

## Prerequisites — verify before writing any code

1. **The phase-2 file exists and is not stale**, at the path `[phases].cython` gives. This
   phase derives from it. If it is missing or stale, stop and hand off — use the `Skill`
   tool with `skill: "dp-compile:cython-translation"`, not `Read`, since only `Skill`
   activates a skill through the harness.

2. **The suite is green** for every existing backend. Run `[commands].build` then
   `[commands].test`. A race is hard enough to diagnose without an inherited failure in
   the same file.

3. **Read the formalization's `Parallel decomposition` section.** It is mandatory in the
   template, and it is the input to this phase — see below.

4. **Read `[project].invariants`.** At least one thing here is usually decided by a
   document rather than discoverable from the kernel; the tie-breaking rule is the one
   this phase can silently break.

## The decomposition is read, never invented

> **`FORMALIZATION.md`'s `Parallel decomposition` section says how this algorithm
> parallelises. This skill implements that answer. It does not choose one.**

The reason is not deference. A decomposition is a claim about which cells of the DP can be
computed without seeing each other, and getting it wrong produces a kernel that is *usually*
right — wrong only under a thread interleaving that a small test may never schedule. That
claim belongs in the document that is reviewed, beside the recurrence it is a claim about,
where a human reading the recurrence can disagree with it.

**If the section reads "undetermined", stop here.** Say so, and route the decision to the
formalization: amend it first, have it reviewed, and come back. Writing the kernel and
recording the decomposition afterwards inverts the whole chain — the formalization stops
being the specification and becomes a description of whatever was written.

**"This algorithm has no anti-diagonals" is a valid and complete answer.** The wavefront
transformation is a property of a 2-D DP whose cell depends on its neighbours; a recurrence
that is 1-D over time with dense coupling across states has no anti-diagonals to find, and
saying so is a finding rather than a failure to look. `references/decomposition-patterns.md`
sets out the families, what parallelises in each, and what does not.

Do not settle a repository-wide question about decompositions here either. Where a
repository's own ADRs assert that one transformation applies to every kernel in a family,
that assertion is the repository's to keep or revise, against a kernel that exists.

## What to write

### Translate from phase 2; check against phase 1

The provenance header names the `cython` file, and that is the right source to
transliterate: both are typed loops over flat arrays, so the translation is mechanical in
the same way phase 2's was.

**But the oracle is phase 1.** It is the readable reference the whole chain is checked
against, and it is the only backend guaranteed to be free of the failure modes this phase
introduces. Where the `.pyx` and the Python disagree about anything, that is a bug already
present in phase 2, and it is fixed there rather than papered over here.

Write the file at the path `[phases].cpu_parallel` gives, and stamp its provenance header:

```
# dp-compile: derived-from <the cython path> sha256:<hash>
```

### The wrapper/kernel split holds, for the same reason

The public entry point is unchanged — every phase implements the same signature or the
parameterised suite cannot run one set of tests against all of them. The kernel stays
purely numeric: it neither validates nor raises, and an impossible input comes back as a
sentinel the wrapper interprets.

In nopython mode this stops being a discipline and becomes a constraint: a `@njit` function
cannot construct or raise an arbitrary Python exception, cannot touch the encoder, and
cannot hold a Python object at all. A kernel written to the phase-1 rule already satisfies
it.

### `prange` goes on the independent axis, and nowhere else

The decomposition names one axis whose iterations do not see each other. `prange` goes
there. Every other loop stays `range`.

**The per-cell reduction over predecessors stays sequential.** This is not a performance
choice — it is what keeps the tie-breaking rule intact. A tie-break is *contract*: two
backends that break ties differently are both correct and disagree, so the suite that
compares them fails on an input neither backend got wrong. A sequential inner reduction
keeps first-wins (or last-wins) exactly as phase 1 spells it; a parallel one has no first.

Numba will happily privatise a recognised reduction pattern for you (`+=`, `*=`, `max()`).
An argmax — "which predecessor won" — is **not** a recognised pattern, and it is precisely
the one a DP backtrace needs. Keep it in a `range` loop.

## Verify — three checks, none of which is optional

### 1. The suite, against every backend

`[commands].build`, then `[commands].test`. If a test fails, the parallel kernel is wrong;
do not modify the test.

### 2. Thread-count invariance

A correct parallel kernel gives the same answer on one thread as on many. A racy one very
often passes on one and fails on many — or passes on both, on a small input, and fails in
production.

```bash
NUMBA_NUM_THREADS=1 <[commands].test_one, or [commands].test>
NUMBA_NUM_THREADS=8 <[commands].test_one, or [commands].test>
```

Compare the results, not just the exit codes. **A disagreement between thread counts is a
race, full stop** — it is never a tolerance problem, and never something to fix by widening
an assertion.

### 3. A constructed tie

Learned float parameters essentially never tie, so a differential test against real data is
evidence about the data and not about the tie-break. Construct the tie deliberately —
uniform parameters, or a scoring matrix whose entries are equal — and assert that the
parallel backend picks the same predecessor as phase 1. This is the check most likely to
be skipped and the one that catches the failure hardest to diagnose later.

Where the suite is not yet parameterised over backends, put these in the labelled
non-shared section described in
`../algorithm-prototype/references/test-patterns.md`.

## Declare the dependency

Phase 3 makes the Numba runtime a **hard** dependency of the consumer package — not an
extra. The reason is the backend registry: a registered backend that will not import is a
hard failure rather than a skip, so making the import optional would turn every install
without the extra into a broken one.

Take the requirement and its location from the manifest's `[dependencies]` table. **If the
table is absent, or says nothing about `cpu_parallel`, report what is needed and stop.** Do
not go looking for a `pyproject.toml`: in a workspace there are several, and a dependency
written into the wrong one is invisible until an install in a clean environment.

The CUDA runtime is a different question and belongs to phase 4, behind an extra.

## Register the backend

Follow `[backends]`. Add a registry row with **`hardware=None`** — this phase needs no
special hardware, so a failed import must escalate to a failure rather than skip. A backend
that skips because it did not import is a suite that went green having tested less than it
reports.

Where `build_manifest` names a build file, check whether it needs the new source listed. A
pure-Python Numba module usually does — a build system that does not glob omits any file
nobody listed, producing a module that imports in development and is absent from a built
wheel.

## What this skill does NOT do

- **No CUDA.** Phase 4 is a separate skill and reuses this decomposition.
- **No change to the public signature**, and no edits to tests to make the kernel pass.
- **No new decomposition.** If the formalization's is wrong, amend the formalization.
- **No performance tuning before correctness.** A parallel kernel that is slower than the
  Cython one at small sizes is an ordinary result, not a defect — report the crossover and
  leave optimisation to a request for it.

## Gotchas

- **A float sum reduced in parallel is not bit-identical to the sequential one.** `prange`
  reassociates, and float addition is not associative. `min` and `max` reductions are
  exact and safe; a *sum* — a forward or posterior recurrence, rather than a Viterbi — will
  differ in the last bits and needs a tolerance the equality-asserting tests may not have.
  Decide which one this kernel is before assuming it is safe.
- **`cache=True` and `parallel=True` interact badly with a moving source.** The cache key
  does not track everything you might change; a stale cache produces the previous kernel's
  behaviour with no warning. Clear `__pycache__` when a result looks impossible, and keep
  Numba's cache files out of version control.
- **An anti-diagonal has variable length**, so a `prange` over one is load-imbalanced at
  both corners — most threads idle on the first and last few. That is a performance
  property, not a correctness one; do not "fix" it by restructuring the decomposition.
- **Allocating inside a `prange` body** allocates per iteration. Hoist buffers out, or give
  each thread a slice of one array allocated before the loop.
- **The first call is compilation, not execution.** Any timing that includes it is
  measuring the compiler. This applies to phase 3 exactly as to phase 4.
- **Numba's threading layer may already be inside another parallel region** — a caller
  using threads, or a BLAS that spawns its own. Oversubscription shows up as a parallel
  kernel slower than the serial one, which reads like a bad decomposition and is not.

## Reference material

- `references/decomposition-patterns.md` — the decomposition families, what parallelises in
  each, and the recurrences that have no anti-diagonals.
