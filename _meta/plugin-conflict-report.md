# Plugin Conflict Report: `workflow-claude` vs. installed plugins

**Date:** 2026-06-25
**Scope:** All components of the `workflow-claude` plugin in this repo, checked against every plugin currently installed under the `claude-plugins-official` marketplace — with focus on `commit-commands` as requested.
**Status:** Living document. Originally written as a review-first report; the §8 reminder hook it recommended has since been implemented (`hooks/remind-disable-commit-commands.py` + a `SessionStart` stanza in `hooks/hooks.json`), and the §6 coexistence policy is now the project's documented stance. Kept in-tree as a deliberately shared rationale/warning for other developers (see §5). It is a **point-in-time snapshot of one author's environment** — the installed-plugin inventory and precedence layers below are illustrative, not a config to copy verbatim.

---

## 1. What was compared

### 1.0 How `workflow-claude` is invoked, and the intended coexistence policy

`workflow-claude` is **not** installed through a marketplace. It is loaded deliberately, per-project, via the CLI flag:

```
claude --plugin-dir <path-to>/workflow-claude
```

It is therefore active **only** in projects the user has explicitly designed to work with it — never globally, never by default. `commit-commands`, by contrast, is a marketplace plugin enabled globally in `~/.claude/settings.json` (`enabledPlugins["commit-commands@claude-plugins-official"] = true`).

**The user's chosen policy (current, not a future "full override"):**

- Keep `commit-commands` **enabled by default** in ordinary sessions — for projects that don't load `workflow-claude`, a minimal `/commit` is "better than nothing."
- **Disable `commit-commands`** whenever a session is launched with `--plugin-dir .../workflow-claude`, so the two never coexist and the silent-skip / duplicate-PR risks in §3 cannot fire.
- Defer making `workflow-claude` the global default (which would justify uninstalling `commit-commands` outright) to some later date.

This reframes the §3 conflicts: they are **real only in the window where both are simultaneously active**. The user's policy closes that window manually; §8 recommends a hook that makes the policy self-enforcing by reminding the user at launch if the window is open. Severities in §3/§7 are stated for the both-active case; under the policy, correctly applied, they are effectively neutralized.

### `workflow-claude` components (this repo)

| Type | Items |
|------|-------|
| Commands | `agents-docs-build`, `agents-docs-check`, `agents-docs-codex-init`, `agents-docs-init`, `agents-docs-update`, `hitl-step`, `new-branch`, `smart-commit`, `smart-merge`, `step` |
| Hooks | `PreToolUse` on `Write\|Edit\|MultiEdit` → `hooks/protect-agent-docs.py` |
| Scripts | `scripts/build-agents-md.sh`, `scripts/check-agents-md.sh` (invoked by commands, not auto-registered) |
| Skills / Agents / MCP | none |

### Installed plugins enumerated (marketplace `claude-plugins-official`)

`commit-commands`, `pyright-lsp`, `pr-review-toolkit`, `security-guidance`, `claude-code-setup`, `claude-md-management`, `skill-creator`, `feature-dev`, `explanatory-output-style`, `learning-output-style`, `ralph-loop`, `context7`, `github`, `code-simplifier`, `plugin-dev`.

`commit-commands` ships exactly three commands and **no hooks, skills, or agents**:

| Command | Behavior (summary) |
|---------|--------------------|
| `/commit` | Stage + create a single commit. Minimal, autonomous, one-shot. |
| `/commit-push-pr` | Branch-if-on-main + commit + push + `gh pr create`, all in one non-interactive message. |
| `/clean_gone` | Delete local branches marked `[gone]` and their worktrees. |

---

## 2. Headline finding

**There are no hard (name-level) command collisions.** The two plugins' command filenames are completely disjoint:

```
workflow-claude:   smart-commit  smart-merge  new-branch  step  hitl-step  agents-docs-*
commit-commands:   commit        commit-push-pr            clean_gone
```

