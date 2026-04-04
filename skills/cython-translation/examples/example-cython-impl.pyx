# example-cython-impl.pyx
#
# Cython translation of example-python-impl.py (linear-gap NW).
# This is the Phase 2 counterpart — every line traces back to the Python.
#
# Patterns demonstrated:
#   1. Wrapper (def align) + inner function (cpdef _align_impl) split
#   2. Encode/decode stays in the wrapper; Cython never touches Alphabet
#   3. Typed memoryviews for DP matrix and sequences
#   4. C type declarations for all loop variables
#   5. GIL release around the inner DP loop
#   6. boundscheck(False) / wraparound(False) decorators
#   7. Pre-allocated traceback output buffers (no Python objects in hot path)
#
# Compile:
#   uv run python setup.py build_ext --inplace
#
# Annotate (find slow lines):
#   uv run cython -a example-cython-impl.pyx

import numpy as np
cimport numpy as np
cimport cython

from tokalign._types import AlignmentResult

# Direction constants — same values as the Python version's NIL/DIAG/UP/LEFT
cdef signed char NIL  = 0
cdef signed char DIAG = 1
cdef signed char UP   = 2
cdef signed char LEFT = 3


# ---------------------------------------------------------------------------
# Wrapper — identical signature to the Python backend
# ---------------------------------------------------------------------------
def align(seq_a, seq_b, alphabet, scoring_matrix):
    """Global alignment with linear gap penalty — Cython backend.

    Signature is identical to _python.align().  Tests run against both.
    """
    # Encode at the boundary
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)
    enc_a = np.ascontiguousarray(enc_a, dtype=np.int32)
    enc_b = np.ascontiguousarray(enc_b, dtype=np.int32)
    scores = np.ascontiguousarray(scoring_matrix._matrix, dtype=np.float64)

    result = _align_impl(
        enc_a, enc_b, scores,
        scoring_matrix.gap_extend,
        alphabet.gap_index,
    )

    # Decode at the boundary
    return AlignmentResult(
        score=result["score"],
        aligned_a=alphabet.decode(result["aligned_a"]),
        aligned_b=alphabet.decode(result["aligned_b"]),
        alphabet=alphabet,
        traceback=result["traceback"],
    )


# ---------------------------------------------------------------------------
# Inner function — pure integer/float computation, no Python objects in loops
# ---------------------------------------------------------------------------
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict _align_impl(
    int[:] seq_a,
    int[:] seq_b,
    double[:, :] scores,
    double gap,
    int gap_index,
):
    cdef int m = seq_a.shape[0]
    cdef int n = seq_b.shape[0]
    cdef int i, j, k
    cdef double s, diag, up, left, best

    # ---- Allocate DP matrix (numpy → memoryview) ----
    D_np = np.zeros((m + 1, n + 1), dtype=np.float64)
    T_np = np.zeros((m + 1, n + 1), dtype=np.int8)
    cdef double[:, :] D = D_np
    cdef signed char[:, :] T = T_np

    # ---- Pre-allocate traceback output (worst case: m + n) ----
    aligned_a_np = np.empty(m + n, dtype=np.int32)
    aligned_b_np = np.empty(m + n, dtype=np.int32)
    cdef int[:] aligned_a_buf = aligned_a_np
    cdef int[:] aligned_b_buf = aligned_b_np

    # ---- Base cases ----
    for i in range(1, m + 1):
        D[i][0] = i * gap
        T[i][0] = UP
    for j in range(1, n + 1):
        D[0][j] = j * gap
        T[0][j] = LEFT

    # ---- Fill (GIL released — entire loop is pure C) ----
    with nogil:
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                s    = scores[seq_a[i - 1], seq_b[j - 1]]
                diag = D[i - 1][j - 1] + s
                up   = D[i - 1][j] + gap
                left = D[i][j - 1] + gap

                best = diag
                T[i][j] = DIAG
                if up > best:
                    best = up
                    T[i][j] = UP
                if left > best:
                    best = left
                    T[i][j] = LEFT
                D[i][j] = best

    # ---- Traceback (outside nogil — fills pre-allocated buffers) ----
    i = m
    j = n
    k = 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and T[i][j] == DIAG:
            aligned_a_buf[k] = seq_a[i - 1]
            aligned_b_buf[k] = seq_b[j - 1]
            i -= 1
            j -= 1
        elif i > 0 and T[i][j] == UP:
            aligned_a_buf[k] = seq_a[i - 1]
            aligned_b_buf[k] = gap_index
            i -= 1
        else:
            aligned_a_buf[k] = gap_index
            aligned_b_buf[k] = seq_b[j - 1]
            j -= 1
        k += 1

    # Slice valid portion and reverse
    return {
        "score": D[m][n],
        "aligned_a": aligned_a_np[:k][::-1].copy(),
        "aligned_b": aligned_b_np[:k][::-1].copy(),
        "traceback": T_np,
    }
