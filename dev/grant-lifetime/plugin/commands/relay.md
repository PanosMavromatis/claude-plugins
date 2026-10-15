---
allowed-tools: Edit, Bash(git add:*), Bash(git commit:*)
description: Have a subagent read a file, then commit once it returns, to measure whether this command's grant covers a commit made after a subagent's hand-back.
---

Do two steps, in order. First, use the Agent tool once, with subagent_type
general-purpose, and give it exactly this task: 'Read AGENTS.md in the current directory and
report its first line. Use no other tool.' Second, once it has returned, run this shell
command yourself, alone, once: git commit -m probe. Report the commit command's result
verbatim, and do not retry a refused call.
