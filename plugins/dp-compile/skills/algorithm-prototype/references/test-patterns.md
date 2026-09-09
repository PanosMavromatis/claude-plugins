# Parametrized testing pattern

One suite per algorithm, run against every backend that exists, so that agreement
between backends is **enforced rather than assumed**. Adding a phase adds a parameter,
and the existing tests run against it unchanged; if one fails, the new backend is wrong,
not the tests.

How a repository *discovers* its backends is its own decision, and the two models in use
differ enough that a skill must read which one applies rather than assume. Both appear
below, followed by a third state that is neither.

## Model A — import auto-discovery

The suite tries to import each phase's module and takes the ones that succeed. Suits a
layout where every algorithm has the same file names, so the module path is derivable
from the algorithm's name.

```python
import importlib

PHASES = ("python", "cython", "cpu_parallel", "cuda")

def get_available_backends(algorithm_name):
    """Discover which phases are importable for a given algorithm."""
    backends = []
    for phase in PHASES:
        try:
            mod = importlib.import_module(f"<pkg>.algorithms.{algorithm_name}._{phase}")
        except ImportError:
            continue
        backends.append((phase, mod.entry_point))
    return backends
```

**The weakness is that it cannot tell "not written yet" from "written but broken".** A
compiled phase whose extension failed to build raises `ImportError` exactly like one that
was never written, so a stale build reads as an absent phase and the suite goes green
having silently tested less than it did yesterday.

## Model B — an explicit registry

The repository lists its backends, and each row says what an absence may legitimately be
blamed on. This is what the manifest's `[backends].registry` points at.

```python
@dataclass(frozen=True)
class Backend:
    name: str            # "python", "cython", "cpu_parallel", "cuda"
    module: str          # the import that proves it is usable here
    hardware: str | None # what an absence may be blamed on, e.g. "CUDA device"

BACKENDS = (
    Backend("python", "<pkg>.<component>._<algorithm>"),
)
```

Three properties are the reason to prefer it, and each is a rule rather than a nicety:

- **A phase not yet reached contributes no row at all.** Absence is the honest
  representation of unwritten; a skip would mean "written, but not runnable here".
- **`hardware=None` makes a failed import a hard failure, not a skip.** Nothing external
  is needed to run pure Python, so the only way it fails to import is a broken working
  copy — precisely what a skip would conceal. This is the gap Model A cannot close.
- **A backend excluded for absent hardware is skipped *loudly*** — named in the session's
  own output, with the reason. A silent skip turns a lost GPU into a green run nobody
  reads.

Membership is a claim about which phases *exist*, so it is deliberately not derived by
probing for build products: a compiled backend whose artifact was never built would then
read as unwritten rather than broken.

## The third state — a suite not yet parameterised

A repository may have a backend matrix and still not run its suites across it. That is
not an oversight in either direction, and it happens for a concrete reason: parameterising
requires the tests to select a backend through the public API, and an entry point with
nowhere to put a backend argument cannot offer one. Adding that argument is a
backend-selection API — a real design decision that may be deliberately deferred.

While that holds, **do not fake it**. Write the ordinary tests against the public API, and
put any test that reaches a specific backend's internals in an explicitly labelled,
non-shared section, so nobody later mistakes it for a parameterised test that lost its
parameters. Read a green run accordingly: a backend listed as present means its module
imports, not that any suite ran twice.

**A corollary that is easy to miss: a tie-breaking rule is contract, not an
implementation detail.** Where a recurrence can reach the same optimum by more than one
path, two correct backends will otherwise legitimately disagree, and the suite that was
supposed to enforce equivalence will fail on a difference neither backend got wrong.
State the rule in the formalization and implement it in every phase.

## Equivalence discipline, phase by phase

Every phase after the first implements the same signature and must produce the same
answers. What changes between phases is **which class of failure is newly possible**, and
the discipline is cumulative: each phase inherits every earlier phase's checks and adds
exactly one.

| Phase | Newly possible failure | The check that finds it |
|---|---|---|
| 1 `python`, written forward | — it *is* the reference | The formalization's TC-XX cases |
| 1 `python`, recovered from | Anything the kernel already got wrong | A differential oracle — nothing else can |
| 2 `cython` | Boundary and type errors introduced by translation | A property test over generated inputs |
| 3 `cpu_parallel` | Races; a tie-break lost to concurrency | Thread-count invariance; a deliberately constructed tie |
| 4 `cuda` | Barrier placement; device-only behaviour | The simulator, then a device — and a skip that is loud |

