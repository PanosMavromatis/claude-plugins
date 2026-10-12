# 02 — Sweep the other plan scripts and lib for early-exit readers

**Goal**: [ ]

- [ ] Inventory every pipe in `scripts/*.sh` and `scripts/lib/plan-rules.sh` whose reader can stop before EOF: an awk `exit` (single- or multi-line), `head`, `grep -q`/`-m`, `sed …q`, or `read` in an `if`/`while`
- [ ] Fix each with goal 01's pattern, or note why it is safe (a file argument, a here-string, or `exit` only in `END`)
- [ ] Name each script changed, for goal 04's large-input cases
