# Generate `docs/agents/[<path>/]codex.md` sidecars for cross-provider Codex review context

Generate a `codex.md` file that configures OpenAI Codex as a cross-provider code
reviewer. Codex is assumed to handle review and occasional implementation, with
Claude Code as the primary implementer. In a monorepo layout, generate one
sidecar per component (in addition to the root) so component-scoped reviews have
focused context. Work through the steps below in order.

---

## Step 1 — Detect targets

The command processes one **target** per `codex.md` to generate. Each target is
identified by its `<path>` (empty for the root, e.g. `ui/` or `ui/components/`
for components). The directory tree under `docs/agents/` is the source of truth
for which components exist.

**Discover candidate targets.**

- **Root.** The root target is a candidate if `docs/agents/core.md` exists.
- **Components.** Run `find docs/agents -mindepth 1 -type d` (any depth). For
  each subdirectory, the component's `<path>` is its location relative to
  `docs/agents/` (with trailing slash).

**Classify each target.**

- **Ready.** Both `docs/agents/<path>core.md` and `docs/agents/<path>claude.md`
  exist, *and* `docs/agents/<path>codex.md` does **not** exist. → generate.
- **Already done.** `docs/agents/<path>codex.md` already exists. → skip
  (silently, unless the user asks to regenerate).
- **Not ready.** One or both of `core.md` / `claude.md` is missing for this
  target. → see precondition handling below.

**Precondition handling for not-ready targets.**

If any candidate target is missing its `core.md` or `claude.md`:

- If the corresponding `CLAUDE.md` exists at the matching location (root
  `CLAUDE.md`, or `<path>CLAUDE.md` for components) but the sources are missing,
  tell the user which target(s) need their sources built, and say:
  > "It looks like `/agents-docs-build` hasn't been run yet for these
  > targets (or the generated source files were deleted). May I run
  > `/agents-docs-build` now to (re)build the `docs/agents/` sources?
  > (yes / no)"
  - If yes → invoke `/agents-docs-build` via the SlashCommand tool, then
    re-check. If it fails, show the error and stop.
  - If no → stop and remind the user to run it before retrying.

- If neither the sources nor the `<path>CLAUDE.md` exists for a not-ready
  target, the user has created an empty `docs/agents/<path>/` directory but
  hasn't yet declared the component's intent. Tell the user:
  > "`docs/agents/<path>/` is empty and there is no `<path>CLAUDE.md` to
  > migrate. Run `/agents-docs-init` first to scaffold this component's
  > `core.md` and `claude.md`, then retry this command."
  Stop here for that target (but continue with other ready targets if any).

- If there is no root `CLAUDE.md` and no `docs/agents/` at all, tell the user:
  > "No `CLAUDE.md` or `docs/agents/` was found. This command requires a
  > project that has already been initialized with Claude Code. Consider
  > running `/init` first to generate `CLAUDE.md`, then `/agents-docs-init`
  > to set up the `docs/agents/` sources, and then retry this command."
  Stop here.

**Confirm scaffolding plan.**

Once the ready-to-generate set is known, present it to the user as a short list
(every `<path>` and the file you'll create), and ask:

> "Generate codex sidecars for the targets above? (yes / no / subset)"

Wait for confirmation. Accept partial subsets (e.g., user picks root + `ui/`
only). This is the single confirmation gate before scaffolding — consistent
with `/agents-docs-init`'s approach of asking before touching new components.

---

## Step 2 — Per-target generation loop

Process the approved targets **one at a time**, sequentially. For each target,
run Steps 2.1 → 2.4 below in full (gather, draft, feedback, revise) before
moving to the next target. This keeps each target's revision loop coherent and
avoids cross-component confusion.

For the rest of this section, `<path>` refers to the current target's path
(empty for root, e.g. `ui/` for a component).

### Step 2.1 — Gather project context

Read the following sources in priority order. Use whatever is available; do not
abort if some sources are missing.

**Primary sources for this target (highest signal — always read these if present):**

1. `docs/agents/<path>core.md` — conventions for this scope
2. `docs/agents/<path>claude.md` — Claude-Code-specific context for this scope
   (reveals what Claude handles well and therefore what Codex should focus on
   differently)
3. `<path>CLAUDE.md` — the dispatcher at this scope (mostly to confirm the
   `@import` wiring is what you expect; the content lives in the sources above)

**Project-wide context (always read for component targets; the root target's
"project-wide" is itself):**

4. `docs/agents/core.md` and `docs/agents/claude.md` — repo-wide conventions
   the component inherits. Use these to avoid duplicating shared content in
   the component sidecar.
5. `docs/agents/codex.md` (if it exists) — repo-wide Codex sidecar. Component
   sidecars should *reference* it for anything project-wide and only add what
   is component-specific.
6. `README.md` — project overview, goals, non-goals

**Secondary sources (read to fill gaps):**

7. The component's source directory (for component targets, this is typically
   the directory whose name matches `<path>` — e.g. `ui/` for a `ui/` target;
   for the root target, scan `src/` or equivalent). Scan the top two levels
   to understand module structure, language(s), and any subdirectories that
   suggest complexity (e.g., `_cython/`, `_cuda/`, `kernels/`, `extensions/`).
