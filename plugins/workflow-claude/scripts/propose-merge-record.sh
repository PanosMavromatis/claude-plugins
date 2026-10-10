#!/usr/bin/env bash
# Propose what /smart-merge writes to record a merge: the branch plan's status line to
# stamp, and the master-plan subgoal that backlinks the branch, with the line its
# `> **Done:**` goes after.
#
# Finding the backlink is a set of rules, so a script applies them and the command edits
# exactly what it lists. The master files are the ones /new-branch backlinks into, chosen
# by the same library function (master_files): the root plan when it is legacy, or each
# open revision's _<model> under a revisions index. A branch is matched as a whole
# `> **Branch:**` value inside an item's block, never as a substring and never in prose,
# so feat/x does not find feat/x-y's item. A miss is reported, never passed over: the
# plan's `**Subgoal**:` header says whether the branch is standalone or the backlink was
# lost.
#
# READ-ONLY. Writes nothing, and never reads the current branch or the clock: the command
# passes the branch and writes the date. Of git it runs only `rev-parse --show-toplevel`,
# and the reads locate-plan.sh's E7 makes. Deterministic, Bash 3.2.
#
# Usage: propose-merge-record.sh <TODO.md|DO.md> <branch> [--item <file>:<line>] [--] [plan]
#        <plan> is the branch plan /smart-merge's step 2 resolved (locate-plan.sh's plan:),
#        left out when the branch has none. --item chooses among duplicate backlinks.
# Exit:  0 = report, result propose, ask or none. 1 = report, result error.
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=propose-merge-record.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> <branch> [--item <file>:<line>] [--] [plan]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

MODEL=""; BRANCH=""; PLAN=""; NPOS=0; ITEM=""
pos() {
  NPOS=$((NPOS + 1))
  case $NPOS in
    1) MODEL="$1" ;;
    2) BRANCH="$1" ;;
    3) PLAN="$1" ;;
    *) usage "at most one plan path, got another: '$1'" ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
    --item)
      [ $# -ge 2 ] || usage "--item needs <file>:<line>"
      case "$2" in *:*[!0-9]*|*:|:*) usage "--item takes <file>:<line>, got '$2'" ;; *:*) ;; *) usage "--item takes <file>:<line>, got '$2'" ;; esac
      ITEM="$2"; shift 2 ;;
    --) shift; while [ $# -gt 0 ]; do pos "$1"; shift; done ;;
    -?*) usage "unknown option '$1'" ;;
    *) pos "$1"; shift ;;
  esac
done
case "$MODEL" in
  TODO.md) OTHER=DO.md ;;
  DO.md)   OTHER=TODO.md ;;
  '')      usage "no model given" ;;
  *)       usage "the model must be TODO.md or DO.md, got '$MODEL'" ;;
esac
[ -n "$BRANCH" ] || usage "no branch name given"
case "$BRANCH" in
  -*)               usage "a branch name cannot start with '-': '$BRANCH'" ;;
  *[[:space:]]*)    usage "a branch name cannot hold whitespace: '$BRANCH'" ;;
esac
case "$PLAN" in
  *"$NL"*|*"$TAB"*) usage "a plan path cannot hold a newline or a tab" ;;
esac
ROOT_PLAN="$PD/$MODEL"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_LAYOUT=""; R_MASTERS=""; R_STAMP=""; R_ITEM=""; R_AFTER=""; R_SUB=""
R_CAND=""; R_WARN=""; R_PROB=""; R_FIX=""; R_MSG=""; VIOL=0

finish() {
  emit result "$R_RESULT";     emit layout "$R_LAYOUT";   emit masters "$R_MASTERS"
  emit stamp "$R_STAMP";       emit item "$R_ITEM";       emit after "$R_AFTER"
  emit subgoal "$R_SUB";       emit candidates "$R_CAND"; emit warnings "$R_WARN"
  emit problem "$R_PROB";      emit fix "$R_FIX";         emit message "$R_MSG"
  if [ "$R_RESULT" = error ]; then exit 1; fi
  exit 0
}

