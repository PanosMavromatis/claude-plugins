# 01 — Move the export script into the plugin, with a suite

**Goal**: [ ]

- [ ] `plugins/workflow-coding/scripts/export-session.py` starts from `tmp/export_session.py`, keeps its output form, and takes the log and the output path as arguments
- [ ] A suite under `dev/export-session/`, in the shape of the other `dev/` suites, renders fixture logs with no model and checks the output
- [ ] Cases for the three defects fixed on 2026-10-11: an em dash is encoded once, the `/compact` instructions are captured, and the title comes from the output filename
