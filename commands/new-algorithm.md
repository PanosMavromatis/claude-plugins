---
description: "Scaffold a new algorithm and start Phase 0 (formalization)"
---

# /new-algorithm

Start the implementation of a new alignment algorithm.

## Behavior

1. Ask the user: "What algorithm do you want to implement? Give me the name and a brief description or reference."

2. Confirm the algorithm name. Convert it to `snake_case` for use as the directory name (e.g., "Smith-Waterman" becomes `smith_waterman`). Show the user the converted name and ask them to confirm.

3. Check if `src/tokalign/algorithms/<name>/` already exists.
   - If it does, ask the user: "A directory for `<name>` already exists. Is this a restart of a previous attempt, or a mistake?" If it's a restart, proceed. If it's a mistake, abort.
   - If it does not exist, proceed to step 4.

4. Hand off to the `algorithm-formalize` skill to guide the Phase 0 (pseudocode) implementation. **Use the `Skill` tool with `skill: "tokalign-dev:algorithm-formalize"`** — do NOT use `Read` on `skills/algorithm-formalize/SKILL.md`. Reading the file just dumps its contents into context; only the `Skill` tool activates the skill through the harness so it runs with its own references and examples. If the `Skill` tool reports the skill is not available, stop and tell the user: "The `algorithm-formalize` skill is missing — check that the plugin loaded correctly."

5. When Phase 0 is complete (formalization reviewed and approved), inform the user: "Phase 0 is done. When you're ready, run `/tokalign-dev:next-phase <name>` to start the Python prototype implementation."
