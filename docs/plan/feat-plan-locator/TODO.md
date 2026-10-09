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
- [x] Test the agent outside this session (scratch session or `claude plugin eval`)
      on each rung, including "explicit path does not resolve → stop" and "several
      matches → ask"; `plugin-validator` passes
  > **Q:** How should the matrix be run (16 agent cases across all five rungs, both
  > models, `blocked:` and all-closed, plus the rewritten `/hitl-step` twice and `/step`
  > once): a headless runner script the user starts once, an interactive session with
  > 19 checkouts, or `claude plugin eval`?
  > **A:** The headless runner script.
  > **Note:** the suite, in the session scratchpad:
  > - `probe-run.sh` builds `suite/fx` (21 branches, one per case) and `suite/wc` (a copy
  >   of the working tree's plugin with an argument-taking probe command), then runs each
  >   case under `claude -p --plugin-dir`;
  > - `probe-grade.py` checks each case's transcripts against expectations read out of the
  >   built fixture.
  > Decoy plans catch a rung that falls through when it should not.
  > **Result:** smoke test c03 passed on every field. Headless (`-p`), the spawn runs in
  > the foreground: the report is the agent's final text, not a `SubagentHandback`, so the
  > grader now reads either, and Step 1's "wait for the report" covers both. The agent
  > made 4 calls: the tolerated fallback `Glob`, plus a line-count `Grep` that its body
  > asks for on master plans only. Both are harmless.
  > **Result:** full suite, 20 cases: 19 pass. The grader was too strict in five cases and
  > was corrected.
  > - c09 and c11: whole-file reads of a 7-line index and of a missing file. Only the
  >   2,498-line master plan must never be read whole, and it never was.
  > - c18–c20: each command checked `next:` inside the `Read` its Step 2 makes anyway
  >   (the whole small branch plan, or lines 2480–2498 of the master plan), not in a
  >   separate one-line `Read`. Every reply says the line matched.
  > c19 is the truncation case, and both the agent and `/hitl-step` used only `Grep`
  > and a 19-line window, landing on line 2,487.
  > **Note:** c09's haiku tried to `Glob` `/Users/…/Developer/Agentic/claude-plugins`, a
  > path it decoded from the scratchpad directory's slug of this repository's path. The
  > headless session refused it, which is the permission boundary working. Consumer
  > repositories have no slug-shaped paths.
  > **Q:** c05 failed. The plan exists flat and as a copy under `archive/`, and the agent
  > took the flat one, because rung 2 tries the exact path first. The fallback glob had
  > seen both copies; 0.9.0 behaves the same way. Should rung 2 always glob and ask if it
  > finds several, or keep "the flat copy wins"?
  > **A:** Always glob, and ask if several.
  > **Note:** "exact path first" was a cost optimisation for the main session. Inside the
  > agent the glob runs on haiku, off the main context, and the transcripts show it ran
  > anyway in 17 of 20 cases. The optimisation bought nothing there, and it hid the
  > likeliest duplicate: a `cp -R` of a flat plan into a group directory.
  > **Q:** Step 1's check said "`Read` the `next:` line alone (`offset` its line,
  > `limit` 1)". All three command cases checked the line inside the read Step 2 needs
  > anyway. Should the wording follow what they do, or should the separate one-line
  > `Read` stay?
  > **A:** Change the wording to match.
  > **Result:** re-run with both changes: 18 of 20 pass, and c05 now asks, listing both
  > copies. Two cases that passed before failed, both through haiku variance on edges the
  > body left open.
  > - c13 reported the root file with absolute paths: no placeholder had a root-file shape.
  > - c14 doubted an empty search, went looking in the real repository path it had decoded
  >   from the scratchpad's slug, was refused, and reported `stop` ("could not reach the
  >   repository") instead of `none`.
  > **Note:** fixed in the agent (body 2,979 characters).
  > - Added "The working directory is the repository: search nowhere else, and an empty
  >   search is an answer."
  > - Rung 5: "report it as `F`".
  > - `result: … stop (rung 1 only) …`.
  > To make room, the stale "A step command loops" trigger went (Step 5 stays a `Grep`),
  > and the closing line was shortened. One pass per case does not show these edges are
  > stable: a case passing once is a sample, not a property.
  > **Result:** two back-to-back runs, `out-a` and `out-b`: 40 of 40 pass, with no
  > searches outside the fixture; the previous run had 4. The variance has moved from
  > results to effort: 2–9 search calls per case (mean 4.3 and 4.5), and sessions take
  > 17–19 s at the median.
  > **Q:** Is the unreliability Haiku's, and would Sonnet be safer? Does the orchestrator
  > catch the agent's errors, and would a retry help? Should resolution be a script?
  > **A:** Measure Sonnet, don't speculate: re-run the suite with it. The orchestrator
  > must be able to vet all subagent work, as a single agent double-checks itself; Step
  > 1's line check covers line errors only, not a wrong resolution. Resolution is a set
  > of rules, so a deterministic script should run it, provided the layout and format
  > conventions hold. Where they do not, and a result is impossible or unreliable (a plan
  > file missing from its expected place, say), the script must neither guess nor fail
  > silently. It should return a diagnostic that the parent passes to the user, naming
  > the problem and suggesting a fix. Grade the agent suite for what it teaches, then plan
  > the script systematically and apply the same suite to it.
  - [x] Haiku suite: 20 cases (17 agent, 3 command) over all five rungs, both models,
        `blocked:` and all-closed; two clean runs back to back, 40 of 40
  - [x] Sonnet comparison: the same suite twice (`out-s1`, `out-s2`) on a plugin copy
        whose only difference is `model: sonnet`. Compare the pass rate, search-call
        variance and wall time with Haiku's `out-a`/`out-b`, and record the numbers
    > **Result:** Sonnet also passed 40 of 40, so on the fixed agent the choice is speed
    > and cost, not correctness. Per-run figures (20 sessions each):
    >
    > | run | model | run wall | session median | agent median | agent p90 | searches | agent output tok | agent input tok |
    > |---|---|---|---|---|---|---|---|---|
    > | a  | haiku  | 6.3 min | 18.8 s | 6.6 s  | 10.8 s | 4.3 | 1,374 | 54,034 |
    > | b  | haiku  | 6.0 min | 17.3 s | 6.4 s  | 10.7 s | 4.5 | 1,476 | 56,026 |
    > | s1 | sonnet | 7.2 min | 21.6 s | 10.6 s | 15.8 s | 4.3 |   889 | 38,188 |
    > | s2 | sonnet | 7.9 min | 23.6 s | 11.1 s | 19.1 s | 4.5 |   906 | 38,747 |
    >
    > "Run wall" sums the sessions' `duration_ms`; file mtimes give 0.6–0.8 min more, which
    > is process start and checkout between cases. Input tokens include cache reads.
    > **Note:** the Sonnet agent is ≈1.65× slower at the median and ≈1.6× at p90, and that
    > accounts for the whole difference in session time. Both made the same number of
    > model turns (3.8–4.0 per agent) and calls per turn, so the ≈30% fewer tokens Sonnet
    > shows sit in fixed per-request overhead (tokenizer, system prompt or tool schemas,
    > which cannot be told apart from here), not in less work done. It says nothing about
    > accuracy, which was equal.
  - [x] `plugin-validator` agent pass on `plugins/workflow-claude`
    > **Result:** pass, no critical issues. The validator confirmed that the agent and both
    > commands agree: `Agent` in `allowed-tools`, the `workflow-claude:plan-locator`
    > name, the four input lines and the twelve report keys. The lockstep diff is empty,
    > and the only `validate-agent.sh` warning is the expected prose-trigger one.
    > **Note:** every finding was checked against the files before acting on it (the
    > orchestrator vets).
    > - Fixed now: the agent's description claimed `/smart-merge` as a caller, and it has
    >   none; the README's "What's in here" had no `agents/` entry; `plugin.json` and the
    >   README said the plugin bundles "skills", and there is no `skills/` directory.
    > - Real logic gaps: on a detached HEAD, `git branch --show-current` prints nothing
    >   (confirmed on the fixture), so rung 2 would glob `docs/plan/**//F`; and rung 3 never
    >   said what happens when `docs/plan/F` is missing.
    > - Already tracked: nothing reads `layout:`. Revision subgoal 2 teaches the commands
    >   goal files before 0.10.0 ships, and no per-goal plan can exist before then.
    > - Dismissed: bump `version` now (the bump is the revision's last subgoal; per branch
    >   it would ship a half-built R1 as 0.10.0); write `tools` as a YAML array (the
    >   sub-agents docs accept a comma-separated string).
    > **Q:** Fix the two logic gaps in the agent too, or only in goal 6's script spec?
    > **A:** Fix the docs now and put both gaps in goal 6. The agent body is at 2,979 of
    > 3,000 characters, and goal 8 may replace it.
  > **Done:** the agent and both rewritten commands were tested outside this session.
  > - 20 headless cases over all five rungs, both models, and the blocked and all-closed
  >   edges, plus three runs of the real commands.
  > - After three fixes, two Haiku runs and two Sonnet runs each passed 40 of 40. Sonnet
  >   is ≈1.65× slower and no more accurate.
  > - `plugin-validator` passed.
  > It also showed that resolution is rule-shaped and that the command's check cannot see
  > a wrong plan, which is why goals 6–10 exist.
