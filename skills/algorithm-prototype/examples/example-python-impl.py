"""Example pure-Python alignment function following tokalign conventions.

This is a minimal Needleman-Wunsch implementation demonstrating the required
patterns. Use it as a template — adapt the DP recurrence and traceback logic
for the specific algorithm being implemented.
"""

from typing import Sequence

from ..._types import Alphabet, AlignmentResult, ScoringMatrix


def align(
    seq_a: Sequence[str],
    seq_b: Sequence[str],
    alphabet: Alphabet,
    scoring_matrix: ScoringMatrix,
) -> AlignmentResult:
    """Global pairwise alignment using the Needleman-Wunsch algorithm.

    Parameters
    ----------
    seq_a : Sequence[str]
        First sequence of symbols (multi-character strings).
    seq_b : Sequence[str]
        Second sequence of symbols (multi-character strings).
    alphabet : Alphabet
        The alphabet defining valid symbols and their integer encoding.
    scoring_matrix : ScoringMatrix
        Scoring matrix with match/mismatch scores and gap penalties.

    Returns
    -------
    AlignmentResult
        Aligned sequences, score, and traceback matrix.
    """
    # --- Encode at the boundary ---
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)

    n = len(enc_a)
    m = len(enc_b)
    gap_open = scoring_matrix.gap_open
    gap_extend = scoring_matrix.gap_extend

    # Handle empty sequences
    if n == 0 and m == 0:
        return AlignmentResult(
            score=0.0, aligned_a=[], aligned_b=[], alphabet=alphabet
        )
    if n == 0:
        gap_cost = gap_open + gap_extend * m
        return AlignmentResult(
            score=gap_cost,
            aligned_a=[alphabet.gap_symbol] * m,
            aligned_b=list(seq_b),
            alphabet=alphabet,
        )
    if m == 0:
        gap_cost = gap_open + gap_extend * n
        return AlignmentResult(
            score=gap_cost,
            aligned_a=list(seq_a),
            aligned_b=[alphabet.gap_symbol] * n,
            alphabet=alphabet,
        )

    # --- DP computation (all integers from here) ---

    # Traceback directions
    DIAG, UP, LEFT = 0, 1, 2

    # Initialize DP and traceback matrices (using plain lists — no numpy)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    traceback = [[0] * (m + 1) for _ in range(n + 1)]

    # First row and column: gap penalties
    for i in range(1, n + 1):
        dp[i][0] = gap_open + gap_extend * i
        traceback[i][0] = UP
    for j in range(1, m + 1):
        dp[0][j] = gap_open + gap_extend * j
        traceback[0][j] = LEFT

    # Fill
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # Integer indices into the scoring matrix — never string symbols
            match_score = dp[i - 1][j - 1] + scoring_matrix.score(
                int(enc_a[i - 1]), int(enc_b[j - 1])
            )
            gap_a = dp[i - 1][j] + gap_extend  # simplified linear gap
            gap_b = dp[i][j - 1] + gap_extend

            best = max(match_score, gap_a, gap_b)
            dp[i][j] = best

            if best == match_score:
                traceback[i][j] = DIAG
            elif best == gap_a:
                traceback[i][j] = UP
            else:
                traceback[i][j] = LEFT

    # --- Traceback ---
    traced_a = []
    traced_b = []
    i, j = n, m
    gap_idx = alphabet.gap_index

    while i > 0 or j > 0:
        if i > 0 and j > 0 and traceback[i][j] == DIAG:
            traced_a.append(int(enc_a[i - 1]))
            traced_b.append(int(enc_b[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and traceback[i][j] == UP:
            traced_a.append(int(enc_a[i - 1]))
            traced_b.append(gap_idx)
            i -= 1
        else:
            traced_a.append(gap_idx)
            traced_b.append(int(enc_b[j - 1]))
            j -= 1

    traced_a.reverse()
    traced_b.reverse()

    # --- Decode at the boundary ---
    aligned_a = alphabet.decode(traced_a)
    aligned_b = alphabet.decode(traced_b)

    return AlignmentResult(
        score=dp[n][m],
        aligned_a=aligned_a,
        aligned_b=aligned_b,
        alphabet=alphabet,
        traceback=traceback,
    )
