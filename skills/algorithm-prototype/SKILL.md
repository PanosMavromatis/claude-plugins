---
name: algorithm-prototype
description: "TRIGGER: when advancing an algorithm from Phase 0 to Phase 1 via /next-phase; when FORMALIZATION.md exists and has been approved and the user asks to implement, prototype, or write the Python backend for a specific algorithm (Needleman-Wunsch, Smith-Waterman, Hirschberg, etc.). NOT for new algorithms or 'add an algorithm' requests — those go to algorithm-formalize (Phase 0)."
---

# algorithm-prototype

Guide the mechanical translation of an approved formalization into a pure Python implementation (Phase 1).

## When to trigger

When the user runs `/next-phase` for an algorithm that has a committed, approved
`FORMALIZATION.md`; when Phase 0 is complete and they ask to implement or prototype the
Python backend for a specific algorithm.

Do **not** trigger on "new algorithm" or "add an algorithm" requests — those belong to
phase 0, which has two skills: `algorithm-formalize` going forward from source material,
and `algorithm-recover` going backward from an implementation that already exists. If the
user asks to implement an algorithm but the formalization is missing, stop and tell them to
run `/new-algorithm` first; it decides between the two.

## What to do

### 0. Verify prerequisites and read the formalization

Before writing any code:

1. Confirm the formalization exists, at the path the manifest's
   `[phases].formalization` template gives for this algorithm. If it does not, stop:
   "The formalization stage comes first. Run `/dp-compile:new-algorithm` to produce it."
2. **Check for a stale artifact (the regeneration case).** If the phase-1 file already
   exists, compare its recorded provenance against the formalization: it is stale when
   the hash in its `derived-from` header no longer matches the formalization's current
   hash. Say so — "the formalization has changed since this was generated; regenerating"
   — then translate as normal and re-run the suite. Do **not** patch the existing file;
   regenerate it, or the mechanical-translation guarantee is gone and nothing will
   notice.
3. Read the formalization in full — pseudocode, test cases (TC-XX), and notes. The
   implementation is a translation of that document, not an independent design.
4. **Read the repository's own shape before writing to it.** The manifest's
   `[project].invariants` state what a kernel here must satisfy; `[project].encoder`
   states how symbols become integers. Neither is guessable and both bind. Then read an
   existing algorithm to see the signature, parameter object and result type this
   repository actually uses — **the plugin knows none of these**. Where the repository
   has no algorithm yet, ask rather than invent one.

### 1. Create the phase-1 file

Write it at the path the manifest's `[phases].python` template gives for this
algorithm, creating any directories that path names. A layout that puts each algorithm
in its own package may also need an `__init__.py`; a flat layout does not. Follow what
the algorithms already there do rather than adding files the repository has no use for.

### 2. Implement the kernel

**The signature is the repository's, not this plugin's.** Match the entry point of an
existing algorithm exactly — same parameter order, same result type, same conventions
for optional arguments. Backend equivalence depends on it: every later phase implements
the same signature, and a suite that runs one set of tests against all of them cannot
do so if the phases disagree about their interface.

Two illustrations, from different repositories. **Neither is a template to copy** — they
are here to show how far apart two correct answers sit, so that reading the code rather
than assuming a shape is understood as necessary rather than pedantic.

A sequence-alignment entry point, taking two sequences plus the objects that score them:

```python
def align(
    seq_a: Sequence[str],
    seq_b: Sequence[str],
    alphabet: Alphabet,
    scoring_matrix: ScoringMatrix,
    # algorithm-specific params follow (e.g., local=False for a local variant)
) -> AlignmentResult:
```

An HMM decode, taking a frozen parameter object and one record, over a private kernel
that sees only arrays:

```python
def viterbi(params: HMMParams, record: Record) -> ViterbiPath:
    ...

def _viterbi(init_p, transition_p, output_p, codes):
    """Purely numeric. Neither validates nor raises: an impossible input
    comes back as an infinite cost, and the wrapper turns that into the
    repository's own exception type."""
```

Same lifecycle, same discipline, nothing else in common — not the arity, not the
parameter style, not the return type, not even whether there is a separate kernel.

#### Mechanical translation from the formalization (mandatory)

Phase 1 is a **mechanical translation** of `FORMALIZATION.md`, not a creative
reimplementation. Follow these rules strictly:

- Every function in the pseudocode becomes one Python function (same name, adapted to
  `snake_case`)
- The recurrence block maps to the inner loop body
- The backtrace procedure becomes a separate Python function
- Variable names carry over from the formalization (minor Python convention adaptations
  are fine)
- The iteration order in the pseudocode is the iteration order in Python
- Any deviation from the formalization requires an explicit comment in the code explaining
  why

#### Encode at the boundary (mandatory)

Symbols become integers at the entry point, all computation between is integer-only,
and integers become symbols again on the way out. **Never index a sequence with a string
symbol inside the recurrence.**

This is not a style rule. It is what makes the compiled and GPU phases mechanical
transliterations rather than rewrites: they never touch a string type, so translating
them is a matter of typing the arrays, not of redesigning the interface. Getting it wrong
here is not discovered until the phase that cannot be written.

Use the encoder the manifest's `[project].encoder` documents describe. **Do not hardcode
any reserved code or user-symbol base** — those are the encoder's, they differ between
repositories, and they have changed within one.

#### Splitting the wrapper from the kernel

Where the repository separates a public entry point from a numeric kernel, follow it, and
**keep the kernel purely numeric — it neither validates nor raises.** An impossible or
degenerate input comes back as a sentinel value the wrapper interprets and turns into
whatever exception the repository raises.

