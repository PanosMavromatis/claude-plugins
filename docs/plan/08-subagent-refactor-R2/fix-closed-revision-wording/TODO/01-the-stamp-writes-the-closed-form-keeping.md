# 01 — The stamp writes the closed form, keeping the note

**Goal**: [ ]

- [ ] Under a revisions index, `close-revision.sh` proposes ``- [x] <label> — <note> — closed. See `docs/plan/<label>/_TODO.md`.`` for the index line, or ``- [x] <label> — closed. See …`` when it has no note, and `--check` accepts that line and rejects the old `[x]`-plus-note form
- [ ] `python3 -I dev/close-revision/suite.py` passes with a case for each, and `--mutants` catches every mutant, one that writes the old form and one that drops the note among them
- [ ] `close-revision-spec.md`, `commands/close-revision.md` and the plugin's `CLAUDE.md` describe the stamp's new index line
