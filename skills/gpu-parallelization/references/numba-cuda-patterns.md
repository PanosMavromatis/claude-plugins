# Numba CUDA patterns for dynamic-programming kernels

**The decomposition is not here.** It lives in the algorithm's `FORMALIZATION.md` and is
argued in `../../cpu-parallelization/references/decomposition-patterns.md`. This document
is about expressing an already-validated decomposition in the CUDA execution model.

## The execution model, in the two facts that change the code

**1. A launch is the only grid-wide barrier.** `cuda.syncthreads()` synchronises the
threads of one block. Blocks are not ordered with respect to each other and may not even be
resident at the same time, so nothing inside a kernel can wait for "all threads
everywhere". A DP's sequential axis therefore lives on the host.

**2. Threads are grouped into warps of 32 that execute together.** Two threads of a warp
taking different branches means both branches run, with the inactive threads masked. A
`if i % 2` inside the hot loop halves throughput; a bounds check at the top of the kernel
costs almost nothing, because whole warps take it the same way.

## Pattern — the wavefront launch loop

The 2-D grid decomposition, expressed for CUDA. One launch per anti-diagonal; the launch
boundary is the barrier between groups.

```python
from numba import cuda
import numpy as np

@cuda.jit
def _diagonal_step(d, m, n, M, back, seq_a, seq_b, scores, gap):
    """One anti-diagonal. Every thread owns one cell of it."""
    t = cuda.grid(1)

    # Cells of anti-diagonal d are (i, d - i) for i in [i_lo, i_hi].
    i_lo = max(1, d - n)
    i_hi = min(d - 1, m)
    i = i_lo + t
    if i > i_hi:                 # the launch is rounded up to whole blocks
        return
    j = d - i

    best = M[i - 1, j - 1] + scores[seq_a[i - 1], seq_b[j - 1]]
    arg = 0
    up = M[i - 1, j] + gap
    if up > best:                # strict >, so the first candidate wins a tie
        best = up
        arg = 1
    left = M[i, j - 1] + gap
    if left > best:
        best = left
        arg = 2

    M[i, j] = best
    back[i, j] = arg


def _run(M, back, seq_a, seq_b, scores, gap, threads=128):
    m = len(seq_a); n = len(seq_b)
    d_M    = cuda.to_device(M)          # copy once, not per launch
    d_back = cuda.to_device(back)
    d_a    = cuda.to_device(seq_a)
    d_b    = cuda.to_device(seq_b)
    d_s    = cuda.to_device(scores)

    for d in range(2, m + n + 1):       # the sequential axis, on the host
        width = min(d - 1, m) - max(1, d - n) + 1
        if width <= 0:
            continue
        blocks = (width + threads - 1) // threads
        _diagonal_step[blocks, threads](d, m, n, d_M, d_back, d_a, d_b, d_s, gap)

    return d_M.copy_to_host(), d_back.copy_to_host()
```

Four things in that fragment are the pattern, and the rest is one family's arithmetic:

- **The host loop is the sequential axis.** Nothing inside the kernel spans anti-diagonals.
- **`cuda.to_device` happens once**, outside the loop. Copying per launch is the most common
  reason a correct GPU kernel is slower end-to-end than the CPU one.
- **The bounds check is against the group's real extent** (`i_hi`), not the array's. A
  wavefront's groups have varying width, so the rounded-up launch overshoots by a different
  amount every time.
- **The tie-break is spelled with a strict comparison**, in the same direction as phase 1.
  It is contract; see below.

For a recurrence over time with dense state coupling, the same shape holds with `t`
replacing `d` and the states of one timestep replacing the cells of one anti-diagonal.

## Pattern — grid-stride loop

Where the group is much larger than a comfortable launch, or the launch configuration
should be independent of the data size:

```python
@cuda.jit
def _kernel(out, n):
    start = cuda.grid(1)
    stride = cuda.gridsize(1)
    for i in range(start, n, stride):
        out[i] = ...
```

This makes the kernel correct for any launch configuration, which is what lets block and
grid size become a tuning knob rather than a correctness parameter. Prefer it once the
kernel is right.

## Launch configuration

```python
threads = 128                                    # 64-256 is the usual useful range
blocks  = (work + threads - 1) // threads        # ceiling division, never floor
```

- Threads per block should be a multiple of 32 (the warp size). 128 is a reasonable
  starting point; treat anything else as a measured choice.
- Occupancy is limited by registers and shared memory per block as well as by thread count.
  A kernel using a lot of either runs fewer blocks concurrently, which can make a *smaller*
  block size faster.
- **Do not tune before the suite is green.** Every knob here trades throughput for nothing
  else; none of them can make a wrong answer right.

## Memory

### Coalescing

Adjacent threads should touch adjacent addresses. The hardware services a warp's loads in
as few transactions as it can, and consecutive addresses collapse to one.

This is where a wavefront hurts: cells of an anti-diagonal are `(i, d-i)`, so in a
row-major matrix consecutive threads read with a stride of `cols - 1`. The fix is a layout
change — store the grid by anti-diagonal, so a group is contiguous — and it is **not** an
algorithm change. Do it only if a measurement says it matters.

### Shared memory

Per-block, fast, and explicitly managed. Worth staging into when a value is read by many
threads of the same block:

```python
@cuda.jit
def _kernel(data, out):
    buf = cuda.shared.array(shape=128, dtype=numba.float64)
    tid = cuda.threadIdx.x
    buf[tid] = data[cuda.grid(1)]
    cuda.syncthreads()          # every thread has written before any reads
    ...
```

The `syncthreads()` after the write is not optional, and it must be reached by **every**
thread of the block — a `syncthreads()` inside a branch that some threads skip is undefined
behaviour, not a slow path.

### Host/device transfer

Copy in before the sequential loop, copy out after. `cuda.to_device` returns a device array
that can be passed to many launches. For an algorithm whose backtrace is read on the host,
the backtrace matrix is a device array for the whole run and comes back once.

## Atomics, ties, and determinism

**A tie-breaking rule is contract**, because two backends breaking ties differently are
both correct and disagree — and the equivalence suite then fails on an input neither got
wrong. Spell the comparison in the same direction as phase 1 (`>` for first-wins, `>=` for
last-wins) and keep the reduction over predecessors inside one thread. Do not distribute a
per-cell argmax across threads: there is no "first" among threads.

`cuda.atomic.add` on floats is **not deterministic** — the accumulation order is the
hardware's choice, so two runs of the same input can differ in the last bits. Where a
kernel needs one, say so wherever the test tolerance is set; an equality assertion will
fail intermittently, which is the worst way to learn this.

## The simulator

```bash
NUMBA_ENABLE_CUDASIM=1 pytest ...
```

Executes `@cuda.jit` code on the CPU, so indexing, bounds, and barrier *placement* can be
tested with no device. It models neither coalescing, nor occupancy, nor warp divergence,
nor races between blocks — so it is evidence about logic and about nothing else. Always
report that a result came from the simulator.

## Diagnosing

| Symptom | Usual cause |
|---|---|
| Correct on small input, wrong on large | The sequential axis is inside the kernel, so it only worked while the grid fitted one block |
| Wrong at the edges of the result | Bounds checked against the array rather than the group's real extent |
| Intermittently wrong, same input | A race between blocks, or a float atomic |
| Kernel fast, end-to-end slow | Host/device copies inside the launch loop |
| Correct but uniformly slow | Uncoalesced access, or a launch per tiny group |
| Fails only on the first call | Compilation, not execution — discard the warm-up |
| Import fails | Environment: `numba-cuda` and its toolkit, not the code |
