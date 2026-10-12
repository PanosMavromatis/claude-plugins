# 01 — Move the export script into the plugin, with a suite

**Goal**: [~]

- [x] `plugins/workflow-coding/scripts/export-session.py` starts from `tmp/export_session.py`, keeps its output form, and takes the log and the output path as arguments
  > **Note:** Ported with four changes: a header for the plugin, a usage error that exits 2 as the plugin's scripts do, UTF-8 named on both read and write, and closed file handles. On a snapshot of a real 15 MB log (125 operator messages, 281 replies, 4 compactions) its output is byte-identical to `tmp/export_session.py`'s. Under `LC_ALL=en_US.ISO8859-1` the original crashes encoding its own header's em dash, while the port writes each em dash once, with no mojibake: the case subgoal 3 needs, since a UTF-8 locale cannot tell them apart. Pyright flags `b.get` where a content block might be a string; that is unchanged from the original, since logs hold dicts.
- [ ] A suite under `dev/export-session/`, in the shape of the other `dev/` suites, renders fixture logs with no model and checks the output
- [ ] Cases for the three defects fixed on 2026-10-11: an em dash is encoded once, the `/compact` instructions are captured, and the title comes from the output filename
