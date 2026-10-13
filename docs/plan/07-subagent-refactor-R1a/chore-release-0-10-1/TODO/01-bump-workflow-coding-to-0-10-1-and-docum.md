# 01 — Bump workflow-coding to 0.10.1 and document the release

**Goal**: [ ]

- [ ] `plugins/workflow-coding/.claude-plugin/plugin.json` reads 0.10.1, and no other file in the repository names a version that disagrees with it
- [ ] The root `README.md` and `plugins/workflow-coding/README.md` describe `/session-handoff` and `/session-export-full`, and what else 0.10.1 changes: the plan scripts survive SIGPIPE, `/new-branch` writes each goal file with its subgoals, and every command that grants `git` states how to phrase a command, checked by `dev/command-phrasing`
- [ ] The plugin's `CLAUDE.md` names both commands where it describes the others, and its `claude plugin validate` entry records a run at 0.10.1, which the user runs
