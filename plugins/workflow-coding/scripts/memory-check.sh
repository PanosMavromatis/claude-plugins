#!/usr/bin/env bash
# Report the size of each plan file the commands read, against a threshold.
#
# The per-goal layout exists to keep each file a command reads whole small, so a step
# loads only the goal it works on. This measures whether it does. It lists the plan files
# of the open revision, of a revision named by its label, or, under a legacy root plan, of
# the whole tree, and reports each one's bytes, words, lines and ≈ tokens, with totals per
# branch, each naming its plan's layout, and overall. Files are classed by how the commands
# access them: a branch plan's index, its goal files and a single-file branch plan are read
# whole, and each one over the threshold gets a warning; a revision's _TODO.md and the root
# plan are located by line, so their size never reaches a command, and they are only
# reported.
#
# Tokens are bytes × 3 / 7, labelled ≈, and a total's are its own bytes × 3 / 7. The ratio
# was calibrated on 2026-10-14 against claude-opus-5-5, on nine plan files as Read returns
# them to a command, line numbers included: 2.34 bytes a token, where bytes / 4, the rule
# dev/measure-context.sh uses, was 42% low. dev/memory-check/calibrate.py repeats it.
#
# The interface was settled in goal 01 of the feat-memory-check branch plan (found by name
# under docs/plan/, like any plan), with the reasons; the rules it shares with the other
# plan scripts come from lib/plan-rules.sh.
#
# READ-ONLY. Writes nothing; of git it runs only `rev-parse --show-toplevel`. Its result
# gates nothing: a report exits 0 whatever the sizes. Deterministic, Bash 3.2, BSD or GNU.
#
# Usage: memory-check.sh <TODO.md|DO.md> [--threshold <tokens>] [--] [<label>]
#        <label> names docs/plan/<label>/, a revision open or closed. Without one: the open
#        revision under a revisions index, with the root plan; the whole tree under a
#        legacy root plan. The threshold is in ≈ tokens, 2000 by default: about twice the
#        median of R2's first goal files, and above every one that shipped.
# Exit:  0 = a report: measured, ask or none. 1 = the plans could not be measured
#        (result: error). 2 = usage error, no report. 3 = a tool failed; message on stderr.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=memory-check.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> [--threshold <tokens>] [--] [<label>]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

MODEL=""; LABEL=""; NPOS=0; THRESHOLD=2000
pos() {
  NPOS=$((NPOS + 1))
  case $NPOS in
    1) MODEL="$1" ;;
    2) LABEL="$1" ;;
    *) usage "more than one label: '$1'" ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
    --) shift; while [ $# -gt 0 ]; do pos "$1"; shift; done ;;
    --threshold) [ $# -ge 2 ] || usage "--threshold needs a number of tokens"
                 THRESHOLD="$2"; shift 2 ;;
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
case "$THRESHOLD" in
  ''|*[!0-9]*) usage "the threshold must be a whole number of tokens, got '$THRESHOLD'" ;;
