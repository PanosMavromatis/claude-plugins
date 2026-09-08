---
description: "Register an algorithm with the plugin and start it at phase 0, by whichever entrance applies"
---

# /new-algorithm

Bring an algorithm under this plugin's lifecycle and start it at phase 0.

**"New" means new to the plugin, not newly written.** An algorithm whose kernel already
exists and was never formalized is exactly as new here as one that does not exist at all —
neither is in the manifest, and neither has a specification. Which entrance applies is what
the mode step settles, and it is settled partly by the filesystem rather than entirely by
asking.

## The manifest comes first

@references/manifest.md

Resolve every path, command and algorithm name through the manifest above. If the
repository has no `dp-compile.toml`, stop and say so with the template — do not
proceed against an assumed layout.

## `workflow-claude` is assumed

@references/workflow-claude.md

**`/new-algorithm` takes the stop-at-the-delegation severity.** Print the one line at the head, do
every step that needs nothing from `workflow-claude`, and stop when you reach the step that
does — naming what is left undone. Do not substitute: no `git commit` run here, no branch
created here, and no quiet finish as though the step had not existed.

## The three entrances

| Mode | The user has | Phase 0 comes from | Routes to |
|---|---|---|---|
| **Forward** | Source material — a paper, a URL, a description | Writing it from that material | `dp-compile:algorithm-formalize` |
| **Reverse** | An existing phase-1 implementation | Recovering it from the code | `dp-compile:algorithm-recover` |
| **Supplied** | A formalization already written | Nothing — it exists | No skill: the checks in 5a, then `/next-phase` |

All three end at the same place: a document at the path `[phases].formalization` gives,
reviewed and approved, which every later phase translates from.

## Behavior

### 1. Name the algorithm

Ask: "What algorithm do you want to bring under `dp-compile`? Give me its name."

Normalise the answer to `snake_case` (`"Smith-Waterman"` → `smith_waterman`), show the
converted name, and ask the user to confirm it. The name is the `[algorithms.<name>]`
heading and is substituted into every path template as `{algorithm}`, so a wrong one is
expensive to change later.

### 2. Resolve the paths and read the filesystem

Substitute the confirmed name into every `[phases]` template and record, for each declared
phase, whether the file exists. **Report what you found before asking anything else** —
the user is about to answer a question whose right answer depends on it, and a template
that resolved to an unexpected directory is far cheaper to catch here than after a skill
has started writing.

### 3. Determine the entry mode

**Do not ask what the filesystem already answers.**

- **The phase-1 file exists** → the mode is **reverse**. Say so and confirm rather than
  offering a choice:

  > "A phase-1 implementation already exists at `<path>`. That makes this the reverse
  > entrance: I will recover a formalization from the code rather than write one from
  > source material. Correct?"

  There is no forward option here. `algorithm-formalize`'s own trigger excludes an
  algorithm whose phase-1 file exists, because with a kernel present and no source
  material it would end up describing that kernel. Confirm rather than assume, though: a
  `yes` also confirms that the file found is this algorithm's and not a near-miss from a
  mis-normalised name.

- **The formalization file already exists** → this algorithm has already started. Do not
  scaffold it again. Tell the user it exists and send them to
  `/dp-compile:next-phase <name>`, which will resolve the target properly. If they meant
  to replace the document, that is an edit to a living specification, not a new algorithm.

- **A phase-2, -3 or -4 file exists but phase 1 does not** → stop and report it. Something
  is wrong with either the templates or the name; do not guess which.

- **No phase file exists** → ask the one question the filesystem cannot answer:

  > "Two entrances are possible. Are you starting from **source material** — a paper, a
  > URL, or a description I should formalize — or do you already have a **written
  > formalization** to bring in?"

### 4. Register the algorithm in the manifest — propose, confirm, then write

**Algorithms are listed, never discovered**, so an algorithm absent from `[algorithms]` is
invisible to `/phase-check` and `/next-phase` no matter how many of its files exist. This
step is most of what "scaffold" means here, and it applies to every mode.

If `[algorithms.<name>]` is missing, propose the block and **wait for approval before
writing it** — `dp-compile.toml` is the repository's contract with this plugin, not a
scratch file:

```toml
[algorithms.<name>]
package = "<value>"   # only if the templates use {package}
```

Include `oracles` only in the reverse mode, and only if the user names files that hold
known-good outputs from the legacy implementation. Do not go looking for them.

If the entry already exists, say so and change nothing.

### 5. Route

**Use the `Skill` tool** with the fully namespaced skill name — do NOT use `Read` on the
corresponding `SKILL.md`. `Read` only loads the file's contents as context; only `Skill`
activates the skill through the harness so its references and examples are wired up. If
the `Skill` tool reports the skill is unavailable, stop and tell the user the plugin has
not loaded correctly, naming the skill.

- **Forward** → `dp-compile:algorithm-formalize`.
- **Reverse** → `dp-compile:algorithm-recover`.
- **Supplied** → no skill. Do the checks in step 5a, then stop.

### 5a. The supplied mode: place it, check it, do not rewrite it

A formalization the user already has skips the *authoring* of phase 0. It does not skip
phase 0's gate.

1. **Get the document.** Accept a path — inside the repository or outside it — or pasted
   text. Copy it to the path `[phases].formalization` gives, creating the directories that
   path names. Show the destination and confirm before writing.

2. **Leave `Derived from` empty.** A document brought in from outside derives from nothing
   in this repository, so nothing here can make it stale — the same as one written from a
   paper. Do not stamp it with a header naming a file it did not come from.

3. **Check it against the template.**
   `skills/algorithm-formalize/references/formalization-template.md` is canonical for
   structure; read it and check every section it marks mandatory, rather than working from
   a list written here that would drift from it. Report what is present and what is
   missing, section by section.

   **Two absences cost the most and are the easiest to miss**, because neither fails now:

   - **No `Parallel decomposition`.** Nothing consumes it until phase 3, where
     `cpu-parallelization` stops and routes the decision back to the document. Finding it
     now costs a question; finding it then costs the phase.
   - **No `Test Cases`, or cases without their precision level.** Phase 1 translates the
     specification *and its tests* from this document. A formalization with no test cases
     leaves phase 1 to invent them, which is where the equivalence chain would have
     started.

4. **Check it against `[project].invariants`.** A document written for a different
   repository — or for none — may contradict a rule this one holds, and the contradiction
   is invisible to every later phase because each translates faithfully from it. The two
   that recur: a hardcoded reserved symbol code where the encoder owns the numbering, and
   a recurrence stated in the formulation the literature uses rather than the one this
   repository committed to.

5. **Report gaps; do not fill them silently.** Where a section is missing, offer to write
   it by asking the user the questions that settle it. Do not rewrite the document into
   the template's voice — the user wrote it, and reformatting a specification is a change
   to it that no diff will make legible.

6. **Stop for review** exactly as the two authoring skills do, then tell the user:

   > "The formalization is in place at `<path>` and registered as `<name>`. Review it —
   > particularly `<any section flagged above>` — then run `/dp-compile:next-phase <name>`
   > to begin the Python prototype."

### 6. Report

Say which mode was used and why, where the formalization is or will be, what was added to
`dp-compile.toml`, and what the next command is. **Name the mode explicitly even when it
was inferred rather than chosen** — a user who did not realise the reverse entrance had
been selected will not understand why the resulting document cites their own code.
