---
description: "Run cross-backend benchmarks for an algorithm"
---

# /benchmark

Run a cross-backend performance benchmark for a single algorithm.

## Argument handling

**An algorithm name is required.** If `$ARGUMENTS` is empty, ask:
> "Which algorithm should I benchmark? (e.g., `needleman_wunsch` or `Needleman-Wunsch`)"

Wait for the user's answer before proceeding.

**Normalise the algorithm name:**
1. Strip leading/trailing whitespace.
2. Convert to lowercase.
3. Replace spaces, hyphens, and other separators with underscores.
   - Examples: `"Needleman-Wunsch"` -> `needleman_wunsch`, `"smith waterman"` -> `smith_waterman`
4. Look up the resulting name in the manifest's `[algorithms]` table.

**If the normalised name does not match any existing directory:**
- Compute the edit distance between the normalised name and each key in `[algorithms]`.
- If exactly one candidate has an edit distance <= 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, use that algorithm. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

## The manifest comes first

@references/manifest.md

Resolve every path, command and algorithm name through the manifest above. If the
repository has no `dp-compile.toml`, stop and say so with the template — do not
proceed against an assumed layout.

## `workflow-claude` is assumed

@references/workflow-claude.md

**`/benchmark` takes the note-and-continue severity.** It delegates nothing, so its absence
changes what this command can do not at all — print the one line and carry on to the full
report. Refusing here would be refusing for a dependency this command never reaches.

## Execution

Once the algorithm name is resolved to snake_case:

### 1. Run phase-check (staleness gate)

Before benchmarking, check for staleness using the phase-detection logic:

@references/phase-detection.md

Apply the phase-detection logic above. If **any implementation phase is `stale` or
`blocked`**, stop and report:
> "Cannot benchmark `<algorithm>`: `<file>` is `<stale|blocked>` (`<source>` has changed
> since it was generated). Run `/next-phase <algorithm>` to regenerate it before
> benchmarking."

Do **not** proceed if anything is stale or blocked. **Blocked counts here even though it
is not yet a regeneration target**: it means an ancestor has changed, so the backend is
about to be regenerated and the number measured now describes code that is on its way out.
A benchmark compares backends only if they all implement the same algorithm — that is the
entire premise, and a stale or blocked backend breaks it.

The formalization's own state is **not** a gate. It is a document; it compiles to nothing
and contributes no timing. A stale formalization is a documentation problem, and refusing
to measure four working backends over it would be a gate on the wrong artifact.

### 2. Check backend count

Count the **fresh implementation phases** — `python`, `cython`, `cpu_parallel`, `cuda`,
as far as the manifest declares them. Benchmarking needs at least two:

> "Only the Python backend exists for `<algorithm>`. Benchmarking requires at least two
> backends to compare. Run `/next-phase <algorithm>` to add a Cython backend."

Name every backend that will be measured, and every declared phase excluded, with its
reason — absent, stale, blocked, or (for `cuda`) no device available. **A skipped GPU
backend must be as visible as a measured one**: a table of three rows where four were
expected is otherwise read as a result rather than as an omission.

### 3. Run the repository's benchmark command

Take it from the manifest's `[commands].benchmark`, substituting `{algorithm}`.

**`benchmark` is optional.** If the manifest does not define it, stop and report that this
repository has no benchmark command configured — do not invent one, and do not guess at a
script path. A repository may legitimately have no benchmark infrastructure at all; saying
so is the correct outcome, not a failure.

Where the command writes its output is the repository's business, not this command's. Read
what the command prints and follow it to whatever files it names.

**Pass no flag the manifest did not give you.** A request like "benchmark with memory" is a
request about the repository's harness, not about this command: whether it profiles memory,
and what it spells that as, is the harness's business. Run the configured command, say what
was asked for, and let the user point at the option if one exists. Appending an invented
flag either errors or — worse, on a harness that ignores unknown arguments — silently
returns an ordinary timing run labelled as something else.

### 4. Present results

After the command completes:
1. Display whatever tabular result it printed, or read the file it names
2. Mention any plot or artifact path it reports, so the user can open it
3. Highlight **each** crossover, naming the pair it lies between. With four backends
   there are three transitions worth reporting — python → cython, cython → cpu_parallel,
   cpu_parallel → cuda — and each has its own crossover length, or none. A crossover that
   does not exist within the lengths measured is a finding, not a gap: it says the faster
   backend never repays its overhead at this scale.
4. **Report the machine.** Core count, the thread count the parallel backend ran with, the
   device if one was present, and every declared backend excluded with its reason. A
   crossover is a property of the machine rather than of the algorithm — the
   cython → cpu_parallel one moves with core count, the cpu_parallel → cuda one with the
   device — so a number without its conditions is neither reproducible nor comparable, and
   is one copy-paste away from becoming a false claim about the algorithm in a README.
5. Offer a brief (2-3 sentence) interpretation of the results

Do **not** suggest code optimizations unless the user asks.