That division is load-bearing rather than tidy: every later phase implements the same
kernel, and a GPU device function cannot raise a Python exception at all. A kernel that
validates is a kernel that cannot be transliterated.

#### Style

- Prefer the standard library and whatever numeric array type the repository's existing
  algorithms use. This phase is the readable reference; performance belongs to the phases
  after it.
- Prioritise readability over speed. This file is the oracle every later phase is checked
  against, and it has to be readable to serve as one.
- Include type hints, and a docstring in whatever style the surrounding code uses.

### 3. Register the backend

Follow the manifest's `[backends]`. Where `registry` names a file, add the row it
expects. Where `build_manifest` names a build file, add the source there too —
**a build system that does not glob will silently omit a file nobody listed**, and the
result is a module that imports in development and is absent from a built artifact.

### 4. Create the test file

Create `tests/algorithms/test_<name>.py` using the parametrized backend pattern from
`tests/conftest.py` (see `references/test-patterns.md` for the full fixture pattern
and worked examples).

**Implement the TC-XX test case specifications from `FORMALIZATION.md` directly** —
each test case identifier and name in the formalization becomes a named test function.
The formalization is the source of truth for what inputs to use and what properties to
assert (exact values, property-based, or relational, as specified per case).

#### TC-XX to pytest translation rules

1. **Naming**: Each `TC-XX: <Descriptive Name>` becomes
   `test_tcXX_<snake_case_name>(align_fn, ...)`. Do not invent test cases beyond what
   the formalization specifies.

2. **Integer-to-symbol mapping**: the formalization specifies integer arrays, and the
   public entry point may take symbols. Translate through the repository's own encoder,
   read from the `[project].encoder` documents. **Never hardcode a reserved code or a
   user-symbol base into a test.** Build the encoder so it covers the highest index the
   case uses, and let it tell you which integer any sentinel is — that mapping is the
   encoder's to state and it does change.

3. **Fixture grouping**: group test cases sharing identical parameters under a shared
   fixture, and build parameters inline for cases that are one-offs. **Pass every
   parameter explicitly rather than relying on a default** — a default that changes
   later silently changes what the test was asserting.

4. **Assertion precision**: Match the formalization's precision level for each TC:
   - **Exact**: `assert result.score == pytest.approx(X)` and
     `assert result.aligned_a == [...]`
   - **Property-based**: assert exact score, then check structural properties
     (gap count, match count, alignment length)
   - **Relational**: call `align_fn` with swapped/varied inputs and compare results

If a test scenario seems necessary but is not in the formalization, do not silently add
it. Instead: alert the user, add the test case specification to `FORMALIZATION.md`
first, then implement it in the test file.

### 5. Run tests and confirm

Run `uv run pytest tests/algorithms/test_<name>.py -v` and confirm all tests pass.

### When a test failure traces back to FORMALIZATION.md

If a test fails and investigation reveals the cause is an error in `FORMALIZATION.md`'s
Test Cases section (wrong expected score, incorrect index mapping, impossible expected
alignment, arithmetic error in the rationale), you **must not** silently adjust the test
or the implementation to paper over it. Follow this order strictly:

1. **Verify** — manually compute the correct expected value from the algorithm's
   recurrence and inputs to confirm the formalization is wrong (not the implementation)
2. **Amend `FORMALIZATION.md` first** — fix the erroneous TC-XX entry (expected values,
   rationale, index mappings) so the formalization is self-consistent and correct
3. **Then update the test** — write or revise the pytest case against the amended spec
4. **Do not modify `_python.py` to match a wrong spec** — the implementation is a
   mechanical translation of the pseudocode sections, which are independent of the
   test case expected values

This ensures FORMALIZATION.md remains the single source of truth. If the test is
adjusted without fixing the spec, later phases (Cython, GPU) will inherit the
discrepancy.

## When edge cases are discovered

If an edge case surfaces during implementation that the formalization does not cover:

1. **Amend `FORMALIZATION.md`** — add the edge case treatment to the Notes section (or
   the relevant pseudocode section and the Test Cases section)
2. **Then** implement the fix in `_python.py` and add the corresponding test

Never silently handle edge cases only in code. The formalization must remain the
authoritative specification so that Cython and GPU translators in later phases inherit
the same treatments.

## What NOT to do

- Don't creatively reinterpret the formalization — if the pseudocode says it, the Python
  says it; deviations require explicit justification in comments
- Don't add test cases beyond the formalization's TC-XX specs without first amending
  `FORMALIZATION.md`
- Don't optimize the Python implementation — clarity over speed
- Don't use numpy inside the DP computation — save that for Phase 2
- Don't skip edge-case tests "for now"
- **Don't create any later phase's file yet** — not the `cython` translation, not the
  `cpu_parallel` kernel, not the `cuda` one. Each is translated from the phase before it
  by its own skill, and a file written ahead of its turn has no source to be checked
  against. (There is no phase named `numba`: both parallel phases use that library, so
  the name cannot distinguish them.)

## Gotchas

- **Return whatever a later phase or a consumer will need, and decide it now.** A
  backtrace array that downstream code wants is painful to add once four phases
  implement the signature without it.
- **Read parameters through the accessor the repository provides**, not from a raw dict
  or a nested attribute reached by hand. The compiled phases pass flat typed arrays, so
  a lookup that is already a single indexed read transliterates and one that is not has
  to be redesigned.
- **Parameterise from the start whatever the family varies over.** Retrofitting a
  parameter that every phase and every test assumed constant is the expensive kind of
  change.
- **Never hardcode a reserved code.** They belong to the encoder, they differ between
  repositories, and a hardcoded one is wrong in a way no test detects — it indexes a
  real position and returns a confident answer computed from the wrong symbol.