Because Claude Code only forces `/<plugin>:<command>` disambiguation when **filenames** collide, every command from both plugins remains invocable by its bare name. Likewise, no other installed plugin shares a filename with `workflow-claude` (checked: `revise-claude-md`, `feature-dev`, `review-pr`, `create-plugin`, `cancel-ralph`/`help`/`ralph-loop`, plus skills `claude-md-improver`, `skill-creator`, `agent-development`, etc. — all distinct).

**The real conflict is semantic redundancy, not naming**, and it is concentrated entirely in `commit-commands`. Three `workflow-claude` commands functionally supersede the three `commit-commands` commands, but with the opposite operating philosophy. That mismatch is the substance of this report.

---

## 3. Conflicts with `commit-commands` (the focus)

### 3.1 `/smart-commit` ⟷ `/commit` — overlapping job, opposite philosophy

| Dimension | `/smart-commit` (workflow-claude) | `/commit` (commit-commands) |
|-----------|-----------------------------------|------------------------------|
| Doc sync | Delegates to `/workflow-claude:agents-docs-update` before committing | None |
| Version bump | Reads `VERSION`, syncs `package.json`/`pyproject.toml`, requires `CHANGELOG.md` section, creates annotated tag, pushes `--follow-tags` | None |
| Push | Yes (`git push --follow-tags`) | No |
| Style | Verbose, reports each step | **"Do not send any other text or messages besides these tool calls."** |

**Why this is a conflict, not just duplication:** the two commands both answer "make a commit," so whichever is invoked first wins — and they produce materially different repository states. If a user (or the model, reacting to the word "commit") triggers `/commit` when the curated pipeline was intended, the commit silently **skips doc-sync, version-manifest sync, the CHANGELOG gate, tagging, and the push**. There is no error; the omission is invisible. This is the highest-impact item in the report.

### 3.2 `/smart-merge` ⟷ `/commit-push-pr` — both own "open a PR," incompatibly

| Dimension | `/smart-merge` | `/commit-push-pr` |
|-----------|----------------|-------------------|
| Interaction model | Interactive; **confirm before every write** (push, PR create, merge, branch/doc delete) | Fully autonomous; **"MUST do all of the above in a single message"** |
| PR body source | `docs/git/<branch>.md` branch doc + thematically grouped commit log | Generated ad hoc from the diff |
| End state | Creates **and merges** the PR (`gh pr merge`), syncs local `main` | Creates the PR only; stops there |
| Branch creation | Assumes branch already exists (made by `/new-branch`) | Creates the branch itself if on `main` |

**Why this is a conflict:** they partition the same "branch → PR" surface differently and assume different upstream state. Used together they can **double up** — e.g. `/commit-push-pr` opens a PR, then `/smart-merge` (expecting to drive PR creation itself) opens a second one or operates on an unexpected branch. Their confirmation philosophies are also directly opposed (HITL-everything vs. one-shot-no-text), so mixing them in one session produces inconsistent, jarring UX. Critically, `/commit-push-pr` never consumes or deletes the `docs/git/<branch>.md` artifact, so the whole `new-branch → smart-merge` doc lifecycle is bypassed.

### 3.3 `/clean_gone` ⟷ `/smart-merge`'s `--delete-branch` — mild overlap, mostly complementary

`/smart-merge` deletes the merged branch inline (`gh pr merge --delete-branch`). `/clean_gone` sweeps *already-gone* local branches and their worktrees. These don't fight; `/clean_gone` is a reasonable post-merge janitor and *was* the **one `commit-commands` command with no `workflow-claude` equivalent**.

**Resolved (rec 6.3, shipped):** it has since been ported to `workflow-claude` as **`/clean-gone`** (`commands/clean-gone.md`) — adapted to this plugin's conventions rather than copied: a confirm-before-delete gate with a prominent ">1 branch" warning, real-name resolution instead of a placeholder pipeline, and a correctness fix (`git branch -vv`, since the original's `-v` does not actually surface `[gone]`). With this, `commit-commands` no longer holds any capability `workflow-claude` lacks, clearing the last blocker to the eventual uninstall in rec. 1.