8. Test files within the component's scope — look for parametrized test
   suites, fixtures that define invariants, and any cross-implementation
   equivalence tests.
9. Tech-stack files (`pyproject.toml`, `package.json`, `Cargo.toml`, etc.) —
   dependencies, build targets, test configuration.
10. `<path>AGENTS.md` if present — the generated Codex base context for this
    scope. Knowing its contents avoids duplication in the override.
11. Other markdown under `docs/` that mentions or scopes to this component.

From these sources, extract and note for **this target's scope**:

- **Scope purpose** in one or two sentences (the whole project for root; the
  component's role for component targets)
- **Technology stack** at this scope — language(s), key libraries, build
  toolchain (often shared with the project for components, but call out
  divergences)
- **Architectural phases or layers** that exist or are planned (e.g.,
  prototype → optimized → accelerated)
- **High-complexity subsystems** — the parts of this scope's code most
  likely to harbour subtle correctness bugs: hot-loop numerical code,
  FFI/extension boundaries, concurrency, GPU kernels, serialization seams,
  security-critical paths
- **Invariants that must hold** within this scope — equivalence tests,
  protocol boundaries, encode/decode seams, interface contracts
- **What Claude Code owns** at this scope (from the relevant `claude.md`) —
  use this to position Codex's review focus on the gaps and blind spots
- **Existing review output conventions** — PR reviews, `REVIEW.md`, or other
- **Gotchas already documented** anywhere in the scope's sources

### Step 2.2 — Write the first draft to disk

Write the file to `docs/agents/<path>codex.md`. Do not ask for permission first
— write it, then move to the feedback step.

The file must contain the following sections. Populate each section from the
context gathered in Step 2.1; do not use placeholders except in the Gotchas
section where the scope has none yet.

For **component targets**, lead with a short statement that the file extends
the root `docs/agents/codex.md` and only adds component-specific content; the
root's reviewer-role framing, shared conventions, etc. should not be repeated.

---

#### Required file structure

```
## [Brief title describing Codex's role on this scope]

[One-paragraph preamble. For the root target: explain that this file is
Codex-specific, how it relates to AGENTS.md (the shared base), and that it
functions as a higher-precedence override; explain how Claude Code and Codex
divide responsibilities on this project. For a component target: state that
this file extends docs/agents/codex.md with component-specific content, and
that everything not stated here inherits from the root sidecar.]

### Primary role

[Describe Codex's primary role at this scope — typically cross-provider
reviewer rather than primary implementer. Prioritise:
  1. Correctness of [domain-specific] code in this scope
  2. Edge cases and boundary conditions specific to this scope
  3. Performance regressions in hot paths
  4. Architectural overengineering relative to the current phase
Tailor the list to what this scope's highest-risk areas actually are.
For component targets, point out anything that diverges from the root role.]

### High-signal review targets

[List the specific parts of this scope's code where a second set of eyes from
a different model family has the highest payoff. Be concrete: name actual
directories, file patterns, or subsystems. For each, explain *why* it's
high-signal — what class of bugs is most likely there.

Also include a "Lower-priority targets" subsection noting what Claude Code
handles reliably at this scope (so Codex doesn't duplicate effort).]

### Review output conventions

[Describe the formats Codex should use depending on how it is invoked:
  - GitHub PR review (inline suggestion blocks + summary comment)
  - REVIEW.md at repo root for working-tree reviews (organised by severity:
    blocking / important / nice-to-have, with file:line references, gitignored)
  - Terse terminal output for quick spot checks via codex exec
Adapt if the project uses different conventions. For component targets, only
state what differs from the root sidecar; otherwise reference it.]

### When asked to implement rather than review

[Point back to AGENTS.md for shared implementation conventions. Add any
scope-specific constraints Codex must respect when it does implement — e.g.,
phase lifecycle rules, invariants that must hold, encoding boundaries, test
suite contracts. Keep this section short; the details live in AGENTS.md
(and, for components, in the parent docs/agents/codex.md).]

### Do not edit generated files

[If the project uses a build script to generate AGENTS.md or this file from
source docs, state it here. Name the script and the source files. State that
Codex should edit the sources and re-run the script, not edit the generated
files directly. For component targets, this section can simply reference the
root sidecar.]

### Gotchas

[List any patterns already documented where Codex's defaults diverge from the
project's intent at this scope. If none are known yet, include a single
placeholder entry:
  - _(none yet — add entries after the first Codex review session)_]
```

---

### Step 2.3 — Structured first-pass feedback

After writing the file, print a summary of the key decisions you made, then ask
the user the following structured questions. Number them and ask all at once so
the user can answer in a single reply.

> I've written the first draft to `docs/agents/<path>codex.md`. Here's a
> summary of the key decisions I made:
>
> - **Codex's primary role at this scope**: [one sentence]
> - **High-signal review targets identified**: [bulleted list]
> - **Review output conventions assumed**: [one sentence]
> - **Implementation constraints included**: [one sentence or "none beyond AGENTS.md"]
> - **(component only) What this sidecar inherits from the root**: [one sentence]
>
> A few structured questions before we iterate:
>
> 1. **Role framing** — Is the reviewer-first framing right at this scope?
>    Should Codex have a broader or narrower implementation mandate here?
>
> 2. **Review targets** — Are these the right high-signal areas for this
>    scope? Any subsystems I missed, or any I included that you'd rather
>    keep Claude Code-only?
>
> 3. **Review output format** — Are the three output forms (PR review,
>    REVIEW.md, terminal) accurate for how you use Codex on this scope?
>    Any additions or changes?
>
> 4. **Missing context** — Is there anything scope-specific (an invariant,
>    a sharp edge, a known failure mode) that should appear in the Gotchas
>    section now rather than waiting for a live review session?
>
> 5. **Generated-file mechanics** — The file currently points at
>    `/agents-docs-build` (the workflow-claude plugin's build command) as
>    the way to regenerate `AGENTS.md` / `AGENTS.override.md`. Is that
>    accurate for your project, or do you have a different build path?
>
> Answer any or all — I'll incorporate your feedback and write an updated draft.

### Step 2.4 — Incremental revision loop

After the user's first structured response:

1. Apply all requested changes to `docs/agents/<path>codex.md` and write the
   updated file to disk (overwriting the previous version so diffs are
   visible in git).
2. Briefly summarise what changed.
3. Ask open-endedly:
   > "Anything else you'd like to adjust on this sidecar?"

Repeat Step 2.4 until the user indicates they are done with **this target**
(e.g., "looks good", "ship it", "done", no further changes requested).

Then loop back to Step 2.1 for the next approved target, or proceed to Step 3
if this was the last target.

---

## Step 3 — Offer to regenerate derived artifacts

Once **all approved targets** are finalized, the affected `AGENTS.override.md`
files are now stale relative to the new codex sidecars. `/agents-docs-check`
will report drift until the build is re-run. Offer to handle it:

> "All requested codex sidecars are finalized. The corresponding
> `AGENTS.override.md` files (root and per-component) are now stale — shall
> I run `/agents-docs-build` to regenerate them? (yes / no)"

- If yes → invoke `/agents-docs-build` via the SlashCommand tool and show
  its output. If it fails, surface the error, do not retry silently, and
  let the user decide how to proceed.
- If no → acknowledge and remind the user that the `AGENTS.override.md`
  files should be regenerated before committing, or `/agents-docs-check`
  will flag the drift.

`/agents-docs-build` writes `AGENTS.md` and `AGENTS.override.md` (and the
per-component equivalents) via shell redirects in its bundled script.
The `protect-agent-docs.py` hook matches only `Write|Edit|MultiEdit`, so
those redirect writes pass through untouched. Do not attempt to write any
`AGENTS.override.md` directly with Write or Edit — that would (correctly)
be blocked by the hook.

The plugin's `/agents-docs-build` already walks `docs/agents/` and emits a
matching `<path>/AGENTS.md` + `<path>/AGENTS.override.md` for every
component subdirectory it finds (any depth), in addition to the root pair.
No consumer-side build script is required.

---

## Notes on tone and content

- Write each `codex.md` in the same register as the corresponding `claude.md` —
  direct, technical, opinionated. Avoid filler phrases.
- The file is read by a model, not a human audience. Prefer dense, precise
  instructions over readable prose where the two conflict.
- Do not duplicate content already in `docs/agents/<path>core.md` or
  `<path>AGENTS.md`, or in the parent `docs/agents/codex.md` for component
  sidecars. Reference those by name rather than repeating their content.
- The Gotchas section is meant to grow over time through real Codex sessions.
  Seed it only with things that are genuinely known now.
