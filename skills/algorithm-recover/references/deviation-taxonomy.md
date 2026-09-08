# Deviations of a port from its legacy source

A recovered formalization's `Deviations from the legacy source` section is the reverse
entrance's counterpart to `Adaptations from Source`, and it is where most of the
recovery's value ends up. This file sets out the kinds of divergence, what each one does
to the document, and the two mistakes that make the section useless.

The worked instances below come from one repository's HMM port — a Lush implementation
translated to Python. They are labelled as instances, not as a template: another port will
have different entries, and possibly kinds not listed here.

## Why this section is not a diff

Two mistakes empty it out.

**Recording only the differences.** A port makes decisions in both directions, and the
decision to *match* the original on something it could reasonably have changed leaves no
trace at all — not in the diff, not in the code, not in the tests. Those are the entries a
later cleanup breaks, because to a reader with no history the behaviour looks like an
oversight.

**Recording mechanism instead of consequence.** "Replaced `LU-solve` with
`numpy.linalg.solve`" is a changelog line. What the document needs is what changed for a
caller: the original substituted a tiny value for a zero pivot and returned a silently
perturbed answer, where the replacement raises. One of those is a behaviour a specification
has to state; the other is a library name.

## The kinds

| Kind | Behaviour differs today? | Reaches the recurrence? |
|---|---|---|
| 1. Defect fixed | Yes, deliberately | **Yes** — the recurrence states the fixed behaviour |
| 2. Defect not reproduced, judged harmless | No | No — a note with its argument |
| 3. Representation replaced | Not where checkable | Sometimes — if the identity or ordering changes |
| 4. Primitive substituted | Only in failure | No — but the failure mode is part of the contract |
| 5. Repository invariant imposed | No, under the mapping | **Sometimes** — array shapes and index ranges |
| 6. Convention deliberately preserved | No | No — but its absence from the section is the risk |

### 1. A defect in the source, fixed

The port found the original wrong and did not reproduce it. This is the only kind that
changes the recurrence: the formalization specifies the *fixed* behaviour, because that is
what this repository's kernel does and what every later phase must reproduce.

Three things belong in the entry, and the third is the one usually missing:

- what the original did, cited;
- why it is wrong, in the algorithm's own terms;
- **how far the two actually diverge, measured.** "Differs at exactly one position in
  3807, on one of three models" is a finding a reviewer can check. "Fixes a seeding bug"
  is a claim.

It also changes what an oracle means. Where the oracle was produced by the defective
original, the differential test is no longer an equality check, and the case in the
`Test Cases` section must say where the difference is expected and why — see the
`oracles` key in the manifest contract, which states the same rule from the other end.

*Instance.* The original seeded its accumulator with a raw probability where every other
term is a description length in bits. Since smaller is better in that domain, it inverted
the preference among start states, and an impossible start state seeded the best possible
value. The port seeds the bit-domain value instead, so the degenerate case becomes correct
by arithmetic rather than by a guard.

### 2. A defect not reproduced, but harmless

The original was wrong in a way that changes no result — a value round-tripped through a
type wide enough to hold it exactly, a redundant guard, a computation whose result is
discarded. The port corrected it anyway.

The entry records the defect and **the argument for why it was harmless**, because that
argument is what a future reader will want to re-check when the surrounding conditions
change. "Every index below 2^24 is exactly representable in float64" is fine today and
stops being fine at a state count nobody expects to reach.

Do not promote these into the recurrence. A formalization that specifies a type is
specifying an implementation.

### 3. A representation replaced

The original encoded something — absence, impossibility, an error — as a sentinel value,
and the port uses a different one. The replacement is usually chosen because it has the
right *arithmetic*: it absorbs under the operation the recurrence accumulates with, and it
sorts where the thing it stands for belongs.

That property is what the entry must state, and it is checkable. A sentinel that absorbs
under addition and compares as worse than every real value collapses a whole class of
special-case guards into ordinary arithmetic, which is why the code around it looks
simpler than the original's.

This kind reaches the recurrence only when the identity element or the ordering changes.
State the identity explicitly in the `Objective` row either way.

*Instance.* The original used `-1` for log-zero and guarded every comparison against it.
The port uses `+inf`, which absorbs under addition and sorts where it means, so the
guarded comparison becomes a plain one. Faithfulness to `-1` was declined as
**uncheckable** — there is no runtime for the original language in the repository, and the
sentinel reaches no persisted artifact — which is a legitimate reason to deviate and
belongs in the entry, since it is also the reason no test can be written for it.

### 4. A primitive or library substituted

A routine the original implemented by hand was replaced with a library call. Results agree
on well-conditioned input; the two differ in **how they fail**, and that difference is part
of the contract.

The entry names the failure behaviour on both sides. Where the substitution turns a silent
wrong answer into a raised error, say so — it is an improvement, and it is also a
behavioural change that a caller written against the original would not survive.

Where the substitution requires a preparatory step the original folded into its own
routine — a singular system made non-singular by replacing one equation with a
normalisation, say — that step is part of the algorithm and belongs in the recurrence or
the base cases, not in a note.

### 5. A repository invariant imposed

The port had no choice: an ADR, an encoder, or a container's layout required a different
shape, index base, or reserved block, and the original's could not survive contact with it.

The entry states the mapping and **what is invariant under it**. A renumbered symbol
alphabet that widens an array's last axis changes every index in the original and no
result, provided every derived quantity is invariant under the widening — which is a claim
worth making explicitly, because it is the claim that lets fixtures produced under the old
numbering still be used.

This kind can reach the recurrence, through array shapes and index ranges. It never
reaches it as a concrete code: the formalization names sentinels abstractly and leaves the
integers to the encoder.

### 6. A convention deliberately preserved

The port matched the original where it could reasonably have done otherwise. Nothing in the
diff records it, and nothing in the tests distinguishes "we chose this" from "we copied
this without noticing".

The entry says what the alternative was and why it was not taken. These are cheap to write
and they are the section's highest-value entries, because every other kind leaves *some*
trace and this one leaves none.

*Instance.* A division helper returns zero for both `0/0` and `x/0`, matching the original
rather than raising. It has no caller yet in the current release, which makes it even
easier to "tidy" into something stricter.

## Three questions for each entry

1. **Does it change a result?** If yes, the recurrence states the new behaviour and the
   entry explains the old one. If no, the entry stands alone.
2. **Does it change what an oracle means?** If the divergence is inside something an oracle
   measures, the corresponding test case stops being an equality check and must say so.
3. **What would a reader who does not know the original conclude from the code alone?** If
   the answer is "that this was an oversight", the entry is load-bearing — write it even if
   the deviation is one line.
