# The `dp-compile.toml` manifest — shared reference

Every `dp-compile` command and skill reads this before doing anything else. It is
`@`-included rather than duplicated, for the same reason `phase-detection.md` is: two
copies of a resolution rule drift, and the drift is invisible until a command that was
never re-read behaves differently from one that was.

## What it is for

The plugin knows the *shape* of the work — a formalization, then four implementation
phases, each checked against the one before. It cannot know anything about the repository
it is working in: where kernels live, what phase files are called, how the project builds
or tests, how a new backend is registered, or which documents state invariants a kernel
must satisfy. Every one of those differs between consumers, and none is guessable.

`dp-compile.toml` states them. It sits at the **repository root**.

## It is required — there are no defaults

If no `dp-compile.toml` is found at the repository root, **stop and say so**. Do not
proceed with an assumed layout.

> `dp-compile` needs a `dp-compile.toml` at the repository root, and none was found.
> It states where kernels live, how to build and test them, and what a phase skill must
> read before writing. Here is a starting template — fill in the paths for this
> repository:
>
> *(emit the minimal template below)*

**This is deliberate, and it reverses an earlier design.** An earlier draft had the plugin
fall back to a built-in default layout so its original consumer would keep working with no
file. The failure that rules out: in any *other* repository, the plugin would silently
resolve paths under a layout that repository does not have, find nothing, and report
"algorithm not found" — misdiagnosing a missing manifest as a missing algorithm. A missing
file must present as a missing file. Baking one consumer's layout into a
consumer-agnostic plugin was also, on reflection, the wrong shape regardless.

### Minimal template

```toml
[project]
name = "my-project"
invariants = []          # documents every phase skill reads before writing
encoder = []             # where the symbol/code mapping is defined

[commands]
build = "..."
test  = "..."

[phases]
formalization = "docs/algorithms/{algorithm}/FORMALIZATION.md"
python        = "src/{algorithm}/_python.py"

[algorithms.my_algorithm]
```

## Schema

### `[project]`

| Key | Meaning |
|---|---|
| `name` | The repository's name. Used only in messages. |
| `invariants` | Paths a phase skill **must read before writing any kernel**. These carry rules no amount of reading the existing code reveals. Never optional; an empty list is a claim that the repository has none. |
| `encoder` | Where the symbol-to-integer mapping is defined. **The plugin hardcodes no reserved block and no user-symbol base** — it reads these. Assuming any particular numbering is how a kernel silently indexes the wrong symbol. |

### `[commands]`

| Key | Required | Meaning |
|---|---|---|
| `build` | yes | Makes compiled phases importable. May be a no-op string for a repository whose editable install rebuilds on import. |
| `test` | yes | Runs the whole suite. |
| `test_one` | no | Runs one file; `{path}` is substituted. Falls back to `test` when absent. |
| `benchmark` | no | Cross-backend benchmark. **When absent, the benchmarking skill reports that no benchmark command is configured and stops.** It does not invent one. |

### `[phases]`

One **path template** per phase. This is the whole of the layout question: any layout
expressible as a path is expressible here, so the plugin needs no notion of layout
"kinds", and the phase *filename* is data in the manifest rather than a constant in the
plugin.

The canonical phase names are fixed, and are the same string everywhere — as a key here,
as the filename token a template usually contains, and as the backend name a consumer
registers:

```
formalization → python → cython → cpu_parallel → cuda
```

`formalization` is not an implementation phase; it is the specification stage that
precedes them. `cpu_parallel` is `@njit(parallel=True)` on the CPU; `cuda` is the GPU
kernel. Neither is called `numba`: that names the *library*, and both phases use it, so
the name would not distinguish what it exists to distinguish.

A phase key may be omitted, which asserts that this repository will never have that phase.
Omitting one is different from having not reached it yet — a phase whose template is
present but whose file does not exist is simply unwritten.

### `[backends]`

How a consumer registers a newly written phase so its test suite can see it.

| Key | Meaning |
|---|---|
| `registry` | The file holding the backend list, if the consumer uses an explicit registry rather than import auto-discovery. |
| `build_manifest` | The build file that must also list the new source, where one exists. **Not optional where it applies**: a build system that does not glob will silently omit a file nobody added to it. |
| `require_env` | Optional. The environment variable that escalates a hardware skip to a failure, for CI. Named so a skill can *tell the user how to stop skipping* without guessing a variable name; nothing in this plugin ever sets it. |