### 3.4 Output-style tension (active right now)

`commit-commands`' `/commit` and `/commit-push-pr` both hard-instruct *"Do not send any other text or messages besides these tool calls."* That directly contradicts the currently-active **`explanatory-output-style`** (this session) and `learning-output-style`, both of which inject "always provide educational explanations." This isn't a `workflow-claude` defect, but it means the two `commit-commands` writes will behave inconsistently with the rest of your environment's narration contract.

---

## 4. Conflicts / interactions with other installed plugins

These are outside the `commit-commands` focus but surfaced during the sweep and are worth recording.

### 4.1 `security-guidance` hooks stack onto `smart-commit` / `smart-merge` (interaction, not a bug)

`security-guidance` registers `PostToolUse` hooks with `asyncRewake` on `Bash(git commit:*)` and `Bash(git push:*)` (plus `Stop`). Because hooks from all plugins **stack**, every `git commit`/`git push` that `smart-commit` and `smart-merge` run will trigger a background security review that re-wakes the agent mid-pipeline with findings. Expected consequence: extra review prompts interleaved into the commit/merge flow. Nothing breaks, but it's a behavioral surprise worth knowing; if it becomes noisy, it's a reason to scope or disable `security-guidance` during these workflows.

### 4.2 `workflow-claude` PreToolUse hook coexists cleanly with `security-guidance` PostToolUse

Both match `Write|Edit|MultiEdit`. They run at different phases (Pre vs. Post) and have non-overlapping jobs: `protect-agent-docs.py` *blocks* writes to sentinel-protected `CLAUDE.md`/`AGENTS.md`/`AGENTS.override.md`; `security_reminder_hook.py` *warns*. No mutual exclusion — they compose correctly. **No action needed.**

### 4.3 No collision with `pr-review-toolkit`, `github`, `feature-dev`, `claude-md-management`

- `pr-review-toolkit:/review-pr` is review-only; no overlap with commit/merge.
- `github` plugin is MCP/tooling, ships no colliding command files.
- `claude-md-management:/revise-claude-md` + skill `claude-md-improver` touch `CLAUDE.md`. In a *consuming* project that adopts the agent-docs convention, those edits to a protected `CLAUDE.md` would be **blocked by `workflow-claude`'s hook** when the sentinel is present — a potential future friction point in consumers, **not** in this repo (no sentinel layout here). Flagged for awareness only.

### 4.4 `dp-compile` composes with `workflow-claude` by layer, not by arrangement

**Added 2026-09-08.** `dp-compile` is a companion plugin, not a marketplace one — it guides
dynamic-programming algorithms through a staged translation and assumes `workflow-claude` is
present, delegating branches, plans, commits, merges and documentation rather than
reimplementing them. It is loaded the same three ways `workflow-claude` is (see §1.0), and
one of those — a plugin tree placed in a project's `.claude/skills/` — is how at least one
repository loads *this* plugin today.

**The two `PreToolUse` hooks cannot collide.** `workflow-claude`'s `protect-agent-docs.py`
matches `Write|Edit|MultiEdit`; `dp-compile`'s `pre-commit-check.py` matches `Bash`. No tool
call matches both, so there is no ordering question between them and no possibility of one
masking the other. This is a stronger property than §4.2's "they compose correctly" — those
two at least run on the same calls.

**`dp-compile`'s gate fires inside `/smart-commit`, and that is the design.** Hooks stack,
so the `git commit` that `/smart-commit` runs at its Step 4 triggers the gate exactly as a
hand-typed one would. The consequence is the one worth wanting: **delegating the commit does
not bypass the check.** `dp-compile` enforces deterministically through a hook and
`workflow-claude` orchestrates advisorily through commands, so the two occupy different
layers rather than competing for the same one.

