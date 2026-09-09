---
name: gpu-parallelization
description: >
  TRIGGER: when advancing an algorithm to Phase 4, the `cuda` phase; when the user says
  "GPU", "CUDA", "cuda.jit", "numba-cuda", "run it on the GPU", or asks to scale a DP
  kernel beyond what CPU threads give. Also trigger when /next-phase resolves a target
  whose phase key is `cuda`.
  Do NOT trigger for the CPU-parallel phase 3, `@njit(parallel=True)` or `prange` — that is
  cpu-parallelization; nor for torch/deep-learning GPU work, which is an unrelated stack.
---

# gpu-parallelization

Guide the translation of a validated CPU-parallel kernel into a Numba CUDA kernel: the
final phase, and the narrowest one.

## What this phase is, and what it is not

**The algorithm is not redesigned here, and the decomposition is not chosen here.** Both
were settled at phase 3 and validated there against the phase-1 oracle on hardware anyone
has. This phase re-expresses the *same* decomposition in the CUDA execution model.

That is the whole reason ADR 0016 inserted a CPU-parallel phase in front of this one.
Before it, a first GPU attempt had to debug the decomposition and the hardware at once,
with the two failure modes producing the same symptom — a wrong answer that appears
intermittently. Now the decomposition arrives already known-correct under concurrency, and
what remains is genuinely hardware:

- **Where the barriers are.** `cuda.syncthreads()` synchronises a block, not a grid.
- **Memory coalescing** — whether adjacent threads read adjacent addresses.
- **Occupancy** — block size, register pressure, shared-memory budget.
- **The host/device boundary** — what is copied, when, and how often.
- **`cuda.jit` semantics** — what a device function may and may not do.

If, while writing this, the decomposition itself looks wrong, that is a **phase 3 finding**.
Say so and go back; do not fix it here, or the two backends stop implementing the same
argument and the equivalence suite becomes the only thing holding them together.

## The manifest comes first

Every path, command and dependency below is resolved through the consumer's root
`dp-compile.toml`, whose contract is `commands/references/manifest.md`. This skill knows no
repository's layout. If there is no manifest, stop and say so.

## Prerequisites

1. **The phase-3 file exists and is not stale**, at the path `[phases].cpu_parallel` gives.
   This phase derives from it. If it is missing or stale, stop and hand off with the
   `Skill` tool — `skill: "dp-compile:cpu-parallelization"`, not `Read`.

   Where the manifest declares no `cpu_parallel` phase at all, this phase derives from
   `cython` instead and **the decomposition has never been validated under concurrency**.
   Say that plainly before starting: it is a real position for a repository to take, and it
   is also the situation ADR 0016 exists to avoid.

2. **The suite is green** for every existing backend: `[commands].build`, then
   `[commands].test`.

3. **Read the formalization's `Parallel decomposition` section and the phase-3 kernel.**
   The section is the argument; the kernel is that argument already made concrete once.
   Both, not one.

4. **Establish whether a CUDA device is actually present**, and say so before writing
   anything:

   ```bash
   python -c "from numba import cuda; print(cuda.is_available()); print(cuda.detect())"
   ```

   A device is **not** required to write this phase — see the simulator below — but whether
   one is present changes what the verification step can claim, and that has to be stated
   up front rather than discovered at the end.

## Writing the kernel

### The sequential dimension becomes a sequence of launches

This is the structural difference from phase 3, and most of the work.

Every decomposition has a sequential axis: the anti-diagonal index `d` for a 2-D grid, the
timestep `t` for a recurrence over time. Under `prange` that axis is an ordinary Python
loop, and the parallel region ends at each iteration, which is the barrier.

CUDA has no grid-wide barrier inside a kernel. `cuda.syncthreads()` synchronises threads
**within one block** and says nothing about any other block. So the sequential axis moves
to the host, and each of its steps becomes a kernel launch — the launch boundary is the
grid-wide barrier:

```python
for d in range(num_groups):                 # host loop: the sequential axis
    _step[blocks, threads](d, ...)          # device: the whole group, in parallel
```

Trying to keep the sequential loop inside the kernel is the single most common way to get
a GPU DP wrong. It produces a kernel that is correct whenever the grid happens to fit in
one block and wrong above that — so it passes on the small test and fails on the input the
GPU was for.

The cost is a launch per group, which is why the phase pays off on large problems and not
on small ones. Report that as a measurement, not an apology.

### The device function is even more constrained than phase 3's kernel

The rule was already "purely numeric, neither validates nor raises". On the device it is
enforced by the platform: no Python objects, no exceptions, no dynamic allocation, no
calls into the encoder. A kernel written to the phase-1 rule needs no rework here — which
was the point of writing that rule at phase 1 rather than discovering it now.

The public entry point stays identical, as at every phase.

### Indexing

Use `cuda.grid(1)` (or `cuda.grid(2)`) for the global thread index, and **bounds-check
it**. A launch is rounded up to whole blocks, so the last block almost always has threads
past the end of the data; unchecked, they write outside the array.

```python
i = cuda.grid(1)
if i >= n:
    return
```

See `references/numba-cuda-patterns.md` for the grid-stride form, shared-memory staging,
and the wavefront launch pattern in full.

## Declare the dependency — behind an extra, not as a hard requirement

The CUDA runtime goes into the **optional** dependency group the manifest's
`[dependencies].cuda` names via its `extra` key. This is the opposite of phase 3, and the
difference is not arbitrary:

- Phase 3's backend registers with no hardware requirement, so a failed import is a **hard
  failure** — the dependency must therefore be present in every install.
- Phase 4's backend requires a device, so its absence is a **skip**. A base install with no
  GPU must remain a fully working library rather than a stub, which it would not be if it
  demanded a CUDA runtime.

**If `[dependencies]` is absent or says nothing about `cuda`, report what is needed and
stop.** Do not search for a packaging file, and do not add the requirement to the hard
dependency list "for now" — that inverts the decision above silently.

## Register the backend

Follow `[backends]`. The row for this phase declares its hardware requirement — in
pfsmgraph's vocabulary, `hardware="CUDA device"` — and that field is what makes an absent
GPU a **loud skip** rather than either a silent pass or a hard failure. Contrast it with
phase 3's `hardware=None`, where a failed import must escalate.

Say all three things in the report, because a skip is easy to misread as a pass:

1. The backend is registered.
2. On a machine with no device it will skip, and the session header will name it.
3. How to make CI fail instead of skipping. Take that from `[backends].require_env` when
   the manifest declares it. Where it does not, say the escalation mechanism is not
   recorded in the manifest and the repository's own suite has to be consulted — do not
   guess an environment variable name.

Where `build_manifest` names a build file, list the new source there too: a build system
that does not glob omits any file nobody listed, and the module will import in development
and be missing from the wheel.

## Verify

### 1. The suite

`[commands].build`, then `[commands].test`. The parameterised suite is the equivalence
check; if a test fails, the CUDA kernel is wrong.

### 2. Without a device — the simulator

**A GPU is not needed to test the logic.** Numba ships a simulator that executes
`@cuda.jit` code on the CPU:

```bash
NUMBA_ENABLE_CUDASIM=1 <[commands].test_one, or [commands].test>
```

It is slow and it does not model coalescing, occupancy or warp divergence at all — so it
proves nothing about performance and everything about indexing, bounds and barrier
placement, which is where the correctness bugs are. Use it, and **say in the report that
the result came from the simulator**: a green simulator run is not evidence that the kernel
runs on a device.

### 3. On a device, if one is present

Run the suite for real, and confirm the session header stops reporting this backend as
skipped. A backend that still reports as skipped on a machine with a working GPU is a
registration problem, not a hardware one.

### 4. Everything phase 3 checked, again

