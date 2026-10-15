#!/bin/sh
# Run one of this plugin's PreToolUse hooks so that it fails closed for this plugin's agents.
#
#   fail-closed.sh <hook>
#
# Claude Code blocks a tool call only when a hook exits 2. Any other status is a non-blocking
# error, and the call runs, so a hook that crashed, or whose python3 could not start (127),
# would let through every call it exists to refuse. This wrapper hands the hook its input and
# passes its exits 0 and 2 through. On any other, it refuses the call when the input names an
# agent the hooks guard: an agent_type starting `workflow-coding:`, or, while the test seam
# WORKFLOW_CODING_GUARDED_AGENTS is set, any agent_type. The main session's calls, which carry
# none, get the hook's own status back, so a broken hook never blocks the user.
#
# The input is matched with grep, not parsed: python3 may be what failed. JSON escapes every
# quote inside a string, so `"agent_type"` followed by a bare quote is a key, never text in a
# command. Every occurrence is matched, so none can hide another. If grep fails too, the call
# is refused.
input=$(cat)
printf '%s\n' "$input" | "$@"
status=$?
case $status in 0|2) exit "$status" ;; esac
agent='"workflow-coding:'
[ -n "${WORKFLOW_CODING_GUARDED_AGENTS+set}" ] && agent='"'
printf '%s\n' "$input" | grep -Eq "\"agent_type\"[[:space:]]*:[[:space:]]*$agent"
[ $? -eq 1 ] && exit "$status"
echo "Blocked: ${1##*/}, the hook that guards this plugin's agents, failed with exit $status, so the call is refused rather than let through unchecked. Check that python3 runs." >&2
exit 2
