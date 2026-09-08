# Detecting `workflow-claude` — shared reference

`dp-compile` owns the algorithm lifecycle and nothing else. Branches, plans, commits,
merges and documentation belong to the `workflow-claude` plugin, and this plugin delegates
to it rather than reimplementing any of it. That assumption has to be checked, because a
delegation to a plugin that is not loaded fails at the moment it is needed rather than at
the moment it is assumed.

This file is the shared contract. Every command `@`-includes it and then states its own
severity.

## How to detect it

**Read your own tool list, and look for anything namespaced `workflow-claude:`** — a skill
or a command. That is the whole check.

There is no shell command that reports which plugins are loaded. This follows the
precedent `/smart-merge` sets for its own MCP check: *you can see your own tools, so judge
from that*.

Three things not to do, each ruled out on evidence rather than on principle:

- **Do not inspect the plugin configuration.** `workflow-claude` appears in no
  `~/.claude/plugins/*.json`, and in at least one repository it is not an installed plugin
  at all — it is a full plugin tree sitting in the project's `.claude/skills/`. A config
  check would report "absent" for a plugin that is loaded and working.
- **Do not shell out to find the files.** Presence on disk is not presence in the session,
  and the path differs by load method.
- **Do not ask the user.** They should not have to know how their own tooling is wired, and
  the answer is already in front of you.

## What absence means — two severities

**Absence is not uniform.** No `dp-compile` command strictly *needs* `workflow-claude`:
reporting a phase needs no branch machinery, and writing a `.pyx` needs no commit
machinery. Refusing a report for a dependency that report never uses reads as a bug the
first time someone hits it.

So the severity follows the delegation, and each command declares which it takes:

| Command | Severity | Why |
|---|---|---|
| `/phase-check` | Note and continue | Report-only. Delegates nothing. |
| `/benchmark` | Note and continue | Runs the repository's own benchmark command and reports. Delegates nothing. |
| `/next-phase` | Note at the head, **stop at the delegation** | Writes a phase artifact — which needs nothing from `workflow-claude` — and then hands the commit to `/smart-commit`. |
| `/new-algorithm` | Note at the head, **stop at the delegation** | Registers and scaffolds, then hands branch creation to `/new-branch` and the commit to `/smart-commit`. |

**The check happens at the head; the stop happens at the delegation.** Those are different
places on purpose. Checking early means the user learns at the start that the commit step
will not be available, rather than after the work. Stopping late means the work that needed
nothing from `workflow-claude` still happens — a `.pyx` written and left uncommitted costs
the user one `git commit`, while a `/next-phase` that refused to start costs them the
phase.

**What a stop must never do is substitute.** A delegating command that finds
`workflow-claude` absent does not run `git commit` itself, does not open a branch itself,
and does not finish quietly as though the step had not existed. It stops at that point and
says plainly what is left undone and who owns it.

## The line to print when it is absent

Print it **once**, at the head, and not again on each later step.

> `workflow-claude` is not loaded in this session. `dp-compile` delegates branches, plans,
> commits and merges to it, so `<the delegated step>` will not run — everything before it
> will. Three ways it gets loaded, and which one applies is yours to know: a marketplace
> install, `claude --plugin-dir <path>/workflow-claude`, or a plugin tree placed at
> `.claude/skills/workflow-claude/` in this project.

**Name all three load paths.** A message naming only `--plugin-dir` sends a user to fix
something that is not how they loaded it — and the `.claude/skills/` route is neither a
marketplace install nor the `--plugin-dir` the plugin's own README documents, yet it is how
at least one repository loads it today.

Do not guess which path this repository uses, and do not offer to install anything: loading
a plugin changes the user's session, and it is theirs to do.