The gate is scoped: it runs the consumer's build and test commands only when the staged set
touches a path that a `dp-compile.toml` `[phases]` template resolves to, and exits silently
otherwise. Three consequences for this plugin's commands:

- **`/agents-docs-update` runs first and changes the staged set** — it is `/smart-commit`'s
  Step 1 — so the gate sees the *final* staged set, which is the right one. It stages only
  documentation, never a kernel, so it cannot change the gate's decision. That holds only
  while it stays documentation-only; a future version staging anything else would move the
  gate's scoping decision without either plugin noticing.
- **The suite runs once per commit**, after the docs are staged and before the commit
  object exists. A blocked commit leaves the staged set intact, so re-running
  `/smart-commit` after a fix is the ordinary recovery.
- **`security-guidance`'s `PostToolUse` review is downstream of the gate.** If `dp-compile`
  blocks, no commit happens and no security review fires — correct ordering by construction
  rather than by arrangement.

**Two accepted costs, named so they are not mistaken for defects.**

- The hook matches `Bash` with no `if` filter and decides for itself whether the command is
  a commit, so it spawns one short-lived process per `Bash` tool call. That is deliberate:
  §3 of `dp-compile`'s own notes records that the two official plugins using the `if` field
  spell their patterns incompatibly, so at least one syntax matches nothing — and a matcher
  that matches nothing yields a hook that never fires and never says so.
- In a repository that loads `dp-compile` but has **no** `dp-compile.toml`, every commit
  prints one line saying the gate was skipped. That is the no-op-with-a-message rule working
  as intended — a silent skip would leave a repository ungated with nothing saying so — but
  it is a line on every commit, and worth expecting rather than diagnosing.

**Not verified:** the hook declares a 600-second timeout, and what Claude Code does when a
`PreToolUse` hook exceeds it — allow, block, or report — has not been measured here, and
there is no CLI that exercises hook runtime behaviour. A consumer whose suite approaches ten
minutes should establish that behaviour before relying on the gate, or point
`[commands].test` at a faster subset.

---

## 5. Note on the `_meta/` directory itself — and why it's tracked

Creating `_meta/` at the repo root is safe: Claude Code only interprets `commands/`, `skills/`, `agents/`, `hooks/`, and the manifest as plugin components, so `_meta/` will never be loaded as a command or hook. It is inert with respect to the plugin's runtime behaviour.

**This directory is intentionally version-controlled and shipped**, rather than gitignored. The reasoning:

- **Some of it is directly useful to end users** — e.g. `_meta/consumer-settings.template.json` is a ready-to-copy `.claude/settings.json` override for disabling `commit-commands` in a consuming project (see §6.1).
- **In the open-source spirit of an experimental plugin, the thought process is worth sharing.** This report is left in-tree as a worked rationale and a *warning*: a fellow developer evaluating `workflow-claude` — quite possibly with a denser, more complex Claude Code plugin setup than the author's — benefits from seeing exactly how it overlaps with the official `commit-commands` plugin, why the overlap is a silent-failure risk, and how it was resolved, before they hit it themselves.
- **It is environment-specific, so read it as a case study, not a recipe.** The installed-plugin inventory (§1) and the settings precedence layers (§8.2) describe *this author's* machine on the date above. Your plugin set, marketplaces, and managed/enterprise layers may differ; adapt the conclusions rather than copying paths or plugin lists verbatim. The one genuinely portable artifact is the §6.1 override (and its template file), which is keyed only on `commit-commands@*`.

No personal data is embedded here (paths use `~` / `<path-to>` placeholders), which is part of what makes it safe to publish. If a future maintainer prefers to keep this dev-only, gitignoring `_meta/` remains a one-line, behaviour-neutral change.

---

## 6. Recommendations

Ordered by impact. The core decision is **who owns the commit/PR surface.** Status as of this revision: rec. 1's reminder hook (§8) is **shipped**; the per-project `.claude/settings.json` override is **documented with a template** (`_meta/consumer-settings.template.json`) and applied per consuming project by the user; the `clean_gone` port (rec. 3 / §3.3) is **shipped** as `/clean-gone`; the full `commit-commands` uninstall remains **deferred** until `workflow-claude` is promoted to default — now with no functionality blocking it.

