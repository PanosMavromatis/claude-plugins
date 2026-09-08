# docs/plan-notes-and-interop

**Status**: active
**Created**: 2026-09-08
**Subgoal**: standalone

## Tasks

- [x] `/hitl-step` and `/step`: document `> **Note:**` as the way to record a finding, and
      say plainly that a finding is never a checkbox.
- [x] `/hitl-step` Step 4: check the subgoals before flipping the parent, rather than
      relying on memory of a goal that may have spanned many turns.
- [x] `/hitl-step` Step 6: verify a section-completion claim at every indent, since that is
      the one report a reader will not re-check.
- [ ] `dp-compile` interoperation: README "Companion plugins" pointer, conflict-report
      section, and a `CLAUDE.md` line.
  - [x] Conflict report §4.4 — how the two plugins' hooks compose, and why `dp-compile`'s
        gate firing inside `/smart-commit` is the design rather than a leak.
  - [ ] README "Companion plugins" pointer.
  - [ ] `CLAUDE.md` line.
