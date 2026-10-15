# 05 — Run the migration end to end

**Goal**: [ ]

- [ ] `/agents-docs-migrate`, loaded from this branch with `--plugin-dir`, runs to the end on a copy of `tmp/pfsmgraph` (the dispatcher entrance) and on a repository with one legacy `CLAUDE.md`.
- [ ] On both, `AGENTS.md` ends at 200 lines or fewer, and a grader finds every moved paragraph verbatim in its destination and every source paragraph either moved or dropped with a reason.
- [ ] On both, `CLAUDE.md` is gone, or the shim is present on an older Claude Code or beside a `CLAUDE.local.md`.
- [ ] On both, nothing is deleted before the confirmation: a run declined at the destructive step leaves every source in place.
- [ ] Each run and its cost are recorded in this goal file; the user runs the paid sessions.
