---
allowed-tools: Skill(workflow-claude:master-plan)
argument-hint: "<label> [spec] [--dry-run <path>]"
description: Open a revision. An alias of /master-plan, kept for one revision.
---

# /open-revision

`/open-revision` is an alias of `/master-plan`, which opens a revision by drafting its
master plan from a specification and listing it in the root plan. The alias is kept for one
revision, so the name keeps working where it is written down (`dp-compile`'s README names
it), and is then removed.

Invoke `/workflow-claude:master-plan` with the Skill tool (skill
`workflow-claude:master-plan`), passing this command's `$ARGUMENTS` through unchanged, and
follow it to the end. Do nothing before it.
