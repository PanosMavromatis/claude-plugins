# 02 — check-agents-md.sh keeps its in-sync check and gains two lints

**Goal**: [ ]

- [ ] After a build, the check reports the pair in sync. It fails, naming the file, when an `AGENTS.override.md` differs from its guide or is missing
- [ ] It warns without failing on an `AGENTS.md` over 200 lines and on one with a dated sentence (`20\d\d-\d\d-\d\d`), at the root and in a component
