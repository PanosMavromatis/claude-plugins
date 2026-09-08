# Phase detection — shared reference

This document is the single source of truth for deciding **what to do next** with an
algorithm. `/phase-check`, `/next-phase` and `/benchmark` all include it via
`@references/phase-detection.md`.

It answers three questions in order:

1. **Which artifacts exist?** — the *nominal phase*.
2. **Which of them are out of date?** — *staleness*, decided by recorded provenance.
3. **Which one does work happen on?** — *the target*.

The third question is not "which phase are we in". Under recorded provenance the
artifacts form a directed graph rather than a line, and on a graph "the current phase" is
not always a single number. The target always exists and is always well defined, so it is
what the commands act on. For an algorithm built forward — formalization first, each
phase from the one before — the graph *is* a line and the target rule reduces exactly to
picking up where the chain broke. Nothing about the ordinary case changes.

## Step 1 — Resolve the artifact paths

The five stages, in nominal order:

| # | Phase key | What it is |
|---|---|---|
| 0 | `formalization` | The specification. Not an implementation phase. |
| 1 | `python` | Pure Python. The readable reference every later phase is checked against. |
| 2 | `cython` | Compiled, single-threaded. |
| 3 | `cpu_parallel` | `@njit(parallel=True)` with `prange`. Parallel correctness, no GPU required. |
| 4 | `cuda` | `@cuda.jit`. Scale. |

**The paths come from the manifest, never from this document.** Substitute the algorithm
into each `[phases]` template per `@references/manifest.md`. A phase whose key is absent
from `[phases]` is one this repository asserts it will never have: it is not missing, it
is not stale, and it is never a target. That is different from a phase whose template is
present and whose file does not exist, which is simply unwritten.

Phases 3 and 4 are both Numba, and neither is called `numba` — that names the library,
and a name shared by two phases cannot distinguish them.

## Step 2 — Nominal phase

The nominal phase is the **highest-numbered phase whose file exists**, counting only
phases the manifest declares.

A gap is possible and is not an error to correct silently: an algorithm with phases 0, 1
and 4 present but no 2 or 3 has nominal phase 4. Report the gap; the target rule below
will fill it, because an unwritten declared phase is a target and a later existing one
does not hide it.

## Step 3 — Read the dependency edges

**The graph is read from the files, not assumed.** Each derived artifact records where it
came from:

- In `.py` and `.pyx`, a comment above the module docstring:

  ```
  # dp-compile: derived-from <path> sha256:<hash>
  ```

- In a Markdown formalization, the `Derived from` row of the Metadata table defined in
  `skills/algorithm-formalize/references/formalization-template.md`:

  ```
  | Derived from | <path> `sha256:`<hash> |
  ```

The path in that header is the artifact's **one incoming edge**. Build the graph from
those headers.

For an algorithm built forward, every header names the previous phase and the graph is
the familiar chain:

```
formalization → python → cython → cpu_parallel → cuda
```

For an algorithm whose formalization was **recovered from an implementation** — the
legacy-code entrance, where there was never a natural-language description — the
formalization's header names the kernel, and the graph branches at the root:

```
              ┌──────────────────→ formalization
python (root) │
              └──→ cython → cpu_parallel → cuda
```

This is the case that makes the graph worth reading rather than assuming. The doc is
phase 0 by number and *downstream* of phase 1 by dependency, so a stale formalization is
a reason to regenerate **the formalization** — never a reason to touch the kernel it was
derived from. A rule that walked the phase numbers would conclude the opposite and
regenerate the kernel from a document that describes it.

An empty `Derived from` — a formalization written from a paper — means the artifact
derives from nothing in the repository, so it has no incoming edge and nothing in the
repository can make it stale.

### Legacy fallback: a file with no header

A file carrying no `dp-compile` provenance line falls back to **mtime** against the
previous declared phase, and **the fallback must be reported, naming the file**:

> `_cython.pyx` has no provenance header — falling back to modification time against
> `_python.py`. Add a header when it is next regenerated.

The warning is what keeps the fallback from becoming permanent by inattention. A silent
fallback leaves a repository on mtime forever with nothing saying so.

A headerless file also supplies no edge, so its dependency is taken to be the previous
declared phase — the forward chain, which is the only thing that can be assumed in the
absence of a record.

## Step 4 — Staleness

An artifact is **stale** when the SHA-256 recorded in its header no longer matches the
current hash of the file that header names.

