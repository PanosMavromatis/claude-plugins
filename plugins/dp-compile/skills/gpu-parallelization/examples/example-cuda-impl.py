# example-cuda-impl.py
#
# ONE FAMILY'S WORKED INSTANCE, not a template. This is sequence alignment, so it
# has a score matrix and a gap penalty; a kernel from another family will have
# neither, and a recurrence over time will put timesteps where this puts
# anti-diagonals. What generalises is the *shape*: a thin Python wrapper that
# encodes and decodes, a device function that is purely numeric and cannot raise,
# the sequential axis as a host loop of kernel launches, one host-to-device copy
# rather than one per launch, and a tie-break spelled in the same direction as the
# phase-1 reference. Take the shape; take the types from your own repository.
#
# CUDA translation of example-python-impl.py (linear-gap Needleman-Wunsch), via the
# phase-3 CPU-parallel kernel. It reuses that kernel's decomposition unchanged --
# the anti-diagonal wavefront -- and changes only how the decomposition is executed.
#
# Patterns demonstrated:
#   1. Wrapper (def align) + device kernel split; the kernel never sees a string
#   2. The sequential axis (the anti-diagonal index d) as a host loop of launches,
#      because cuda.syncthreads() is per-block and there is no grid-wide barrier
#   3. One cuda.to_device per array, outside the loop, not per launch
#   4. Bounds check against the GROUP's extent, not the array's
#   5. First-wins tie-break preserved with strict `>`, kept inside one thread
#   6. Backtrace read back once, and walked on the host
#
# Not demonstrated, deliberately: shared memory, grid-stride loops and a
# coalescing-friendly layout. All three are performance work, and all three belong
# after the equivalence suite is green. See references/numba-cuda-patterns.md.

import numpy as np
from numba import cuda

# Backtrace directions. Plain integers, not an IntEnum: a device function holds no
# Python objects, so the enum would have to be unwrapped at the boundary anyway.
DIAG, UP, LEFT = 0, 1, 2

THREADS_PER_BLOCK = 128  # multiple of the 32-wide warp; a starting point, not a result


@cuda.jit
def _diagonal_step(d, m, n, M, back, seq_a, seq_b, scores, gap):
    """Compute every cell of anti-diagonal `d`. One thread per cell.

    Purely numeric, and it cannot be otherwise: a device function may not raise, may
    not allocate, and may not touch a Python object. The phase-1 rule that the kernel
    neither validates nor raises is enforced by the platform here rather than by
    discipline -- which is why it was worth following at phase 1.

    Cells of anti-diagonal d are (i, d - i). Both indices must stay inside the
    interior of the (m+1) x (n+1) matrix, which bounds i to [max(1, d-n), min(d-1, m)].
    """
    t = cuda.grid(1)

    i_lo = max(1, d - n)
    i_hi = min(d - 1, m)

    i = i_lo + t
    # The launch is rounded up to whole blocks, so the tail of the last block runs
    # past the end of THIS ANTI-DIAGONAL -- which is shorter than the matrix. A check
    # against the array bounds would let those threads write real cells of another
    # diagonal, silently, with the wrong recurrence.
    if i > i_hi:
        return
    j = d - i

    # The reduction over predecessors stays inside this one thread. Distributing it
    # would leave the tie-break undefined: there is no "first" among threads, and a
    # tie-break is contract -- two backends breaking ties differently are both correct
    # and disagree, so the equivalence suite fails on an input neither got wrong.
    best = M[i - 1, j - 1] + scores[seq_a[i - 1], seq_b[j - 1]]
    arg = DIAG

    cand = M[i - 1, j] + gap
    if cand > best:          # strict >, so the earlier candidate keeps a tie
        best = cand
        arg = UP

    cand = M[i, j - 1] + gap
    if cand > best:
        best = cand
        arg = LEFT

    M[i, j] = best
    back[i, j] = arg


def _align_impl(enc_a, enc_b, scores, gap, gap_code):
    """Host side: allocate, seed the borders, run the wavefront, walk the backtrace.

    Returns raw integers. Nothing here knows what a symbol is.
    """
    m = enc_a.shape[0]
    n = enc_b.shape[0]

    M = np.zeros((m + 1, n + 1), dtype=np.float64)
    back = np.zeros((m + 1, n + 1), dtype=np.int8)
    # Border cells have one predecessor each and no choice to make, so they are seeded
    # on the host rather than costing a launch apiece.
    for i in range(1, m + 1):
        M[i, 0] = i * gap
        back[i, 0] = UP
    for j in range(1, n + 1):
        M[0, j] = j * gap
        back[0, j] = LEFT

    # Copied once. A to_device inside the launch loop is the most common reason a
    # correct GPU kernel is slower end-to-end than the CPU one it replaced.
    d_M = cuda.to_device(M)
    d_back = cuda.to_device(back)
    d_a = cuda.to_device(enc_a)
    d_b = cuda.to_device(enc_b)
    d_scores = cuda.to_device(scores)

    # The sequential axis. Each launch is the grid-wide barrier that syncthreads()
    # cannot provide: every cell of diagonal d reads cells of d-1 and d-2, so d-1 must
    # be complete across the whole grid before d begins.
    for d in range(2, m + n + 1):
        width = min(d - 1, m) - max(1, d - n) + 1
        if width <= 0:
            continue
        blocks = (width + THREADS_PER_BLOCK - 1) // THREADS_PER_BLOCK
        _diagonal_step[blocks, THREADS_PER_BLOCK](
            d, m, n, d_M, d_back, d_a, d_b, d_scores, gap
        )

    M = d_M.copy_to_host()
    back = d_back.copy_to_host()

    # The backtrace is serial by nature -- each step depends on the last -- so it stays
    # on the host. Moving it to the device would buy nothing and cost a launch.
    out_a, out_b = [], []
    i, j = m, n
    while i > 0 or j > 0:
        step = back[i, j]
        if step == DIAG:
            out_a.append(enc_a[i - 1]); out_b.append(enc_b[j - 1]); i -= 1; j -= 1
        elif step == UP:
            out_a.append(enc_a[i - 1]); out_b.append(gap_code); i -= 1
        else:
            out_a.append(gap_code); out_b.append(enc_b[j - 1]); j -= 1

    out_a.reverse(); out_b.reverse()
    return {"score": M[m, n], "aligned_a": out_a, "aligned_b": out_b}


def align(seq_a, seq_b, alphabet, scoring_matrix):
    """The public entry point. Identical in signature to every other phase.

    Encoding and decoding live here and only here. The device code never sees a
    string, which is what makes this phase a transliteration of phase 3 rather than a
    redesign -- and what made phase 3 a transliteration of phase 2 before it.

    The gap code is READ FROM THE ENCODER and passed down, never hardcoded and never
    held in a module global: reserved blocks differ between repositories and have been
    renumbered within one, and a hardcoded code indexes a real position and returns a
    confident answer computed from the wrong symbol.
    """
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)
    enc_a = np.ascontiguousarray(enc_a, dtype=np.int32)
    enc_b = np.ascontiguousarray(enc_b, dtype=np.int32)

    result = _align_impl(
        enc_a, enc_b,
        np.ascontiguousarray(scoring_matrix._matrix, dtype=np.float64),
        scoring_matrix.gap,
        alphabet.gap_code,
    )

    return AlignmentResult(                      # the repository's own result type
        score=result["score"],
        aligned_a=alphabet.decode(result["aligned_a"]),
        aligned_b=alphabet.decode(result["aligned_b"]),
        alphabet=alphabet,
    )
