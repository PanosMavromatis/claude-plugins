# 01 — Write the session-handoff command

**Goal**: [ ]

- [ ] Read the models: the R1→R1a handoff (`tmp/session-handoff-r1-r1a.md`), §4.4's Keep / Drop / Say where, and an existing command's form under `plugins/workflow-coding/commands/`
- [ ] Decide how the command finds the revision, branch and goal file with no `${CLAUDE_PLUGIN_ROOT}` to reach `locate-plan.sh`, and log the decision here
- [ ] `plugins/workflow-coding/commands/session-handoff.md` writes `tmp/session-handoff.md` in three parts: Keep (§4.4's list), Drop (whatever a path retrieves) and Say where (pointers, not contents)
- [ ] The file needs no `$ARGUMENTS`, no `${CLAUDE_PLUGIN_ROOT}` and no `allowed-tools`: no step depends on the command runtime
