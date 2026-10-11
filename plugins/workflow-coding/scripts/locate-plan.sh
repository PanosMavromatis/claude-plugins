#!/usr/bin/env bash
# Resolve which plan file /step or /hitl-step works on, and what is next in it.
#
# Resolution is a set of rules, so a script runs it rather than a model: the same
# tree and arguments always give the same answer. Where the repository breaks a
# convention the rules rely on, the script neither guesses nor fails silently. It
# returns `result: error` with a `problem:` and a `fix:`, which the calling command
# relays to the user. Valid but suspicious results carry `warnings:`.
#
# The contract is locate-plan-spec.md in the feat-plan-locator branch plan (found by
# name under docs/plan/, like any plan). In short, the first rung that yields wins:
#   1. an explicit path (never falls through: a typo must not run another plan);
#   2. the current branch's plan, by flattened name, anywhere under docs/plan/;
#   3. docs/plan/F: a legacy master plan, or a `**Layout**: revisions` index whose
#      one open revision is docs/plan/<label>/_F;
#   4. every docs/plan/**/F, merged plans filtered out;
#   5. F at the repository root.
#
# The rules it shares with check-plan-index.sh and propose-branch-plan.sh live in
# lib/plan-rules.sh, beside it, which it sources.
#
# READ-ONLY. Writes nothing, temporary files included; of git it runs only
# `rev-parse`, `symbolic-ref`, and, to tell a missing file that was never committed from
# one that was deleted, `cat-file -e` and `rev-list`. Deterministic, Bash 3.2.
#
# A fix: line says what the repository shows, read from the evidence, and falls back to
# a generic line where the evidence does not decide: "create it" only for a file git has
# never seen, "remove the header" only when nothing in the plan justifies it.
#
# FAILS LOUDLY. `set -e` does not apply inside a function used as a condition, nor to a
# command substitution in a condition, a `case` word or `[ ]`, so nothing here relies on
# it: every file is checked readable before it is read (E15), every tool's status is
# checked where it runs, and a failure the rules cannot explain exits 3. An empty value
# from a failed read is never taken as an answer.
#
# Usage: locate-plan.sh <TODO.md|DO.md> [--goal <line>] [--branch <name>] [--] [path]
# Exit:  0 = report, result found/ask/none. 1 = report, result error.
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=locate-plan.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> [--goal <line>] [--branch <name>] [--] [path]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

MODEL=""; ARG_PATH=""; NPOS=0; GOAL=0; BRANCH=""; HAVE_BRANCH=0
pos() {
  NPOS=$((NPOS + 1))
  case $NPOS in
    1) MODEL="$1" ;;
    2) ARG_PATH="$1" ;;
    *) usage "more than one path: '$1'" ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
    --goal)
      [ $# -ge 2 ] || usage "--goal needs a line number"
      case "$2" in ''|*[!0-9]*) usage "--goal takes a line number, got '$2'" ;; esac
      GOAL=$((10#$2))
      [ "$GOAL" -gt 0 ] || usage "--goal takes a line number, got '$2'"
      shift 2 ;;
    --branch)
      [ $# -ge 2 ] || usage "--branch needs a name"
      BRANCH="$2"; HAVE_BRANCH=1; shift 2 ;;
    --) shift; while [ $# -gt 0 ]; do pos "$1"; shift; done ;;
    -?*) usage "unknown option '$1'" ;;
    *) pos "$1"; shift ;;
  esac
done
case "$MODEL" in
  TODO.md) OTHER=DO.md; CMD=/hitl-step; OTHER_CMD=/step; TODO=1 ;;
  DO.md)   OTHER=TODO.md; CMD=/step; OTHER_CMD=/hitl-step; TODO=0 ;;
  '')      usage "no model given" ;;
  *)       usage "the model must be TODO.md or DO.md, got '$MODEL'" ;;
