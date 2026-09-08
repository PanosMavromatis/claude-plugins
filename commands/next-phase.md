---
description: "Advance an algorithm to the next implementation phase"
---

# /next-phase

Advance a single algorithm to the next implementation phase.

## Argument handling

`/next-phase` works on exactly one algorithm at a time.

**If no argument is provided**, stop immediately and ask the user:
> "Which algorithm would you like to advance? Please provide its name (e.g. `needleman_wunsch` or "Needleman-Wunsch")."
Do not attempt to infer or guess — wait for an explicit answer.

**If an argument is provided**, normalise it:
1. Strip leading/trailing whitespace.
2. Convert to lowercase.
3. Replace spaces, hyphens, and other separators with underscores.
   - Examples: `"Needleman-Wunsch"` → `needleman_wunsch`, `"smith waterman"` → `smith_waterman`
4. Look up the resulting name in the manifest's `[algorithms]` table.

**If the normalised name does not match any existing directory**:
- Compute the edit distance (or Levenshtein distance) between the normalised name and each key in `[algorithms]`.
- If exactly one candidate has an edit distance ≤ 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, proceed with the candidate. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

## The manifest comes first

@references/manifest.md

Resolve every path, command and algorithm name through the manifest above. If the
repository has no `dp-compile.toml`, stop and say so with the template — do not
proceed against an assumed layout.

## Behavior

@references/phase-detection.md

1. Resolve the algorithm name (see above) and confirm it has an entry in the manifest's `[algorithms]` table.
2. Apply the phase-detection logic above to determine **the target** — the artifact this
   invocation acts on. It is either a stale artifact to regenerate or an unwritten phase
   to write; the reference decides which, and there is always exactly one to start from.
3. If the phase the target depends on is failing (its tests fail, or the formalization has
   not been approved), stop and tell the user what needs to be fixed before advancing.

   **One further gate, and only when advancing past phase 1**: if the manifest declares
   `[algorithms.<name>].oracles`, confirm that phase 1's suite actually exercises them
   before writing phase 2. Phases 2 to 4 are checked against phase 1, so a phase 1 that has
   never been compared to anything outside this repository makes the whole chain agree with
   itself — and for an algorithm whose formalization was *recovered*, the document and the
   extracted test cases came from that same kernel, so there is nothing left in the chain
   that could disagree with it. Where the oracle exists and is unused, stop and say which
   file is declared and unexercised; where the manifest declares none, say so and continue,
   because a forward algorithm's specification came from outside the repository already.
4. **Say what the target is and why, before routing.** Name it, say whether it is being
   regenerated or written for the first time, and — when regenerating — name the source
   whose change made it stale. When the phase-detection step reported *two* minimal stale
   artifacts, name both and say which is being done first; the other is the next
   invocation's target, not something silently dropped.
5. Route to the skill for **the target's own phase**, not for "the phase after the current
   one". These differ whenever the target is a regeneration rather than an advance, and
   they differ in a recovered graph even when nothing is stale. **Use the `Skill` tool**
   with the fully namespaced skill name — do NOT use `Read` on the corresponding
   `SKILL.md` file. `Read` just loads the file's contents as context; only `Skill`
   activates the skill through the harness so its references and examples are wired up
   correctly.

   | Target phase | Skill |
   |---|---|
   | 0 `formalization`, phase-1 file absent | `dp-compile:algorithm-formalize` |
   | 0 `formalization`, phase-1 file present | `dp-compile:algorithm-recover` |
   | 1 `python` | `dp-compile:algorithm-prototype` |
   | 2 `cython` | `dp-compile:cython-translation` |
   | 3 `cpu_parallel` | `dp-compile:cpu-parallelization` |
   | 4 `cuda` | `dp-compile:gpu-parallelization` |

   Phase 0 appears in this table because a **recovered** formalization can be a target: it
   derives from the kernel, so editing the kernel makes the document stale and regenerating
   it is ordinary work rather than a special case. A formalization written from a paper has
   no source in the repository and never becomes a target this way.

   **Phase 0 is the one row that splits, and the discriminator is a file rather than a
   preference.** The two skills produce the same artifact at the same path from opposite
   evidence — one from source material, one from the code that already exists — so the
   presence of the phase-1 file settles which is possible. A target of phase 0 with a
   phase-1 file present is a recovery whether it is the first write or a regeneration after
   the kernel moved; `dp-compile:algorithm-formalize` has no source material to work from
   in that case and would end up describing the kernel without the discipline that keeps
   the description honest. Report which entrance was chosen and why, in step 4's line.

6. When phase detection reports no target — nothing stale, and every phase the manifest
   declares already exists — report "This algorithm is complete across every backend this
   repository declares." and stop. Say which phases those were: a repository that omits
   `cuda` from `[phases]` is complete at 3, and reporting a bare "fully implemented" would
   read as though a GPU backend had been written.