`require_env` exists because a skip is the one test outcome that is easy to misread as a
pass. A GPU backend on a machine with no device must skip — that is the design — but a
report that says only "skipped" leaves unsaid whether CI is also skipping it. Where the key
is absent, say the escalation mechanism is not recorded here and the repository's own suite
has to be consulted. Do not invent a variable name: an instruction to set a variable that
does nothing is worse than no instruction, because it looks like it was followed.

### `[dependencies]` — optional

Where a phase's runtime dependency is declared, and what it is. **The parallel phases add
a dependency to the consumer package**: phase 3 makes the Numba runtime a hard requirement
of the package, because a backend that is registered and unimportable is a hard failure
rather than a skip; phase 4's CUDA runtime goes behind an extra instead, since a GPU
backend that is absent skips loudly and a base install must remain fully working without
one.

| Key | Meaning |
|---|---|
| `declared_in` | Path template naming the file that declares this package's dependencies — typically a `pyproject.toml`. Substituted like any other template. |
| `<phase>` | An inline table: `requires` is the requirement string to add, and `extra`, when present, names the optional-dependency group it goes under. **No `extra` means a hard runtime dependency.** |

```toml
[dependencies]
declared_in  = "packages/pfsmgraph-{package}/pyproject.toml"
cpu_parallel = { requires = "numba>=0.61" }
cuda         = { requires = "numba-cuda", extra = "gpu" }
```

`declared_in` is **not** `[backends].build_manifest`, and the two must not be collapsed
into one key. They are different files answering different questions in the same package:
a build manifest lists the *sources* a compiled artifact is built from, while dependencies
are what an installed wheel pulls in. In the one repository that has a manifest today they
are `meson.build` and `pyproject.toml` respectively.

**When the table is absent — or present but silent about the phase being written — report
what is needed and stop.** Name the requirement and say the manifest does not record where
it goes. Do not search for a `pyproject.toml` and do not edit a packaging file you were not
pointed at: a dependency written into the wrong file of a workspace is invisible until an
install in a clean environment, which is the slowest possible way to find out.

The version floor is the consumer's to choose and to justify, not this plugin's to invent.
Where the package already declares a numeric floor that the Numba runtime must be
compatible with — a `numpy` bound is the usual one — the manifest is where that pairing is
recorded, so that raising one is visibly a reason to review the other.

### `[algorithms.<name>]`

**Algorithms are listed, never discovered.** A per-algorithm directory can be globbed
safely; a flat package cannot — globbing `_*.py` there returns every private module,
algorithms and helpers alike. Since one of the two layouts cannot support discovery, the
manifest lists them, and the plugin has one code path.

| Key | Meaning |
|---|---|
| `package` | Substituted into `{package}` in the templates. Omit in a single-package repository whose templates do not use it. |
| `oracles` | Files holding known-good outputs for a differential test — typically produced by a legacy implementation being ported. **An oracle is not necessarily an equality check**: where a port deliberately fixes a defect in its source, the difference is expected and must be stated in the formalization. |

**An oracle is a pairing, not a file.** An output is a differential test only alongside the
inputs that produced it, so both must be tracked — an output whose inputs live on one
machine cannot be made into a test later. This key records *where the files are*, which is
layout and the plugin's business; what they mean, what produced them, which inputs they
pair with and where the comparison is expected to disagree belong in the formalization's
`Differential oracles` section, which is what a human reviews.

Declaring an oracle has a consequence: `/next-phase` will not advance past phase 1 while a
declared oracle is unexercised by the suite. Phases 2 to 4 are checked against phase 1, so
an unchecked phase 1 makes the chain agree with itself.

Any phase key may also appear inside `[algorithms.<name>]`, overriding the repository-wide
template for that one algorithm.

## Substitution

Three placeholders, substituted wherever they appear in a template:

- `{algorithm}` — the algorithm's name, as written in its `[algorithms.<name>]` heading.
- `{package}` — that algorithm's `package` value.
- `{path}` — used only in `[commands].test_one`.

Substitution is literal. A template naming a placeholder that has no value for the
algorithm being resolved is an error, reported with the template and the algorithm named —
never resolved to a path with a hole in it.

## Worked example — a workspace with flat packages

