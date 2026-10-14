# 03 — Rewrite this repository's closed and stale lines

**Goal**: [x]
> **Done:** The root plan now reads as the current scripts write it: R1a's line closes as the stamp would, and the prose describes the stamp, not the legacy close. Both scripts still read it.

- [x] `docs/plan/TODO.md:25` reads ``- [x] 07-subagent-refactor-R1a — Session handoff and full-log export commands, and the plan scripts' SIGPIPE fix; workflow-coding 0.10.1 — closed. See `docs/plan/07-subagent-refactor-R1a/_TODO.md`.``
  > **Note:** Byte for byte the line `close-revision.sh` now proposes for a `[~]` line: the note kept, then `— closed. See` and the revision's `_TODO.md`, which exists. Lines 20–25 now all end alike.
- [x] `docs/plan/TODO.md`'s prose, lines 6–8 and 12, describes the stamp, and no line in it says a close extracts or moves a revision
  > **Note:** Lines 7–8 now say `/close-revision` stamps a finished revision closed in `docs/plan/<label>/`, and line 12 that it is stamped `[x]` with a pointer to its master plan. `grep -c -i "extract\|move"` on the root plan counts 0.
- [x] The scripts still read the root plan: `propose-revision.sh` refuses `07-subagent-refactor-R1a` and `08-subagent-refactor-R2` as listed, and `close-revision.sh 07-subagent-refactor-R1a` refuses it as already closed
  > **Note:** `propose-revision.sh` refuses both labels as already listed, at lines 25 and 26; `close-revision.sh` refuses R1a as already closed, "docs/plan/TODO.md:25 marks it [x]". Both read the rewritten line as a label and a note.