1. **Adopt the chosen coexistence policy and make it self-enforcing (see §8).** Per §1.0, the decision is *not* to uninstall `commit-commands` yet, but to keep it enabled globally and disable it per-session whenever `workflow-claude` is loaded. To execute that policy reliably:
   - **Disable `commit-commands` per-project, in version control.** In each project launched with `--plugin-dir .../workflow-claude`, add a **shared** `.claude/settings.json` (not `settings.local.json`) containing `{"enabledPlugins": {"commit-commands@claude-plugins-official": false}}`. Project settings override the global `true`, so the plugin is off exactly in the projects where `workflow-claude` is active, and the override travels with the repo. This is the durable form of the policy.
   - **SessionStart reminder hook (shipped, §8).** `hooks/remind-disable-commit-commands.py` is the backstop for any project where you haven't (yet) added that override — it nudges you at launch instead of letting both run silently, and self-silences once `commit-commands` is disabled.
   - **Later, when you promote `workflow-claude` to default:** uninstall `commit-commands` outright. Its one non-redundant command, `/clean_gone`, has already been ported as `/clean-gone` (§3.3, rec. 3 — done), so nothing is lost.

2. **Do NOT rename `workflow-claude` commands to match `commit-commands`.** The current disjoint naming is an asset — renaming `smart-commit` → `commit` would manufacture a *hard* collision and force disambiguation everywhere. Keep the distinct names.

3. **Absorb `clean_gone` into `workflow-claude`** — **done.** Ported as `/clean-gone` (`commands/clean-gone.md`), so the branch lifecycle is now self-contained (`new-branch` → `step`/`hitl-step` → `smart-commit` → `smart-merge` → `clean-gone`) and `commit-commands` can be removed without losing functionality. Adapted to plugin conventions (confirm-before-delete, `>1`-branch warning, no placeholders, `-vv` fix) rather than copied verbatim.

4. **Document the `security-guidance` interaction** (§4.1) — **done.** Added an "Interaction with `security-guidance`" subsection to the README: users running `smart-commit`/`smart-merge` with `security-guidance` installed should expect background security-review rewakes around commits and pushes. Informational; no code change.

5. **No hook changes required.** The `protect-agent-docs` ↔ `security-guidance` coexistence (§4.2) is correct as-is.

---

## 7. Summary table

| # | Conflict | With | Severity | Recommended action |
|---|----------|------|----------|--------------------|
| 3.1 | `smart-commit` vs `commit` — silent skip of doc-sync/version/tag/push | commit-commands | **High** *(only while both active)* | Per-project disable (§6.1) + §8 reminder hook |
| 3.2 | `smart-merge` vs `commit-push-pr` — duplicate PRs, opposite UX, bypassed branch-doc | commit-commands | **High** *(only while both active)* | Same as 3.1 |
| 3.3 | `clean_gone` vs `--delete-branch` | commit-commands | Low (complementary) | **Done** — ported as `/clean-gone`; commit-commands now fully replaceable |
| 3.4 | "no extra text" directive vs active explanatory style | commit-commands | Low | Resolved by removing commit-commands; else accept inconsistency |
| 4.1 | security review rewakes around `smart-commit`/`smart-merge` git ops | security-guidance | Info | **Done** — documented in README ("Interaction with `security-guidance`") |
| 4.2 | doc-protect (Pre) + security warn (Post) on Write/Edit | security-guidance | None | No action — composes correctly |
| 4.3 | `revise-claude-md` editing protected CLAUDE.md in consumers | claude-md-management | Info (future) | Awareness only; not present in this repo |

