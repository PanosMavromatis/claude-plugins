# 01 — Run every scenario that reaches a pointer

**Goal**: [~]

- [x] `check.py` fails any session that reads or searches the plugin copy's directory from the shell (`grep`, `rg`, `find`, `ls`, `cat`, `head` or `sed` on a path under it), where today it only prints commands starting `grep`, `rg` or `find`; and it names each session that `Read` `smart-commit.md`
  > **Note:** Tested on run r11's recorded sessions (`RUN=r11 check.py e1 e3 e4`): the new check fails exactly e1-merge and e4-merge, whose `grep -n … smart-commit.md` the README's r11 entry records, and passes the other ten sessions; every session that commits (e1, e3, e4 and the three merges) `Read`s `smart-commit.md` before its first commit, so that half is a check, not a list. `common()` computes the call indices inline: the scenarios run at module level between the definitions, so `at()` and `ran()`, defined below it, do not exist yet when it runs.
- [ ] A run of every scenario whose sessions commit, and so reach a pointer (e1, e3 and e4 with their merge sessions, m1, m2, c1 and c2; m3, c3 and e5 never commit), passes every `check.py` check: the user runs it
- [ ] In that run, every session that commits `Read`s `smart-commit.md`, and none reads or searches the plugin's directory from the shell