- [x] Specify `scripts/locate-plan.sh`, a deterministic replacement for the agent's
      resolution, with the same five rungs and the same report keys, so Step 1's
      contract barely changes
  > **Q:** Approve the drafted spec (usage, 16-key report, rungs, reading rules,
  > diagnostics E1–E13, warnings W1–W11, exit codes, guarantees) with its four
  > defaults: D1 `stop` retired into `error`; D2 a `goal-file:` key now, with
  > `subgoals:` pointing into the goal file; D3 list values on two-space continuation
  > lines instead of commas (branch names may contain commas); D4 the spec kept as
  > `docs/plan/feat-plan-locator/locate-plan-spec.md`?
  > **A:** Approve all.
  - [x] Diagnostics: `result: error` with `problem:` (which convention broke, and where)
        and `fix:` (the command or edit that repairs it) wherever a result would be
        impossible or a guess. At least: a `[~]` revision whose `_F` is missing; a
        malformed index line; `**Layout**: per-goal` with a goal file missing or
        duplicated; a branch plan present only under the other model; a path naming a
        directory with no plan file in it
    > **Note:** the spec has fourteen (E1–E14). E14 was added while writing it out: a path
    > naming the root index when no revision is open, where rung 3 would fall through but
    > rung 1 must not.
  - [x] Warnings: a `warnings:` line for results that are valid but suspicious (no
        `**Status**:`, which counts active as today; an unrecognised status value).
        The command shows them and carries on
  - [x] Exit codes, and the script's guarantees: read-only, deterministic, Bash 3.2-safe,
        the style of `open-revision.sh`
  - [x] Edge rules found by `plugin-validator`, each with a fixture case: an empty branch
        (detached HEAD, as in a rebase, a bisect or a CI checkout) skips rung 2; no
        `docs/plan/F` at rung 3 falls through to rung 4
    > **Note:** both are specified; their fixture cases are goal 7's to build. The
    > detached HEAD is covered by W4's case, and the rung-3 fall-through needs a case of
    > its own, since it raises no diagnostic unless `docs/plan/F′` exists (W8).
  > **Done:** `docs/plan/feat-plan-locator/locate-plan-spec.md` (12.7 KB) is the contract
  > goal 7 implements against: usage with `--goal <line>` and `--branch`, a fixed 16-key
  > report (the agent's 12 less `stop`, plus `goal-file:`, `warnings:`, `problem:`,
  > `fix:`), the five rungs, reading rules (fences ignored, all subgoal markers listed,
  > per-goal goal files), diagnostics E1–E14, warnings W1–W11, exit codes 0/1/2, and the
  > read-only, deterministic, Bash 3.2 guarantees.
