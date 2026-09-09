# dp-compile

Guides a dynamic-programming algorithm through a staged translation — a formalization,
then pure Python, Cython, and two Numba backends — enforcing that every backend agrees with
the reference at each stage.

**It knows no repository's layout.** Paths, build and test commands, backend registration,
the encoder and the documents stating a kernel's invariants all come from a
`dp-compile.toml` at the consumer's root, so the plugin works in any repository that
carries one and in none that does not.

**It assumes [`workflow-claude`](https://github.com/PanosMavromatis/workflow-claude) and
delegates to it.** Branches, plans, commits, merges and documentation belong to that
plugin; this one runs no `git` command of its own, opens no branch, and writes no plan
file. **Install both.** Every command checks for the companion at its head, and when it is
missing prints one line and stops at the point where it would have delegated — so
`dp-compile` alone still runs, but stops short of the surrounding workflow rather than
reimplementing half of it badly.

## Overview

Every algorithm progresses through five stages — a formalization, then four executable
backends:

| # | Phase key | What it is |
|---|---|---|
| 0 | `formalization` | Language-agnostic pseudocode; understanding and adaptation |
| 1 | `python` | Pure Python; correctness. The reference every later phase is checked against |
| 2 | `cython` | Typed memoryviews; single-threaded performance |
| 3 | `cpu_parallel` | `@njit(parallel=True)` with `prange`; parallel correctness, no GPU required |
| 4 | `cuda` | `@cuda.jit`; scale |

**The filenames are the repository's, not the plugin's** — each phase is a path template in
the manifest. Phases 3 and 4 are both Numba, and neither is called `numba`: that names the
library, and a name shared by two phases cannot distinguish them.

**Phase 0 has two entrances.** The chain above assumes prose → pseudocode → Python, and
real code does not always arrive that way: a kernel translated from a legacy
implementation in another language has a reference, but it is source in a language nobody
here runs. `algorithm-recover` produces the same document at the same path from the code
instead, and the provenance edge then points from the kernel to the document — so editing
the kernel marks the formalization stale, and not the reverse. Which entrance applies is
decided by a file rather than a preference: if the phase-1 file already exists, only the
reverse one has anything to work from.

The plugin ensures the agent follows this sequence without skipping phases, losing test
coverage, or introducing behavioral differences between backends. **Staleness is decided by
recorded provenance, not by modification time**: each derived artifact carries a
`derived-from` header naming its source and that source's SHA-256, and is stale when the
recorded hash no longer matches. That survives `git checkout`, which resets every mtime,
and it records the *direction* of each edge — so a formalization recovered from an
implementation is marked stale by a change to the kernel, rather than the reverse. The full
rule is `commands/references/phase-detection.md`.

## Prerequisites

**`dp-compile` assumes the [`workflow-claude`](https://github.com/PanosMavromatis/workflow-claude) plugin is loaded**, and
delegates to it rather than duplicating it: branches through `/new-branch`, plans through
`/step` or `/hitl-step`, commits through `/smart-commit`, merges through `/smart-merge`, and
documentation through `/agents-docs-update`. This plugin owns the algorithm lifecycle and
nothing else.

Three ways it gets loaded, and a command that finds it missing names all three rather than
assuming one:

| Load path | What it looks like |
|---|---|
| Marketplace install | `/plugin install workflow-claude@<marketplace>`, once one is published |
| Session flag | `claude --plugin-dir <path>/workflow-claude` — what that plugin's own README documents |
| Project tree | the plugin's directories placed at `.claude/skills/workflow-claude/` in the consuming repository |

The third is neither a marketplace install nor a `--plugin-dir`, and it is how at least one
repository loads it today — which is why a message naming only `--plugin-dir` would send a
user to fix something that is not how they loaded it.

**Absence is not fatal, and is not uniform either.** `/phase-check` and `/benchmark`
delegate nothing, so they print one line and produce their full output. `/next-phase` and
`/new-algorithm` do every step that needs nothing from `workflow-claude` and then stop at
the step that does — a phase file written and left uncommitted costs one `git commit`, and
is a better outcome than a command that refused to start.

## The manifest

Every consumer carries a `dp-compile.toml` at its root. **There are deliberately no
defaults**: with none, a repository lacking the file would resolve paths under a layout it
does not have, find nothing, and report "algorithm not found" — a missing file misdiagnosed
as a missing algorithm. Every command stops and says so instead.

| Table | What it settles |
|---|---|
| `[project]` | The repository's name, the documents stating a kernel's invariants, and the documents describing its encoder |
| `[commands]` | How to build, how to test, how to test one file, and optionally how to benchmark |
| `[phases]` | One path template per stage. **The filenames are the repository's, not the plugin's** |
| `[backends]` | Where a new backend is registered, which build file lists its sources, and the environment variable that escalates a skip to a failure |
| `[dependencies]` | Where a runtime requirement is declared, and what each parallel phase needs |
| `[algorithms.<name>]` | One entry per algorithm, with its package and any differential oracles |

**Algorithms are listed, never discovered.** A per-algorithm directory could be globbed
safely; a flat package cannot — globbing `_*.py` there returns every private module, helpers
and kernels alike. Since one of the two layouts cannot support discovery, the manifest lists
them and the plugin has a single code path. This is not theoretical: the pre-commit hook's
first implementation wildcarded a phase template and matched two helper modules in the only
repository that had a manifest.

The full contract, with a worked example and the rules for each key, is
`commands/references/manifest.md`.

## Skills

| Skill                    | Purpose                                                  |
| ------------------------ | -------------------------------------------------------- |
| `algorithm-formalize`    | Phase 0 forward: pseudocode formalization from source material |
| `algorithm-recover`      | Phase 0 reverse: formalization recovered from an existing implementation |
| `algorithm-prototype`    | Phase 1: pure Python implementation + tests              |
| `cython-translation`     | Phase 2: Cython translation with equivalence check       |
| `cpu-parallelization`    | Phase 3: `@njit(parallel=True)` with `prange`            |
| `gpu-parallelization`    | Phase 4: Numba CUDA parallelization                      |
| `benchmarking`           | Compare performance across backends                      |

## Commands

| Command          | Description                                        |
| ---------------- | -------------------------------------------------- |
| `/new-algorithm` | Register an algorithm with the plugin and start phase 0 by whichever of the three entrances applies |
| `/phase-check`   | Report phase and staleness status for one algorithm (or all); exits without suggesting next steps |
| `/next-phase`    | Advance one algorithm to the next phase; requires an explicit name argument (asks if missing) |
| `/benchmark`     | Run cross-backend benchmarks for an algorithm      |

## Hooks

One `PreToolUse` hook on `Bash`, `hooks/scripts/pre-commit-check.py`. It runs the
manifest's `[commands].build` and `[commands].test` before a commit, and **blocks the commit
if either fails** — a wrong compiled kernel is what it exists to catch, and a hook is used
rather than an instruction precisely because it always runs where an instruction is
advisory.

It is **scoped**, which is what makes blocking tolerable: it runs only when the staged set
touches a path that a `[phases]` template resolves to, for an algorithm the manifest lists.
A docs-only commit runs nothing. The `formalization` phase is excluded — a prose edit
compiles to nothing and is imported by nothing, so staging it cannot break a backend, and
staleness reports that edit's consequence separately.

Two deliberate no-ops, each with a message rather than silent:

- **No `dp-compile.toml`** → the gate is skipped and says so. In a repository that loads
  this plugin without a manifest, that is one line on every commit; a silent skip would
  leave the repository ungated with nothing saying so.
- **No `[commands].test`** → same.

### Coexistence with other plugins' hooks

Hooks from every loaded plugin **stack**, so this one composes rather than competes:

- **It fires inside `/smart-commit`.** That command runs `git commit`, so the gate applies
  exactly as it would to a hand-typed one. **Delegating the commit does not bypass the
  check** — this plugin enforces deterministically through a hook while `workflow-claude`
  orchestrates advisorily through commands, so the two sit on different layers.
- **It cannot collide with `workflow-claude`'s `PreToolUse` hook**, which matches
  `Write|Edit|MultiEdit` where this one matches `Bash`. No tool call matches both.
- **A `PostToolUse` security review, where one is installed, is downstream of it.** If this
  gate blocks, no commit happens and no review fires — correct ordering by construction.

The hook matches `Bash` with no `if` filter and decides for itself whether the command
creates a commit, so it spawns one short-lived process per `Bash` call. That is deliberate;
`CLAUDE.md` records why an `if` matcher was rejected. The full analysis lives in
`workflow-claude`'s `_meta/plugin-conflict-report.md` §4.4.

## Typical Workflow

```
/dp-compile:new-algorithm
  → produce FORMALIZATION.md → human reviews and approves

/dp-compile:next-phase needleman_wunsch
  → implement in pure Python from formalization → all tests pass

/dp-compile:next-phase needleman_wunsch
  → Cython translation → same tests pass automatically

/dp-compile:next-phase needleman_wunsch
  → Numba CPU-parallel (prange) → same tests pass, on any machine

/dp-compile:next-phase needleman_wunsch
  → Numba CUDA → same tests pass, or skip loudly if no GPU

/dp-compile:benchmark needleman_wunsch
  → see performance comparison across backends
```

**Every one of those steps ends the same way**: the artifact is written, the suite runs,
and the commit is named as `/smart-commit`'s to make rather than run here. `dp-compile`
runs no `git` command at all.

### The full loop, with `workflow-claude`

The sequence above is what `dp-compile` contributes. In practice it runs inside the other
plugin's branch lifecycle, and each phase is a subgoal of a branch plan rather than a
free-standing command:

```
/open-revision 05-viterbi-backends        # workflow-claude: opens the revision
  └─ /new-branch                          # workflow-claude: branch + doc + plan
       └─ /hitl-step 1                    # workflow-claude: works one subgoal
            └─ /dp-compile:new-algorithm  # dp-compile: registers + phase 0
               /dp-compile:next-phase …   #   or advances one phase
          → /smart-commit                 # workflow-claude: doc sync, commit, push
       … repeat /hitl-step per phase …
  → /smart-merge                          # workflow-claude: PR, CI gate, merge
```

**`dp-compile` writes the artifact and reports; everything around it belongs to the other
plugin.** It runs no `git` command, opens no branch and edits no plan file — the plan has a
single writer. What it contributes instead is what `/hitl-step` cannot know: the artifact's
path, the source and hash its provenance header records, and what the suite did, offered as
a line that pastes straight under a subgoal.

Two things follow that are easy to get wrong in the opposite direction. **A phase artifact
is not documentation** — a formalization or a kernel is the thing being produced, so
`dp-compile` writes it, while a `README.md` or anything under `docs/agents/` belongs to
`/agents-docs-update` even when a phase changed something it describes. And **the commit
must go through `/smart-commit`**, not a plain `git commit`, because that command performs a
documentation sync; committing around it leaves a repository carrying a new backend and docs
describing the old set.

### Starting from code that already exists

An algorithm whose kernel was translated from a legacy implementation has no source
material to formalize from, and `/new-algorithm` detects that rather than asking:

```
/dp-compile:new-algorithm
  → name it; phase-1 file already exists at the resolved path
  → "That makes this the reverse entrance." → confirm
  → registers it in dp-compile.toml → recovers FORMALIZATION.md from the kernel
  → human reviews and approves

/dp-compile:next-phase viterbi
  → the formalization is fresh and phase 1 exists → Cython translation
```

The recovered document's `Derived from` names the kernel, so the kernel is the root of
this algorithm's graph and the document is downstream of it. **Phase 1 is not stale after a
recovery**, even though the document is newer than it — that direction is recorded, and a
headerless root is never given a reversed edge by the mtime fallback.

A third entrance covers a formalization the user already has: `/new-algorithm` places it,
checks it against the template's mandatory sections and the repository's invariants, and
stops for review without authoring anything.

### Updating a formalization mid-lifecycle

If the formalization is edited after later phases already exist, `/phase-check` reports the
phase-1 file as **stale** and everything below it as **blocked**, and `/next-phase`
regenerates the stale artifact rather than patching it:

```
# Edit the formalization after the Cython backend already exists
/dp-compile:phase-check needleman_wunsch
  → python: stale (formalization changed) — cython: blocked

/dp-compile:next-phase needleman_wunsch
  → regenerates the python phase from the updated formalization → tests pass

/dp-compile:next-phase needleman_wunsch
  → the cython phase is now stale in its own right → regenerated → tests pass
```

**Stale and blocked are different states, and the difference is what makes this
converge.** A blocked artifact's own recorded source has not changed yet, so it is not
regenerated speculatively; it becomes stale the moment its source actually is. Each
artifact is rebuilt exactly once, when the thing it was derived from really moves.

## The patterns the phases rely on

Three properties make phases 2, 3 and 4 transliterations rather than rewrites. The plugin
does not impose them — it reads them out of the consumer's own code and invariants — but a
repository lacking them will find each phase a redesign instead of a translation.

### Encode at the boundary

Symbols become integers at the entry point of a public call, every inner computation is
integer-only, and results decode back on the way out. The recurrence therefore never touches
a string type, which is exactly what a compiled or device backend cannot do.

**Which integers, and which are reserved, is the repository's to say.** The plugin reads the
encoder from `[project].encoder` and never names a code: a formalization calls a sentinel by
name and leaves the number to the encoder, because reserved-block numbering differs between
repositories and has changed inside one. A hardcoded index is wrong in the way no test
catches — it addresses a real position and returns a confident answer computed from some
other symbol.

### A thin wrapper over a purely numeric kernel

Each phase implements the same signature, split into a wrapper that validates, encodes and
raises, and a kernel that does neither. An impossible input comes back from the kernel as a
sentinel the wrapper interprets.

That split is a requirement rather than a style: **a CUDA device function cannot raise a
Python exception**, so a kernel written to validate would have to be redesigned at phase 4
instead of transliterated. Writing it correctly at phase 1 is what makes the rest mechanical.

### Equivalence enforced, not assumed

One suite, run against every available backend, so a new backend inherits every existing
test the moment it is registered. If a test fails, the new backend is wrong — not the test.

**Not every repository can parameterise over backends yet**, and the plugin does not pretend
otherwise: a suite written against a public API has nowhere to put a backend until that API
offers backend selection. Where that is the case the phase-specific checks go in a labelled,
explicitly non-shared section, and a passing run must not be reported as backend equivalence,
because nothing ran twice. The three arrangements and where each check belongs are in
`skills/algorithm-prototype/references/test-patterns.md`.

A related consequence, easy to miss: **a tie-breaking rule is contract.** Two backends that
break ties differently are both correct and will disagree, so the suite meant to prove their
equivalence fails on an input neither got wrong.

## Development

### Smoke test

After modifying the plugin, verify all components have valid syntax and load correctly:

```bash
./dev/smoke-test.sh
```

When adding a new skill, command, or other component, update the `expected` array in `dev/smoke-test.sh` so the smoke test covers it.

## Directory Structure

```
dp-compile/
├── .claude-plugin/
│   └── plugin.json
├── dev/
│   └── smoke-test.sh             # Verify all plugin components load
├── skills/
│   ├── algorithm-formalize/       # Phase 0 skill, forward entrance
│   ├── algorithm-recover/         # Phase 0 skill, reverse entrance (from code)
│   ├── algorithm-prototype/       # Phase 1 skill
│   ├── cython-translation/        # Phase 2 skill
│   ├── cpu-parallelization/       # Phase 3 skill
│   ├── gpu-parallelization/       # Phase 4 skill
│   └── benchmarking/              # Cross-backend benchmarking
├── commands/
│   ├── new-algorithm.md
│   ├── phase-check.md
│   ├── next-phase.md
│   ├── benchmark.md
│   └── references/               # @-included fragments, not commands
│       ├── manifest.md           # The dp-compile.toml contract
│       ├── phase-detection.md    # Nominal phase, staleness, and the target
│       └── workflow-claude.md    # Presence check and the two absence severities
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── pre-commit-check.py
└── README.md
```

## What this plugin decides, and what it does not

It decides the **shape of the lifecycle**: what the five stages are, what each one must
verify before the next begins, how staleness is determined, and which skill owns which
phase. Those live in this repository — in the skills, in `commands/references/`, and as
accumulated gotchas in `CLAUDE.md`.

It decides **nothing about the algorithms themselves**. Whether an HMM is arc- or
state-emission, where a reserved symbol block starts, which semiring a decode accumulates
in, whether a backend may be skipped — all of that belongs to the consuming repository and
is stated in the documents `[project].invariants` names. The plugin reads them before
writing anything and treats them as binding: **where a source paper and an invariant
disagree, the invariant wins**, because a source cannot overrule a decision by not having
heard of it.

That division is why the plugin has no architecture-decision log of its own. A record here
would either duplicate a consumer's ADRs or, worse, quietly compete with them — and this
plugin exists to enforce decisions, not to make them.
