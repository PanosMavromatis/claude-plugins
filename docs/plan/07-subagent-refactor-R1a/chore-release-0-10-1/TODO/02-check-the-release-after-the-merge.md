# 02 — Check the release after the merge

**Goal**: [x]
> **Done:** A fresh session loads `workflow-coding` 0.10.1 from the marketplace install with both new commands listed; `/session-export-full` exported its own session; and the handoff `/session-handoff` wrote was read first by the next session through the root `CLAUDE.md`, then archived on the user's confirmation.

- [x] The marketplace install loads `workflow-coding` 0.10.1, with `/session-handoff` and `/session-export-full` listed
  > **Note:** Checked 2026-10-13 in the session after R1a's last: the project-scope `installed_plugins.json` entry points at `cache/mavromatis-ai-labs/workflow-coding/0.10.1`, whose `plugin.json` reads 0.10.1 and whose `commands/` holds `session-handoff.md` and `session-export-full.md`; both are in the session's skill list. R1a's last session had seen both after `/plugin` and `/reload-plugins`.
- [x] Run with no argument, `/session-export-full` exports the session it runs in
  > **Note:** R1a's last session ran it with no argument from `…/workflow-coding/0.10.1/scripts/`: exit 0, writing `multi-agent-refactor-r1a.{md,jsonl,tar.gz}` to `~/claude-exports/claude-plugins/`, with 282 operator messages, 660 assistant replies and 6 compactions, as it reported. The three files are there, and the Markdown holds the 6 compaction summaries.
- [x] At the end of R1a, the session writes `tmp/session-handoff.md` by following `commands/session-handoff.md` as text, and the next session reads it first through the root `CLAUDE.md`
  > **Note:** R1a's last session wrote it with `/workflow-coding:session-handoff` from the 0.10.1 install, which runs `commands/session-handoff.md` as its prompt: Keep, Drop and Where things are. The next session read it in its first two tool calls, before replying, said what it took from it, and on the user's confirmation archived it to `tmp/handoffs/2026-10-13-main.md`, as `CLAUDE.md` says.
