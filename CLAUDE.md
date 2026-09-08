# CLAUDE.md — dp-compile

<!-- 
  Guidelines:
  - Keep this file under 100 lines after customization (excluding comments).
  - For every line, ask: "Would removing this cause Claude to make mistakes?" If not, cut it.
  - Use @import for detailed docs rather than inlining them here.
  - Add emphasis (IMPORTANT, MUST, NEVER) sparingly — only for rules Claude repeatedly violates.
  - Treat this file like code: review it when things go wrong, prune it regularly.
  - Add compaction instructions so /compact preserves critical context.
-->

## Project overview

**dp-compile** is a Claude Code plugin that guides dynamic-programming algorithms through a staged translation from pseudocode to pure Python to compiled and parallel backends, enforcing equivalence against the reference implementation at every stage.

This is a **plugin repository**, not a traditional application. The codebase is primarily natural language (Markdown + JSON) with optional shell scripts. Components are auto-discovered by Claude Code from their conventional directory locations.

## Directory structure

```
dp-compile/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (name, version, description)
├── commands/                # Slash commands (each .md → /dp-compile:<name>)
│   ├── new-algorithm.md
│   ├── phase-check.md
│   ├── next-phase.md
│   ├── benchmark.md
│   └── references/          # @-included, shared by several commands. NOT commands:
│       ├── manifest.md      #   the dp-compile.toml contract every command reads first
│       ├── phase-detection.md
│       └── workflow-claude.md
├── dev/                     # Developer-only tooling (not part of the plugin runtime)
│   └── smoke-test.sh
├── hooks/                   # Deterministic event handlers
│   ├── hooks.json
│   └── scripts/
│       └── pre-commit-check.py
├── skills/                  # Agent skills (auto-triggered or /dp-compile:<name>)
│   └── <skill-name>/
│       ├── SKILL.md         # Skill entrypoint — goals and constraints, not step-by-step
│       ├── references/      # Domain knowledge, specs (optional)
│       └── examples/        # Annotated examples the agent composes from (optional)
├── CLAUDE.md
└── README.md
```

IMPORTANT: All component directories (skills/, commands/, agents/, hooks/) MUST be at the plugin root level — never nested inside .claude-plugin/. Only plugin.json belongs in .claude-plugin/.

## Conventions

- Use **kebab-case** for all directory and file names.
- Plugin components are namespaced as `dp-compile:component-name` — never conflicts with project-level components.
- Use `${CLAUDE_PLUGIN_ROOT}` for all intra-plugin path references in scripts, hooks, and MCP configs. NEVER use absolute or relative paths — plugins install in different locations depending on the method.
- Skill `description` fields are **triggers, not summaries** — write them for the model ("when should I fire?") with specific keywords and file patterns.
- Keep SKILL.md files under 5,000 words. Move detailed reference material to references/.
- Command files use `$ARGUMENTS` to access user input passed after the slash command.

## Build & test

```bash
# Load plugin for the current session (no install needed)
claude --plugin-dir .

# Verify plugin loaded correctly
claude --debug  # look for "loading plugin" messages

# Smoke test: validate syntax and check component placement
./dev/smoke-test.sh

# Test a specific command
/dp-compile:phase-check <algorithm-name>
```

When adding a new skill, command, or other component, update the `expected` array in `dev/smoke-test.sh` so the smoke test covers it.

