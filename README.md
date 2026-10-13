# claude-plugins

The **`mavromatis-ai-labs`** marketplace: Claude Code plugins published by Mavromatis AI
Labs. Each plugin's full source lives under `plugins/`, carrying the history it had as a
standalone repository.

## Plugins

| Plugin | What it does |
|---|---|
| [`workflow-coding`](plugins/workflow-coding) | Branch, plan, commit and merge commands, with hooks that keep generated agent docs in sync with their sources. Applicable to most projects. |
| [`dp-compile`](plugins/dp-compile) | Staged translation of dynamic-programming kernels — formalization → Python → Cython → CPU-parallel → CUDA — enforcing equivalence against the reference implementation at every stage. Requires a `dp-compile.toml` at the consumer's repository root. |

`dp-compile` declares `workflow-coding` in its `dependencies`: it delegates branches, plans,
commits and merges rather than reimplementing them, so installing one installs both.

`workflow-coding` was named `workflow-claude` before 0.10.0.

## Using it

Declare the marketplace and the plugins in a project's committed `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "mavromatis-ai-labs": {
      "source": { "source": "github", "repo": "PanosMavromatis/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "workflow-coding@mavromatis-ai-labs": true,
    "dp-compile@mavromatis-ai-labs": true
  }
}
```

Claude Code registers the marketplace and installs the enabled plugins the next time a
session starts in that folder, once the folder is trusted. The imperative equivalent writes
the same keys:

```bash
claude plugin marketplace add PanosMavromatis/claude-plugins
claude plugin install workflow-coding@mavromatis-ai-labs --scope project
```

Prefer the declaration — it is what a fresh clone reproduces from, and what a reviewer sees
in a diff.

## Conventions

**No organization prefix.** The plugins are `workflow-coding` and `dp-compile`, not
`mav-workflow-coding`. A plugin's `name` namespaces every component it ships
(`/dp-compile:phase-check`), so a prefix buys immunity from a third-party plugin of the same
name at the cost of typing it forever; with two plugins that is premature. Decided
2026-09-09, and recorded here rather than left implicit because renaming a *published*
plugin costs a permanent `renames` entry in the catalog. Revisit when a real collision
appears.

**An explicit `version` in each `plugin.json`**, and none in the catalog entries, where
`plugin.json` would win anyway. This reverses a 2026-09-09 decision to omit it, which had
the version resolve to this repository's commit SHA so that every push was an update with
no release ceremony. What changed is that the plugins are now developed with themselves:
`workflow-coding` drives the work that edits it, so the installed copy must move only on a
deliberate release, never because `main` moved, or a half-finished change would be running
the session that finishes it. The cost the earlier decision named is real and still applies
— a version nobody bumps freezes every consumer silently, and `/plugin update` reports
"already at the latest version" — so **every revision that changes a plugin ends with a
bump**. Each plugin now resolves to its own version rather than the shared HEAD, so a
commit touching one no longer marks both as updated. Tags are still deferred: they wait
for a dependency that needs a version *constraint* rather than a bare name.

## Developing

```bash
claude --plugin-dir plugins        # loads every plugin here, for one session
```

Do **not** register this checkout as a marketplace to test it. Registration is keyed on the
`name` inside `.claude-plugin/marketplace.json`, so adding a local copy under
`mavromatis-ai-labs` replaces the GitHub one for every project on the machine — silently,
because it is an ordinary write to an existing key. Removing a marketplace from its last
scope then uninstalls the plugins that came from it, so the obvious recovery is worse than
the mistake.

Validate before pushing:

```bash
claude plugin validate .
claude plugin validate ./plugins/<name>
```

Both emit warnings, and that is the expected state: `dp-compile`'s
`commands/references/*.md` are `@`-included fragments that must not carry frontmatter. Each plugin's own `CLAUDE.md` enumerates the warnings it expects — check
against that list rather than aiming for a clean run. `--strict` is unusable here for the
same reason.

Measure what a session and each command load, before and after a change meant to shrink
it:

```bash
dev/measure-context.sh <consumer-repo>   # read-only; defaults to this repository
```

It reports bytes and ≈ tokens (bytes / 4) for the session-start instruction files and
their imports, each command plus what it reads whole, `docs/agents/**`, the branch plans
and the master plan. **It measures the main session only**: a subagent's own reads are
not in it, so total usage is judged separately.

Test `workflow-coding`'s plan resolver, `scripts/locate-plan.sh`, after any change to it or
to `scripts/lib/plan-rules.sh`, the rules it shares with the other plan scripts:

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite   # outside this repository; fixtures are built here
python3 -I dev/locate-plan/suite.py              # 85 cases, no model, ~30 s
python3 -I dev/locate-plan/suite.py --mutants    # the suite must catch each mutant, ~4 min
```

`dev/locate-plan/README.md` covers the answer key and the headless trial that compares
Step 1 with a subagent wrapping the script.

Test its plan check, `scripts/check-plan-index.sh` (drift in a per-goal plan, open items in
either layout), the script `/new-branch` places a new plan with,
`scripts/propose-branch-plan.sh`, the one `/smart-merge` records a merge with,
`scripts/propose-merge-record.sh`, the one `/master-plan` opens a revision with,
`scripts/propose-revision.sh`, and the one `/close-revision` closes it with,
`scripts/close-revision.sh`, the same way. All six share `scripts/lib/plan-rules.sh`,
so run all six suites after a change to it:

```bash
python3 -I dev/check-plan-index/suite.py                 # 39 cases, no model, ~10 s
python3 -I dev/check-plan-index/suite.py --mutants       # the suite must catch each mutant, ~1 min
python3 -I dev/propose-branch-plan/suite.py              # 33 cases, no model, ~20 s
python3 -I dev/propose-branch-plan/suite.py --mutants    # the suite must catch each mutant, ~2 min
python3 -I dev/propose-merge-record/suite.py             # 37 cases, no model, ~15 s
python3 -I dev/propose-merge-record/suite.py --mutants   # the suite must catch each mutant, ~2 min
python3 -I dev/propose-revision/suite.py                 # 72 cases, no model, ~30 s
python3 -I dev/propose-revision/suite.py --mutants       # the suite must catch each mutant, ~7 min
python3 -I dev/close-revision/suite.py                   # 65 cases, no model, ~60 s
python3 -I dev/close-revision/suite.py --mutants         # the suite must catch each mutant, ~15 min
```

Test the session-log renderer, `scripts/export-session.py`, after any change to it:

```bash
python3 -I dev/export-session/suite.py                   # 25 cases, no model, ~1 s
python3 -I dev/export-session/suite.py --mutants         # the suite must catch each mutant, ~9 s
```

`dev/per-goal-e2e/` runs the real `/new-branch`, `/hitl-step`, `/step`, `/smart-merge`,
`/master-plan`, `/open-revision` and `/close-revision` headless on fresh fixture repositories, and grades what they leave behind; `/smart-merge`
runs against a stub `gh` with MCP off, so it never reaches GitHub. Those are real sessions,
which cost money, so run them yourself, after a change to the command text;
`dev/per-goal-e2e/README.md` covers how.

## License

MIT — see [`LICENSE`](LICENSE), and the copy inside each plugin directory, which is the one
that reaches a consumer: a marketplace install copies only the plugin's own directory into
the cache, so a root-only license would never travel with the code.