- [x] Implement `scripts/locate-plan.sh` and run the suite on it
  > **Q:** Copy the script, which passes the suite from the scratchpad, into
  > `plugins/workflow-claude/scripts/locate-plan.sh`? And where should its suite
  > (`script-suite.py` and the `fx-diag` fixture it builds) live?
  > **A:** Copy it and log the results. The suite stays in the session scratchpad, like
  > `probe-run.sh`. The plugin keeps having no test suite, and this plan records the
  > cases and the results.
  - [x] The 17 resolution cases, run directly, with no `claude -p`, and graded by the
        same expectations
    > **Result:** all 20 cases of the agent suite pass: the 17 resolution cases plus the
    > resolution step of the command cases c18–c20, graded by the agent suite's
    > expectations. One expectation changed on purpose: c02 is now `error` (E1), not
    > `stop` (D1).
    > **Note:** 54–78 ms per run at the median on the fixtures, including the 2,498-line
    > master plan (c06), against 6.4–6.6 s for the haiku agent. That is about 100×
    > faster, with no model tokens.
  - [x] A fixture case for every diagnostic and warning in the specification
    > **Result:** 44 cases in a second fixture repository, all passing:
    > - 18 for E1–E14 (E2, E7, E8 and E12 in two forms each, E13 outside any repository);
    > - 11 for W1–W11 (W4 both as a real detached HEAD and as `--branch ''`; W5 is c13);
    > - 8 for edges and reading rules: the rung-3 fall-through with no `docs/plan/F` (x01),
    >   per-goal resolution (x02), fences (x03), `--goal` (x04), a branch with a comma
    >   (x05), a subdirectory working directory (x07), and the DO model with `--` (x08);
    > - 7 usage errors, each exiting 2 with no report.
    > Every case runs twice under `/bin/bash` 3.2 and twice under Bash 5. The four
    > outputs are byte-identical, and both fixtures are clean afterwards. A static check
    > finds no heredoc, `mktemp`, redirect other than to `/dev/null` or a descriptor,
    > Bash 4 feature, or `grep \|`.
    > **Note:** x06 found a bug no rung list suggests. Branch `plan` flattens to `plan`,
    > which is also the name of `docs/plan/TODO.md`'s parent directory, so rung 2 took
    > the master plan as that branch's plan. Rung 2 now excludes `docs/plan/F`.
    > **Note:** the suite itself was vetted by mutation. Ten copies of the script, each
    > breaking one rule, were all caught, each by the cases written for its rule; the
    > `plan`-branch mutant, for one, only by x06. The first mutation run reported all ten
    > caught by every case, because none of the mutants ran: a relative `--script` path,
    > resolved from inside the fixture. A check that fails on everything is as blind as
    > one that passes on everything.
    > **Note:** not tested on a GNU userland. No `gawk` or GNU `find` is installed here.
    > The script uses POSIX `find -type f -name`, `-maxdepth` (in both BSD and GNU) and
    > `sort` under `LC_ALL=C`, but the spec's "BSD or GNU" stays unverified until it
    > runs on Linux (a container, or CI).
  > **Done:** `plugins/workflow-claude/scripts/locate-plan.sh` (19,981 bytes, 755),
  > identical to the scratch copy the suite graded, and the suite passes on the plugin
  > copy too. Run read-only on this repository, it resolves this plan at rung 2
  > (`next:` goal 7, both subgoals), and with `--branch main` the master plan at rung 3
  > (line 25, revision subgoal 1). Nothing calls it yet; that is goal 8.
