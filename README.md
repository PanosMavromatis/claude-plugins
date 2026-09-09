# claude-plugins

The **`mavromatis-ai-labs`** marketplace: Claude Code plugins published by Mavromatis AI
Labs. Each plugin's full source lives under `plugins/`, carrying the history it had as a
standalone repository.

## Plugins

| Plugin | What it does |
|---|---|
| [`workflow-claude`](plugins/workflow-claude) | Branch, plan, commit and merge commands, with hooks that keep generated agent docs in sync with their sources. Applicable to most projects. |
| [`dp-compile`](plugins/dp-compile) | Staged translation of dynamic-programming kernels — formalization → Python → Cython → CPU-parallel → CUDA — enforcing equivalence against the reference implementation at every stage. Requires a `dp-compile.toml` at the consumer's repository root. |

`dp-compile` declares `workflow-claude` in its `dependencies`: it delegates branches, plans,
commits and merges rather than reimplementing them, so installing one installs both.

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
    "workflow-claude@mavromatis-ai-labs": true,
    "dp-compile@mavromatis-ai-labs": true
  }
}
```

Claude Code registers the marketplace and installs the enabled plugins the next time a
session starts in that folder, once the folder is trusted. The imperative equivalent writes
the same keys:

```bash
claude plugin marketplace add PanosMavromatis/claude-plugins
claude plugin install workflow-claude@mavromatis-ai-labs --scope project
```

Prefer the declaration — it is what a fresh clone reproduces from, and what a reviewer sees
in a diff.

## Conventions

**No organization prefix.** The plugins are `workflow-claude` and `dp-compile`, not
`mav-workflow-claude`. A plugin's `name` namespaces every component it ships
(`/dp-compile:phase-check`), so a prefix buys immunity from a third-party plugin of the same
name at the cost of typing it forever; with two plugins that is premature. Decided
2026-09-09, and recorded here rather than left implicit because renaming a *published*
plugin costs a permanent `renames` entry in the catalog. Revisit when a real collision
appears.

**No `version` field**, in either `plugin.json` or the catalog entries. The version then
resolves to this repository's commit SHA, so every push is an update consumers can pick up
with no release ceremony. An explicit version someone forgets to bump freezes every consumer
silently — `/plugin update` reports "already at the latest version" and nothing looks wrong.
The monorepo consequence, which is expected rather than a defect: both plugins resolve to
the repository's HEAD, so a commit touching one marks both as updated. Explicit versions and
`<name>--v<version>` tags arrive together, and only when a dependency first needs a version
*constraint* rather than a bare name.

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

Both emit warnings, and that is the expected state: the omitted `version` is one, and
`dp-compile`'s `commands/references/*.md` are `@`-included fragments that must not carry
frontmatter. Each plugin's own `CLAUDE.md` enumerates the warnings it expects — check
against that list rather than aiming for a clean run. `--strict` is unusable here for the
same reason.

## License

MIT — see [`LICENSE`](LICENSE), and the copy inside each plugin directory, which is the one
that reaches a consumer: a marketplace install copies only the plugin's own directory into
the cache, so a root-only license would never travel with the code.
