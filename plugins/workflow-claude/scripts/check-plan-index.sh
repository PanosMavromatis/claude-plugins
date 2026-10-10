#!/usr/bin/env bash
# Report drift between a per-goal plan's index and its goal files.
#
# In the per-goal layout the goal file is the source of truth for its goal's marker, and
# the index line mirrors it. Edits go goal file first, then index, so an interrupted edit
# leaves the two apart; a goal file can also be lost, duplicated or left behind by a
# rename. This script reads the whole plan and says where the two disagree, each problem
# with a fix: line read from the evidence, in the words locate-plan.sh uses for the same
# conventions. The rules come from lib/plan-rules.sh, which both scripts source, so the
# two cannot disagree about a slug or a goal number.
#
# The contract is per-goal-layout-spec.md in the feat-per-goal-layout branch plan (found
# by name under docs/plan/, like any plan); the findings:
#   D1 an index marker differs from its goal file's **Goal**: (the goal file wins)
#   D2 a goal has no goal file (E10)        D3 a goal matches several files (E11)
#   D4 a goal file no index line claims     D5 an index line has no goal number (E9)
#   D6 a goal number is on several lines    D7 a goal file has no **Goal**: line
#   D8 a goal is [x] but its file still has open items
#
# A legacy (one-file) plan has nothing to drift, so for one the script only reports its
# open items, at every indent, each with the `## ` heading it sits under: the completion
# check /step and /hitl-step run before reporting a plan or section done, in either layout.
#
# READ-ONLY. Writes nothing; of git it runs only `rev-parse --show-toplevel`, and for a
# fix: line, the reads locate-plan.sh's E10 makes. Deterministic, Bash 3.2.
#
# Usage: check-plan-index.sh <TODO.md|DO.md> [--] <index>
#        <index> is the plan file (a per-goal plan's index, or a legacy plan), or its
#        directory, relative to the repository root: the `plan:` locate-plan.sh reports.
# Exit:  0 = clean. 1 = drift, or the plan could not be checked (result: error).
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=check-plan-index.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> [--] <index>" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

MODEL=""; ARG_PATH=""; NPOS=0
pos() {
  NPOS=$((NPOS + 1))
  case $NPOS in
    1) MODEL="$1" ;;
    2) ARG_PATH="$1" ;;
    *) usage "more than one index: '$1'" ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
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
[ $NPOS -ge 2 ] && [ -n "$ARG_PATH" ] || usage "no index given: pass the plan locate-plan.sh resolved"
ROOT_PLAN="$PD/$MODEL"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_PLAN=""; R_GOALS=""; R_OPEN=""; R_WARN=""; R_PROB=""; R_FIX=""; R_MSG=""
VIOL=0

finish() {
  emit result "$R_RESULT";   emit plan "$R_PLAN";       emit goals "$R_GOALS"
  emit open "$R_OPEN";       emit warnings "$R_WARN";   emit problem "$R_PROB"
  emit fix "$R_FIX";         emit message "$R_MSG"
  if [ "$R_RESULT" = clean ]; then exit 0; fi
  exit 1
}