**Where these live depends on which model the repository has** (above). Under Model A or
Model B the shared cases need no change at all when a backend is added — that is the whole
value of the parameterisation — so what a phase contributes is only its own new check.
Under the third state, everything goes in the labelled non-shared section, and the report
must not describe a passing run as backend equivalence, because nothing ran twice.

**A differential test belongs in the shared set, always.** It is the one check written
against something outside the repository, so putting it in a non-shared section means every
backend after the first is compared only against phase 1 — and inherits, unexamined,
whatever phase 1 got wrong. Inheritance across phases is mechanical when the case is shared
and does not happen at all when it is not.

### Phase 1 — the differential test, and what it is evidence of

**Phase 1 is the reference for phases 2 to 4, so nothing downstream can check phase 1
itself.** For an algorithm written forward that is acceptable: the formalization came from a
source outside the repository, and the TC-XX cases were specified before the code existed.
For an algorithm whose formalization was *recovered* from the kernel, it is not — the
document was read off the code, the tests were extracted from the code's own suite, and
every later backend is compared to the code. Everything in the chain then agrees with the
kernel because everything in the chain came from it.

An oracle is the only input that breaks the circle. Where the manifest's
`[algorithms.<name>].oracles` names one, the differential case is mandatory, and where it
names none for a recovered algorithm, say so plainly in the report: the suite is
self-referential, and a green run is evidence of internal consistency and of nothing else.

Three rules for writing it:

- **Pin the divergence; do not widen the assertion.** An oracle produced by an
  implementation whose defect the port deliberately fixed is *wrong* exactly where the fix
  bites, so the test asserts agreement everywhere else and the exact, enumerated
  disagreement there. Relaxing it to a tolerance or a "mostly agrees" threshold buys
  nothing and silently accepts the next divergence, which is the one nobody intended.
- **A green differential run is evidence about the corpus, not about the algorithm.** The
  oracle was produced from whatever data someone happened to have, and real data is not
  adversarial. Measured on one such suite: reversing the tie-breaking rule broke nothing,
  because learned float parameters produced **zero exact ties in 3804 positions**. The
  constructed cases below are what cover that, and the differential test does not replace
  them.
- **An oracle needs its inputs tracked beside its outputs.** The test is the pairing, not
  the output file; an output whose inputs live on one machine is not a differential test
  and cannot be made into one later.

### Phase 2 — the property test

Unit tests drawn from the formalization are *chosen* examples, and chosen examples do not
find off-by-one errors at a boundary or floating-point disagreements near a tie. Generate
many inputs, run the new backend and the phase-1 oracle, and assert they agree.

**Write it into the repository's own suite**, using that repository's types and encoder. A
check that lives outside the suite is a check nobody runs; one inside it runs in CI on every
change. This is what replaces the standalone validation script this plugin used to ship —
that script was run once, by whoever remembered it.

Generate inputs by sampling the encoder's own symbols rather than arbitrary values, which
fail at the encoding boundary and measure the error path. Seed the generator so a failure
is reproducible rather than a story.

### Phase 3 — invariance and a constructed tie

A correct parallel kernel gives the same answer on one thread as on many. Run the suite at
both, and treat any disagreement as a race: it is never a tolerance problem, and never
something to fix by widening an assertion.

Then construct a tie deliberately — uniform parameters, or equal scoring entries. Learned
float parameters essentially never tie, so a differential test against real data is evidence
about the data and not about the tie-break, and a last-wins port would pass it.

One expected difference is worth stating before it is mistaken for a bug: **a float sum
reduced in parallel is reassociated**, and float addition is not associative, so a summing
recurrence will differ in the last bits. A min or max reduction is exact and will not.
Decide which the kernel is before choosing between equality and a tolerance.

### Phase 4 — what a green run is evidence of

The simulator (`NUMBA_ENABLE_CUDASIM=1`) runs device code on the CPU and finds indexing,
bounds and barrier-placement errors. It models neither coalescing nor divergence nor races
between blocks, so a green simulator run is evidence about logic and about nothing else, and
must be reported as such.

On a machine with no device the backend **skips**, and the skip must be visible — a session
header naming it, and a documented way to escalate skips to failures in CI. A skip that
reads like a pass is the one outcome that makes a suite report more than it tested.

## Translating TC-XX specs to pytest

