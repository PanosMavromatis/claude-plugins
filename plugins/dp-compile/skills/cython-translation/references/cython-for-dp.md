# Cython Patterns for Dynamic Programming

Reference for writing efficient Cython implementations of dynamic-programming kernels.

---

## Module-level setup

Every `.pyx` file that uses typed memoryviews needs these imports:

```cython
import numpy as np
cimport numpy as np
cimport cython
```

`cimport numpy` gives access to the C-level numpy declarations (dtypes, array
structs) without going through the Python layer.

---

## DP matrix allocation

Allocate all DP matrices as numpy arrays before declaring the typed memoryview:

```cython
# Allocate as numpy arrays (Python layer)
cdef double NEG_INF = float("-inf")
M_np = np.full((m + 1, n + 1), NEG_INF, dtype=np.float64)
X_np = np.full((m + 1, n + 1), NEG_INF, dtype=np.float64)
Y_np = np.full((m + 1, n + 1), NEG_INF, dtype=np.float64)

# Declare typed memoryviews (C layer — no Python overhead in hot path)
cdef double[:, :] M = M_np
cdef double[:, :] X = X_np
cdef double[:, :] Y = Y_np
```

Typed memoryviews are views into numpy array memory, not separate allocations.
After the `cdef` declarations, all indexed access (`M[i][j]`) goes through the
C layer with no Python calls.

---

## Traceback matrix

For integer-valued traceback matrices, use `int8` to keep memory compact:

```cython
T_np = np.zeros((m + 1, n + 1), dtype=np.int8)
cdef signed char[:, :] T = T_np

# Direction constants (matches the Python IntEnum values)
cdef signed char NIL         = 0
cdef signed char DIAG        = 1
cdef signed char UP_OPEN     = 2
cdef signed char UP_EXTEND   = 3
cdef signed char LEFT_OPEN   = 4
cdef signed char LEFT_EXTEND = 5
```

Using C integer constants (not Python `IntEnum` objects) inside `with nogil:`
blocks avoids touching the Python/C API.

---

## Disabling safety checks

Add these decorators to the `cpdef` inner function after tests pass:

```cython
@cython.boundscheck(False)   # skip index-out-of-bounds checks
@cython.wraparound(False)    # skip negative-index support
@cython.cdivision(True)      # skip division-by-zero check (if dividing)
cpdef dict _align_impl(...):
    ...
```

Do not add these while debugging — they suppress the errors that point to bugs.
Enable them only once the full test suite passes.

---

## GIL release for the inner loop

```cython
with nogil:
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = scores[seq_a[i - 1], seq_b[j - 1]]

            # M matrix
            m_diag    = M[i - 1][j - 1] + s
            m_from_x  = X[i - 1][j - 1] + s
            m_from_y  = Y[i - 1][j - 1] + s
            best_m = m_diag
            if m_from_x > best_m:
                best_m = m_from_x
            if m_from_y > best_m:
                best_m = m_from_y
            M[i][j] = best_m

            # X matrix (gap in B)
            x_open   = M[i - 1][j] + gap_open + gap_extend
            x_extend = X[i - 1][j] + gap_extend
            X[i][j] = x_open if x_open >= x_extend else x_extend

            # Y matrix (gap in A)
            y_open   = M[i][j - 1] + gap_open + gap_extend
            y_extend = Y[i][j - 1] + gap_extend
            Y[i][j] = y_open if y_open >= y_extend else y_extend

            # Traceback
            ...
```

Rules inside `with nogil:`:
- No Python object creation (`list()`, `dict()`, `str()`)
- No Python function calls
- No exceptions (except C-level `nogil` exceptions)
- Typed memoryview access and C-level `if/else/max` are fine

---

## Traceback reconstruction

The traceback walk happens after the DP fill. It navigates the `T` matrix and
builds two integer arrays. Do this outside `with nogil:` if you need to build
Python lists, or pre-allocate fixed-size numpy arrays and truncate after:

```cython
# Pre-allocate worst-case (full gap alignment)
aligned_a_np = np.empty(m + n, dtype=np.int32)
aligned_b_np = np.empty(m + n, dtype=np.int32)
cdef int[:] aligned_a_buf = aligned_a_np
cdef int[:] aligned_b_buf = aligned_b_np
cdef int k = 0

# ... fill aligned_a_buf[k] / aligned_b_buf[k] and increment k ...

# Slice the valid portion and reverse
result_a = aligned_a_np[:k][::-1]
result_b = aligned_b_np[:k][::-1]
```

---

## Annotation workflow

```bash
# Compile with annotation
uv run cython -a <the path [phases].cython gives for this algorithm>

# Open the HTML
open <the same path, with a .html suffix>
```

Color guide:
- **White** — pure C, no Python API calls
- **Yellow** (light) — one or two Python API calls
- **Yellow** (bright / orange) — many Python API calls, investigate

Every line inside the inner `for i / for j` loop must be white. If a line in
the DP fill is yellow, a type declaration is missing somewhere above it.

Common causes of yellow lines in the hot path:
- Loop variable (`i`, `j`) not declared as `cdef int`
- Score variable not declared as `cdef double`
- Using `max()` (Python built-in) instead of C `if/else` comparisons
- Accessing `scores[a, b]` where `a` or `b` is not a C integer

---

## Building

After editing the `.pyx`, recompile before running tests:

```bash
<the manifest's [commands].build>
```

Or trigger a full editable reinstall:

```bash
uv pip install -e .
```

The compiled `.so` (or `.pyd` on Windows) lands wherever the repository's build
system puts it — beside the source for an in-place build, inside the installed package
otherwise.
