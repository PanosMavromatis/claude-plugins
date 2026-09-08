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
├── agents/                   # Subagent definitions with YAML frontmatter
│   └── {{agent-name}}.md
├── commands/                 # Slash commands (each .md file → /plugin-name:command-name)
│   └── {{command-name}}.md
├── dev/                      # Developer-only tooling (not part of the plugin runtime)
│   └── smoke-test.sh
├── hooks/                    # Deterministic event handlers
│   ├── hooks.json
│   └── scripts/             # Hook helper scripts
├── scripts/                  # Shared utilities (optional)
├── skills/                   # Agent skills (auto-triggered or /plugin-name:skill-name)
│   └── {{skill-name}}/
│       ├── SKILL.md          # Skill entrypoint — goals and constraints, not step-by-step
│       ├── references/       # Domain knowledge, API docs, specs (optional)
│       ├── scripts/          # Composable utilities (optional)
│       └── examples/         # Annotated examples the agent composes from (optional)
├── .mcp.json                 # MCP server definitions (optional)
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
/dp-compile:{{command-name}} <test-args>
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
- `/phase-check` and `/next-phase` use `make`-like timestamp logic: a backend file is **stale** if its prerequisite has a newer mtime, even if both exist. Staleness is transitive. The **effective phase** is the phase just before the first stale file — route skill invocations from there, not from file existence alone. The shared detection logic lives in `commands/references/phase-detection.md` and is `@`-included by both commands.
- `/phase-check` is **report-only**: it checks, reports, and exits. Never suggest running `/next-phase` or offer to continue implementation.
- `/next-phase` requires an **explicit algorithm name**; if none is provided, ask — do not infer. Both commands accept natural language names (e.g. "Needleman-Wunsch") and normalise to snake_case. On a near-miss typo (edit distance ≤ 3), prompt "Did you mean X?"; if no close match, list available algorithms and ask again.
- Before writing a test or diagnostic script, verify that the underlying CLI tool actually supports what you need. `claude plugin validate` checks syntax only — there is no CLI command to verify runtime component loading. Don't waste time scripting around a capability that doesn't exist.
- Hooks are **deterministic** (always run), unlike CLAUDE.md instructions which are advisory. Use hooks for actions that must happen every time (formatting, linting, security checks). Use skills for guidance Claude should consider.
- Agent definitions do NOT support `hooks`, `mcpServers`, or `permissionMode` in frontmatter — these are stripped for security.
- If a skill's `description` doesn't trigger when expected, the keywords likely don't match. Test by asking Claude to explain when it would invoke the skill.
- Installed plugins cannot reference files outside their directory. Paths like `../shared-utils` break after installation. Use symlinks if external files are needed.

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
