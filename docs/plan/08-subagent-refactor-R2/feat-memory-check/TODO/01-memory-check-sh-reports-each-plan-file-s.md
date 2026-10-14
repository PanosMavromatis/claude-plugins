# 01 — memory-check.sh reports each plan file's size and the totals

**Goal**: [ ]

- [ ] Run on this repository, `scripts/memory-check.sh` lists the open revision's plan files by size, each with bytes, words, lines and ≈ tokens (bytes / 4, labelled approximate)
- [ ] The report gives totals per branch and for the revision, and the layout it found; a legacy root is measured with `layout: legacy`, and a one-file branch plan is named `single-file`, as subgoal 3 names it
- [ ] Goal files are measured against a threshold, with a `warnings:` line for each one over it; files a script locates by line, such as a master plan, are reported but never warned on
- [ ] The script sources `scripts/lib/plan-rules.sh`, writes nothing, and gates nothing: its exit status never depends on a size
