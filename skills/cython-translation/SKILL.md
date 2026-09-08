---
name: cython-translation
description: >
  TRIGGER: when the user says "cythonize", "translate to Cython", "make it fast",
  "compile", or "the Cython phase" for an algorithm whose phase-1 file exists. Also
  trigger when the user asks to create a `.pyx`, mentions typed memoryviews, or asks
  about Cython performance for a dynamic-programming kernel.
  Do NOT trigger for GPU/Numba work (use gpu-parallelization instead).
---

# Cython Translation Skill

Guide the translation of a Phase 1 pure Python algorithm to Phase 2 Cython.

## Prerequisites — verify before writing any code

1. **The phase-1 file exists**, at the path the manifest's `[phases].python` template
   gives for this algorithm. If it does not,
   stop and hand off to the `algorithm-prototype` skill instead, using the
   `Skill` tool with `skill: "dp-compile:algorithm-prototype"`. Do NOT use
   `Read` on the sibling `SKILL.md` — only the `Skill` tool activates the skill
   through the harness so it runs with its own references and examples.

2. **The phase-1 file is not stale.** Compare provenance, not timestamps: it is stale
   when the hash recorded in its `derived-from` header no longer matches the
   formalization's current hash. If it is stale, the Python backend must be regenerated
   and
   must be regenerated before Cython translation can proceed. Stop and hand off
   to the `algorithm-prototype` skill first via the `Skill` tool with
   `skill: "dp-compile:algorithm-prototype"` (not `Read`) — do not translate
   from a stale source.

3. **Check for a stale artifact (the regeneration case).** If the `.pyx` already
   exists, compare its recorded provenance against the phase-1 file: it is stale when
   the hash in its `derived-from` header no longer matches. Tell the
   user: "the phase-1 file has changed since this was generated.
   Regenerating the Cython backend." Then proceed with the translation as
   normal — read `_python.py`, rewrite `_cython.pyx` from scratch, and re-run
   all tests. Do **not** attempt to patch the existing `.pyx` — regenerate it to
   maintain the mechanical-translation guarantee.

4. **All Python tests pass.** Run:

   ```bash
   uv run pytest tests/algorithms/test_<algorithm>.py -k python
   ```

   Do not proceed if any test fails — the Cython version will inherit any bugs.

5. **Read `_python.py` in full** before writing a single line of Cython. The
   translation must be mechanical, not creative. Every line of Cython should
   trace back to a line in the Python.

6. **Read the repository's own types**, via the manifest's `[project].encoder`
   documents and the parameter or result objects the phase-1 file uses. What matters is
   how each is laid out as an array once flattened, since that is what the kernel
   receives: a typed memoryview cannot see an accessor method.

## Translation instructions

### File to create

Create the `.pyx` at the path the manifest's `[phases].cython` template gives for this
algorithm. In a directory-per-algorithm layout that is a sibling of the phase-1 file:

```
<algorithms root>/<algorithm>/
├── FORMALIZATION.md
├── _python.py        # already exists — read this first
└── _cython.pyx       # create this
```

### Split into wrapper + inner function

The Cython backend splits into two parts: a thin Python wrapper (handles
encode/decode) and a compiled inner function (pure integer/float computation).
**The inner function must never import or touch the encoder**, nor validate, nor
raise. It receives arrays and returns numbers; an impossible input comes back as a
sentinel the wrapper interprets. That is not tidiness — the GPU phase implements this
same kernel, and a device function cannot raise a Python exception at all.

The pair below is from a sequence-alignment repository, shown to make the split
concrete — **the shape is the point, not the names**:

```python
# Python wrapper — stays in Python, handles encode/decode
def align(seq_a, seq_b, alphabet, scoring_matrix):
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)
    result = _align_impl(enc_a, enc_b, scoring_matrix._matrix,
                         scoring_matrix.gap_open, scoring_matrix.gap_extend)
    return AlignmentResult(
        score=result["score"],
        aligned_a=alphabet.decode(result["aligned_a"]),
        aligned_b=alphabet.decode(result["aligned_b"]),
        alphabet=alphabet,
    )
```

```cython
# Cython inner function — receives pre-encoded arrays, returns raw integers
cpdef dict _align_impl(int[:] seq_a, int[:] seq_b,
                       double[:, :] scores,
                       double gap_open, double gap_extend):
    ...
```

The `align()` function signature presented to the user must be **identical** to
the Python version. Tests are parametrized across backends — do not change the
interface.

### C type declarations

Declare C types for all variables used in inner loops:

```cython
cdef int m = seq_a.shape[0]
cdef int n = seq_b.shape[0]
cdef int i, j
cdef double s, best
cdef double NEG_INF = float("-inf")
```