esac
ROOT_PLAN="$PD/$MODEL"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_RUNG=""; R_PLAN=""; R_KIND=""; R_LAYOUT=""; R_STATUS=""; R_LINES=""
R_NEXT=""; R_GOALFILE=""; R_SUB=""; R_BLOCKED=""; R_CAND=""; R_WARN=""; R_PROB=""
R_FIX=""; R_MSG=""; VIOL=0

finish() {
  emit result "$R_RESULT";   emit rung "$R_RUNG";         emit plan "$R_PLAN"
  emit kind "$R_KIND";       emit layout "$R_LAYOUT";     emit status "$R_STATUS"
  emit lines "$R_LINES";     emit next "$R_NEXT";         emit goal-file "$R_GOALFILE"
  emit subgoals "$R_SUB";    emit blocked "$R_BLOCKED";   emit candidates "$R_CAND"
  emit warnings "$R_WARN";   emit problem "$R_PROB";      emit fix "$R_FIX"
  emit message "$R_MSG"
  if [ "$R_RESULT" = error ]; then exit 1; fi
  exit 0
}

fail() {  # fail <rung>: report every violation collected so far
  R_RESULT=error; R_RUNG="$1"
  R_NEXT=""; R_GOALFILE=""; R_SUB=""; R_BLOCKED=""; R_CAND=""
  if [ "$VIOL" -eq 1 ]; then R_MSG="Plan resolution stopped on a convention problem; see problem and fix."
  else R_MSG="Plan resolution stopped on $VIOL convention problems; see problem and fix."; fi
  finish
}

ask() {  # ask <rung> <candidates> <message>
  R_RESULT=ask; R_RUNG="$1"; R_CAND="$2"; R_MSG="$3"
  finish
}

# --- the repository -------------------------------------------------------------

# Only 128 means "not a repository"; any other failure (127: git not found) is the tool's.
if ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then st=0; else st=$?; fi
if [ "$st" -eq 128 ] || { [ "$st" -eq 0 ] && [ -z "$ROOT" ]; }; then
  violation "the working directory is not inside a git repository" "run it from the repository"
  fail ""
elif [ "$st" -ne 0 ]; then
  die "git rev-parse --show-toplevel failed with status $st" "$st"
fi
cd "$ROOT" || die "cannot enter the repository root $ROOT"
ROOTP="$(pwd -P)" || die "pwd -P failed in $ROOT"
if [ $HAVE_BRANCH -eq 0 ]; then
  # Status 1 with no output is a detached HEAD; any other failure is git's, not ours.
  if BRANCH="$(git symbolic-ref --short -q HEAD 2>/dev/null)"; then :
  else
    st=$?
    if [ "$st" -eq 1 ]; then BRANCH=""; else die "git symbolic-ref failed with status $st" "$st"; fi
  fi
fi

# --- helpers --------------------------------------------------------------------