A formalization states its test cases in the internal integer representation, while the
public entry point usually takes symbols. Tests translate between the two **through the
repository's own encoder**, read from the manifest's `[project].encoder` documents.

**Never hardcode a reserved code or a user-symbol base into a test.** Repositories disagree
about them, and one repository has renumbered its own — so a hardcoded index is wrong in the
way no test detects: it addresses a real position and returns a confident answer computed
from some other symbol.

- Build the encoder with enough symbols to cover the highest index the case uses.
- Ask the encoder which integer any sentinel is, rather than writing the number. The
  first user symbol's code is the encoder's to state, not the test's to assume.
- Translate a sentinel in expected output through the same encoder, in the same direction.

So a case written over the first three user symbols becomes whatever three symbols the
encoder assigns those codes — resolved at test time, not written into the file.

## Test file template

**The worked example below is from a sequence-alignment repository**, kept concrete
because an abstract test template teaches nothing. Read the *shapes* — how a TC-XX case
becomes a named test, how fixtures group shared parameters, how each precision level is
asserted — and not the types, which are that repository's.

Each `TC-XX` in `FORMALIZATION.md` becomes a test function named
`test_tcXX_<snake_case_name>`. Test cases that share identical scoring parameters
can share fixtures; cases with unique parameters build their setup inline.

```python
import pytest
from <pkg>._types import Alphabet, ScoringMatrix   # that repository's own types
from tests.conftest import get_available_backends

ALGORITHM = "<name>"  # e.g., "needleman_wunsch"

@pytest.fixture(params=get_available_backends(ALGORITHM), ids=lambda b: b[0])
def align_fn(request):
    """Yield each available backend's align function."""
    _name, fn = request.param
    return fn


# --- Shared fixtures for test cases with common parameters ---
# Group TC cases that share the same alphabet, match, mismatch, and gap penalties.
# Cases with unique parameters should build their setup inline instead.

@pytest.fixture
def alphabet_4():
    """Alphabet with 4 user symbols (covers integer indices 4-7)."""
    return Alphabet(symbols=("A", "B", "C", "D"))

@pytest.fixture
def identity_2_m1(alphabet_4):
    """Identity matrix: match=2.0, mismatch=-1.0, g_o=-5.0, g_e=-1.0."""
    return ScoringMatrix.identity(
        alphabet_4, match=2.0, mismatch=-1.0, gap_open=-5.0, gap_extend=-1.0,
    )


# --- Exact assertion pattern (TC score and alignment are unambiguous) ---

def test_tc01_identical_sequences(align_fn, alphabet_4, identity_2_m1):
    """TC-01: Identical sequences."""
    result = align_fn(["A", "B", "C"], ["A", "B", "C"], alphabet_4, identity_2_m1)
    assert result.score == pytest.approx(6.0)
    assert result.aligned_a == ["A", "B", "C"]
    assert result.aligned_b == ["A", "B", "C"]
    # No gaps in either sequence
    assert alphabet_4.gap_symbol not in result.aligned_a
    assert alphabet_4.gap_symbol not in result.aligned_b


# --- Exact score + property assertion (alignment details are properties) ---

def test_tc02_partially_overlapping(align_fn, alphabet_4, identity_2_m1):
    """TC-02: Partially overlapping sequences."""
    # a = [4, 5, 6, 7] -> ["A", "B", "C", "D"]
    # b = [4, 5, 7, 8] -> need index 8, so use a larger alphabet
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E"))
    matrix = ScoringMatrix.identity(
        alphabet, match=2.0, mismatch=-1.0, gap_open=-5.0, gap_extend=-1.0,
    )
    result = align_fn(["A", "B", "C", "D"], ["A", "B", "D", "E"], alphabet, matrix)
    assert result.score == pytest.approx(2.0)
    assert len(result.aligned_a) == 4
    assert len(result.aligned_b) == 4
    # No gaps (mismatch cheaper than opening a gap)
    assert alphabet.gap_symbol not in result.aligned_a
    assert alphabet.gap_symbol not in result.aligned_b


# --- Gap position assertion pattern ---

def test_tc04_empty_sequence_a(align_fn, alphabet_4, identity_2_m1):
    """TC-04: Empty sequence A."""
    result = align_fn([], ["A", "B", "C"], alphabet_4, identity_2_m1)
    assert result.score == pytest.approx(-8.0)  # g_o + 3 * g_e = -5.0 + -3.0
    assert result.aligned_a == [alphabet_4.gap_symbol] * 3
    assert result.aligned_b == ["A", "B", "C"]


# --- Inline setup pattern (unique parameters per test case) ---

def test_tc09_gap_at_start(align_fn):
    """TC-09: Gap required at the start (different gap penalties)."""
    # This TC uses g_o=-3.0, g_e=-1.0 — different from the shared fixture
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E", "F"))
    matrix = ScoringMatrix.identity(
        alphabet, match=2.0, mismatch=-1.0, gap_open=-3.0, gap_extend=-1.0,
    )
    # a = [6, 4, 5] -> ["C", "A", "B"],  b = [4, 5] -> ["A", "B"]
    result = align_fn(["C", "A", "B"], ["A", "B"], alphabet, matrix)
    assert result.score == pytest.approx(0.0)
    assert result.aligned_a == ["C", "A", "B"]
    assert result.aligned_b == [alphabet.gap_symbol, "A", "B"]


# --- Relational assertion pattern (no single correct output) ---

def test_tc16_symmetry(align_fn, alphabet_4, identity_2_m1):
    """TC-16: Swapping inputs yields the same score."""
    seq_a, seq_b = ["A", "B", "C"], ["C", "B", "A"]
    result_ab = align_fn(seq_a, seq_b, alphabet_4, identity_2_m1)
    result_ba = align_fn(seq_b, seq_a, alphabet_4, identity_2_m1)
    assert result_ab.score == pytest.approx(result_ba.score)


# --- Property-based assertion pattern (multiple valid alignments) ---

def test_tc12_multiple_gaps(align_fn):
    """TC-12: Multiple gaps in the alignment."""
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E"))
    matrix = ScoringMatrix.identity(
        alphabet, match=3.0, mismatch=-1.0, gap_open=-2.0, gap_extend=-0.5,
    )
    # a = [4, 6, 5] -> ["A", "C", "B"],  b = [4, 7, 5, 8] -> ["A", "D", "B", "E"]
    result = align_fn(["A", "C", "B"], ["A", "D", "B", "E"], alphabet, matrix)
    assert result.score == pytest.approx(4.0)
    assert len(result.aligned_a) >= 4
    # At least 2 match positions
    matches = sum(
        1 for a, b in zip(result.aligned_a, result.aligned_b)
        if a == b and a != alphabet.gap_symbol
    )
    assert matches >= 2


# --- Degenerate scoring pattern (non-standard matrix) ---

def test_tc15_all_zeros_matrix(align_fn):
    """TC-15: Degenerate scoring matrix (all zeros)."""
    alphabet = Alphabet(symbols=("A", "B", "C", "D"))
    matrix = ScoringMatrix.identity(
        alphabet, match=0.0, mismatch=0.0, gap_open=-1.0, gap_extend=-0.5,
    )
    result = align_fn(["A", "B"], ["C", "D"], alphabet, matrix)
    assert result.score == pytest.approx(0.0)
    # No gaps (gaps would reduce score below 0)
    assert alphabet.gap_symbol not in result.aligned_a
    assert alphabet.gap_symbol not in result.aligned_b
```

