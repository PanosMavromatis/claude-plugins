# 01 — The stamp writes the closed form, keeping the note

**Goal**: [x]
> **Done:** The stamp now closes an index line as a legacy close's pointer reads, ``- [x] <label> — <note> — closed. See `docs/plan/<label>/_TODO.md`.``, and `--check` refuses the old form. The suite gained `s14`, `k11` and three mutants, and seven files describe the new line.

- [x] Under a revisions index, `close-revision.sh` proposes ``- [x] <label> — <note> — closed. See `docs/plan/<label>/_TODO.md`.`` for the index line, or ``- [x] <label> — closed. See …`` when it has no note, and `--check` accepts that line and rejects the old `[x]`-plus-note form
  > **Note:** `IDX_DONE` is built once in `stamp()` and used by both the proposal's `edits:` and `--check`, so the two cannot disagree; its form is the legacy close's pointer's, `R_POINTER`. `s01` and `s12` (CRLF) propose it with the note, `s14` without one, and `k11` fails the old form under `--check`.
- [x] `python3 -I dev/close-revision/suite.py` passes with a case for each, and `--mutants` catches every mutant, one that writes the old form and one that drops the note among them
  > **Note:** 67 of 67 cases pass, twice under each Bash found; `--mutants` kills 50 of 50, none stale. The new `c43` (old form) and `c44` (note dropped) die at `s01`, `c45` (`--check` expects the old form) at `k01`; the refreshed `c11`, `c30` and `c31` die where they did before, at `s01`, `k02` and `k05`.
- [x] `close-revision-spec.md`, `commands/close-revision.md` and the plugin's `CLAUDE.md` describe the stamp's new index line
  > **Note:** Also rewritten, since they described the old form too: `CLAUDE.md:50`, where the index line's forms are defined, the plugin `README.md`'s command table, and `close-revision.sh`'s header comment. With the header a line longer, all 50 mutants still apply at `-F0`, and 67 of 67 cases pass.
