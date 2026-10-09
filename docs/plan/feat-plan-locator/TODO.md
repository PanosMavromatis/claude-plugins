# feat/plan-locator

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 06-subagent-refactor-R1 — `agents/plan-locator.md`; `/step` and `/hitl-step` Steps 1–2 call it

## Tasks

- [ ] Write `agents/plan-locator.md` with plugin-dev's `agent-development`: the five
      rungs of §4.2, a fixed report shape, under 3,000 characters, and
      `validate-agent.sh` clean
- [ ] Replace Steps 1–2 of `/hitl-step` and `/step` with "spawn `plan-locator`, use
      what it returns", keeping the shared text byte-identical
- [ ] Update the lockstep `sed` check in the plugin's `CLAUDE.md` to match the new
      Step 1
- [ ] Test the agent outside this session (scratch session or `claude plugin eval`)
      on each rung, including "explicit path does not resolve → stop" and "several
      matches → ask"; `plugin-validator` passes