The deliberate tie, and the property test over generated inputs before it. Ties are where
two correct backends legitimately disagree, and a fourth backend is a fourth chance to
disagree. **Reuse those tests rather than writing new ones** — under a parameterised suite
they already run against this backend the moment it is registered, and writing a second copy
is how two checks of one property drift apart.

The cumulative rule is in `../algorithm-prototype/references/test-patterns.md` under
**Equivalence discipline, phase by phase**.

## Handing back

The phase ends when the file is written and the suite is green. **What happens to it next
is not this plugin's to do.**

- **Do not run `git add` or `git commit`.** Say the work is ready and name `/smart-commit`,
  which the `workflow-claude` plugin owns. A plain `git commit` skips the documentation sync
  that command performs, so the repository ends up carrying a new backend and docs
  describing the old set — which is why "just commit it" is the wrong suggestion here rather
  than merely a shortcut.
- **Do not open a branch.** `/new-branch` owns that.
- **Do not edit a plan file.** `/hitl-step` and `/step` own the markers and the notes.
  Report the facts they cannot know — the artifact's path, the source and hash its
  provenance header records, and what the suite did — in a form that pastes under a
  subgoal, and stop:

      > **Done:** phase <n> `<key>` — `<path>`, derived-from `<source>` `sha256:<hash>`,
      > suite green at <N>.

- **Do not touch documentation.** A `README.md`, anything under `docs/agents/`, and every
  generated `AGENTS.md` belong to `/agents-docs-update`, even when this phase changed
  something they describe. The phase artifact is the exception, because it *is* the thing
  being produced rather than a description of the repository.

## What this skill does NOT do

- **No new decomposition, and no algorithmic change.** Both belong to phase 3 or to the
  formalization.
- **No performance tuning before the suite is green.** Coalescing and occupancy are worth
  real effort, and none of it before the answer is right.
- **No change to the public signature**, and no edits to tests to make the kernel pass.
- **No claim about speed from a simulator run**, and no claim that the backend works on
  hardware that was never present.

## Gotchas

- **A grid-wide barrier does not exist inside a kernel.** `cuda.syncthreads()` is
  per-block. If the algorithm needs all threads to agree before continuing, that boundary
  is a kernel launch.
- **Uncoalesced access is the usual reason a correct kernel is slow.** Adjacent threads
  should read adjacent addresses; a wavefront stored by row and indexed by anti-diagonal
  reads with a stride. That is a layout change, not an algorithm change.
- **The first launch compiles.** Any timing including it measures the compiler, exactly as
  at phase 3 — and here the PTX compile is slower still.
- **Host/device transfer often dominates.** A kernel that is faster than the CPU and an
  end-to-end path that is slower usually means the arrays are being copied per launch.
  Move them to the device once, outside the sequential loop.
- **Float atomics are not deterministic.** `cuda.atomic.add` on floats accumulates in an
  order the hardware chooses, so two runs can differ in the last bits and the equivalence
  test may be asserting equality. Prefer a structure that does not need an atomic; where
  one is unavoidable, say so where the tolerance is set.
- **The simulator hides the bugs it cannot model.** Warp divergence, races between blocks
  and coalescing behaviour are all invisible under `NUMBA_ENABLE_CUDASIM`. Do not read a
  green simulator run as a validated kernel.
- **`numba-cuda` is a separate distribution from `numba`** and has its own CUDA toolkit
  expectations. An import failure here is usually an environment problem rather than a code
  one — diagnose it before rewriting anything.
- **"GPU" can mean two unrelated stacks in one repository** — a CUDA DP backend and a deep
  learning framework. They share no dependency and must not be merged into one extra.

## Reference material

- `references/numba-cuda-patterns.md` — launch configuration, the wavefront launch loop,
  grid-stride loops, shared memory, and the host/device boundary.
- `examples/example-cuda-impl.py` — one family's worked instance, end to end.
- `../cpu-parallelization/references/decomposition-patterns.md` — **the decompositions
  themselves.** They are not restated here: phase 4 reuses phase 3's answer, and two copies
  of one argument drift apart.
