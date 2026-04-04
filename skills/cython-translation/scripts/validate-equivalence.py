"""Validate equivalence between Python and Cython backends for a tokalign algorithm.

Generates random sequence pairs sampled from the algorithm's alphabet,
runs both backends, and asserts identical scores and aligned sequences.

Usage
-----
uv run python tokalign-dev/skills/cython-translation/scripts/validate-equivalence.py \
    --algorithm needleman_wunsch \
    --n-pairs 1000 \
    --min-len 3 \
    --max-len 30

Exit codes
----------
0  All pairs matched.
1  One or more pairs produced different results (details printed to stdout).
2  A backend could not be imported (check build / installation).
"""

from __future__ import annotations

import argparse
import importlib
import random
import sys
from typing import Any

import numpy as np


def _make_alphabet_and_scoring(symbols: tuple[str, ...]) -> tuple[Any, Any]:
    """Build a small alphabet and identity scoring matrix for the given symbols."""
    from tokalign._types import Alphabet, ScoringMatrix

    alphabet = Alphabet(symbols=symbols)

    # Build a simple identity-style scoring dict: match=2, mismatch=-1
    scores: dict[tuple[str, str], float] = {}
    for a in symbols:
        for b in symbols:
            scores[(a, b)] = 2.0 if a == b else -1.0

    sm = ScoringMatrix.from_dict(scores, alphabet, gap_open=-2.0, gap_extend=-0.5)
    return alphabet, sm


def _random_sequence(symbols: tuple[str, ...], length: int, rng: random.Random) -> list[str]:
    return [rng.choice(symbols) for _ in range(length)]


def _results_equal(r_py: Any, r_cy: Any, tol: float = 1e-9) -> tuple[bool, str]:
    """Return (equal, reason). reason is empty string when equal."""
    if abs(r_py.score - r_cy.score) > tol:
        return False, f"score mismatch: python={r_py.score} cython={r_cy.score}"
    if r_py.aligned_a != r_cy.aligned_a:
        return False, f"aligned_a mismatch:\n  python={r_py.aligned_a}\n  cython={r_cy.aligned_a}"
    if r_py.aligned_b != r_cy.aligned_b:
        return False, f"aligned_b mismatch:\n  python={r_py.aligned_b}\n  cython={r_cy.aligned_b}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Python/Cython backend equivalence for a tokalign algorithm."
    )
    parser.add_argument(
        "--algorithm",
        required=True,
        help="Algorithm directory name (e.g. needleman_wunsch)",
    )
    parser.add_argument(
        "--n-pairs",
        type=int,
        default=1000,
        help="Number of random sequence pairs to test (default: 1000)",
    )
    parser.add_argument(
        "--min-len",
        type=int,
        default=3,
        help="Minimum sequence length (default: 3)",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=30,
        help="Maximum sequence length (default: 30)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["alpha", "beta", "gamma", "delta", "epsilon"],
        help="Symbol set to use (default: alpha beta gamma delta epsilon)",
    )
    args = parser.parse_args()

    # --- Import backends ---
    base = f"tokalign.algorithms.{args.algorithm}"
    try:
        py_mod = importlib.import_module(f"{base}._python")
    except ImportError as exc:
        print(f"ERROR: cannot import Python backend: {exc}", file=sys.stderr)
        return 2

    try:
        cy_mod = importlib.import_module(f"{base}._cython")
    except ImportError as exc:
        print(
            f"ERROR: cannot import Cython backend: {exc}\n"
            "Run:  uv run python setup.py build_ext --inplace",
            file=sys.stderr,
        )
        return 2

    # --- Build alphabet and scoring matrix ---
    symbols = tuple(args.symbols)
    alphabet, scoring_matrix = _make_alphabet_and_scoring(symbols)

    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    failures: list[tuple[list[str], list[str], str]] = []

    print(
        f"Validating {args.algorithm}: {args.n_pairs} pairs, "
        f"len {args.min_len}–{args.max_len}, symbols={list(symbols)}"
    )

    for pair_idx in range(args.n_pairs):
        len_a = rng.randint(args.min_len, args.max_len)
        len_b = rng.randint(args.min_len, args.max_len)
        seq_a = _random_sequence(symbols, len_a, rng)
        seq_b = _random_sequence(symbols, len_b, rng)

        r_py = py_mod.align(seq_a, seq_b, alphabet, scoring_matrix)
        r_cy = cy_mod.align(seq_a, seq_b, alphabet, scoring_matrix)

        equal, reason = _results_equal(r_py, r_cy)
        if not equal:
            failures.append((seq_a, seq_b, reason))
            if len(failures) <= 5:
                print(f"\nFAIL pair {pair_idx}: seq_a={seq_a}  seq_b={seq_b}")
                print(f"  {reason}")

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{args.n_pairs} pairs produced different results.")
        return 1

    print(f"OK: all {args.n_pairs} pairs matched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