fail() {  # fail <rung>: the plan could not be checked; the rung is the library's, unused
  R_RESULT=error; R_GOALS=""; R_OPEN=""
  R_MSG="The plan could not be checked; see problem and fix."
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

# --- the index ------------------------------------------------------------------

IDX="${ARG_PATH%/}"
case "$IDX" in
  /*) violation "the index was given as an absolute path" "pass it relative to the repository root, as locate-plan.sh's plan: names it"; fail "" ;;
esac
if [ -d "$IDX" ]; then IDX="$IDX/$MODEL"; fi
R_PLAN="$IDX"
if [ ! -e "$IDX" ]; then
  violation "$IDX does not exist" "pass the per-goal plan's index, relative to the repository root, as locate-plan.sh's plan: names it"
  fail ""
fi
need_file "$IDX" ""
if ! check_layout "$IDX" ""; then fail ""; fi
if [ "$LAYOUT_V" = revisions ]; then
  violation "$IDX is a revisions index: its items are revisions, not goals" \
    "check the open revision's plan instead, the plan: locate-plan.sh reports"
  fail ""
fi
if [ "$LAYOUT_V" = legacy ]; then
  # One file holds every goal, so nothing can drift: report the open items, each with the
  # `## ` heading it sits under, which is what a section's completion check needs.
  out="$(awk "$OPEN_AWK" "$IDX")" || die "awk failed reading the items of $IDX"
  IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; ln="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
    case "$typ" in
      OPEN)  h="${rest%%"$TAB"*}"; t="${rest#*"$TAB"}"
             R_OPEN="${R_OPEN:+$R_OPEN$NL}$IDX:$ln $t${h:+ — under $h}" ;;
      W6)    w6 "$IDX" "$ln" "$rest" ;;
      GOALS) R_GOALS="$ln" ;;
    esac
  done
  unset IFS
  no="$(count_items "$R_OPEN")" || exit 3
  R_RESULT=clean
  if [ "$no" -eq 1 ]; then R_MSG="$IDX is a one-file plan, so nothing can drift; 1 item is open."
  else R_MSG="$IDX is a one-file plan, so nothing can drift; $no items are open."; fi
  finish
fi

GDIR="$(goal_dir "$IDX")"
goal_dir_ok "$GDIR" ""
FILES="$(goal_files "$GDIR")" || exit 3

# Index lines: IDX <line> <marker> <NN> <the line>; BADIDX <line> <the line>; W6.
OUT="$(awk -v todo=0 -v goal=0 -v pergoal=1 "$SELECT_AWK" "$IDX")" || die "awk failed reading the items of $IDX"
IL=""; BAD=""; CLAIMED=""; NG=0
IFS="$NL"
for rec in $OUT; do
  typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
  case "$typ" in
    IDX)    IL="${IL:+$IL$NL}$rest"; NG=$((NG + 1))
            r2="${rest#*"$TAB"}"; r2="${r2#*"$TAB"}"; CLAIMED="${CLAIMED:+$CLAIMED$NL}${r2%%"$TAB"*}" ;;
    BADIDX) BAD="${BAD:+$BAD$NL}$n$TAB${rest#*"$TAB"}"; NG=$((NG + 1)) ;;
    W6)     w6 "$IDX" "$n" "${rest#*"$TAB"}" ;;
  esac
done
unset IFS
R_GOALS="$NG"

# D5: every unnumbered index line, with the fix locate-plan.sh's E9 gives.
if [ -n "$BAD" ]; then
  out="$(e9_fixes "$GDIR")" || exit 3
  IFS="$NL"
  for rec in $out; do   # "<line>\t<fix>\t<the line's text>"
    n="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"
    violation "$IDX:$n has no goal number: \`${rest#*"$TAB"}\`" "${rest%%"$TAB"*}"
  done
  unset IFS
fi

# D6: a goal number on more than one index line, compared as numbers (02 is 2). The
# free numbers it offers start past every goal file and past those E9 just gave out.
NBAD="$(count_items "$BAD")" || exit 3
if [ -n "$CLAIMED" ]; then
  out="$(IL="$IL" FILES="$FILES" NBAD="$NBAD" awk "$SLUG_AWK"'
    function see(id) { if (max < id + 0) max = id + 0; match(id, /^[0-9]+/); if (w < RLENGTH) w = RLENGTH }
    BEGIN {
      w = 2
      n = split(ENVIRON["FILES"], F, "\n")
      for (i = 1; i <= n; i++) { b = F[i]; sub(/.*\//, "", b); if (match(b, /^[0-9]+[a-z]?-/)) see(substr(b, 1, RLENGTH - 1)) }
      n = split(ENVIRON["IL"], R, "\n")
      for (i = 1; i <= n; i++) {
        split(R[i], f, "\t"); id = f[3]; k = num(id); see(id)
        L[k] = L[k] (L[k] == "" ? "" : " and ") f[1]; C[k]++; if (!(k in ID)) ID[k] = id
        if (C[k] == 2) order[++m] = k
      }
      max += ENVIRON["NBAD"]
      for (j = 1; j <= m; j++) { k = order[j]; printf "%s\t%0" w "d\t%s\n", ID[k], max + 1, L[k]; max += C[k] - 1 }
    }' </dev/null)" || die "awk failed looking for repeated goal numbers in $IDX"
  IFS="$NL"
  for rec in $out; do   # "<NN>\t<first free number>\t<line> and <line>…"
    nn="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; free="${rest%%"$TAB"*}"
    violation "goal number $nn is on lines ${rest#*"$TAB"} of $IDX" \
      "which line keeps $nn is your call; give each other one an unused number, from $free on, and its goal file"
  done
  unset IFS
fi

# D1, D2, D3, D7, D8 and the open items, goal by goal in index order.
for_goal() {  # for_goal <line> <marker> <NN> <the line>
  local n="$1" mk="$2" nn="$3" text="$4" matches k gf out rec typ rest ln gm="" opn="" fx names
  matches="$(printf '%s\n' "$FILES" | NN="$nn" awk '{ b = $0; sub(/.*\//, "", b) } index(b, ENVIRON["NN"] "-") == 1 && b ~ /\.md$/')" \
    || die "awk failed matching goal $nn's file in $GDIR"
  k="$(count_items "$matches")" || exit 3
  case "$k" in
    0) fx="$(e10_fix "$GDIR" "$nn" "$text")" || exit 3
       violation "goal $nn has no file matching $GDIR/$nn-*.md" "$fx, or correct the number on $IDX:$n"
       return 0 ;;
    1) gf="$matches" ;;
    *) names="$(printf '%s\n' "$matches" | awk '{ sub(/.*\//, ""); s = s (NR == 1 ? "" : ", ") $0 } END { print s }')" \
         || die "awk failed listing goal $nn's files"
       violation "goal $nn matches several files in $GDIR/: $names" \
         "which copy is stale is your call: keep one, and git rm the others or give them unused goal numbers"
       return 0 ;;
  esac
  need_file "$gf" ""
  out="$(awk "$GOALFILE_AWK" "$gf")" || die "awk failed reading the goal file $gf"
  local IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; ln="${rest%%"$TAB"*}"
    case "$typ" in
      SUB)  rest="${rest#*"$TAB"}"
            case "${rest%%"$TAB"*}" in
              ' '|'~'|'!') opn="${opn:+$opn, }$ln"; R_OPEN="${R_OPEN:+$R_OPEN$NL}$gf:$ln ${rest#*"$TAB"}" ;;
            esac ;;
      W6)   w6 "$gf" "$ln" "${rest#*"$TAB"}" ;;
      GOAL) gm="$rest" ;;
    esac
  done
  if [ -z "$gm" ]; then
    violation "$gf has no **Goal** line" "add \`**Goal**: [$mk]\` under its heading, the marker $IDX:$n has"
    return 0
  fi
  if [ "$gm" != "$mk" ]; then
    violation "$IDX:$n has [$mk] but $gf says **Goal**: [$gm]" \
      "the goal file is the source of truth: write $IDX:$n as \`- [$gm]${text#- \[?\]}\`"
  fi
  if [ "$gm" = x ] && [ -n "$opn" ]; then
    case "$opn" in *,*) opn="lines $opn" ;; *) opn="line $opn" ;; esac
    violation "$gf says **Goal**: [x] but has open items, on $opn" \
      "close each item, or reopen the goal (\`**Goal**: [~]\` in $gf, then $IDX:$n); which is your call"
  fi
  return 0
}

# Only the first index line carrying a number is checked against its file; any other is
# D6's, so a file is never read or reported twice.
SEEN=" "
IFS="$NL"
for rec in $IL; do
  n="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; mk="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  nn="${rest%%"$TAB"*}"; text="${rest#*"$TAB"}"
  case "$mk" in ' '|'~'|'!') R_OPEN="${R_OPEN:+$R_OPEN$NL}$IDX:$n $text" ;; esac
  d="${nn%%[a-z]*}"; key="$((10#$d))${nn#"$d"}"
  case "$SEEN" in *" $key "*) continue ;; esac
  SEEN="$SEEN$key "
  unset IFS; for_goal "$n" "$mk" "$nn" "$text"; IFS="$NL"
done
unset IFS

# D4: a goal file whose number no index line claims. Near-miss names (2-two.md for goal
# 02) are claimed by number and reported under D2, with the git mv that fixes them; a
# file whose slug is an unnumbered line's title is E9's to place, as e9_fixes matches it.
out="$(CLAIMED="$CLAIMED" FILES="$FILES" BAD="$BAD" awk "$SLUG_AWK"'
  BEGIN {
    n = split(ENVIRON["CLAIMED"], C, "\n"); for (i = 1; i <= n; i++) if (C[i] != "") claimed[num(C[i])] = 1
    n = split(ENVIRON["BAD"], B, "\n"); for (i = 1; i <= n; i++) if (B[i] != "") { t = B[i]; sub(/^[^\t]*\t/, "", t); bad[slug(title(t))] = 1 }
    n = split(ENVIRON["FILES"], F, "\n")
    for (i = 1; i <= n; i++) {
      b = F[i]; sub(/.*\//, "", b)
      if (!match(b, /^[0-9]+[a-z]?/)) continue
      id = substr(b, 1, RLENGTH)
      if (substr(b, RLENGTH + 1, 1) != "-" || b !~ /\.md$/) continue
      if (substr(b, length(id) + 2, length(b) - length(id) - 4) in bad) continue
      if (!(num(id) in claimed)) print id "\t" F[i]
    }
  }' </dev/null)" || die "awk failed looking for goal files no index line claims in $GDIR"
IFS="$NL"
for rec in $out; do   # "<NN>\t<file>"
  nn="${rec%%"$TAB"*}"; gf="${rec#*"$TAB"}"
  need_file "$gf" ""
  # its own heading and marker say what its index line would be
  ev="$(awk "$SLUG_AWK"'
    /^\*\*Goal\*\*:/ && !g { g = 1; v = $0; sub(/^\*\*Goal\*\*:[ \t]*/, "", v); m = substr(v, 2, 1) }
    /^# / && !h { h = 1; t = $0; sub(/^#[ \t]*/, "", t); t = title("- [ ] " t) }
    END { print (m == "" ? " " : m) "\t" t }' "$gf")" || die "awk failed reading the goal file $gf"
  m="${ev%%"$TAB"*}"; t="${ev#*"$TAB"}"
  if [ -n "$t" ]; then
    violation "$gf is a goal file no index line claims" \
      "add \`- [$m] $nn — $t\` to $IDX, from its heading and **Goal**, or git rm $gf if the goal was dropped; which is your call"
  else
    violation "$gf is a goal file no index line claims" \
      "add \`- [$m] $nn — <its title>\` to $IDX, or git rm $gf if the goal was dropped; which is your call"
  fi
done
unset IFS

# --- the verdict ------------------------------------------------------------------

no="$(count_items "$R_OPEN")" || exit 3
if [ "$VIOL" -gt 0 ]; then
  R_RESULT=drift
  if [ "$VIOL" -eq 1 ]; then R_MSG="$IDX and its goal files disagree in one place; see problem and fix."
  else R_MSG="$IDX and its goal files disagree in $VIOL places; see problem and fix."; fi
else
  R_RESULT=clean
  if [ "$no" -eq 1 ]; then R_MSG="$IDX and its $NG goal files agree; 1 item is open."
  else R_MSG="$IDX and its $NG goal files agree; $no items are open."; fi
fi
finish
