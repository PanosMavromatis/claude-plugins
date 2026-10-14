# 01 — plan-drafter returns a trace beside the draft

**Goal**: [x]
> **Q:** What shape does the trace take: `- N. <tag>; <tag>` lines in a `## Trace` section right after `## Draft` (A), a table in the same place (B), or the same lines last, after `## Questions` (C)?
> **A:** A: lines, second, every subgoal exactly once, so one regex parses it for `check.py`.
> **Q:** The trace is self-reported, so an invented subgoal could carry an invented tag (a side agent's note). Should the form-check script also resolve each tag against the spec?
> **A:** Yes: tags are copied verbatim so they can be found, and goal 02's script reports any it cannot resolve. A real tag on an invented subgoal still passes; that stays with the review.
> **Done:** `plan-drafter` returns a `## Trace` beside the draft, one line per subgoal with verbatim, resolvable tags, and `subdividing.md` holds its rules; `_TODO.md`'s form is unchanged. The plan for goals 02 and 03 now has the script resolve tags and the command turn an unresolved one into a question.

- [x] `plan-drafter.md`'s Output adds a trace beside `## Draft`, `## Left out` and `## Questions`, tagging every subgoal with the spec item it carries in the spec's own terms: a § or heading plus item for a document, a short quoted phrase for pasted text or the conversation
  > **Note:** `## Trace` is the drafter's second section, before `## Left out` and `## Questions`, and a fifth Process step has it tag each subgoal, a subgoal it cannot tag becoming a question. Tags are copied verbatim, a § or heading as the spec writes it, so goal 02's script can resolve them.
- [x] The trace never reaches `_TODO.md`: the draft's form, and `subdividing.md`'s, are unchanged
  > **Note:** The diff leaves `subdividing.md`'s form block untouched, and the drafter's Never list forbids a tag inside the draft's fence. That the trace is self-reported was raised by a side agent; goal 02's script now resolves each tag against the spec (the second Q&A).
- [x] `references/subdividing.md` describes the trace beside the form
  > **Note:** A new last section, "The trace", follows "The form", and the intro names the trace; it records the trace and the left-out list as counterparts that together account for the spec.