<!-- Marketplace install workflow (for when you're ready to distribute):

# Create .claude-plugin/marketplace.json with name, owner, plugins fields
# Register as a local marketplace (one-time)
/plugin marketplace add .
# Install from that marketplace
/plugin install dp-compile@<marketplace-name>
# After making changes, reload without reinstalling
/reload-plugins

If your plugin includes scripts that need dependencies, add setup commands here:
pip install -r requirements.txt --break-system-packages
npm install
-->

## Plugin manifest rules

The `plugin.json` file lives at `.claude-plugin/plugin.json`:

```json
{
  "name": "dp-compile",
  "description": "Guides dynamic-programming algorithms through a staged translation from pseudocode to pure Python to compiled and parallel backends, enforcing equivalence against the reference implementation at every stage.",
  "version": "0.2.0"
}
```

- `name` MUST be lowercase kebab-case and match the plugin directory name.
- `repository` field, if present, MUST be a string URL (not an object).
- Bump `version` on every change you want users to pick up — Claude Code caches plugins and only updates when the version changes.

## Gotchas

<!-- 
  This is the highest-signal section. Add entries here whenever Claude makes a 
  mistake specific to this plugin. Each entry prevents an entire class of future errors.
-->

- NEVER put commands/, agents/, or skills/ inside .claude-plugin/. They will silently fail to load.
- **`claude plugin validate` emits four warnings here, and all four are expected. Do not "fix" any of them.** A clean run is not the goal; a run whose every warning is accounted for is. **The count tracks the number of files in `commands/references/`, so it rises by one whenever a fragment is added** — update this entry in the same commit, or the next reader cannot tell an expected warning from a new one.
  - Three are `commands/references/*.md` having no frontmatter. Those files are `@`-included fragments, not commands — the validator scans every `.md` under `commands/`. Adding frontmatter would silence the warning by registering each fragment as an invocable command, which is worse than the warning.
  - One is `CLAUDE.md at the plugin root is not loaded as project context`, suggesting a skill instead. That is correct about an *installed* plugin and beside the point for this file: it is context for developing the plugin, in this repository, where the repo root and the plugin root are the same directory and it loads normally. Moving it into `skills/` would ship plugin-development instructions to every consumer.
- **Five stages, and no phase is called `numba`.** `formalization → python → cython → cpu_parallel → cuda`. Phases 3 and 4 both use Numba, so that name distinguishes nothing; `cpu_parallel` is `@njit(parallel=True)` with `prange` and needs no GPU, `cuda` is `@cuda.jit`. The same strings are the manifest's `[phases]` keys, the token a path template usually contains, and the backend name a consumer registers.
- **Phase 0 has two skills, and the discriminator is a file.** `algorithm-formalize` goes
  forward from source material; `algorithm-recover` goes backward from an existing phase-1
  kernel. Their triggers are exact negations of each other — the forward one says "do NOT
  trigger if the phase-1 file already exists" — so they must never be merged into one
  skill with a mode switch: a single `description` cannot state both conditions, and the
  description is what decides whether the skill fires at all. The recovered document's
  provenance edge runs *from the kernel to the document*, which is why editing the kernel
  marks the formalization stale rather than the reverse.
- **A recovered formalization must not describe the kernel it was read from.** Phases 2-4
  translate from the document, so a document translated from phase 1 adds a step and no
  independent check, and a phase-1 defect gets written down as the specification. What
  keeps it honest is evidence the code cannot supply: the legacy source, an account of it,
  the manifest's `[algorithms.<name>].oracles`, and the human review.
- **The mtime fallback must never reverse an edge that is already recorded.** A headerless
  file normally falls back to "its source is the previous declared phase", but if another
  artifact's header already names it, that pair's edge is on record running the other way,
  and adding the guess makes a cycle. This is not hypothetical: a recovered algorithm's
  `_python.py` is correctly headerless and its formalization names it, so the naive
  fallback would report the kernel stale against a document written *from* it — the moment
  the recovery lands, every time.
- **A kernel must never be the only thing validating itself.** Phases 2-4 are checked
  against phase 1, so nothing downstream can check phase 1. Written forward that is fine —
  the specification came from outside. Recovered, it is not: the document was read off the
  kernel and the test cases were extracted from the kernel's own suite, so the whole chain
  agrees with the kernel because it all came from it. A differential oracle is the only
  input that breaks the circle, which is why `/next-phase` refuses to advance past phase 1
  while a declared one is unexercised. Where the comparison is not an equality check, **pin
  the divergence rather than widening the assertion** — a tolerance accepts the next
  divergence too.
- **This plugin runs no `git` command, edits no plan file, and touches no documentation.**
  Commits are `/smart-commit`'s, branches `/new-branch`'s, plan markers and notes
  `/hitl-step`'s, and `README.md` / `docs/agents/*` / every generated `AGENTS.md`
  `/agents-docs-update`'s. The reason is not tidiness about destructive commands: a plain
  `git commit` skips the documentation sync `/smart-commit` performs, so a repository ends
  up with a new backend and docs describing the old set. Suggesting `git commit` is how that
  starts, so do not suggest it either. **A phase artifact is the one exception** — a
  formalization or a kernel is the thing being produced, not a description of the
  repository. The contract is `commands/references/workflow-claude.md`.
- **`dp-compile` reports facts for a plan; it never writes one.** The plan file has a single
  writer. What this plugin contributes is what that writer cannot know — an artifact's path,
  the source and hash its provenance header records, what the suite did — offered as a line
  that pastes under a subgoal. Offer it; do not write it, and do not ask whether to.
- **`stale` and `blocked` are different states.** An artifact is stale when its own recorded source hash no longer matches; it is blocked when something further upstream is stale but its own source has not changed yet. Only stale artifacts are regeneration targets — a blocked one becomes stale of its own accord once its source is regenerated, which is what makes the process terminate with each artifact rebuilt once. Under the old mtime rule staleness propagated by fiat; here it propagates by consequence.
- **Staleness is decided by recorded provenance, not by mtime.** Each derived artifact carries a `derived-from` header naming its source and that source's SHA-256, and is stale when the recorded hash no longer matches. This survives `git checkout`, which resets every mtime, and it encodes *direction* — a formalization recovered from an implementation records that it derives from the code, so editing the kernel marks the document stale rather than the reverse, which a timestamp cannot express. Compute the hash with the file's own header line excluded, or re-stamping any file spuriously invalidates everything downstream of it. The shared logic lives in `commands/references/phase-detection.md`.
- **Nothing in this plugin knows a repository's layout.** Paths, build and test commands, backend registration and the encoder all come from the consumer's root `dp-compile.toml`, whose contract is `commands/references/manifest.md`. There are deliberately **no defaults**: with none, a repository without a manifest would resolve paths under a layout it does not have, find nothing, and be told "algorithm not found" — a missing file misdiagnosed as a missing algorithm.
- **Algorithms are listed in the manifest, never discovered by globbing.** A flat package makes globbing unsafe: `_*.py` returns helper modules alongside kernels. This is not theoretical — the pre-commit hook's first implementation wildcarded a phase template and matched two helper modules in the only repository with a manifest.
- `/phase-check` is **report-only**: it checks, reports, and exits. Never suggest running `/next-phase` or offer to continue implementation.
- `/next-phase` requires an **explicit algorithm name**; if none is provided, ask — do not infer. Both commands accept natural language names (e.g. "Needleman-Wunsch") and normalise to snake_case. On a near-miss typo (edit distance ≤ 3), prompt "Did you mean X?"; if no close match, list available algorithms and ask again.
- Before writing a test or diagnostic script, verify that the underlying CLI tool actually supports what you need. `claude plugin validate` checks syntax only — there is no CLI command to verify runtime component loading. Don't waste time scripting around a capability that doesn't exist.
- Hooks are **deterministic** (always run), unlike CLAUDE.md instructions which are advisory. Use hooks for actions that must happen every time (formatting, linting, security checks). Use skills for guidance Claude should consider.
- **The gate fires inside `/smart-commit`, and that is the point.** Hooks stack, so the
  `git commit` that command runs triggers `pre-commit-check.py` exactly as a hand-typed one
  would — delegating the commit does not bypass the check. It also cannot collide with
  `workflow-claude`'s `PreToolUse` hook, which matches `Write|Edit|MultiEdit` where this one
  matches `Bash`: no tool call matches both. One latent coupling to keep in mind when either
  plugin changes: `/smart-commit` runs `/agents-docs-update` *before* committing, so the gate
  reads a staged set that command has already modified. It stages only documentation today,
  so it cannot change the gate's scoping decision — but nothing enforces that.
- **The pre-commit hook decides for itself whether a command is a `git commit`**, rather than relying on the hook entry's `if` matcher. The two official plugins using that field spell their patterns incompatibly — `Bash(git commit:*)` against `Bash(python3 *scripts/*.py *)` — so at least one syntax matches nothing, and a matcher that matches nothing yields a hook that never fires and never says so. The plugin using the colon form re-checks with its own regex anyway. Do not "simplify" this back into an `if`.
- Agent definitions do NOT support `hooks`, `mcpServers`, or `permissionMode` in frontmatter — these are stripped for security.
- If a skill's `description` doesn't trigger when expected, the keywords likely don't match. Test by asking Claude to explain when it would invoke the skill.
- Installed plugins cannot reference files outside their directory. Paths like `../shared-utils` break after installation. Use symlinks if external files are needed.

## Commit convention

**Imperative subject, no prefix, and a body that explains why.** This repository does
*not* use conventional commits, and `/smart-commit`'s Step 3 template specifies that it
does — so the override has to be written down, which is what this section is for. The
history is the authority: "Implement benchmarking skill and benchmark command", not
`feat(benchmarking): ...`.

The sibling `workflow-claude` plugin uses conventional commits. That divergence is
deliberate and known; each repository follows its own history.

## Compaction instructions

When compacting, ALWAYS preserve: the current plugin directory structure, the list of all modified files, any test results or error messages, and the active implementation plan.

<!-- 
  OPTIONAL SECTIONS — uncomment and customize if your plugin uses these:

  ## Agent definitions
  Agents use YAML frontmatter: name, description, model (sonnet|opus|haiku), 
  effort (low|medium|high), maxTurns, tools/disallowedTools. 
  The only valid `isolation` value is "worktree".

  ## MCP server configuration  
  MCP configs go in .mcp.json at plugin root. Keep tool counts minimal —
  each server's tool schemas consume context window budget.

  ## Hook events
  Supported events: SessionStart, PreToolUse, PostToolUse, Stop, 
  UserPromptSubmit, and many more. See official docs for the full list.
  Hook types: command (shell), http (POST), prompt (LLM eval), agent (agentic verifier).

  ## Cross-platform notes
  If maintaining both CLAUDE.md and AGENTS.md, keep shared facts in sync.
  Use CLAUDE.md as canonical source; generate AGENTS.md with minor adaptations.
-->

@README.md
