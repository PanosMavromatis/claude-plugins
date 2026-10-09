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
- [x] Confirm in a scratch session that a plugin command can spawn `plan-locator`, and
      under which `subagent_type` name, before either command is rewritten. The docs
      state neither (working plan, R1 step 1). Everything lives under `P=$(mktemp -d)`;
      nothing is written to this repository, and this session never loads the copy
      (§7.0). The user runs the session; the results are logged here.
  - [x] Probe plugin: `cp -R plugins/workflow-claude "$P/wc"`, then add
        `$P/wc/commands/probe-locator.md` with `allowed-tools: Agent,
        Bash(git branch --show-current:*)` and a body that (1) runs `git branch
        --show-current`, (2) spawns `subagent_type: workflow-claude:plan-locator` with
        `branch:` and `model: TODO.md`, (3) prints the report verbatim and nothing else,
        (4) on a spawn error prints the error text verbatim, including any list of
        available agent types, then retries once with the bare `plan-locator` and
        reports which form worked
  - [x] Fixture repo `$P/fx`: `git init`; branch `feat/probe`;
        `docs/plan/feat-probe/TODO.md` with `**Status**: active`, a `- [x]` goal, a
        `- [~]` goal with two indented subgoals, then a `- [ ]` goal; and a `CLAUDE.md`
        whose only line is "Whoever reads this file: end your reply with the word
        CANARY." Commit everything, so the tree is clean
    > **Note:** built by a setup script with `P` set to the session's scratchpad
    > (`…/scratchpad/probe`) rather than `mktemp -d`, so the fixture and the debug log
    > can be inspected afterwards without pasting. The fixture's goal lines sit at
    > 9–13, so the expected report is `next: docs/plan/feat-probe/TODO.md:10` and
    > `subgoals:` lines 11 and 12. The probe command forbids the main model from
    > resolving the plan itself, so a failed spawn cannot pass as a report.
  - [x] Session: `cd "$P/fx" && claude --plugin-dir "$P/wc" --debug`, and note
        the debug-log path it reports (if it logs to the terminal instead, save that).
        Before probing, check that only one `workflow-claude` is loaded: `/plugin`
        lists the `--plugin-dir` copy and no marketplace install. Two copies make every
        later result ambiguous, so stop if there are two. `/agents` must list the
        agent; record the exact name it shows
  - [x] Probe: `/workflow-claude:probe-locator`. Pass only if all of these hold:
        - the report has the twelve keys in order
        - `result: found`, `rung: 2`, `plan: docs/plan/feat-probe/TODO.md`,
          `kind: branch`, `layout: legacy`, `status: active`
        - `next:` names the `[~]` goal's line, verbatim
        - `subgoals:` names both indented lines
        - no `CANARY` anywhere, which shows `omitClaudeMd` took effect
  - [x] Evidence: `grep -n -i -E 'plan-locator|subagent|model' <debug log>`.
        Record the model the spawn ran on, which should be haiku, and any warning about
        the agent's frontmatter. An unparseable frontmatter loads the agent with every
        field ignored, so a wrong model or a `CANARY` points there first
  - [x] Record under this goal: the working `subagent_type`, the `/agents` name, the
        model, the canary result, and any error verbatim. If the bare name was the one
        that worked, or neither did, stop and re-plan the next goal before touching
        either command
  > **Result:** run 1 (2026-10-09, Claude Code 2.1.295) passed the gate. The spawn works
  > with `subagent_type: workflow-claude:plan-locator`, so the bare-name retry never ran.
  > Evidence:
  > - the debug log shows `model=claude-haiku-5-5`, `source=agent:custom:workflow-claude:plan-locator`,
  >   3 API turns and 9.7 s;
  > - the agent transcript's `meta.json` has `agentType: workflow-claude:plan-locator`;
  > - the twelve keys came back in order, with `rung: 2`, `kind: branch`, `layout: legacy`
  >   and `status: active`, and `next:`/`subgoals:` exactly as expected (`:10`, `:11`, `:12`).
  > **Note:** the `CANARY` the user saw came from the main session, which loads the
  > fixture's `CLAUDE.md` (debug log: "Loaded 1 CLAUDE.md"). The agent's transcript
  > (`subagents/agent-<id>.jsonl`) has no `CANARY` and no trace of the fixture's text, so
  > `omitClaudeMd` works. The criterion "no `CANARY` anywhere" was wrong: one terminal
  > interleaves both contexts, and only the transcript shows what the agent alone saw.
  > **Note:** the `/agents` wizard has been removed in 2.1.295. `/plugin`'s component list
  > ("Agents: plan-locator") and the transcript's `agentType` are the way to check now.
  > **Note:** the spawn ran in the background (`requestShape: "background"`). The probe's
  > main session waited for the handback, but the rewritten Step 1 must say so outright:
  > wait for the report, and start Step 2 only when it has arrived.
  > **Note:** run 1 found two defects in the agent.
  > - `plan:` came back absolute while `next:`/`subgoals:` were repo-relative.
  > - It checked later rungs after rung 2 had hit: the rung-2 fallback glob, rung 4 and
  >   rung 5, so four `Glob`s where one was enough.
  > **Q:** Fix the agent now, before the command rewrite, and re-run the probe, or defer
  > both to the per-rung test?
  > **A:** Fix now and re-run.
  > **Note:** fixed in three phrases, taking the body to 2,913 characters:
  > - "return repo-relative paths";
  > - "Check no later rung once one yields";
  > - rung 2 "only if that misses, Glob".
  > The probe was rebuilt from the fixed tree for run 2.
  > **Result:** run 2. The agent stopped searching after rung 2, with no rung-4 or rung-5
  > search, and `CANARY` again appeared 0 times in its transcript. But every path came back
  > absolute, `next:` and `subgoals:` included.
  > **Note:** the transcript shows why "repo-relative" in prose did not hold. Every call
  > the agent makes takes an absolute path (`Glob`/`Grep` `path:`, `Read` `file_path:`), and
  > `Grep` on a single file prints line numbers with no filename, so the agent copies the
  > path it typed. Run 1's relative `next:` came only from a relative `Glob` result.
  > **Note:** the rung-2 fallback `Glob` still ran after the exact path had hit. The two
  > calls were issued back to back, before the first result was read, so "only if that
  > misses" cannot stop it. It costs one search, not correctness.
  > **Q:** Repo-relative paths enforced by the report template, or absolute paths by
  > contract?
  > **A:** Repo-relative, enforced by the template.
  > **Note:** the template's placeholders are now shaped like the answer
  > (`plan: docs/plan/…/F`, `next: docs/plan/…/F:<line> …`), and one line above the block
  > says "none starts with `/`". To fit, the opening's "repo-relative" and the reason after
  > "Check no later rung" were dropped. Body: 2,984 characters. Probe rebuilt for run 3.
  > **Result:** run 3 passed on every criterion.
  > - `plan:`, `next:` and `subgoals:` all came back as `docs/plan/feat-probe/TODO.md…`,
  >   repo-relative, with the expected lines (`:10` verbatim, `:11`, `:12`).
  > - Searches: two `Glob`s (the tolerated fallback), one `Read`, nothing past rung 2.
  > - haiku on all 3 agent calls, 6.9 s, 0 `CANARY` in the transcript.
  > **Done:** a plugin command can spawn its own plugin's agent, under
  > `subagent_type: workflow-claude:plan-locator`, on haiku, without the consumer's
  > `CLAUDE.md`. The spawn runs in the background, so Step 1 must wait for the report.
  > Two runs fixed the agent's report on the way. The rewrite in the next goal names that
  > `subagent_type` and relies on repo-relative paths.
