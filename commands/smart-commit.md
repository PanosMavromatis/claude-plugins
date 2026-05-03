---
allowed-tools: Bash(git:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Bash(dev/build-agents-md.sh:*), Read, Write, Glob, Grep, SlashCommand(/workflow-claude:agents-docs-update)
description: Update docs to match staged changes, commit with an appropriate message, and push.
argument-hint: "[extra doc paths...]"
---

# Smart Commit

End-to-end commit workflow: sync documentation with the staged diff via `/workflow-claude:agents-docs-update`, then commit and push.

This command delegates all documentation handling to that command via the SlashCommand tool. Do not duplicate or override its steps here — let it run to completion, then resume with the commit and push.

## Step 1: Sync Documentation

Invoke `/workflow-claude:agents-docs-update` via the SlashCommand tool, passing this command's `$ARGUMENTS` through unchanged as its arguments. Wait for it to complete its Step 6 (Report) before proceeding.

The invoked command stops at staging — it stages any documentation updates it makes but does not commit. Continue with Step 2 below using the staged set it produced (the original staged changes plus any doc edits or regenerated artifacts).

## Step 2: Generate Commit Message

Based on the **full set of staged changes** now in the index (the original staged changes plus any doc updates or regenerated artifacts from Step 1), write a commit message.

Follow conventional commit format:
```
<type>(<scope>): <short summary>

<optional body with bullet points for notable changes>
```

- `type`: feat, fix, refactor, docs, chore, test, style, perf, ci, build
- `scope`: the primary area affected (e.g., auth, api, cli, config)
- Summary: imperative mood, lowercase, no period, ≤72 chars
- If documentation was updated as part of this commit, mention it briefly in the body (e.g., "- update README to reflect new CLI flags", "- sync docs/agents/core.md with new module layout")

## Step 3: Commit and Push

1. Run the commit: `git commit -m "<message>"`
2. Push to the remote tracking branch using the branch identified during Step 1's preflight:
   - `git push`
   - If no upstream is set, use `git push -u origin <branch>`.
3. Report the final result: commit hash, branch, and a summary of what was committed and which docs (if any) were updated or regenerated. This extends (not replaces) the report from Step 1.
