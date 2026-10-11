#!/usr/bin/env bash
# Propose where a new branch's plan goes, what its files are called, and where its backlink
# is inserted, for /new-branch to write.
#
# Placement is a set of rules, so a script decides it and the command writes exactly what
# the script lists. The root plan decides the layout: a `**Layout**: revisions` index gets
# per-goal plans, inside the open revision's directory for a subgoal of it, flat for a
# standalone branch; a legacy master plan, or none, keeps today's flat single file. Goal
# files are named by the slug rule locate-plan.sh reads them by, from lib/plan-rules.sh,
# which both scripts source, so the writer and the reader cannot disagree.
#
# The contract is per-goal-layout-spec.md in the feat-per-goal-layout branch plan (found
# by name under docs/plan/, like any plan).
#
# READ-ONLY. Writes nothing, and never reads the current branch: /new-branch runs it before
# `git checkout -b`, so a refused name costs nothing. Of git it runs only
# `rev-parse --show-toplevel`, and the reads locate-plan.sh's E7 makes. Deterministic, no
# clock (the command writes the date), Bash 3.2.
#
# Usage: propose-branch-plan.sh <TODO.md|DO.md> <branch> [--subgoal <file>:<line> | --standalone]
#                               [--] [title]...
#        The titles are the plan's goals, in order (the Scope items); per-goal needs one.
# Exit:  0 = report, result propose or ask. 1 = report, result error.
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=propose-branch-plan.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> <branch> [--subgoal <file>:<line> | --standalone] [--] [title]..." >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

MODEL=""; BRANCH=""; NPOS=0; SUBGOAL=""; STANDALONE=0; TITLES=""; NT=0
pos() {
  NPOS=$((NPOS + 1))
  case $NPOS in
    1) MODEL="$1" ;;
    2) BRANCH="$1" ;;
    *) case "$1" in
         *"$NL"*|*"$TAB"*) usage "a title cannot hold a newline or a tab" ;;
       esac
       TITLES="${TITLES:+$TITLES$NL}$1"; NT=$((NT + 1)) ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
    --subgoal)
      [ $# -ge 2 ] || usage "--subgoal needs <file>:<line>"
      case "$2" in *:*[!0-9]*|*:|:*) usage "--subgoal takes <file>:<line>, got '$2'" ;; *:*) ;; *) usage "--subgoal takes <file>:<line>, got '$2'" ;; esac
      SUBGOAL="$2"; shift 2 ;;
    --standalone) STANDALONE=1; shift ;;
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
if [ -n "$SUBGOAL" ] && [ $STANDALONE -eq 1 ]; then usage "--subgoal and --standalone exclude each other"; fi
ROOT_PLAN="$PD/$MODEL"
FLAT="$(printf '%s' "$BRANCH" | awk '{ gsub(/\//, "-"); printf "%s", $0 }')" || die "awk failed flattening the branch name"
GSTEM="${MODEL%.md}"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_LAYOUT=""; R_REV=""; R_SUB=""; R_DIR=""; R_INDEX=""; R_GOALS=""; R_BACK=""
R_CAND=""; R_WARN=""; R_PROB=""; R_FIX=""; R_MSG=""; VIOL=0

finish() {
  emit result "$R_RESULT";     emit layout "$R_LAYOUT";   emit revision "$R_REV"
  emit subgoal "$R_SUB";       emit dir "$R_DIR";         emit index "$R_INDEX"
  emit goals "$R_GOALS";       emit backlink "$R_BACK";   emit candidates "$R_CAND"
  emit warnings "$R_WARN";     emit problem "$R_PROB";    emit fix "$R_FIX"
  emit message "$R_MSG"
  if [ "$R_RESULT" = error ]; then exit 1; fi
  exit 0
}

fail() {  # fail <rung>: report every violation so far; the rung is the library's, unused
  R_RESULT=error; R_REV=""; R_SUB=""; R_DIR=""; R_INDEX=""; R_GOALS=""; R_BACK=""; R_CAND=""
  if [ "$VIOL" -eq 1 ]; then R_MSG="No plan can be proposed for $BRANCH; see problem and fix."
  else R_MSG="No plan can be proposed for $BRANCH: $VIOL problems; see problem and fix."; fi
  finish
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

# --- the name: no plan directory may carry it already ------------------------------

scan_dirs
if [ -d "$PD" ]; then
  taken="$(find "$PD" -type d -name "$FLAT")" || die "find failed looking for $FLAT under $PD"
  if [ -n "$taken" ]; then
    taken="$(printf '%s\n' "$taken" | sort)" || die "sort failed"
    IFS="$NL"
    for d in $taken; do
      if [ -f "$d/$MODEL" ] || [ -f "$d/$OTHER" ]; then
        p="$d/$MODEL"; [ -f "$p" ] || p="$d/$OTHER"
        violation "a plan named $FLAT already exists: $p" \
          "branch $BRANCH has been planned before: resume that plan, or pick another branch name (a second $FLAT/ would be a stale copy to every command that finds plans by name)"
      else
        violation "$d/ already exists, and holds no plan" \
          "pick another branch name, or remove $d/ if nothing in it is wanted (your call)"
      fi
    done
    unset IFS
    fail ""
  fi
fi

# --- the layout, and the master files a subgoal can come from ----------------------

master_files ""
case "$MLAYOUT" in
  revisions) R_LAYOUT=per-goal ;;
  legacy)    R_LAYOUT=legacy ;;
  none)      R_LAYOUT=legacy
             if [ -f "$PD/$OTHER" ]; then
               warn "there is no $ROOT_PLAN, but $PD/$OTHER exists: the master plan uses the other model, so this plan will not be backlinked to it"
             fi ;;
esac
master_items ""

# --- the subgoal ----------------------------------------------------------------------

