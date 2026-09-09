"""Minimal pure-Python alignment — example for the algorithm-prototype skill.

This is a simplified linear-gap Needleman-Wunsch to demonstrate the mandatory
patterns.  Real implementations will be more complex (affine gaps, multiple
matrices, separate traceback helpers), but every one follows the same skeleton
shown here.

Patterns demonstrated:
  1. Canonical ``align()`` signature (Sequence[str] in, AlignmentResult out)
  2. Encode-at-the-boundary (strings → integers at entry)
  3. All DP computation on integer arrays via ``scoring_matrix.score(i, j)``
  4. Decode-at-the-boundary (integers → strings at exit)
  5. Traceback matrix included in the result
"""

from __future__ import annotations

from typing import Sequence

from ..._types import Alphabet, AlignmentResult, ScoringMatrix


def align(
    seq_a: Sequence[str],
    seq_b: Sequence[str],
    alphabet: Alphabet,
    scoring_matrix: ScoringMatrix,
) -> AlignmentResult:
    """Global alignment with linear gap penalty (simplified NW).

    Parameters
    ----------
    seq_a, seq_b : Sequence[str]
        Input sequences of string symbols.
    alphabet : Alphabet
        Symbol ↔ integer mapping.
    scoring_matrix : ScoringMatrix
        Score lookup and gap penalties.  Only ``gap_extend`` is used
        (linear model — ``gap_open`` is ignored).

    Returns
    -------
    AlignmentResult
    """
    # ---- Encode at the boundary ----
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)

    m = len(enc_a)
    n = len(enc_b)
    g = scoring_matrix.gap_extend          # linear gap penalty

    # ---- Allocate DP and traceback matrices ----
    #   D[i][j] = best score aligning enc_a[:i] with enc_b[:j]
    #   T[i][j] = direction we came from (0=nil, 1=diag, 2=up, 3=left)
    NIL, DIAG, UP, LEFT = 0, 1, 2, 3

    D = [[0.0] * (n + 1) for _ in range(m + 1)]
    T = [[NIL] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        D[i][0] = i * g
        T[i][0] = UP
    for j in range(1, n + 1):
        D[0][j] = j * g
        T[0][j] = LEFT

    # ---- Fill ----
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = scoring_matrix.score(int(enc_a[i - 1]), int(enc_b[j - 1]))
            diag = D[i - 1][j - 1] + s
            up   = D[i - 1][j] + g
            left = D[i][j - 1] + g

            best = diag
            T[i][j] = DIAG
            if up > best:
                best = up
                T[i][j] = UP
            if left > best:
                best = left
                T[i][j] = LEFT
            D[i][j] = best

    # ---- Traceback ----
    gap = alphabet.gap_index
    traced_a: list[int] = []
    traced_b: list[int] = []
    i, j = m, n

    while i > 0 or j > 0:
        if i > 0 and j > 0 and T[i][j] == DIAG:
            traced_a.append(int(enc_a[i - 1]))
            traced_b.append(int(enc_b[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and T[i][j] == UP:
            traced_a.append(int(enc_a[i - 1]))
            traced_b.append(gap)
            i -= 1
        else:
            traced_a.append(gap)
            traced_b.append(int(enc_b[j - 1]))
            j -= 1

    traced_a.reverse()
    traced_b.reverse()

    # ---- Decode at the boundary ----
    return AlignmentResult(
        score=D[m][n],
        aligned_a=alphabet.decode(traced_a),
        aligned_b=alphabet.decode(traced_b),
        alphabet=alphabet,
        traceback=T,
    )