phys() {  # the physical absolute path of an existing file or directory; 2 if it cannot be entered
  local d
  if [ -d "$1" ]; then (cd "$1" 2>/dev/null && pwd -P) || return 2
  else
    d="$(cd "$(dirname "$1")" 2>/dev/null && pwd -P)" || return 2
    printf '%s/%s\n' "${d%/}" "$(basename "$1")"
  fi
}
relpath() {  # repository-relative form of a physical path; fails if outside
  case "$1" in
    "$ROOTP")   printf '' ;;
    "$ROOTP"/*) printf '%s' "${1#"$ROOTP"/}" ;;
    *)          return 1 ;;
  esac
}

# --- reading the resolved plan ----------------------------------------------------

resolved() {  # resolved <file> <rung> <kind>
  local f="$1" rung="$2" out rec typ rest n nn="" nnm="" gdir matches gm="" fx IFS="$NL"
  local BAD="" CLAIMED="" FILES=""
  R_RESULT=found; R_RUNG="$rung"; R_PLAN="$f"; R_KIND="$3"
  if ! check_layout "$f" "$rung"; then fail "$rung"; fi
  R_LAYOUT="$LAYOUT_V"
  R_STATUS="$(status_of "$f")" || exit 3
  case "$R_STATUS" in
    '')              if [ "$3" = branch ]; then warn "$f has no **Status** line, so it counts as active"; fi ;;
    active|open)     ;;
    merged*)         if [ "$3" = branch ]; then warn "$f is stamped merged: the branch was probably reopened after merging"; fi ;;
    closed*)         ;;
    *)               warn "$f has the status '$R_STATUS', which is none of active, merged, open or closed" ;;
  esac
  R_LINES="$(awk 'END { print NR }' "$f")" || die "awk failed counting the lines of $f"

  local pg=0; if [ "$R_LAYOUT" = per-goal ]; then pg=1; fi
  out="$(awk -v todo="$TODO" -v goal="$GOAL" -v pergoal="$pg" "$SELECT_AWK" "$f")" || die "awk failed reading the items of $f"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
    case "$typ" in
      NEXT)    R_NEXT="$f:$n ${rest#*"$TAB"}" ;;
      SUB)     R_SUB="${R_SUB:+$R_SUB$NL}$f:$n" ;;
      BLK)     R_BLOCKED="${R_BLOCKED:+$R_BLOCKED$NL}$f:$n" ;;
      W6)      w6 "$f" "$n" "${rest#*"$TAB"}" ;;
      NN)      nn="$n"; nnm="${rest#*"$TAB"}" ;;
      NUM)     CLAIMED="${CLAIMED:+$CLAIMED$NL}${rest#*"$TAB"}" ;;
      BADIDX)  BAD="${BAD:+$BAD$NL}$n$TAB${rest#*"$TAB"}" ;;
      GOALERR)
        if [ "$GOAL" -gt "$R_LINES" ]; then
          violation "--goal $GOAL is past the end of $f ($R_LINES lines)" "pass the line of an item"
        elif [ "$TODO" -eq 1 ]; then
          violation "--goal $GOAL is not a top-level item in $f" "pass the line of an indent-0 item"
        else
          violation "--goal $GOAL is not an item in $f" "pass the line of an item"
        fi ;;
    esac
  done
  gdir="$(goal_dir "$f")"
  if [ -n "$BAD" ]; then   # E9, every unnumbered line at once, numbered in order
    goal_dir_ok "$gdir" "$rung"
    FILES="$(goal_files "$gdir")" || exit 3
    out="$(e9_fixes "$gdir")" || exit 3
    for rec in $out; do   # "<line>\t<fix>\t<the line's text>"
      n="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"
      violation "$f:$n has no goal number: \`${rest#*"$TAB"}\`" "${rest%%"$TAB"*}"
    done
  fi
  if [ "$VIOL" -gt 0 ]; then fail "$rung"; fi

  if [ -n "$nn" ]; then
    goal_dir_ok "$gdir" "$rung"
    FILES="$(goal_files "$gdir")" || exit 3
    matches="$(printf '%s\n' "$FILES" | NN="$nn" awk '{ b = $0; sub(/.*\//, "", b) } index(b, ENVIRON["NN"] "-") == 1 && b ~ /\.md$/')" \
      || die "awk failed matching goal $nn's file in $gdir"
    n="$(count_items "$matches")" || exit 3
    case "$n" in
      0) fx="$(e10_fix "$gdir" "$nn" "${R_NEXT#* }")" || exit 3
         violation "goal $nn has no file matching $gdir/$nn-*.md" "$fx, or correct the number on ${R_NEXT%% *}"; fail "$rung" ;;
      1) R_GOALFILE="$matches" ;;
      *) violation "goal $nn matches several files:$NL$matches" \
           "which copy is stale is your call: keep one, and git rm the others or give them unused goal numbers"; fail "$rung" ;;
    esac
    need_file "$R_GOALFILE" "$rung"
    out="$(awk "$GOALFILE_AWK" "$R_GOALFILE")" || die "awk failed reading the goal file $R_GOALFILE"
    for rec in $out; do
      typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
      case "$typ" in
        SUB)  R_SUB="${R_SUB:+$R_SUB$NL}$R_GOALFILE:$n" ;;
        W6)   w6 "$R_GOALFILE" "$n" "${rest#*"$TAB"}" ;;
        GOAL) gm="$rest" ;;
      esac
    done
    if [ -n "$gm" ] && [ "$gm" != "$nnm" ]; then
      warn "${R_NEXT%% *} has [$nnm] but $R_GOALFILE says **Goal**: [$gm]; the goal file is the source of truth"
    fi
  fi

  if [ -n "$R_NEXT" ]; then
    n="${R_NEXT#"$f":}"
    R_MSG="Resolved $f at rung $rung ($3); the next item is on line ${n%% *}."
  else
    R_MSG="Resolved $f at rung $rung ($3); every item in it is closed."
  fi
  finish
}

# --- rung 1: an explicit path -------------------------------------------------------

# E14: the path named the index and no revision is open. Other plans are named if there
# are any; reopening a closed revision is never suggested, since that only trades E14 for
# E7 when its directory is gone, and closing was a decision.
e14() {  # e14 <index>
  local idx="$1" all f st active="" nm=0 IFS="$NL"
  scan_dirs
  all="$(list_named "$MODEL")" || exit 3
  for f in $all; do
    if [ "$f" = "$ROOT_PLAN" ]; then continue; fi
    need_file "$f" 1
    st="$(status_of "$f")" || exit 3
    case "$st" in merged*) nm=$((nm + 1)) ;; *) active="${active:+$active$NL}$f" ;; esac
  done
  if [ -n "$active" ]; then
    violation "$idx is the revisions index and no revision in it is [~]" \
      "no revision is open, but these $MODEL plans are active: name one as the path, or omit the path to resolve by branch:$NL$active"
  else
    violation "$idx is the revisions index and no revision in it is [~]" \
      "no revision is open and no other $MODEL plan is active$( [ "$nm" -eq 0 ] || printf ' (%s merged)' "$nm" ): open one by adding \`- [~] <label> — <note>\` under \`## Revisions\` and creating $PD/<label>/_$MODEL, or create a plan (/new-branch)"
  fi
}

# E2 with neither F nor F′ in the directory: plans further down are listed, since that is
# almost certainly what was meant; otherwise say what the directory does hold.
e2() {  # e2 <dir>
  local d="$1" below="" all names="" k=0 x IFS="$NL"
  if [ "$d" != . ]; then
    below="$(find "$d" -mindepth 2 -type f -name "$MODEL" | sort)" || die "find failed listing plans under $d"
  fi
  if [ -n "$below" ]; then
    violation "$d/ holds no $MODEL itself, but these below it do:$NL$below" \
      "name the one you mean (which is your call), as the path"
    return 0
  fi
  all="$(find "$d" -mindepth 1 -maxdepth 1 | sort)" || die "find failed listing $d"
  for x in $all; do
    k=$((k + 1))
    if [ "$k" -le 10 ]; then
      if [ -d "$x" ]; then x="$(basename "$x")/"; else x="$(basename "$x")"; fi
      names="${names:+$names, }$x"
    fi
  done
  if [ "$k" -gt 10 ]; then names="$names, and $((k - 10)) more"; fi
  if [ "$k" -eq 0 ]; then
    violation "$d/ holds no $MODEL (and no $OTHER): it is empty" "name the plan file itself, or a directory holding $MODEL"
  else
    violation "$d/ holds no $MODEL (and no $OTHER), only: $names" \
      "name the plan file itself, or a directory holding $MODEL; if one of these files is meant to be the plan, git mv it to $d/$MODEL (your call)"
  fi
}

rung1() {
  local p="$ARG_PATH" r1="" r2="" ok1=0 ok2=0 out=0 denied="" pp rel f o kind
  # phys returns 2 for a directory it cannot enter: E15, never misread as "outside"
  if [ -n "$p" ] && [ -e "$p" ]; then
    if pp="$(phys "$p")"; then
      if r1="$(relpath "$pp")"; then ok1=1; else out=1; fi
    else denied="$p"; fi
  fi
  case "$p" in
    /*) ;;
    *) if [ -n "$p" ] && [ -e "$PD/$p" ]; then
         if pp="$(phys "$PD/$p")"; then
           if r2="$(relpath "$pp")"; then ok2=1; else out=1; fi
         else denied="${denied:-$PD/$p}"; fi
       fi ;;
  esac
  if [ $ok1 -eq 0 ] && [ $ok2 -eq 0 ] && [ -n "$denied" ]; then
    if [ -d "$denied" ]; then o="$denied"; else o="$(dirname "$denied")"; fi
    violation "$o/ cannot be entered or listed" "chmod u+rx $o"; fail 1
  fi
  if [ $ok1 -eq 1 ]; then
    rel="$r1"
    if [ $ok2 -eq 1 ] && [ "$r1" != "$r2" ]; then
      warn "'$p' also resolves under $PD/ (${r2:-.}); the repository-relative ${r1:-.} was used"
    fi
  elif [ $ok2 -eq 1 ]; then
    rel="$r2"
  elif [ $out -eq 1 ]; then
    violation "'$p' lies outside the repository" "give a path inside it, relative to its root"; fail 1
  else
    violation "nothing exists at '$p' (tried it repository-relative and under $PD/)" \
      "check the path, or omit it to resolve by branch"; fail 1
  fi

  if [ -d "${rel:-.}" ]; then
    f="${rel:+$rel/}$MODEL"
    if [ ! -f "$f" ]; then
      o="${rel:+$rel/}$OTHER"
      if [ -f "$o" ]; then
        violation "${rel:-.}/ holds no $MODEL, but $o exists" \
          "that plan is driven by $OTHER_CMD, so run it instead; or name a $MODEL plan"
      else
        e2 "${rel:-.}"
      fi
      fail 1
    fi
  else
    f="$rel"
  fi
  case "$(basename "$f")" in
    "$OTHER"|"_$OTHER") warn "$f is a $OTHER plan, which $OTHER_CMD drives, not $CMD" ;;
  esac

  if [ "$f" = "$ROOT_PLAN" ]; then
    if ! check_layout "$f" 1; then fail 1; fi
    if [ "$LAYOUT_V" = revisions ]; then
      warn "$f is the revisions index, not a plan; it was followed as rung 3 would"
      index_open "$f" 1
      case "$OPEN_N" in
        0) e14 "$f"; fail 1 ;;
        1) resolved "$OPEN_LIST" 1 revision-master ;;
        *) ask 1 "$OPEN_LIST" "Several revisions are open in $f; choose which to work on." ;;
      esac
    fi
    resolved "$f" 1 legacy-master
  fi
  kind=branch
  case "$f" in
    "$MODEL") kind=root-file; warn "plans belong under $PD/: git mv $MODEL $ROOT_PLAN" ;;
    "$PD"/*)  case "$(basename "$f")" in _*) kind=revision-master ;; esac ;;
  esac
  resolved "$f" 1 "$kind"
}

# --- rung 2: the branch plan, by name --------------------------------------------------

by_name() {  # entries of a list whose parent directory is named $NAME (never the root plan)
  printf '%s\n' "$1" | NAME="$NAME" ROOT_PLAN="$ROOT_PLAN" awk '
    $0 != "" && $0 != ENVIRON["ROOT_PLAN"] { n = split($0, p, "/"); if (n >= 2 && p[n-1] == ENVIRON["NAME"]) print }' \
    || die "awk failed matching plans by name"
}

nostatus_warnings() {  # nostatus_warnings <list> <rung>: W1 for each plan with no **Status** line
  local f st IFS="$NL"
  for f in $1; do
    need_file "$f" "$2"
    st="$(status_of "$f")" || exit 3
    if [ -z "$st" ]; then warn "$f has no **Status** line, so it counts as active"; fi
  done
}

rung2() {
  local m o n
  if [ -z "$BRANCH" ]; then
    warn "no current branch (a detached HEAD: a rebase, a bisect or a CI checkout), so rung 2 was skipped"
    return 0
  fi
  NAME="${BRANCH//\//-}"
  m="$(by_name "$ALL_F")" || exit 3
  n="$(count_items "$m")" || exit 3
  case "$n" in
    0) ;;
    1) resolved "$m" 2 branch ;;
    *) nostatus_warnings "$m" 2
       ask 2 "$m" "The plan for $BRANCH exists in several places; one is a stale copy, so choose which to use." ;;
  esac
  o="$(list_named "$OTHER")" || exit 3
  o="$(by_name "$o")" || exit 3
  if [ -n "$o" ]; then
    violation "the plan for $BRANCH exists only as $OTHER:$NL$o" "run $OTHER_CMD instead; $CMD drives $MODEL plans"
    fail 2
  fi
  return 0
}

# --- rung 3: the master plan ------------------------------------------------------------

rung3() {
  if [ ! -f "$ROOT_PLAN" ]; then
    if [ -f "$PD/$OTHER" ]; then
      warn "there is no $ROOT_PLAN, but $PD/$OTHER exists: this repository's master plan uses $OTHER"
    fi
    return 0
  fi
  if ! check_layout "$ROOT_PLAN" 3; then fail 3; fi
  if [ "$LAYOUT_V" = revisions ]; then
    index_open "$ROOT_PLAN" 3
    case "$OPEN_N" in
      0) return 0 ;;
      1) resolved "$OPEN_LIST" 3 revision-master ;;
      *) ask 3 "$OPEN_LIST" "Several revisions are open in $ROOT_PLAN; choose which to work on." ;;
    esac
  fi
  resolved "$ROOT_PLAN" 3 legacy-master
}

# --- rung 4: every plan, merged ones filtered out ------------------------------------------

rung4() {
  local f st active="" merged="" na nm IFS="$NL"
  for f in $ALL_F; do
    if [ "$f" = "$ROOT_PLAN" ]; then continue; fi
    need_file "$f" 4
    st="$(status_of "$f")" || exit 3
    case "$st" in
      merged*) merged="${merged:+$merged$NL}$f" ;;
      *)       active="${active:+$active$NL}$f" ;;
    esac
  done
  na="$(count_items "$active")" || exit 3; nm="$(count_items "$merged")" || exit 3
  if [ "$na" -eq 1 ]; then resolved "$active" 4 branch; fi
  if [ "$na" -gt 1 ]; then
    nostatus_warnings "$active" 4
    if [ "$nm" -eq 0 ]; then ask 4 "$active" "Several active $MODEL plans exist; choose which to use."
    else ask 4 "$active" "Several active $MODEL plans exist; choose which to use ($nm merged plans not shown; name one explicitly to use it)."; fi
  fi
  if [ "$nm" -gt 0 ]; then
    ask 4 "$merged" "Every $MODEL plan is stamped merged; name one explicitly to use it."
  fi
  return 0
}

# --- rung 5: the legacy root file ----------------------------------------------------------

rung5() {
  if [ -f "$MODEL" ]; then
    warn "plans belong under $PD/: git mv $MODEL $ROOT_PLAN"
    resolved "$MODEL" 5 root-file
  fi
  return 0
}

# --- resolution ------------------------------------------------------------------------------

if [ $NPOS -ge 2 ]; then rung1; fi
scan_dirs
ALL_F="$(list_named "$MODEL")" || exit 3
rung2
rung3
rung4
rung5
R_RESULT=none
R_MSG="No $MODEL plan was found: none for the branch, none under $PD/, none at the root."
finish
