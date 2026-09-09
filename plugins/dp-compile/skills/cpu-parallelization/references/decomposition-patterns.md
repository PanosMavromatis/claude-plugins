# Decomposition patterns for dynamic-programming kernels

**This document does not choose a decomposition for an algorithm.** That belongs in the
algorithm's `FORMALIZATION.md`, in its `Parallel decomposition` section, where a reviewer
reads it beside the recurrence it is a claim about. What is here is the set of shapes a
recurrence can have and what each one does or does not admit, so that the section can be
filled in with an argument rather than an assumption.

## The question a decomposition answers

> Which cells of this DP can be computed at the same time without seeing each other?

A decomposition is a partition of the cells into groups, plus an order on the groups, such
that every cell's dependencies lie in an earlier group. Parallelism is then *within* a
group. Everything else — anti-diagonals, batching, scans — is a particular answer to that
question, and the answer follows from the shape of the dependency set, not from the
algorithm's name or its family's reputation.

## Family 1 — 2-D grid with neighbour dependencies

The alignment family: `M[i][j]` depends on `M[i-1][j-1]`, `M[i-1][j]`, `M[i][j-1]`. Every
dependency decreases `i + j`.

**Decomposition: the anti-diagonal wavefront.** Group cells by `d = i + j`. Every cell on
anti-diagonal `d` depends only on cells on `d-1` and `d-2`, so a whole anti-diagonal
computes in parallel and the diagonals run in sequence.

```
  j →      0   1   2   3
      0 [  0   1   2   3 ]      d = i + j
  i   1 [  1   2   3   4 ]      cells with equal d are independent
  ↓   2 [  2   3   4   5 ]
      3 [  3   4   5   6 ]
```

`prange` goes over the cells of one anti-diagonal; the loop over `d` stays sequential.

Properties worth knowing before writing it:

- **Length varies**: the first and last diagonals hold one cell. Load imbalance at the
  corners is inherent, not a bug, and for an `m × n` grid the average width is what
  determines the useful parallelism — a `3 × 100000` alignment has almost none.
- **Indexing is the whole difficulty.** For a given `d`, `i` ranges over
  `max(0, d - n) … min(d, m)` and `j = d - i`. Off-by-one here produces cells silently
  skipped rather than an error, so the first check is that the count of cells visited
  equals `m × n`.
- **Affine gaps** add matrices, not dependencies: the three coupled recurrences all read
  cells with smaller `i + j`, so the same wavefront carries them. Compute all three within
  one anti-diagonal pass.
- Storing the grid by anti-diagonal rather than by row is a memory-layout question, worth
  raising only after the kernel is correct.

## Family 2 — 1-D over time with dense state coupling

The HMM family: `delta[t][j]` depends on `delta[t-1][i]` for **every** state `i`. The
recurrence is a sequence of dense steps over time.

**There are no anti-diagonals here, and saying so is the finding.** An anti-diagonal exists
because a 2-D cell depends on a *bounded neighbourhood*, which orders the grid by `i + j`.
Here the only axis with a dependency is time, and every state at `t` depends on every state
at `t-1`, so the time steps are strictly sequential and there is nothing to skew. A search
for the wavefront transformation in this family does not find a hard one — it finds that
the question does not apply.

Three decompositions do apply. They are not alternatives to one another so much as
parallelism found at three different scales:

### 2a. States within a timestep

At each `t`, the `S` states are mutually independent: each reads all of `delta[t-1]` and
writes one entry of `delta[t]`. `prange` over destination states; the loop over `t` stays
sequential; the reduction over source states stays sequential inside the body, which is
what preserves the tie-break.

The natural first choice, and its limit is `S`. For a model with a handful of states there
is little to gain and the thread overhead can dominate — which is a benchmark result, not a
reason to skip the phase, since correctness under concurrency is what this phase is for.

### 2b. Batch over sequences

Decoding many independent sequences is embarrassingly parallel: `prange` over sequences,
each running the whole sequential recurrence. Scales with the batch rather than the model,
composes with nothing else needed, and is usually the largest available win in training,
where the whole corpus is decoded every iteration.

Two costs to state rather than discover: per-sequence working arrays must be allocated
outside the parallel loop or sliced from one buffer, and ragged lengths make the loop
imbalanced.

### 2c. An associative scan over time

The recurrence step is a matrix–vector product in a semiring — `(min, +)` over description
lengths, `(max, +)` over log-probabilities, `(+, ×)` over probabilities. Semiring
matrix product is associative, so the composition of `T` steps can be evaluated as a
parallel prefix scan in `O(log T)` depth instead of `O(T)`.

This is the only one of the three that parallelises *time itself*, and it is by a distance
the most work: it changes the arithmetic performed, so the backtrace has to be recovered
differently, and floating-point results need not match the sequential order bit for bit.
Reach for it when `T` is large and both `S` and the batch are small — and record in the
formalization that the operation order differs, because the equivalence test will see it.

## Family 3 — 1-D over a sequence with a bounded window

Segmentation-shaped recurrences: `best[i]` depends on `best[i-k]` for `k` in a bounded
range. Like family 2 the axis is sequential, and unlike it there is no second axis to
parallelise — the work at each position is the window, not a state space.

What parallelises is the *scoring* of candidate segments, which is independent across
candidates and often the dominant cost. The recurrence itself stays sequential. This is a
legitimate answer of the form "the recurrence does not parallelise; its inner cost does".

## When the answer is "not usefully"

A recurrence may have no decomposition worth implementing: too little work per step, an
axis too short, or a dependency structure that is genuinely serial. **Record that in the
formalization and stop.** A `prange` over four states is slower than a `range` over four
states, and shipping it buys a backend that is harder to reason about and no faster.

That is a different outcome from "undetermined", which means the question has not been
answered yet and blocks this phase. "Not usefully" is an answer, and it is one a repository
should be able to record without appearing to have skipped a step.

## Checking a decomposition before trusting it

Whatever the shape, the same three checks apply, and they are cheap next to debugging a
race:

1. **Every dependency lies in an earlier group.** State the group index as a function of
   the cell, then check each term of the recurrence against it. This is a five-minute
   argument on paper and it is what the `Parallel decomposition` section should contain.
2. **The groups cover the cells exactly once.** Count them. A wavefront that misses the
   last anti-diagonal still returns a plausible number.
3. **Nothing in the parallel body writes a location another iteration reads.** Accumulators
   and "best so far" variables are where this fails; they belong inside the sequential
   inner loop, not shared across the parallel one.
