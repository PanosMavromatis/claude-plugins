# Generate `docs/agents/codex.md` for cross-provider Codex review context

Generate a `docs/agents/codex.md` file that configures OpenAI Codex as a
cross-provider code reviewer for this project. Codex is assumed to handle
review and occasional implementation, with Claude Code as the primary
implementer. Work through the steps below in order.

---

## Step 1 — Precondition checks

Run these checks before doing anything else.

**Check A: Does `docs/agents/core.md` exist AND `docs/agents/claude.md` exist?**

- If both exist → proceed to Step 2.
- If one or both are missing → fall through to Check B.

**Check B: Does `CLAUDE.md` exist in the project root?**

- If `CLAUDE.md` exists but the `docs/agents/` files are missing:
  Tell the user which file(s) are missing and say:
  > "It looks like `dev/build-agents-md.sh` hasn't been run yet (or the
  > generated files have been deleted). That script builds `docs/agents/core.md`
  > and `docs/agents/claude.md` from the source documents under `docs/agents/`.
  > May I run it now? (yes / no)"
  - If yes → run `dev/build-agents-md.sh`, then re-check. If it fails, show
    the error and stop.
  - If no → stop and remind the user to run the script before retrying.

- If `CLAUDE.md` does not exist:
  Tell the user:
  > "No `CLAUDE.md` was found in the project root. This command requires a
  > project that has already been initialized with Claude Code. Consider running
  > `/init` first to generate `CLAUDE.md`, then run `dev/build-agents-md.sh`
  > to produce the `docs/agents/` sources, and then retry this command."
  Stop here.

---

## Step 2 — Gather project context

Read the following sources in priority order. Use whatever is available; do not
abort if some sources are missing.

**Primary sources (highest signal — always read these if present):**

1. `docs/agents/core.md` — shared conventions for all agents
2. `docs/agents/claude.md` — Claude Code-specific context (reveals what Claude
   handles well and therefore what Codex should focus on differently)
3. `CLAUDE.md` — root project context file
4. `README.md` — project overview, goals, non-goals

**Secondary sources (read to fill gaps):**

5. `docs/` directory — any other markdown files present (architecture docs,
   design docs, decision records, API specs)