esac
THRESHOLD=$((10#$THRESHOLD))   # base 10: a leading zero must not read as octal
[ "$THRESHOLD" -ge 1 ] || usage "the threshold must be at least 1 token"
ROOT_PLAN="$PD/$MODEL"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_ROOT=""; R_LAYOUT=""; R_REV=""; R_THRESH="≈$THRESHOLD tokens"; R_FILES=""
R_BRANCHES=""; R_TOTAL=""; R_CAND=""; R_WARN=""; R_PROB=""; R_FIX=""; R_MSG=""
VIOL=0

finish() {
  emit result "$R_RESULT";       emit root "$R_ROOT";           emit layout "$R_LAYOUT"
  emit revision "$R_REV";        emit threshold "$R_THRESH";    emit files "$R_FILES"
  emit branches "$R_BRANCHES";   emit total "$R_TOTAL";         emit candidates "$R_CAND"
  emit warnings "$R_WARN";       emit problem "$R_PROB";        emit fix "$R_FIX"
  emit message "$R_MSG"
  if [ "$R_RESULT" = error ]; then exit 1; fi
  exit 0
}

fail() {  # fail <rung>: the plans could not be measured; the rung is the library's, unused
  R_RESULT=error; R_FILES=""; R_BRANCHES=""; R_TOTAL=""; R_CAND=""
  R_MSG="The plans could not be measured; see problem and fix."
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

scan_dirs
master_files ""
R_LAYOUT="$MLAYOUT"
if [ -f "$ROOT_PLAN" ]; then R_ROOT="$ROOT_PLAN"; fi

# --- the scope: which directory, and whether the root plan is measured ----------

WITH_ROOT=0
if [ -n "$LABEL" ]; then
  case "$LABEL" in
    */*|.|..)
      violation "'$LABEL' is not a label: a label names one directory under $PD/" \
        "pass the label alone, as the root plan's line for the revision gives it"
      fail "" ;;
  esac
  DIR="$PD/$LABEL"
  if [ ! -d "$DIR" ]; then
    violation "$DIR/ does not exist" "pass the label of a revision whose directory is under $PD/, open or closed"
    fail ""
  fi
  R_REV="$LABEL"
elif [ "$MLAYOUT" = none ]; then
  R_RESULT=none
  R_MSG="There is no root plan, $ROOT_PLAN, so no revision is open; pass a label to measure one."
  finish
elif [ "$MLAYOUT" = revisions ]; then
  n="$(count_items "$MASTERS")"
  if [ "$n" -eq 0 ]; then
    R_RESULT=none
    R_MSG="No revision is open in $ROOT_PLAN; pass a label to measure a closed one."
    finish
  fi
  if [ "$n" -gt 1 ]; then
    IFS="$NL"
    for m in $MASTERS; do R_CAND="${R_CAND:+$R_CAND$NL}$(basename "$(dirname "$m")")"; done
    unset IFS
    R_RESULT=ask
    R_MSG="$n revisions are open; pass the one to measure as the label, after --."
    finish
  fi
  DIR="$(dirname "$MASTERS")"; R_REV="$(basename "$DIR")"; WITH_ROOT=1
else
  DIR="$PD"; WITH_ROOT=1   # legacy: the root plan is the master, and the tree its branches
fi

# --- the files: <access> <branch directory> <its layout> <path>, one per line ----

RECS=""
add() { RECS="${RECS:+$RECS$NL}$1$TAB$2$TAB$3$TAB$4"; }

if [ "$WITH_ROOT" -eq 1 ]; then need_file "$ROOT_PLAN" ""; add "by line" "" "" "$ROOT_PLAN"; fi
if [ "$DIR" != "$PD" ] && [ -f "$DIR/_$MODEL" ]; then need_file "$DIR/_$MODEL" ""; add "by line" "" "" "$DIR/_$MODEL"; fi

plans="$(find "$DIR" -type f -name "$MODEL")" || die "find failed listing $MODEL under $DIR"
if [ -n "$plans" ]; then plans="$(printf '%s\n' "$plans" | sort)" || die "sort failed"; fi
IFS="$NL"
for p in $plans; do
  if [ "$p" = "$ROOT_PLAN" ]; then continue; fi
  need_file "$p" ""
  b="$(dirname "$p")"
  # A branch plan whose **Layout** header is wrong is still measured, as one file: this
  # reports sizes, and locate-plan.sh and check-plan-index.sh report the header.
  sp="$R_PROB"; sf="$R_FIX"; sv="$VIOL"
  if ! check_layout "$p" ""; then
    R_PROB="$sp"; R_FIX="$sf"; VIOL="$sv"; LAYOUT_V=single-file
    warn "$p has a **Layout** header that is not valid there, so it was measured as one file; check-plan-index.sh says why"
  fi
  add whole "$b" "$LAYOUT_V" "$p"
  if [ "$LAYOUT_V" = per-goal ]; then
    g="$(goal_dir "$p")"
    goal_dir_ok "$g" ""
    if [ -d "$g" ]; then
      gf="$(find "$g" -maxdepth 1 -type f -name '[0-9]*-*.md')" || die "find failed listing $g"
      if [ -n "$gf" ]; then gf="$(printf '%s\n' "$gf" | sort)" || die "sort failed"; fi
      for f in $gf; do need_file "$f" ""; add whole "$b" per-goal "$f"; done
    fi
  fi
done
unset IFS

# --- the sizes ------------------------------------------------------------------

# wc -c counts bytes exactly, and BSD wc pads its count with spaces, so keep the digits;
# awk counts words and lines. A row: <bytes> <words> <lines> <access> <branch> <layout>
# <path>.
ROWS=""
IFS="$NL"
for rec in $RECS; do
  acc="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; b="${rest%%"$TAB"*}"; rest="${rest#*"$TAB"}"
  lay="${rest%%"$TAB"*}"; p="${rest#*"$TAB"}"
  by="$(wc -c < "$p")" || die "wc failed reading $p"
  by="${by//[!0-9]/}"
  wl="$(awk '{ w += NF } END { print w + 0 "\t" NR }' "$p")" || die "awk failed reading $p"
  ROWS="${ROWS:+$ROWS$NL}$by$TAB$wl$TAB$acc$TAB$b$TAB$lay$TAB$p"
done
unset IFS
if [ -n "$ROWS" ]; then
  ROWS="$(printf '%s\n' "$ROWS" | sort -t "$TAB" -k1,1nr -k7,7)" || die "sort failed"
fi

# Largest first; branches by their bytes, then name. Records: F a file, B a branch, T the
# total, W a warning, N the counts of files and warnings. Comparisons are written with `<`,
# since the suite's static check reads a `>` before a word as a redirect.
out="$(printf '%s' "$ROWS" | awk -v th="$THRESHOLD" '
  BEGIN { FS = "\t" }
  function s(k) { return k == 1 ? "" : "s" }
  NF == 7 {
    t = int($1 * 3 / 7)
    print "F\t" $7 " — " $1 " bytes, " $2 " words, " $3 " lines, ≈" t " tokens, " $4
    n++; tb += $1
    if ($4 == "whole") {
      nw++; wb += $1
      if (th < t) { print "W\t" $7 ": ≈" t " tokens, over the threshold of ≈" th; k++ }
    }
    if ($5 != "") { if (!($5 in bn)) { o[++nb] = $5; bl[$5] = $6 } bn[$5]++; bb[$5] += $1 }
  }
  END {
    for (i = 1; i <= nb; i++)
      for (j = i + 1; j <= nb; j++)
        if (bb[o[i]] < bb[o[j]] || (bb[o[j]] == bb[o[i]] && o[j] < o[i])) { x = o[i]; o[i] = o[j]; o[j] = x }
    for (i = 1; i <= nb; i++) {
      name = o[i]; sub(/.*\//, "", name)
      print "B\t" name " — " bl[o[i]] ", " bn[o[i]] " file" s(bn[o[i]]) ", " bb[o[i]] " bytes, ≈" int(bb[o[i]] * 3 / 7) " tokens"
    }
    print "T\t" n + 0 " file" s(n) ", " tb + 0 " bytes, ≈" int(tb * 3 / 7) " tokens; read whole: " nw + 0 " file" s(nw) ", ≈" int(wb * 3 / 7) " tokens"
    print "N\t" n + 0 "\t" k + 0
  }')" || die "awk failed totalling the sizes"

NF_=0; NW_=0
IFS="$NL"
for rec in $out; do
  typ="${rec%%"$TAB"*}"; val="${rec#*"$TAB"}"
  case "$typ" in
    F) R_FILES="${R_FILES:+$R_FILES$NL}$val" ;;
    B) R_BRANCHES="${R_BRANCHES:+$R_BRANCHES$NL}$val" ;;
    T) R_TOTAL="$val" ;;
    W) warn "$val" ;;
    N) NF_="${val%%"$TAB"*}"; NW_="${val#*"$TAB"}" ;;
  esac
done
unset IFS

R_RESULT=measured
where="revision $R_REV"
if [ -z "$R_REV" ]; then where="$PD/, under a legacy root plan"; fi
R_MSG="Measured $NF_ plan file$([ "$NF_" -eq 1 ] || echo s) in $where; ≈ tokens are bytes × 3 / 7, calibrated on claude-opus-5-5 as Read returns a file."
if [ "$NW_" -gt 0 ]; then
  R_MSG="$R_MSG $NW_ read whole $([ "$NW_" -eq 1 ] && echo is || echo are) over the threshold; see warnings."
fi
finish