**Bottom line:** No naming conflicts anywhere. The only meaningful conflict is `commit-commands`, which is functionally redundant with — and behaviorally opposed to — `workflow-claude`'s commit/PR pipeline, but **only during the window where both are active simultaneously**. Because `workflow-claude` is loaded deliberately via `--plugin-dir` (§1.0), the user's policy is to keep `commit-commands` globally enabled but disable it whenever `workflow-claude` is loaded. The durable execution of that policy is a per-project `.claude/settings.json` override (§6.1); the safety net that makes it self-enforcing is the SessionStart reminder hook designed in §8.

---

## 8. Recommended mechanism: a SessionStart reminder hook

**Goal (restated from the request):** when a session is launched with `claude --plugin-dir .../workflow-claude` *and* `commit-commands` is still enabled, print a recommendation to disable it at launch. When `commit-commands` is already disabled, stay completely silent.

### 8.1 Why a SessionStart hook in `workflow-claude` is the right vehicle

- **Presence is the trigger.** The hook ships *inside* `workflow-claude`, so it executes **only** when `workflow-claude` is loaded — which happens **only** via `--plugin-dir`. The hook running at all *is* the "`--plugin-dir` was used" signal. No need to inspect the launch command, parse `argv`, or detect the flag — that information is implicit in the fact that the hook fired.
- **`SessionStart` fires once, at launch** — exactly "upon launch," matching the request. (This is the same event `explanatory-output-style` and `security-guidance` already use, so it's a proven channel in this environment.)
- **`systemMessage` is the user-facing output channel.** A `SessionStart` hook prints a JSON object on stdout; its top-level `systemMessage` field is rendered **directly to the user in the terminal** at launch (Claude Code shows it as `SessionStart:startup says: …`). The hook also sets `hookSpecificOutput.additionalContext` so the *model* learns to prefer the `/smart-*` commands. See §8.4 for why the other two candidate channels (`additionalContext` alone, and `stderr`+`exit 2`) do **not** reach an unprompted user.

### 8.2 What it must check, and where the truth lives

Enable/disable state is stored in `enabledPlugins` as `"commit-commands@<marketplace>": true|false`, and is **layered** with precedence **user < project < project-local**:

| Layer | Path | Role |
|-------|------|------|
| User (global) | `~/.claude/settings.json` | Where `commit-commands` is currently `true`. |
| Project (shared) | `<cwd>/.claude/settings.json` | The §6.1 per-project override (`false`) lives here. |
| Project (local) | `<cwd>/.claude/settings.local.json` | Personal, gitignored override. |

The hook must compute the **effective** value by merging these in order (last definition wins). If the key is absent from all layers, treat the plugin as enabled when it appears in `~/.claude/plugins/installed_plugins.json` (marketplace default is enabled). Match any key whose plugin part is `commit-commands` (i.e. `commit-commands@*`) so a different marketplace suffix still matches. Emit the reminder **iff** effective state is enabled.

### 8.3 Implementation (shipped)

This is now live in the plugin: one script plus one stanza. The code below is the as-shipped version.

**`hooks/remind-disable-commit-commands.py`** (mark executable: `chmod +x`):

```python
#!/usr/bin/env python3
"""SessionStart hook: if commit-commands is still enabled while workflow-claude
is loaded (i.e. this hook ran at all), recommend disabling it. Silent otherwise."""
import json, os, sys

PLUGIN = "commit-commands"  # match commit-commands@<any-marketplace>

def load(path):
    try:
        with open(os.path.expanduser(path)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

def enabled_in(settings):
    """Return True/False if any commit-commands@* key is set here, else None."""
    result = None
    for key, val in (settings.get("enabledPlugins") or {}).items():
        if key.split("@", 1)[0] == PLUGIN:
            result = bool(val)
    return result

def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()

    # Precedence: user < project < project-local. Last defined wins.
    effective = None
    for path in ("~/.claude/settings.json",
                 os.path.join(cwd, ".claude/settings.json"),
                 os.path.join(cwd, ".claude/settings.local.json")):
        v = enabled_in(load(path))
        if v is not None:
            effective = v

    # Absent everywhere: enabled iff installed (marketplace default = on).
    if effective is None:
        installed = load("~/.claude/plugins/installed_plugins.json").get("plugins", {})
        effective = any(k.split("@", 1)[0] == PLUGIN for k in installed)

    if not effective:
        sys.exit(0)  # already disabled — say nothing

    # "systemMessage" is shown directly to the user in the terminal at launch;
    # "additionalContext" is added to the model's context so it also prefers the
    # /smart-* commands. (stdout->additionalContext alone is invisible to an
    # unprompted user, and stderr+exit-2 is not surfaced by the tested CLI build.)
    user_msg = (
        "⚠️  workflow-claude is loaded, but commit-commands is still enabled. "
        "/smart-commit and /smart-merge supersede /commit and /commit-push-pr "
        "(the commit-commands versions skip doc-sync, version tagging, and the "
        "branch-doc PR flow). Disable it for this project by adding "
        "{\"enabledPlugins\": {\"commit-commands@claude-plugins-official\": false}} "
        "to ./.claude/settings.json (or toggle it off via /plugin). "
        "This reminder disappears once commit-commands is disabled."
    )
    print(json.dumps({
        "systemMessage": user_msg,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "commit-commands is enabled alongside "
                                 "workflow-claude. Prefer /smart-commit and "
                                 "/smart-merge over /commit and /commit-push-pr.",
        },
    }))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**`hooks/hooks.json`** — add a `SessionStart` array alongside the existing `PreToolUse`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/protect-agent-docs.py" }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/remind-disable-commit-commands.py" }
        ]
      }
    ]
  }
}
```

### 8.4 Properties and trade-offs

- **Self-silencing:** once you disable `commit-commands` (globally, per-project, or local), the hook detects the `false` and emits nothing — no recurring nag. This is the behavior you asked for.
- **Zero cost elsewhere:** in any project *not* launched with `--plugin-dir .../workflow-claude`, the hook doesn't exist, so it never runs and never touches normal sessions.
- **Reaches the user directly via `systemMessage`** — *the channel choice was settled empirically*, because two plausible alternatives turned out not to work for an unprompted user on the tested build (Claude Code v2.1.191):
  - `stdout` → `hookSpecificOutput.additionalContext` is **model-facing only**; it never prints to the terminal, so the user sees nothing unless the model happens to relay it on a later turn. (First attempt — silent.)
  - `stderr` + `exit 2` is documented as "shows stderr to user," but this build did **not** surface it at launch. (Second attempt — also silent, even though a filesystem-probe confirmed the hook *was* executing.)
  - `systemMessage` (a universal hook JSON field) **is** rendered to the user (`SessionStart:startup says: …`). (Third attempt — works.) `additionalContext` is kept alongside it purely to inform the model.
- **No marketplace coupling:** matching `commit-commands@*` keeps it working if the plugin is ever reinstalled from a different marketplace.
- **Manifest gotcha (resolved).** The plugin manifest must **not** declare `"hooks": "./hooks/hooks.json"` — Claude Code auto-loads the standard `hooks/hooks.json`, and pointing the manifest at that same path triggers a "Duplicate hooks file detected" error that fails the *entire* plugin load (commands included). `plugin.json` should omit the `hooks` key unless referencing *additional* hook files at non-standard paths. The script otherwise uses `${CLAUDE_PLUGIN_ROOT}` and a shebang exactly like `protect-agent-docs.py`.

> **Shipped & verified live:** `hooks/remind-disable-commit-commands.py` (executable) and the `SessionStart` stanza in `hooks/hooks.json` were confirmed firing on a real `claude --plugin-dir .../workflow-claude` launch in another project — the `systemMessage` banner printed at startup, and the hook self-silences once `commit-commands` is disabled. Unit-verified across three scenarios (enabled emits; per-project disabled silent; local-overrides-project precedence emits). The override template lives at `_meta/consumer-settings.template.json`; the README's "Installing & the `commit-commands` overlap" section documents the consumer-facing setup.