```toml
# dp-compile manifest -- pfsmgraph
[project]
name = "pfsmgraph"

# These carry invariants no amount of reading a kernel reveals: arc-emission
# (output_p[i, j, sym], never B[s, sym]), the N+1 state geometry, min-sum over bits
# rather than max-product, and the rule that a tie-breaking rule is contract because
# two correct backends would otherwise legitimately disagree.
invariants = [
  "docs/agents/core.md",
  "docs/design/adr/0002-three-phase-algorithm-lifecycle.md",
  "docs/design/adr/0003-one-parameterized-test-suite-per-algorithm.md",
  "docs/design/adr/0015-arc-emission-mealy-formulation.md",
  "docs/design/adr/0016-numba-cpu-parallel-phase.md",
  "docs/design/adr/0017-frozen-parameter-object-for-hmm.md",
]
encoder = [
  "docs/api/dataseq/encoder.md",
  "docs/design/adr/0011-fixed-reserved-symbol-block-and-strict-encoding.md",
]

[commands]
build    = "uv sync"        # editable install; compiled phases rebuild on import
test     = "uv run pytest"
test_one = "uv run pytest {path}"
# `benchmark` is deliberately absent: this repository has no benchmark
# infrastructure, and the skill must say so rather than assume a command.

[phases]
formalization = "docs/design/algorithms/{algorithm}/FORMALIZATION.md"
python        = "packages/pfsmgraph-{package}/src/pfsmgraph/{package}/_{algorithm}.py"
cython        = "packages/pfsmgraph-{package}/src/pfsmgraph/{package}/_{algorithm}_cython.pyx"
cpu_parallel  = "packages/pfsmgraph-{package}/src/pfsmgraph/{package}/_{algorithm}_cpu_parallel.py"
cuda          = "packages/pfsmgraph-{package}/src/pfsmgraph/{package}/_{algorithm}_cuda.py"

# A new backend is a row in the registry plus, for a compiled phase, an entry in that
# member's build file. meson does not glob, so the second half is not optional.
[backends]
registry       = "_backends.py"
build_manifest = "packages/pfsmgraph-{package}/meson.build"
require_env    = "PFSMGRAPH_REQUIRE_BACKENDS"

# Note this is pyproject.toml, not the meson.build above: build sources and runtime
# dependencies are different questions about the same package. `gpu` is the extra this
# member already declares (ADR 0004 keeps numba-cuda and dl's torch deliberately
# unmerged, so there is no family-wide [gpu]). The numba floor pairs with the
# numpy>=2.1 this member declares; raising either is a reason to review the other.
[dependencies]
declared_in  = "packages/pfsmgraph-{package}/pyproject.toml"
cpu_parallel = { requires = "numba>=0.61" }
cuda         = { requires = "numba-cuda", extra = "gpu" }

[algorithms.viterbi]
package = "hmm"
# Not a pure equality check: the delta-seeding defect of the original is fixed rather
# than reproduced, so one of these three differs at exactly one position.
oracles = [
  ".scratch/hmm-lush/Training/set02a/set02a_200/m001_0001_001.vpath.xls",
  ".scratch/hmm-lush/Training/set02a/set02a_200/m001_0005_005.vpath.xls",
  ".scratch/hmm-lush/Training/set02a/set02a_200/m008_0001_008.vpath.xls",
]
```

## Worked example — one directory per algorithm

The same five templates express a completely different layout, which is the point. No
`{package}`, and the phase name is the whole filename rather than a suffix:

```toml
[project]
name = "tokalign"
invariants = ["docs/decisions/adr/"]
encoder = ["src/tokalign/_types.py"]

[commands]
build     = "uv run --extra dev python setup.py build_ext --inplace"
test      = "uv run --extra dev pytest tests/"
benchmark = "uv run python benchmarks/run_benchmark.py {algorithm}"

[phases]
formalization = "src/tokalign/algorithms/{algorithm}/FORMALIZATION.md"
python        = "src/tokalign/algorithms/{algorithm}/_python.py"
cython        = "src/tokalign/algorithms/{algorithm}/_cython.pyx"
cpu_parallel  = "src/tokalign/algorithms/{algorithm}/_cpu_parallel.py"
cuda          = "src/tokalign/algorithms/{algorithm}/_cuda.py"

# Single-package repository, so no {package} here either.
[dependencies]
declared_in  = "pyproject.toml"
cpu_parallel = { requires = "numba" }
cuda         = { requires = "numba-cuda", extra = "gpu" }

[algorithms.needleman_wunsch]
```

This one declares no `[backends]`, which is a claim rather than an omission: a repository
whose suite discovers backends by import needs no registry, and one whose build system
globs needs no build manifest. The cost of that choice is argued in
`skills/algorithm-prototype/references/test-patterns.md` — import discovery cannot tell
"not written yet" from "written but the build is broken", and both look like a skip.