fail() {  # fail <rung>: report every violation so far; the rung is the library's, unused
  R_RESULT=error; R_STAMP=""; R_ITEM=""; R_AFTER=""; R_CAND=""
  if [ "$VIOL" -eq 1 ]; then R_MSG="The merge of $BRANCH cannot be recorded; see problem and fix."
  else R_MSG="The merge of $BRANCH cannot be recorded: $VIOL problems; see problem and fix."; fi
  finish
}

joined() {  # a list, one per line, as "a, b, c"
  printf '%s' "$1" | awk 'BEGIN { ORS = "" } { print (NR == 1 ? "" : ", ") $0 }' || die "awk failed joining a list"
}

# --- the repository -------------------------------------------------------------

# As locate-plan.sh: only 128 means "not a repository"; any other failure is git's.
if ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then st=0; else st=$?; fi
if [ "$st" -eq 128 ] || { [ "$st" -eq 0 ] && [ -z "$ROOT" ]; }; then
  violation "the working directory is not inside a git repository" "run it from the repository"
  fail ""
elif [ "$st" -ne 0 ]; then
  die "git rev-parse --show-toplevel failed with status $st" "$st"
fi
cd "$ROOT" || die "cannot enter the repository root $ROOT"

# --- the branch plan: its status line, and the subgoal it says it executes -----------

if [ -n "$PLAN" ]; then
  case "$PLAN" in
    /*) violation "the plan path $PLAN is absolute" "pass it repository-relative, as locate-plan.sh reports it in plan:"; fail "" ;;
  esac
  if [ ! -f "$PLAN" ]; then
    violation "$PLAN is not a file" "pass the plan: path locate-plan.sh reported, or no plan if the branch has none"
    fail ""
  fi
  need_file "$PLAN" ""
  if [ "$(basename "$PLAN")" != "$MODEL" ]; then
    violation "$PLAN is not a $MODEL plan" "pass the model the plan was resolved with: $(basename "$PLAN")"
    fail ""
  fi
  # The first **Status** line anywhere, as status_of reads it, with its line number.
  out="$(awk '/^\*\*Status\*\*:/ { s = $0; sub(/[ \t\r]+$/, "", s); print NR "\t" s; exit }' "$PLAN")" \
    || die "awk failed reading the status of $PLAN"
  if [ -z "$out" ]; then
    violation "$PLAN has no **Status** line, so it cannot be stamped merged, and it would count as active for good" \
      "add \`**Status**: active\` under its title, then run this again"
    fail ""
  fi
  R_STAMP="$PLAN:${out%%"$TAB"*} ${out#*"$TAB"}"
  val="$(status_of "$PLAN")"
  case "$val" in
    merged*) warn "$PLAN is already stamped \`$val\`: the merge may be recorded already" ;;
  esac
  R_SUB="$(awk '/^\*\*Subgoal\*\*:/ { sub(/^\*\*Subgoal\*\*:[ \t]*/, ""); sub(/[ \t\r]+$/, ""); print; exit }' "$PLAN")" \
    || die "awk failed reading the subgoal of $PLAN"
fi

# --- the master files, and every item in them that backlinks the branch ---------------

master_files ""
case "$MLAYOUT" in
  revisions) R_LAYOUT=revisions
             if [ -z "$MASTERS" ]; then warn "no revision is open in $ROOT_PLAN, so there is no subgoal to close"; fi ;;
  legacy)    R_LAYOUT=legacy ;;
  none)      if [ -f "$PD/$OTHER" ]; then
               warn "there is no $ROOT_PLAN, but $PD/$OTHER exists: the master plan uses the other model, so no subgoal is closed in it"
             fi ;;
esac
R_MASTERS="$MASTERS"
master_items ""

# Hits: "<file>\t<line>\t<marker>\t<last>\t<text>", for items whose branches hold this one whole.
HITS=""
IFS="$NL"
for rec in $ITEMS; do
  f="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  mk="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"; last="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  br="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"; text="${rest#*"$TAB"}"
  case " $br " in
    *" $BRANCH "*) HITS="${HITS:+$HITS$NL}$f$TAB$n$TAB$mk$TAB$last$TAB$text" ;;
  esac
