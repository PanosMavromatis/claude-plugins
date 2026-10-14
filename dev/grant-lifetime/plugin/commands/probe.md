---
allowed-tools: Bash(touch probe-*)
argument-hint: "<n>"
description: Run touch probe-<n>, to measure how long an allowed-tools grant lasts.
---

Run this shell command, alone, once, and nothing else: `touch probe-$ARGUMENTS`

Then reply with one line: the command, and whether it ran or was refused. Do not retry a
refused command, and do not run anything else.