**Compute the hash with the target file's own `dp-compile` provenance line removed.** A
file's header records its *source's* hash; if the header counted toward its own file's
hash, re-stamping any file would spuriously invalidate everything below it, and stamping
an existing chain would take one pass per link instead of one pass. A dependent depends
on its source's content, never on its source's provenance bookkeeping.

Under mtime fallback, stale means the source's mtime is strictly newer.

### Stale is not the same as blocked

The old mtime rule propagated staleness transitively. Hashes do not, and the difference
is real rather than pedantic. If `_python.py` is edited, `_cython.pyx` goes stale — but
`_cpu_parallel.py`'s header names `_cython.pyx`, whose hash has not changed yet, so
`_cpu_parallel.py` is **not** stale. It is **blocked**: an ancestor is stale, so its
content cannot be trusted even though its own record still matches.

The distinction is what makes the process converge. Regenerating `_cython.pyx` changes
its hash, at which point `_cpu_parallel.py` becomes genuinely stale and is regenerated in
turn. Each artifact goes stale exactly when its own source actually changes.

**Blocked also covers an artifact whose named source is absent.** Phases can be skipped —
a `cuda` kernel written straight from the `.pyx`, or a repository that filled a gap out of
order — and then a header names a file that does not exist. There is nothing to hash, so
the artifact is neither fresh nor stale, and it is not a target either: an artifact cannot
be regenerated from a source that is not there. It is blocked on the absent phase, which
the target rule reaches as an unwritten phase in its own right.

For each artifact, record exactly one of:

| State | Meaning |
|---|---|
| `absent` | The file does not exist. |
| `fresh` | Its recorded hash matches its source, and no ancestor is stale or absent. |
| `stale` | Its recorded hash no longer matches the source its header names. |
| `blocked` | Its own record still matches, but an ancestor is stale or absent. |

## Step 5 — The target

> **The target is the first stale artifact in dependency order, regenerated from the
> source its own header names. When nothing is stale, the target is the lowest-numbered
> unwritten declared phase.**

"First in dependency order" means: **a stale artifact with no stale ancestor.** Blocked
artifacts are never targets; they become stale on their own once the thing above them is
regenerated, or — where they are blocked on an *absent* ancestor — once that phase is
written for the first time.

**When two stale artifacts are both minimal, they are independent.** In the recovered
graph above, editing the kernel makes the formalization and the `.pyx` stale
simultaneously, and neither is upstream of the other — the partial order does not rank
them. Report both, and take the **lower phase number first**, so the document is brought
back into agreement with the code before anything is translated from it. That tie-break
is a convention, not a derivation; what matters is that both are named rather than one
silently chosen.

When nothing is stale and every declared phase exists, the algorithm is complete across
all backends.

### Why this replaces "effective phase" rather than extending it

The former rule was *"the phase just before the first stale file in the chain"*. It
assumes a single linear order that is simultaneously the phase order and the dependency
order. That assumption holds for the forward chain and fails for the recovered graph in
both directions at once: the formalization is numerically first and dependency-last, so
"the phase before it" is not a phase at all, and a stale doc would be read as a reason to
regenerate the kernel that is its own source.

The target rule agrees with the old one everywhere the old one was right. On a chain,
the first stale artifact is the first broken link, and regenerating it is exactly what
"advance from the effective phase" meant.

## Phase-specific validation

- **Phase 0** — verify the formalization is non-empty and that its mandatory sections are
  filled. Ask the user whether it has been reviewed and approved.
- **Phases 1–4** — run the tests for **fresh** backends only. A stale or blocked backend's
  tests are not run: its source may disagree with the thing it was derived from, so a pass
  and a failure are equally uninformative. Say which backends were skipped and why.

## Worked examples

| Situation | Nominal | Stale | Blocked | Target |
|---|---|---|---|---|
| Formalization only | 0 | — | — | write `python` |
| Formalization + python, both fresh | 1 | — | — | write `cython` |
| Formalization edited after `_python.py` was generated | 1 | `python` | — | regenerate `python` from the formalization |
| `_python.py` edited; cython, cpu_parallel, cuda all present | 4 | `cython` | `cpu_parallel`, `cuda` | regenerate `cython`; the other two follow once its hash changes |
| Recovered doc; kernel then edited | 4 | `formalization`, `cython` | `cpu_parallel`, `cuda` | both named; `formalization` first |
| All declared phases present and fresh | 4 | — | — | none — complete |
| `cuda` omitted from `[phases]`; 0–3 present and fresh | 3 | — | — | none — complete for this repository |
| `cuda` written straight from `cython`; `cpu_parallel` never written | 4 | — | `cuda` (source absent) | write `cpu_parallel` — the gap, which the later file does not hide |
