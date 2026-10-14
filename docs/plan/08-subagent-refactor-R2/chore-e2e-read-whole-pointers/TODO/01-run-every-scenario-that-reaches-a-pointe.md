# 01 — Run every scenario that reaches a pointer

**Goal**: [ ]

- [ ] `check.py` fails any session that reads or searches the plugin copy's directory from the shell (`grep`, `rg`, `find`, `ls`, `cat`, `head` or `sed` on a path under it), where today it only prints commands starting `grep`, `rg` or `find`; and it names each session that `Read` `smart-commit.md`
- [ ] A run of every scenario whose sessions commit, and so reach a pointer (e1, e3 and e4 with their merge sessions, m1, m2, c1 and c2; m3, c3 and e5 never commit), passes every `check.py` check: the user runs it
- [ ] In that run, every session that commits `Read`s `smart-commit.md`, and none reads or searches the plugin's directory from the shell