- [x] Switch Step 1 of `/step` and `/hitl-step` to the script
  > **Q:** What happens to `agents/plan-locator.md` once Step 1 runs the script: delete
  > it, keep it unused, or defer the decision to goal 10?
  > **A:** Delete it. Nothing shipped calls it, git history keeps it, and goal 10 builds
  > its variant that wraps the script on a scratch copy. The plugin's self-descriptions
  > ("an agent") are reverted with it.
  - [x] Run it through `Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*)`; on
        `error`, relay `problem:` and `fix:` to the user and stop; keep the `next:`
        check, which now guards against the file changing between the script and the
        edit; lockstep diff empty
    > **Note:** the new Step 1 handles the five outcomes:
    > - `found`: state it and show the warnings;
    > - `ask`: re-run with the chosen path;
    > - `none`: stop;
    > - exit 1 `error`: relay each `problem:` with its `fix:`, and stop without working
    >   around it;
    > - exit 2, another status, or no `result:` line: stop, as a failed spawn did.
    >
    > A goal the user names out of order is now `Grep`ped by the command and passed as
    > `--goal <line>`. A `per-goal` plan stops with "not yet supported", because no
    > command edits goal files before revision subgoal 2. A `next:` mismatch re-runs the
    > script once before stopping. `allowed-tools` drops `Agent` and
    > `Bash(git branch --show-current:*)`, since the script reads the branch itself.
    > The body runs the path unquoted, as `/open-revision` does, so it matches its
    > `allowed-tools` pattern; goal 9's headless runs test exactly that. Sizes:
    > `hitl-step.md` 16,533 → 16,813 bytes and `step.md` 7,824 → 8,103. The text is a
    > little longer than the spawn version because it now has two halting outcomes.
    > The lockstep diff is empty.
  - [x] Decide the fate of `agents/plan-locator.md` (deleted, or kept for work that needs
        judgement)
    > **Note:** deleted with `git rm`, which also removes the empty `agents/` directory.
    > The plugin's "commands, an agent, hooks, and scripts" in `plugin.json` and the
    > README became "commands, hooks, and scripts". The README's `agents/` entry is
    > gone, and its `scripts/` entry now counts four plan scripts, `locate-plan.sh` first.
  - [x] Update the plugin's `CLAUDE.md`, the working plan's §4.1 table, and the R1
        subgoal's wording in `docs/plan/TODO.md`
    > **Note:** the plugin's `CLAUDE.md` (38,827 → 39,375 bytes):
    > - "Why resolution is an agent" became "Why resolution is a script", recording why
    >   the agent was replaced, the 16-key report as the interface, and `error` as a
    >   halt the command relays;
    > - the command list, the rung-list intro, the status-stamp parties, the lockstep
    >   bullet and the script-backed-commands bullet name the script; the last now
    >   lists six commands.
    >
    > The master plan: the R1 preamble now gives resolution to a script and drafting to
    > `plan-drafter`, and subgoals 1 and 3 name the script. The working plan (untracked):
    > - the §4.1 row is replaced, and a dated "Changed" paragraph says why;
    > - every place where the agent resolved now names the script (§4.2, §4.3's guide
    >   list, §4.4's flush, the command-delta rows, D5, R1 steps 1 and 3, §7.7);
    > - the historical mentions and the `feat/plan-locator` examples are left alone.
  > **Done:** Step 1 of both commands runs `scripts/locate-plan.sh`, the agent is
  > deleted, and every description of the plugin, the master plan and the working plan
  > says so. Checks: `claude plugin validate` passes with its pre-existing advisory
  > items only; no file in the plugin names the agent; the 64-case suite passes on the
  > shipped script. The rewritten commands themselves are untested until goal 9.
- [x] Re-run the command cases (c18–c20, headless) against the script version, so the
      Step 1 that ships is the one that was tested
  > **Note:** run against `suite/wc-script`, a fresh copy of the committed tree, with
  > `probe-grade.py` in a new `MODE=script` mode. That mode requires a `locate-plan.sh`
  > call, no `Agent` spawn, no agent transcript and no `permission_denials`. Run against
  > the agent-version run `out-a`, it failed all three cases on all three counts.
  > **Result:** runs `g9a` and `g9b`, 6 sessions, 0 pass. Resolution was right in all 6:
  > - the plan, the rung and the `next:` line (10, 2,487, 8);
  > - the line confirmed within Step 2's read, with only a 19-line window on the 2,498-line
  >   master plan;
  > - no edits and no spawn.
  >
  > The unquoted `${CLAUDE_PLUGIN_ROOT}` invocation does match `allowed-tools`. But every
  > first call was `locate-plan.sh … --; echo "exit=$?"`, which the harness rejected
  > ("contains multiple operations … requires approval: echo"), and the model then retried
  > without the echo. Headless, that is a wasted turn; interactively it would be a
  > permission prompt on every run.
  > **Note:** the cause is Step 1's "act on the exit status". The Bash tool shows an exit
  > code only when it is non-zero, so the model echoed it to see it. The exit code is also
  > redundant for the command: `result:` already tells 0 (`found`/`ask`/`none`) from 1
  > (`error`), and no `result:` line means 2 or a crash. The exit codes serve hooks, CI
  > and other scripts.
  > **Note:** sessions took 14–27 s, against 20–34 s for the agent version, despite the
  > wasted turn. Cost was $0.06–0.07 on `g9b`; `g9a`'s $0.21–0.26 is the first run on a
  > new plugin copy, with the cache not yet written. Both used 4 turns, the same as the
  > agent version.
  > **Q:** How should Step 1 change: key on `result:` alone and say "run it alone"; keep
  > the exit status and explain how the tool shows it; or allow-list `echo`?
  > **A:** Key on `result:`, and say to run it alone with nothing appended. The exit
  > codes stay in the script and its spec for hooks and CI. Then re-run c18–c20 twice
  > (`g9c`, `g9d`).
  > **Result:** after the fix, runs `g9c` and `g9d` pass 6 of 6 on every check:
  > - one `locate-plan.sh` call per case, no permission denial, no spawn;
  > - the right plan, rung and `next:` line, confirmed within Step 2's read (19 lines of
  >   the 2,498-line master plan);
  > - no edits.
  >
  > | Step 1 | calls per case | turns | session |
  > |---|---|---|---|
  > | agent (`a`, `b`) | 1 spawn | 4 | 19.7–33.7 s |
  > | script, first text (`g9a`, `g9b`) | 2, 1 denied | 4 | 14.1–26.7 s |
  > | script, fixed (`g9c`, `g9d`) | 1 | 3 | 12.2–19.0 s |
  >
  > Cost per session ran $0.05–0.25 for the same case and follows whether the prompt
  > cache was warm (the command text changed between runs), so it is not compared here.
  > **Done:** the Step 1 that ships is the tested one. The first runs found that
  > "act on the exit status" made the model chain an `echo` that `allowed-tools` cannot
  > match. Step 1 now keys on `result:` and says to run the script alone, with nothing
  > appended. Both commands were changed, the lockstep diff is empty, and two runs pass
  > 6 of 6, one turn shorter than the agent version.