6. `pyproject.toml` (or `setup.cfg` / `setup.py` / `Cargo.toml` / `package.json`
   / equivalent for the project's language) — tech stack, dependencies, build
   targets, test configuration
7. `src/` directory — scan the top two levels of the source tree to understand
   module structure, language(s), and any subdirectories that suggest complexity
   (e.g., `_cython/`, `_cuda/`, `kernels/`, `extensions/`)
8. Test files — scan `tests/` or equivalent; look for parametrized test suites,
   fixtures that define invariants, and any cross-implementation equivalence tests
9. `AGENTS.md` if present — the generated Codex base context (Codex reads this
   in addition to the override; knowing its contents avoids duplication)

From these sources, extract and note:

- **Project purpose** in one or two sentences
- **Technology stack** — language(s), key libraries, build toolchain
- **Architectural phases or layers** that exist or are planned (e.g., prototype →
  optimized → accelerated)
- **High-complexity subsystems** — the parts of the codebase most likely to
  harbour subtle correctness bugs: hot-loop numerical code, FFI/extension
  boundaries, concurrency, GPU kernels, serialization seams, security-critical
  paths
- **Invariants that must hold across implementations** — equivalence tests,
  protocol boundaries, encode/decode seams, interface contracts
- **What Claude Code owns** (from `docs/agents/claude.md`) — use this to
  position Codex's review focus on the gaps and blind spots, not the areas
  Claude Code already handles well
- **Existing review output conventions** — does the project use PR reviews,
  `REVIEW.md`, or something else?
- **Gotchas already documented** anywhere in the sources

---

## Step 3 — Write the first draft to disk

Write the file to `docs/agents/codex.md`. Do not ask for permission first —
write it, then move to the feedback step.

The file must contain the following sections. Populate each section from the
context gathered in Step 2; do not use placeholders except in the Gotchas
section where the project has none yet.

---

### Required file structure

```
## [Brief title describing Codex's role on this project]

[One-paragraph preamble: explain that this file is Codex-specific, how it
relates to AGENTS.md (the shared base), and that it functions as a
higher-precedence override. Explain how Claude Code and Codex divide
responsibilities on this project.]

### Primary role

[Describe Codex's primary role — typically cross-provider reviewer rather than
primary implementer. Prioritise:
  1. Correctness of [domain-specific] code
  2. Edge cases and boundary conditions specific to this codebase
  3. Performance regressions in hot paths
  4. Architectural overengineering relative to the current phase
Tailor the list to what this codebase's highest-risk areas actually are.]

### High-signal review targets

[List the specific parts of the codebase where a second set of eyes from a
different model family has the highest payoff. Be concrete: name actual
directories, file patterns, or subsystems. For each, explain *why* it's
high-signal — what class of bugs is most likely there.

Also include a "Lower-priority targets" subsection noting what Claude Code
handles reliably (so Codex doesn't duplicate effort).]

### Review output conventions

[Describe the formats Codex should use depending on how it is invoked:
  - GitHub PR review (inline suggestion blocks + summary comment)
  - REVIEW.md at repo root for working-tree reviews (organised by severity:
    blocking / important / nice-to-have, with file:line references, gitignored)
  - Terse terminal output for quick spot checks via codex exec
Adapt if the project uses different conventions.]

### When asked to implement rather than review

[Point back to AGENTS.md for shared implementation conventions. Add any
project-specific constraints Codex must respect when it does implement — e.g.,
phase lifecycle rules, invariants that must hold, encoding boundaries, test
suite contracts. Keep this section short; the details live in AGENTS.md.]

### Do not edit generated files

[If the project uses a build script to generate AGENTS.md or this file from
source docs, state it here. Name the script and the source files. State that
Codex should edit the sources and re-run the script, not edit the generated
files directly.]

### Gotchas

[List any patterns already documented where Codex's defaults diverge from the
project's intent. If none are known yet, include a single placeholder entry:
  - _(none yet — add entries after the first Codex review session)_]
```

---

## Step 4 — Structured first-pass feedback

After writing the file, print a summary of the key decisions you made, then ask
the user the following structured questions. Number them and ask all at once so
the user can answer in a single reply.

> I've written the first draft to `docs/agents/codex.md`. Here's a summary of
> the key decisions I made:
>
> - **Codex's primary role**: [one sentence]
> - **High-signal review targets identified**: [bulleted list]
> - **Review output conventions assumed**: [one sentence]
> - **Implementation constraints included**: [one sentence or "none beyond AGENTS.md"]
>
> A few structured questions before we iterate:
>
> 1. **Role framing** — Is the reviewer-first framing right? Should Codex have
>    a broader or narrower implementation mandate on this project?
>
> 2. **Review targets** — Are these the right high-signal areas? Any subsystems
>    I missed, or any I included that you'd rather keep Claude Code-only?
>
> 3. **Review output format** — Are the three output forms (PR review,
>    REVIEW.md, terminal) accurate for how you use Codex? Any additions or
>    changes?
>
> 4. **Missing context** — Is there anything project-specific (an invariant,
>    a sharp edge, a known failure mode) that should appear in the Gotchas
>    section now rather than waiting for a live review session?
>
> 5. **Generated-file mechanics** — The file currently [does / does not]
>    reference `dev/build-agents-md.sh` as the build script. Is this accurate
>    for your project?
>
> Answer any or all — I'll incorporate your feedback and write an updated draft.

---

## Step 5 — Incremental revision loop

After the user's first structured response:

1. Apply all requested changes to `docs/agents/codex.md` and write the updated
   file to disk (overwriting the previous version so diffs are visible in git).
2. Briefly summarise what changed.
3. Ask open-endedly:
   > "Anything else you'd like to adjust?"

Repeat Step 5 until the user indicates they are done (e.g., "looks good",
"ship it", "done", no further changes requested). Then proceed to Step 6.

---

## Step 6 — Offer to regenerate the derived artifact

Once the user signals completion, `docs/agents/codex.md` is current but
`AGENTS.override.md` is now stale relative to it. `dev/check-agent-docs.sh`
will fail in CI until the build is re-run. Offer to handle it:

> "`docs/agents/codex.md` is finalized. `AGENTS.override.md` is now stale
> relative to it — shall I run `dev/build-agents-md.sh` to regenerate it?
> (yes / no)"

- If yes → invoke `dev/build-agents-md.sh` via the Bash tool and show its
  output. If the script exits non-zero, surface the error, do not retry
  silently, and let the user decide how to proceed.
- If no → acknowledge and remind the user that `AGENTS.override.md` should
  be regenerated before committing, or CI will flag the drift.

Invoking the build script via Bash is the correct path — it runs
`dev/build-agents-md.sh`, which writes `AGENTS.md` and `AGENTS.override.md`
via shell redirects. The `protect-agent-docs.py` hook matches only
`Write|Edit|MultiEdit`, so bash execution and its redirect writes pass
through untouched. Do not attempt to write `AGENTS.override.md` directly
with Write or Edit — that would (correctly) be blocked by the hook.

---

## Notes on tone and content

- Write `docs/agents/codex.md` in the same register as `docs/agents/claude.md` —
  direct, technical, opinionated. Avoid filler phrases.
- The file is read by a model, not a human audience. Prefer dense, precise
  instructions over readable prose where the two conflict.
- Do not duplicate content already in `docs/agents/core.md` or `AGENTS.md`.
  Reference those files by name rather than repeating their content.
- The Gotchas section is meant to grow over time through real Codex sessions.
  Seed it only with things that are genuinely known now.
