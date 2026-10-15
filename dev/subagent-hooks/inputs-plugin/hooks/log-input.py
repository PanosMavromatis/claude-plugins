#!/usr/bin/env python3
"""A fixture PreToolUse hook: append each input it receives, one JSON object a line, to
.hook-inputs.jsonl at the project root, and allow the call."""
import json, os, sys

raw = sys.stdin.read()
try:
    line = json.dumps(json.loads(raw))
except ValueError:
    line = json.dumps({"unparsed": raw})
with open(os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), ".hook-inputs.jsonl"), "a") as f:
    f.write(line + "\n")
sys.exit(0)