## Key conventions

- `ids=lambda b: b[0]` makes test output show the backend names — `python`, `cython`,
  `cpu_parallel`, `cuda` — so a failure names the phase that failed
- Each TC-XX from `FORMALIZATION.md` maps to one `test_tcXX_<name>` function
- Fixtures are shared only when test cases have identical scoring parameters;
  cases with unique parameters use inline setup
- When adding a new backend, **no test changes are needed** — the parametrization
  picks it up automatically
- Backend-specific tests — those that reach past the public API into one phase's
  internals — go in their own file or in the labelled non-shared section described above,
  never among the shared cases. Mark the GPU ones so a machine without a device can
  deselect them (`@pytest.mark.gpu` is the usual spelling; the repository's own convention
  wins). Name such a file after the **phase**, not after the library: `cpu_parallel` and
  `cuda` both use Numba, so a `_numba_` in the filename says which library and not which
  backend.
- Use `pytest.approx()` for all score comparisons (float precision)
- Match the formalization's assertion precision level:
  - **Exact**: `assert result.score == pytest.approx(6.0)` and
    `assert result.aligned_a == [...]`
  - **Property-based**: assert score, then check structural properties (gap count,
    match count, alignment length) rather than exact sequences
  - **Relational**: run `align_fn` twice with swapped/varied inputs and compare
