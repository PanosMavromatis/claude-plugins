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
4. Look up the resulting name as a directory under `src/tokalign/algorithms/`.

**If the normalised name does not match any existing directory:**
- Compute the edit distance between the normalised name and each directory under `src/tokalign/algorithms/`.
- If exactly one candidate has an edit distance <= 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, use that algorithm. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

## Execution

Once the algorithm name is resolved to snake_case:

### 1. Run phase-check (staleness gate)

Before benchmarking, check for staleness using the phase-detection logic:

@references/phase-detection.md

Apply the staleness rules above to the algorithm directory. If **any backend file is stale**, stop and report:
> "Cannot benchmark `<algorithm>`: `<file>` is stale (its prerequisite `<prereq>` was modified more recently). Run `/next-phase <algorithm>` to regenerate stale backends before benchmarking."

Do **not** proceed to benchmarking if any staleness is detected.

### 2. Check backend count

Verify at least two non-stale backends exist (Python + Cython, or Python + Cython + Numba). If only one backend exists:
> "Only the Python backend exists for `<algorithm>`. Benchmarking requires at least two backends to compare. Run `/next-phase <algorithm>` to add a Cython backend."

### 3. Run the benchmark script

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/benchmarking/scripts/run-benchmark.sh" <algorithm_name>
```

Or invoke the canonical script directly from the project root:

```bash
uv run python benchmarks/run_benchmark.py <algorithm_name>
```

The script auto-discovers backends, runs timing benchmarks across sequence lengths, and saves results to `benchmarks/results/<algorithm>/`.

If the user requested memory profiling (e.g., "benchmark with memory", "include memory"), add the `--memory` flag. This requires `memory-profiler` to be installed.

### 4. Present results

After the script completes:
1. Display the markdown table from stdout (or read `benchmarks/results/<algorithm>/results.md`)
2. Mention the scaling plot file path so the user can open it
3. Highlight crossover points and any anomalies
4. Offer a brief (2-3 sentence) interpretation of the results

Do **not** suggest code optimizations unless the user asks.