- [~] Measure the alternative split: a subagent that runs the script, reads its
      diagnostics, re-runs it with corrected inputs where it can, and returns a clean
      result, against goals 6–9's split, where the parent troubleshoots
  > **Note:** proposed by the user as a possible general principle of agentic
  > development: pair a script with a specialised subagent, so that determinism is the
  > default and an LLM's flexibility is kept for troubleshooting. Goals 6–9 keep the
  > troubleshooting in the parent; this keeps it in the subagent. Neither is assumed
  > better; measure both. Two constraints carry over. The subagent stays read-only, so
  > its "corrected inputs" are re-parameterisations (another model, an explicit path),
  > never edits, and anything only a human can settle (which duplicate is stale) still
  > goes back as `ask` or `error`. And the parent must still be able to vet the result,
  > so the subagent returns the exact script invocation it settled on together with its
  > raw output. The parent can then re-run that one command and compare, deterministically
  > and cheaply.
  > **Q:** (asked before this goal started) Should the troubleshooting subagent run on
  > Haiku or Sonnet, and how are failures produced, now that the script passes every case?
  > **A:** The subagent is always on, as the goal says, and runs the script on every Step 1.
  > Any model can launch the script; the model should matter only in failure mode, where
  > Sonnet is expected to troubleshoot better. Measure both models rather than assume it.
  > **Note:** an agent has one model, fixed before the spawn, and the parent cannot know in
  > advance whether a run will fail, so each arm runs one model on both paths. The
  > hypothesis predicts equal correctness on the happy path, with a difference in time and
  > tokens only (the plan-locator agent's median was 6.6 s on Haiku, 10.6 s on Sonnet),
  > and a difference in quality in failure mode.
  - [x] Probe Bash scoping in a plugin agent first: does `tools: Bash(<pattern>)` block a
        command outside the pattern? That decides whether the wrapper is read-only by
        enforcement or only by its body's rule
    > **Note:** the probe ran in the scratchpad (`suite/wc-scope`, `scope-run.sh`, results
    > in `out-scope/`). Two Haiku agents had identical bodies, each running the script,
    > `git log -1` and `date`, one call apiece:
    > - `scope-a` had `tools: Bash(git log:*), Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*)`;
    > - `scope-b` had `tools: Bash`.
    >
    > The session's `--allowedTools` permitted all three commands and `Agent`, so the
    > only thing that could block `date` was the agent's `tools:` field.
    > **Result:** not enforced. `scope-a` ran `date`, and its tool result is real output,
    > the same as `scope-b`'s. A Bash pattern in a plugin agent's `tools:` grants the
    > whole Bash tool, so the wrapper arms get plain `Bash`. Their read-only property
    > rests on two things: the body's rule, and the parent re-running and checking every
    > command the agent reports. The honesty measure therefore doubles as the arms'
    > safety check. In an interactive session, the permission prompt on a command not
    > allowed would also stand as a second gate, but nothing here relies on it.
    > **Note:** `${CLAUDE_PLUGIN_ROOT}` does expand in an agent body: both agents issued
    > the absolute path. The `CANARY` in both replies came from the main session, which
    > loads the fixture's `CLAUDE.md`; it appears in no agent tool result, as in goal 2.
  - [x] Build `agents/plan-resolver.md` on a scratch plugin copy, not the shipped tree.
        One body, in two copies that differ only in `model:` (haiku, sonnet), plus a
        Step 1 that spawns it. It runs the script and passes a clean report through
        verbatim. On `error` or a missing `result:` it troubleshoots, read-only. It
        returns the exact invocations it ran, with their raw output
    > **Q:** When does the parent vet the wrapper by re-running its invocation: always,
    > only on failure, or both, as separate arms? Vetting always means the parent runs
    > the script anyway, so on the happy path the subagent adds a spawn and saves
    > nothing.
    > **A:** Always. That is the strictest reading of "the orchestrator vets all subagent
    > work". The trial then measures the wrapper's pure cost on the happy path, and its
    > value in failure mode only.
    > **Note:** two rules in the drafted body keep over-reach measurable rather than
    > silent. A corrected invocation the agent tests comes back as a `suggested:` line,
    > never as the result, and only the user can adopt it. `also-ran:` lists every other
    > command it ran, since `tools: Bash` cannot be scoped (subgoal 1).
    > **Note:** built in the scratchpad by `build-resolver.py`, as `suite/wc-resolver-haiku`
    > and `suite/wc-resolver-sonnet`. Each holds:
    > - `agents/plan-resolver.md` (body 2,085 characters), the two copies differing only
    >   in `model:`;
    > - the variant Step 1 in `/hitl-step` and `/step`, lockstep diff empty;
    > - `commands/probe-resolver.md`, which runs that Step 1 alone, so the resolution
    >   cases do not go on to execute a fixture's goals.
    >
    > Both validators pass; `validate-agent.sh`'s one warning is the expected prose-trigger
    > one. `resolver-run.sh` runs cases per arm. It leaves out e12/e12b, since a bad
    > `--goal` line is the parent's own mistake.
    > **Result:** smoke test, c03 and e07 on each arm. On all four sessions the spawn ran
    > on the intended model, a clean report came back verbatim, the parent's re-run
    > printed `vetting: match`, and both fixtures were clean afterwards. On e07:
    > - Haiku found the evidence that is in the files (only `_DO.md`, index line 7), but
    >   both its `git log` calls were denied, so it cited no commit. It said so honestly
    >   and left the choice of fix to the user.
    > - Sonnet ran plain `git log --stat`, found `_TODO.md` was never committed, and so
    >   replaced the script's "restore it" (impossible here) with "create it". That is a
    >   better fix than the script's own.
    > - Neither noticed the likelier real fix, `git mv _DO.md _TODO.md`: the revision's
    >   plan exists, written under the other model.
    >
    > Sessions took 21.6–31.4 s; cost is not compared (cache).
    > **Note:** two launch problems came up, both in the body's instructions rather than
    > in either model:
    > - `Glob` was "not available in this session … find files with `find` via the Bash
    >   tool", although the agent's `tools:` lists it. `plan-locator`, which had no Bash,
    >   could use `Glob`, so having Bash in the list may withhold it. That is unverified.
    > - Command form decides what is permitted: `git log …` ran, but `git -C <path> log …`
    >   and `…; git status` were denied. The body's "alone" rule covers only the script
    >   call.
    > **Q:** Apply an arm-neutral fix to the body (`find` in place of `Glob`; every
    > investigation command alone, no `git -C`, nothing chained), rebuild both copies,
    > and re-run the smoke test? Or run the trial as it is?
    > **A:** Fix and re-run the smoke test. The smoke test exists to fix launch problems
    > before measuring, as goal 2 did with `plan-locator`.
    > **Result:** `smoke2`, on the fixed body (2,254 characters; `tools: Bash, Read, Grep`).
    > All four sessions show 0 denials, no "tool not available" errors, `vetting: match`,
    > and clean fixtures, and c03 is unchanged. On e07 the arms now agree:
    >
    > | e07 | commands | denials | finding | fix |
    > |---|---|---|---|---|
    > | Haiku v1 | 5 | 2 | only `_DO.md`; history unknown | restore once found, or close |
    > | Haiku v2 | 6 | 0 | `_TODO.md` never committed | create it, or close |
    > | Sonnet v1 | 3 | 0 | never committed | create it, or close |
    > | Sonnet v2 | 4 | 0 | never committed | create it, or close |
    >
    > The v1 gap between the models on e07 came from the environment, not the
    > troubleshooting. That is one case, not a conclusion, and the trial tests it.
    > **Note:** neither arm ran `Grep`, so whether it is delivered alongside `Bash` is
    > still unknown. Neither proposed `git mv _DO.md _TODO.md` either. The grading in
    > subgoal 4 must define each case's correct fix in advance, from the fixture, or an
    > arm's plausible fix gets credited by default.
    > **Note:** the first-version copies are kept as `suite/wc-resolver-{haiku,sonnet}.v1`,
    > their runs as `out-r-*-smoke`.
  - [ ] Inputs:
        - the 20 suite cases (the script succeeds);
        - the 18 E-cases in `fx-diag` (the script reports `error`; no mocks);
        - faults injected through the real call path, in the scratch copy only: `chmod
          000` on a plan (exit 2), a `PATH` without `awk` (exit 127), a truncated report,
          and a mutant that returns a wrong plan in a well-formed report
  - [ ] Run three arms: the baseline (the parent runs the script, as shipped),
        wrapper-haiku and wrapper-sonnet. Compare them on:
        - correct results;
        - time, and main-session tokens;
        - fix quality, graded by applying each arm's suggested fix to a throwaway clone of
          the fixture and re-running the script (the baseline is the script's own `fix:`);
        - honesty, with the parent re-running each returned invocation and comparing;
        - over-reach: "fixing" E1 with a similar-looking path, or accepting the mutant's
          plan, counts as a failure
  - [ ] Decide on the evidence: ship the baseline or one of the wrapper arms, and record
        why