### DP matrices as typed memoryviews

Replace Python lists with numpy arrays accessed via typed memoryviews:

```cython
import numpy as np

M_np = np.full((m + 1, n + 1), NEG_INF, dtype=np.float64)
cdef double[:, :] M = M_np
```

See `references/typed-memoryviews.md` for the full syntax reference and
`references/cython-for-dp.md` for DP-specific patterns.

### Scoring matrix lookup

The scoring matrix is the hottest path. It arrives as `double[:, :] scores`
— access it directly with integer indices:

```cython
s = scores[seq_a[i - 1], seq_b[j - 1]]
```

Never call `scoring_matrix.score()` inside the Cython inner function. The Python
wrapper already passed the raw `_matrix` array.

### GIL release

Release the GIL around the inner DP loop so the code is ready for
multi-threading in the future:

```cython
with nogil:
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            ...
```

Note: memoryview access is GIL-safe, but Python object creation is not. Move all
Python object creation (numpy allocations, list construction) outside the
`with nogil:` block.

### Disable bounds checking and wraparound

Add these decorators to the inner function to eliminate Python-level safety
checks in the hot path:

```cython
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict _align_impl(...):
    ...
```

Only add these after confirming the Python tests pass on the Cython build.

### Build configuration

Add the new `.pyx` to the build file the manifest's `[backends].build_manifest` names,
following the pattern any existing extension there uses, and add the backend row that
`[backends].registry` expects.

**Neither half is optional, and the build half fails silently.** A build system that
does not glob will simply omit a source nobody listed — producing a module that imports
during development, because the source is right there, and is absent from any built
artifact.

## Equivalence validation

After compilation, the translation must be verified in two ways:

### 1. Full test suite (automated)

The parametrized `conftest.py` fixture auto-discovers backends. Compiling
the extension makes it visible. Run the manifest's `[commands].build`, then its
`[commands].test`:

```bash
<[commands].build>
<[commands].test_one, or [commands].test>
```

If any test fails, fix the Cython — do not modify the tests.

### 2. A property test for boundary errors (write it into the suite)

Unit tests drawn from the formalization's TC-XX cases are chosen examples, and chosen
examples do not find off-by-one errors at a boundary or floating-point disagreements near
a tie. Add a property test that generates many random inputs, runs both backends and
asserts they agree.

**Write it into the repository's own suite**, using that repository's types and encoder —
not as a script beside the plugin. A check that lives outside the suite is a check nobody
runs, and one inside it runs in CI on every change. Where the suite is not yet
parameterised over backends, put it in the labelled non-shared section described in
`references/test-patterns.md`.

Generate inputs by sampling from the encoder's own symbols rather than by generating
arbitrary values: arbitrary values fail at the encoding boundary and tell you nothing
about the kernel. Seed the generator so a failure is reproducible.

## Annotation — find the slow lines

Compile with `-a` to generate annotation HTML:

```bash
uv run cython -a <the path [phases].cython gives for this algorithm>
```

Open the generated `.html` file. Yellow lines still touch the Python/C API — they
are slow. The inner DP loop must be white (pure C). If any line in the DP loop
is yellow, add missing type declarations.

## Gotchas

- **`cdef` vs `cpdef`**: `cdef` functions cannot be called from Python. Use
  `cpdef` for `_align_impl` so tests can call it directly.

- **Memoryview input type**: `int[:, :]` and `double[:, :]` require contiguous
  numpy arrays. Add the conversion at the wrapper boundary, not inside callers:

  ```python
  enc_a = np.ascontiguousarray(enc_a, dtype=np.int32)
  ```

- **GIL and Python objects**: `with nogil:` blocks cannot create Python objects
  (lists, dicts, strings). Pre-allocate all output arrays as numpy arrays before
  entering the block.

- **Integer type alignment**: an encoder commonly returns numpy `int64` by
  default. The memoryview `int[:] ` expects `int32`. Cast at the boundary:

  ```python
  enc_a = enc_a.astype(np.int32)
  ```

- **Traceback matrix**: If the traceback uses an `IntEnum`, use its integer
  values (not the enum objects) in the Cython matrix. Define the direction
  constants as C integers at the top of the `.pyx` file.

- **`NEG_INF`**: `float("-inf")` works in Cython, but declare it as a `double`
  constant at module level for clarity and performance.

## Reference material

- `references/typed-memoryviews.md` — Cython typed memoryview syntax
- `references/cython-for-dp.md` — DP-specific Cython patterns
- `examples/example-cython-impl.pyx` — Annotated minimal example showing
  the wrapper + `_align_impl` pattern end-to-end
