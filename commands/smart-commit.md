---
allowed-tools: Bash(git:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Bash(dev/build-agents-md.sh:*), Read, Write, Glob, Grep
description: Update docs to match staged changes, commit with an appropriate message, and push.
argument-hint: "[extra doc paths...]"
---

# Smart Commit

End-to-end commit workflow: sync documentation with the staged diff via `/agents-docs-update`, then commit and push.

This command delegates all documentation handling to the imported update command below. Do not duplicate or override those steps here — follow them as written, using this command's `$ARGUMENTS` (`$ARGUMENTS`) as the extra doc paths for the imported Step 2.

## Step 1: Sync Documentation

Execute the steps from the following imported command to completion before proceeding. Treat its `$ARGUMENTS` as identical to this command's `$ARGUMENTS`.

@.claude/commands/agents-docs-update.md

Once the imported Step 6 (Report) has printed its summary, continue with Step 2 below.

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
