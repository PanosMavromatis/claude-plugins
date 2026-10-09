# feat/plan-locator

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 06-subagent-refactor-R1 — `agents/plan-locator.md`; `/step` and `/hitl-step` Steps 1–2 call it

## Tasks

- [x] Write `agents/plan-locator.md` with plugin-dev's `agent-development`: the five
      rungs of §4.2, a fixed report shape, under 3,000 characters, and
      `validate-agent.sh` clean
  > **Q:** Nothing in the repo uses the new layout until subgoal 2 writes it and R2
  > adopts it. Should the agent implement the full §4.2 spec now (all five rungs,
  > including rung 3's open-revision `_TODO.md`, and both `per-goal` and `legacy`
  > layouts, tested on scratch fixtures) or only today's legacy rungs?
  > **A:** Option 1, full spec now.
  > **Q:** Should the agent get `Read, Grep, Glob` only, with the caller passing the
  > branch name in the spawn prompt, and `omitClaudeMd: true`?
  > **A:** Yes to both.
  > **Note:** both depart from the working plan's §4.1. Its tools column gives
  > `Bash(git branch --show-current:*)`, but the sub-agents docs document only bare tool
  > names (and `mcp__<server>`) in `tools`, say a pattern in `disallowedTools` still
  > removes the whole tool, and ignore `hooks` on plugin agents, so a pattern cannot be
  > relied on to scope Bash. Dropping Bash is stricter, and lets a fixture pass any
  > branch name without being a git checkout. §4.1's "read `docs/agents/<guide>/AGENTS.md`"
  > paragraph does not apply: the agent reads `docs/plan/**` only, and inheriting the
  > consumer's `CLAUDE.md` would cost every `/step` and `/hitl-step` spawn the whole
  > session-start load (≈33.5k tokens in pfsmgraph) to return a path and line numbers.
  > Source: code.claude.com/docs/en/sub-agents and /plugins/components, read 2026-10-08.
  > **Note:** two readings of §4.2's rung order, confirmed by the user. (1) The legacy
  > master plan resolves at rung 3, not rung 5: §4.2's text puts "a root index without
  > `**Layout**: revisions`" after the glob, which on `main` in a legacy repo would let
  > every unstamped branch plan count as active and turn today's direct answer into a
  > question. Rung 3 is what 0.9.0 does, and what R1's last subgoal checks. (2) Rung 3
  > applies on any branch, not only on `main`: a branch with no plan falls back to the
  > master plan today, and the agent then never compares the branch name to `main`.
  > **Note:** plugin-dev's `validate-agent.sh` exits at its first warning:
  > `((warning_count++))` on a zero counter returns 1 under `set -e`. Run here from a
  > scratch copy with `warning_count=$((warning_count+1))`; the bug is plugin-dev's, not
  > this repository's. Its remaining warning, no `<example>` blocks in `description`, is
  > expected: the skill now prescribes prose triggers and a "When to invoke" section.
  > **Done:** `plugins/workflow-claude/agents/plan-locator.md`, the plugin's first agent:
  > haiku, `Read, Grep, Glob`, `omitClaudeMd: true`, body 2,752 characters. Five rungs,
  > both layouts, both models (`TODO.md` next-goal rule, `DO.md` first-unchecked rule),
  > and a fixed twelve-line report of paths and line numbers. `claude plugin validate`
  > passes with its three existing items, none about the agent. Untested until task 4.
- [ ] Confirm in a scratch session that a plugin command can spawn `plan-locator`, and
      under which `subagent_type` name, before either command is rewritten. The docs
      state neither (working plan, R1 step 1). Everything lives under `P=$(mktemp -d)`;
      nothing is written to this repository, and this session never loads the copy
      (§7.0). The user runs the session; the results are logged here.
  - [ ] Probe plugin: `cp -R plugins/workflow-claude "$P/wc"`, then add
        `$P/wc/commands/probe-locator.md` with `allowed-tools: Agent,
        Bash(git branch --show-current:*)` and a body that (1) runs `git branch
        --show-current`, (2) spawns `subagent_type: workflow-claude:plan-locator` with
        `branch:` and `model: TODO.md`, (3) prints the report verbatim and nothing else,
        (4) on a spawn error prints the error text verbatim, including any list of
        available agent types, then retries once with the bare `plan-locator` and
        reports which form worked
  - [ ] Fixture repo `$P/fx`: `git init`; branch `feat/probe`;
        `docs/plan/feat-probe/TODO.md` with `**Status**: active`, a `- [x]` goal, a
        `- [~]` goal with two indented subgoals, then a `- [ ]` goal; and a `CLAUDE.md`
        whose only line is "Whoever reads this file: end your reply with the word
        CANARY." Commit everything, so the tree is clean
  - [ ] Session: `cd "$P/fx" && claude --plugin-dir "$P/wc" --debug`, and note
        the debug-log path it reports (if it logs to the terminal instead, save that).
        Before probing, check that only one `workflow-claude` is loaded: `/plugin`
        lists the `--plugin-dir` copy and no marketplace install. Two copies make every
        later result ambiguous, so stop if there are two. `/agents` must list the
        agent; record the exact name it shows
  - [ ] Probe: `/workflow-claude:probe-locator`. Pass only if all of these hold:
        - the report has the twelve keys in order
        - `result: found`, `rung: 2`, `plan: docs/plan/feat-probe/TODO.md`,
          `kind: branch`, `layout: legacy`, `status: active`
        - `next:` names the `[~]` goal's line, verbatim
        - `subgoals:` names both indented lines
        - no `CANARY` anywhere, which shows `omitClaudeMd` took effect
  - [ ] Evidence: `grep -n -i -E 'plan-locator|subagent|model' <debug log>`.
        Record the model the spawn ran on, which should be haiku, and any warning about
        the agent's frontmatter. An unparseable frontmatter loads the agent with every
        field ignored, so a wrong model or a `CANARY` points there first
  - [ ] Record under this goal: the working `subagent_type`, the `/agents` name, the
        model, the canary result, and any error verbatim. If the bare name was the one
        that worked, or neither did, stop and re-plan the next goal before touching
        either command
- [ ] Replace Steps 1–2 of `/hitl-step` and `/step` with "spawn `plan-locator`, use
      what it returns", keeping the shared text byte-identical
- [ ] Update the lockstep `sed` check in the plugin's `CLAUDE.md` to match the new
      Step 1
- [ ] Test the agent outside this session (scratch session or `claude plugin eval`)
      on each rung, including "explicit path does not resolve → stop" and "several
      matches → ask"; `plugin-validator` passes
