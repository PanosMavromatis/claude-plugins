# docs/settled-workflow

**Status**: merged — PR #12 — 2026-08-30
**Created**: 2026-08-30
**Subgoal**: Document the settled workflow, including the plan-filing sweep

## Tasks

- [x] README: add the filing sweep to the branch-lifecycle section — what it is, when to run it, and that a plan's revision is derived from the `## Subgoals — revision N` heading enclosing its backlink rather than chosen. Show the resulting `docs/plan/` shape.
  > **Done:** The lifecycle diagram now shows the sweep hanging off the end of the loop, followed by a `#### The filing sweep` subsection: what accumulates and why, the resulting `docs/plan/` shape with real counts, the `awk` derivation, and the two cases that resist it (no backlink; a heading with no revision number). States plainly that nothing depends on the `rev-N` grouping and that a monorepo might group by component instead, reading the list from `docs/agents/`.
- [x] README: refresh the conventions bullets — the two-tier plans bullet should carry identity-vs-location plainly, and add one for locate-then-window master-plan access. Amend the PR-body bullet to note that a path pointer decays once plans move, flagging the fix as pending rather than describing it as solved.
  > **Done:** Added a locate-then-window conventions bullet with the measured numbers and the zero-match rule. Amended the PR-body bullet to admit the decaying-pointer gap rather than describe it as solved, including the practical workaround — treat a `Plan:` path in an older PR as a name to search for. The two-tier bullet already carried identity-vs-location from PR #8; left as is.
- [x] CLAUDE.md: state the same loop for the model, with the filing sweep, the derivation rule, and an explicit correction of the earlier "judgement worth keeping manual" framing so it does not get cited later.
  > **Done:** `CLAUDE.md` gained two paragraphs before the layout example: filing is a lookup with the derivation, and an explicit **that was wrong** on the earlier 'judgement worth keeping manual' framing, with the distinction spelled out — the no-taxonomy argument governs inventing a hierarchy at creation time, not reading back one already recorded. Plus the general rule that paths written into immutable records decay while identities do not.
- [x] Verify no doc claims a path that the regrouping invalidated — grep both files for `docs/plan/<...>` forms and check each against the current layout.
  > **Found while doing this:** the `awk` snippet I had just written into three files was wrong — unanchored, it matched prose that merely *mentions* `> **Branch:**`, which the surrounding paragraph does, yielding rows like `silent.` and `premature.`. Anchored to `^[[:space:]]*` and re-run: 14 rows for 14 backlink lines. The master plan's copy carries a note saying why the anchor is load-bearing, since the failure is invisible until a prose mention exists.
  > **Done:** Audited every `docs/plan/…` form in both files against the current layout. All accurate; one clarified — the README command table said `/new-branch` writes the plan at `docs/plan/<type>-<slug>/` without noting that is the *creation* location, which now reads as flat-then-filed.
