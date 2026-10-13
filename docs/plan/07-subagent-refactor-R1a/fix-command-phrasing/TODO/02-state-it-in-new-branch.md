# 02 — State it in /new-branch

**Goal**: [x]
> **Done:** `/new-branch` states the phrasing rule for every step in its Guidelines, says "each alone" at its two multi-command blocks, and gives the path to `Read` where it points at another command.
> **Q:** In r9 both `/new-branch` denials came from the session reading another command's text from the plugin directory with chained `ls` and `grep`: `/smart-commit` Step 3 for the subject rule (e3), `/hitl-step` for the TODO form (e4). Besides stating the phrasing rule, give each pointer its path, to `Read` (A), state the subject rule inline in step 8 (B), or state the phrasing rule only (C)?
> **A:** A: each pointer says how to follow it, `Read` `${CLAUDE_PLUGIN_ROOT}/commands/smart-commit.md`, never `ls` or `grep`, and step 7 says the form it shows is the whole of it; goal 03 changes the other four copies of the pointer the same way.

- [x] `commands/new-branch.md` states the rule for every step, as `/smart-merge`'s Guidelines do, including step 8's commit-subject check, the step where e3's session chained `git log` with a `grep`
  > **Note:** Each step's commands are stated alone, steps 3 and 8 beside their bash blocks, and a Guidelines bullet states the whole rule. The r9 denials came from following a pointer: e3 and e4 searched the plugin's directory with `ls` and `grep` for `/smart-commit` Step 3 and for `/hitl-step`'s form, e3 guessing a `skills/` directory that does not exist. So step 8 gives `smart-commit.md`'s path to `Read`, and step 7 says its block is the whole form.