SEL=""
if [ -n "$SUBGOAL" ]; then
  sf="${SUBGOAL%:*}"; sl="${SUBGOAL##*:}"; sl=$((10#$sl))
  case "$NL$MASTERS$NL" in
    *"$NL$sf$NL"*) ;;
    *) if [ -z "$MASTERS" ]; then
         violation "--subgoal names $sf, but there is no master plan to take a subgoal from" "pass --standalone"
       else
         violation "--subgoal names $sf, which is not $( [ "$R_LAYOUT" = per-goal ] && echo "an open revision's _$MODEL" || echo "the master plan" )" \
           "name a line in one of: $(printf '%s' "$MASTERS" | awk 'BEGIN { ORS = "" } { print (NR == 1 ? "" : ", ") $0 }')"
       fi
       fail "" ;;
  esac
  IFS="$NL"
  for rec in $ITEMS; do
    f="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
    if [ "$f" = "$sf" ] && [ "$n" = "$sl" ]; then SEL="$rec"; fi
  done
  unset IFS
  if [ -z "$SEL" ]; then
    violation "$sf:$sl is not a subgoal: no item line starts there" "pass the line of an indent-0 item in $sf"
    fail ""
  fi
  rest="${SEL#*"$TAB"}"; rest="${rest#*"$TAB"}"; mk="${rest%%"$TAB"*}"
  case "$mk" in
    ' '|'~') ;;
    *) violation "$sf:$sl is not open: its marker is [$mk]" "pass an open ([ ] or [~]) subgoal, or --standalone"; fail "" ;;
  esac
elif [ $STANDALONE -eq 0 ]; then
  IFS="$NL"
  for rec in $ITEMS; do
    f="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
    mk="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"; rest="${rest#*"$TAB"}"; br="${rest%%"$TAB"*}"
    rest="${rest#*"$TAB"}"; rest="${rest#*"$TAB"}"
    case "$mk" in ' '|'~') if [ -z "$br" ]; then R_CAND="${R_CAND:+$R_CAND$NL}$f:$n $rest"; fi ;; esac
  done
  unset IFS
  if [ -n "$R_CAND" ]; then
    R_RESULT=ask
    R_MSG="Choose the subgoal $BRANCH executes and pass it as --subgoal <file>:<line>, or pass --standalone."
    finish
  fi
  if [ "$R_LAYOUT" = per-goal ] && [ -z "$MASTERS" ]; then
    warn "no revision is open in $ROOT_PLAN, so the plan is standalone; to file it under a revision, open one first"
  elif [ -n "$MASTERS" ]; then
    warn "no open subgoal in $(printf '%s' "$MASTERS" | awk 'BEGIN { ORS = "" } { print (NR == 1 ? "" : ", ") $0 }') is without a branch, so the plan is standalone"
  fi
fi

# --- the proposal -------------------------------------------------------------------

if [ -n "$SEL" ]; then
  f="${SEL%%"$TAB"*}"; rest="${SEL#*"$TAB"}"; n="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  rest="${rest#*"$TAB"}"; last="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"; br="${rest%%"$TAB"*}"
  rest="${rest#*"$TAB"}"; head="${rest%%"$TAB"*}"; text="${rest#*"$TAB"}"
  R_SUB="$f:$n $text"; R_BACK="$f:$last"
  if [ -n "$br" ]; then warn "$f:$n already has a branch ($br): the subgoal may have been branched before"; fi
  if [ "$R_LAYOUT" = per-goal ]; then
    R_REV="$(basename "$(dirname "$f")")"
    R_DIR="$(dirname "$f")/$FLAT"
  else
    case "$head" in
      "## Subgoals — revision "*) R_REV="${head#"## Subgoals — revision "}"; R_REV="${R_REV%% *}" ;;
    esac
    R_DIR="$PD/$FLAT"
  fi
else
  R_SUB=standalone; R_DIR="$PD/$FLAT"
fi
R_INDEX="$R_DIR/$MODEL"

if [ "$R_LAYOUT" = per-goal ]; then
  if [ "$NT" -eq 0 ]; then
    violation "no goal titles were given, and a per-goal plan needs at least one" "pass the Scope items as titles, after --"
    fail ""
  fi
  out="$(TITLES="$TITLES" GD="$R_DIR/$GSTEM" awk "$SLUG_AWK"'
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
    BEGIN {
      n = split(ENVIRON["TITLES"], T, "\n"); w = length(n "") < 2 ? 2 : length(n "")
      for (i = 1; i <= n; i++) {
        t = trim(T[i]); if (t == "") { print "EMPTY\t" i; continue }
        id = sprintf("%0" w "d", i)
        print "GOAL\t" ENVIRON["GD"] "/" id "-" slug(t) ".md - [ ] " id " — " t
      }
    }' </dev/null)" || die "awk failed naming the goal files"
  IFS="$NL"
  for rec in $out; do
    case "$rec" in
      EMPTY*) violation "title ${rec#*"$TAB"} is empty" "drop it, or give it some text" ;;
      GOAL*)  R_GOALS="${R_GOALS:+$R_GOALS$NL}${rec#*"$TAB"}" ;;
    esac
  done
  unset IFS
  if [ "$VIOL" -gt 0 ]; then fail ""; fi
fi

R_RESULT=propose
# not `$( [ … ] && printf … )`: an assignment takes the status of its last substitution,
# so under set -e a false test there ends the script before it reports
back=""; if [ -n "$R_BACK" ]; then back=", and insert the backlink after $R_BACK"; fi
if [ "$R_LAYOUT" = per-goal ]; then R_MSG="Write $R_INDEX and its $NT goal files$back."
else R_MSG="Write $R_INDEX as a single-file plan$back."; fi
finish
