# fix/hardcoded-commit-convention

**Created**: 2026-09-08
**Base**: main at e4e2421
**Status**: active

## Purpose

Every commit-message and PR-title decision in this plugin encodes one repository's
convention, and a plugin cannot know its consumer's. Nine sites across seven command files
plus a README row hardcode a form — six literal `git commit -m` strings, a prescriptive
"Follow conventional commit format" rule, a PR-title rule, and a suggested-message example.
They are wrong in one direction or the other in **both** repositories using this plugin
today.

The fix is to have each site read the convention from the repository's own history rather
than assert one, keeping the message *content* the templates already got right.

## Scope

- Replace the six literal `git commit -m` template strings so the subject defers to the
  detected convention while keeping its content.
- Rewrite `/smart-commit` Step 3, which prescribes conventional format outright — the site a
  consumer already had to override in writing.
- Rewrite `/smart-merge` step 3's PR-title rule, the same defect as prose rather than a
  `-m` string.
- Decide and fix `/hitl-step` step 6's `feat(docker): <section topic>` example.
- Correct `README.md`'s command table, which advertises `/smart-commit` as "Conventional
  commit format".

## Context

Found by an audit of this plugin's own history against its own convention, run from the
pfsmgraph side while revising the companion `dp-compile` plugin. That audit is Section F3
of `tmp/TODO.md` in pfsmgraph; the fix is its Section G.

The evidence runs both ways, which is what makes it a defect rather than a preference:

- pfsmgraph has **zero** conventional-prefixed commits in its history, and overrode the
  conventional templates every time `/file-plans` and `/open-revision` ran there. The
  overrides were also better than the templates, naming the actual revision.
- This repository is conventional in commits *and* PR titles, and the imperative templates
  pasted through verbatim and broke it — `afdf57f Remove branch doc (merging to main)`, two
  commits before this branch's base, is `smart-merge.md:92` doing exactly that.

pfsmgraph's `docs/agents/claude.md` carries a standing override note for `/smart-commit`
Step 3, which is the same defect stated from the consumer's side: a repository writing a
correction because the plugin encodes a convention it cannot know.

## Notes

- **Detection, not configuration.** Settled before any edit: a command reads the last ~20
  subjects and matches the dominant form. A config field would be a second thing to keep
  true, and is silently wrong when stale where a history never is. This follows the
  precedent `/smart-merge` already sets for MCP availability — there is no command that
  reports it, so judge from what is visible.
- **Content stays, form goes.** The templates carry real information — which commit this is
  — and only their prefix was wrong.
- **No shared fragment.** This plugin uses no `@import` anywhere; the rule is two sentences,
  and a fragment would pay both costs, since each site still needs a local line saying the
  rule applies there.