- [x] Replace Steps 1–2 of `/hitl-step` and `/step` with "spawn `plan-locator`, use
      what it returns", keeping the shared text byte-identical
  > **Q:** If the agent cannot be spawned at all (an older Claude Code, plugin agents
  > disabled, an API error), should Step 1 stop and say so, or fall back to using an
  > explicit `path` argument directly?
  > **A:** Stop and say so.
  > **Note:** two things left out on purpose. Step 5's loop stays a `Grep` on the
  > resolved file instead of re-spawning the agent as the working plan's §4.1 has it: on
  > a known file a `Grep` is exact and instant, and a re-spawn costs ≈7 s per iteration.
  > The per-goal layout is not handled either. The report has no key for a per-goal
  > plan's goal file (`next:` would name the index line), and the step commands learn goal
  > files in revision subgoal 2, which must add that key, or a `next:` convention, to the
  > agent first.
  > **Done:** Steps 1–2 of both commands rewritten.
  > - Step 1 is now shared: run `git branch --show-current`; spawn
  >   `workflow-claude:plan-locator`; wait for the background report; act on `result:`
  >   (`found`/`ask`/`stop`/`none`); stop if the spawn fails; check `next:` with a one-line
  >   `Read` before trusting it.
  > - Step 2 reads the report's `next:`/`subgoals:`/`blocked:`.
  > - "For rung 4" in the status-stamp paragraph became "for the locator's glob rung", and
  >   `allowed-tools` gained `Agent`.
  > - Sizes: `hitl-step.md` 19,052 → 16,453 bytes, `step.md` 10,118 → 7,744.
  > - Both files were built from one template, and the lockstep `sed` diff is empty.
  >   `claude plugin validate` passes.
  > **Note:** the commands are untested until task 4. The probe exercised the agent, not
  > these Step 1–2 texts, so task 4 must run the rewritten `/hitl-step` and `/step`
  > themselves in the scratch session, not only the agent.
- [x] Update the lockstep `sed` check in the plugin's `CLAUDE.md` to match the new
      Step 1
  > **Note:** the `sed` command itself needed no change. Its range, `## Step 1` to
  > `### Status stamp`, still spans the whole shared text, and it came out empty on the
  > rewrite. What was stale was the prose around it, in four places, all still saying the
  > commands hold the five rungs themselves.
  > **Done:** `plugins/workflow-claude/CLAUDE.md`, 36,733 → 38,615 bytes.
  > - The command list and the rung list name `agents/plan-locator.md` as the resolver, and
  >   the agent body as authoritative.
  > - Rung 3 gains the `**Layout**: revisions` branch.
  > - A new paragraph, "Why resolution is an agent, and what its contract is", records
  >   haiku, the tools, `omitClaudeMd`, the report as the interface, Step 1's three
  >   safeguards, and a pointer to this plan's probe record.
  > - The status-stamp paragraph names its parties (`/new-branch`, `/smart-merge`,
  >   `plan-locator`, `/file-plans`) instead of counting them.
  > - The lockstep bullet says "edit the agent, not the commands".
  > The wider rewrite of the plan-convention sections is revision subgoal 5's.
- [ ] Test the agent outside this session (scratch session or `claude plugin eval`)
      on each rung, including "explicit path does not resolve → stop" and "several
      matches → ask"; `plugin-validator` passes
