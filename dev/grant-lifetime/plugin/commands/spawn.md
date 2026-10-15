---
allowed-tools: Edit, Bash(git add:*), Bash(git commit:*)
argument-hint: "<task>"
description: Hand one task to a subagent, to measure whether this command's allowed-tools grant reaches it.
---

Use the Agent tool once, with subagent_type general-purpose, and give it exactly this task,
word for word:

$ARGUMENTS

Use no other tool yourself. When it returns, reply with its answer verbatim.
