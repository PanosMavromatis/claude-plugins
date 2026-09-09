# Cython Typed Memoryviews

Reference for users new to Cython. Typed memoryviews are the primary way to
access numpy array data at C speed inside Cython functions.

---

## What they are

A typed memoryview is a C-level view into a contiguous block of memory (usually
a numpy array). Once declared, indexed access (`buf[i, j]`) compiles to a direct
C pointer dereference — no Python call, no reference counting, no GIL.

---

## Declaration syntax

```cython
# 1D int32 array
cdef int[:] seq_a

# 2D float64 array
cdef double[:, :] M

# 1D int8 array (compact traceback)
cdef signed char[:] trace
```

Assign a numpy array to populate the view:

```cython
import numpy as np

arr = np.zeros((m + 1, n + 1), dtype=np.float64)
cdef double[:, :] M = arr
```

`M` and `arr` now share the same memory. Writing `M[i, j] = 1.0` also changes
`arr[i, j]`.

---

## Dtype mapping

| Cython type       | NumPy dtype       | C type        |
| ----------------- | ----------------- | ------------- |
| `int[:]`          | `np.int32`        | `int`         |
| `long[:]`         | `np.int64`        | `long`        |
| `double[:]`       | `np.float64`      | `double`      |
| `float[:]`        | `np.float32`      | `float`       |
| `signed char[:]`  | `np.int8`         | `signed char` |

**The dtype of the numpy array must exactly match the memoryview type.** A
mismatch raises `ValueError: Buffer dtype mismatch` at runtime. Cast at the
boundary if needed:

```python
# In the Python wrapper, before calling the Cython function:
enc_a = np.asarray(enc_a, dtype=np.int32)
scores = np.asarray(scoring_matrix._matrix, dtype=np.float64)
```

---

## Contiguity

By default, `double[:, :]` accepts any memory layout (C-contiguous, Fortran-
contiguous, or strided). For maximum performance, declare C-contiguous explicitly:

```cython
cdef double[:, ::1] M   # C-contiguous (row-major)
```

NumPy arrays created with `np.zeros` / `np.full` / `np.empty` are C-contiguous
by default. Arrays produced by slicing or transposing may not be — use
`np.ascontiguousarray()` at the boundary.

---

## Indexing

```cython
# Reading
cdef double val = M[i, j]

# Writing
M[i, j] = 3.14

# 1D
cdef int sym = seq_a[k]
```

With `@cython.boundscheck(False)` and `@cython.wraparound(False)`, these
compile to raw pointer arithmetic.

---

## Passing to functions

Declare the parameter type in the `cpdef` or `cdef` signature:

```cython
cpdef dict _align_impl(int[:] seq_a,
                       int[:] seq_b,
                       double[:, :] scores,
                       double gap_open,
                       double gap_extend):
    ...
```

The caller (Python wrapper) passes numpy arrays directly:

```python
result = _align_impl(enc_a, enc_b, scoring_matrix._matrix,
                     scoring_matrix.gap_open, scoring_matrix.gap_extend)
```

---

## Returning data

Typed memoryviews cannot be returned from `cpdef` functions directly (they are
C-level views). Return the underlying numpy array instead:

```cython
cpdef dict _align_impl(...):
    aligned_a_np = np.empty(m + n, dtype=np.int32)
    cdef int[:] aligned_a = aligned_a_np
    # ... fill aligned_a[k] ...
    return {"score": best_score,
            "aligned_a": aligned_a_np[:k][::-1].copy(),
            "aligned_b": aligned_b_np[:k][::-1].copy()}
```

---

## GIL compatibility

Typed memoryview reads and writes are GIL-safe and can appear inside
`with nogil:` blocks. The following are NOT GIL-safe and must stay outside:

- Allocating numpy arrays (`np.zeros(...)`)
- Calling Python functions
- Raising Python exceptions
- Returning Python objects (dicts, lists)

Pattern: allocate all numpy arrays before the `with nogil:` block, fill them
inside, then build the return value after.

---

## Common errors

| Error | Cause | Fix |
| ----- | ----- | --- |
| `Buffer dtype mismatch` | numpy dtype ≠ memoryview type | Cast array to correct dtype at boundary |
| `ndarray is not C-contiguous` | Sliced or transposed array | Wrap with `np.ascontiguousarray()` |
| `Cannot convert ... to memoryview slice` | Passing a Python list | Convert to numpy array first |
| `Cannot assign to ... in nogil` | Assignment to Python object in `with nogil:` | Move assignment outside nogil block |