done
unset IFS
NH="$(count_items "$HITS")"

cands() {  # every hit as "<file>:<line> <text>"
  local rec f n rest IFS="$NL"
  for rec in $HITS; do
    f="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
    rest="${rest#*"$TAB"}"; rest="${rest#*"$TAB"}"; rest="${rest#*"$TAB"}"
    printf '%s:%s %s\n' "$f" "$n" "$rest"
  done
}

SEL=""
if [ -n "$ITEM" ]; then
  sf="${ITEM%:*}"; sl="${ITEM##*:}"; sl=$((10#$sl))
  IFS="$NL"
  for rec in $HITS; do
    f="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
    if [ "$f" = "$sf" ] && [ "$n" = "$sl" ]; then SEL="$rec"; fi
  done
  unset IFS
  if [ -z "$SEL" ]; then
    if [ "$NH" -eq 0 ]; then
      violation "--item names $sf:$sl, but no item backlinks $BRANCH" "run it again without --item"
    else
      violation "--item names $sf:$sl, which is not an item that backlinks $BRANCH" \
        "pass one of: $(joined "$(cands | awk '{ print $1 }')")"
    fi
    fail ""
  fi
elif [ "$NH" -eq 1 ]; then
  SEL="$HITS"
elif [ "$NH" -gt 1 ]; then
  R_RESULT=ask; R_CAND="$(cands)"
  R_MSG="$NH items backlink $BRANCH, so one is a duplicate; choose the one to close and pass it as --item <file>:<line>."
  finish
fi

# --- the proposal -------------------------------------------------------------------

if [ -n "$SEL" ]; then
  f="${SEL%%"$TAB"*}"; rest="${SEL#*"$TAB"}"; n="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  mk="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"; last="${rest%%"$TAB"*}"; text="${rest#*"$TAB"}"
  R_ITEM="$f:$n $text"; R_AFTER="$f:$last"
  case "$mk" in
    x|-) warn "$f:$n is already closed ([$mk]): the merge may be recorded already" ;;
  esac
  if [ "$R_SUB" = standalone ]; then
    warn "$PLAN says the branch is standalone, but $f:$n backlinks $BRANCH"
  fi
elif [ -n "$PLAN" ] && [ "$R_SUB" != standalone ]; then
  # With no master file, the warning above (or the missing master plan) is the reason, and
  # nothing was lost; with some, the plan expected a backlink they do not hold.
  if [ -n "$MASTERS" ]; then
    where="no item in $(joined "$MASTERS") backlinks $BRANCH"
    if [ -n "$R_SUB" ]; then
      warn "$PLAN names the subgoal \`$R_SUB\`, but $where: the backlink was lost or misspelled"
    else
      warn "$PLAN has no **Subgoal** line to say whether it is standalone, and $where"
    fi
  elif [ "$MLAYOUT" = none ] && [ ! -f "$PD/$OTHER" ] && [ -n "$R_SUB" ]; then
    warn "$PLAN names the subgoal \`$R_SUB\`, but there is no master plan to close it in"
  fi
fi

if [ -z "$R_STAMP" ] && [ -z "$R_ITEM" ]; then
  R_RESULT=none
  R_MSG="Nothing to record: $BRANCH has no plan, and no item backlinks it."
  finish
fi
R_RESULT=propose
msg=""
if [ -n "$R_STAMP" ]; then msg="Stamp ${R_STAMP%% *} merged"; fi
if [ -n "$R_ITEM" ]; then
  close="lose ${R_ITEM%% *}, with the Done line after line ${R_AFTER##*:}"
  if [ -n "$msg" ]; then msg="$msg, and c$close"; else msg="C$close"; fi
elif [ "$R_SUB" = standalone ]; then
  msg="$msg; $BRANCH is standalone, so no subgoal is closed"
else
  msg="$msg; no subgoal is closed (see warnings)"
fi
R_MSG="$msg."
finish
