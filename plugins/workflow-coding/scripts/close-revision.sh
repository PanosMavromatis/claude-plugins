#!/usr/bin/env bash
# Propose closing a revision, and check the command's writes before they are committed.
#
# Under a revisions index a close is a stamp: the revision's _<model> goes from
# `**Status**: open` to `**Status**: closed — <date>`, and its index line from [~] to [x].
# The directory already is the archive, and /new-branch created every branch plan inside it,
# so nothing moves. Under a legacy root plan a close is a cut: the revision's
# `## Subgoals — revision <label>` section moves, verbatim, to docs/plan/<label>/_<model>,
# a pointer takes its place under `## Closed revisions`, and the revision's merged branch
# plans, still flat under docs/plan/, are filed into the directory: the job /file-plans did.
#
# Whether a revision is finished is the user's call, never inferred. An open item refuses
# the close as a safety net, not as the decision.
#
# The archive is _<model>, never <model>: plan resolution matches a branch plan by that
# filename, and an unstamped archive would count as active. The underscore keeps a closed
# revision out of resolution; an explicit path still reaches it.
#
# Every read goes through src, which reads the working tree, or HEAD under --check. A check
# is the proposal computed against HEAD, compared with what the command wrote: one set of
# rules, so the check cannot disagree with the proposal it checks.
#
# The contract is close-revision-spec.md in the feat-master-plan branch plan (found by name
# under docs/plan/, like any plan).
#
# READ-ONLY. Writes nothing: --render prints a file, and /close-revision writes it. Of git
# it runs `rev-parse --show-toplevel`, the reads locate-plan.sh's E7 makes, and, under
# --check, reads of HEAD. Deterministic, Bash 3.2.
#
# Usage: close-revision.sh <label> --date <YYYY-MM-DD> [--render root|archive | --check]
# Exit:  0 = report, result proposed or verified; with --render, the file, printed.
#        1 = report, result refused or error; with --render, the report goes to stderr.
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=close-revision.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <label> --date <YYYY-MM-DD> [--render root|archive | --check]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

LABEL=""; NLAB=0; DATE=""; RENDER=""; CHECK=0
lab() {
  NLAB=$((NLAB + 1))
  [ $NLAB -eq 1 ] || usage "one label only, got another: '$1'"
  LABEL="$1"
}
while [ $# -gt 0 ]; do
  case "$1" in
    --date)   [ $# -ge 2 ] || usage "--date needs YYYY-MM-DD"; DATE="$2"; shift 2 ;;
    --render) [ $# -ge 2 ] || usage "--render needs root or archive"; RENDER="$2"; shift 2 ;;
    --check)  CHECK=1; shift ;;
    --) shift; while [ $# -gt 0 ]; do lab "$1"; shift; done ;;
    -?*) usage "unknown option '$1'" ;;
    *) lab "$1"; shift ;;
  esac
done
[ $NLAB -eq 1 ] || usage "no label given"
case "$LABEL" in
  '')                            usage "the label is empty" ;;
  *[[:space:]]*|*/*|*"$DASH"*)   usage "a label holds no whitespace, '/' or '$DASH', got '$LABEL'" ;;
  '#'*|-*)                       usage "a label does not start with '#' or '-', got '$LABEL'" ;;
esac
[ -n "$DATE" ] || usage "--date is required: the closing date, YYYY-MM-DD"
case "$DATE" in
  [0-9][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]) ;;
  *) usage "--date takes YYYY-MM-DD, got '$DATE'" ;;
esac
case "$RENDER" in ''|root|archive) ;; *) usage "--render takes root or archive, got '$RENDER'" ;; esac
[ -z "$RENDER" ] || [ $CHECK -eq 0 ] || usage "--render and --check are separate runs"

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_LAYOUT=""; R_ROOT=""; R_REV=""; R_CHANGE=""; R_EDITS=""; R_SECTION=""
R_POINTER=""; R_MOVES=""; R_WARN=""; R_PROB=""; R_FIX=""; VIOL=0

report() {
  emit result "$R_RESULT";   emit layout "$R_LAYOUT";   emit root "$R_ROOT"
  emit revision "$R_REV";    emit change "$R_CHANGE";   emit edits "$R_EDITS"
  emit section "$R_SECTION"; emit pointer "$R_POINTER"; emit moves "$R_MOVES"
  emit warnings "$R_WARN";   emit problem "$R_PROB";    emit fix "$R_FIX"
}

finish() {  # print the report, or with --render the file, and exit
  case "$R_RESULT" in
    proposed)
      if [ -n "$RENDER" ]; then render; else report; fi
      exit 0 ;;
    verified) report; exit 0 ;;
  esac
  if [ -n "$RENDER" ]; then report >&2; else report; fi
  exit 1
}

fail() {  # fail <rung>: report every violation so far; the rung is the library's, unused
  R_RESULT=error; R_CHANGE=""; R_EDITS=""; R_SECTION=""; R_POINTER=""; R_MOVES=""; finish
}

refuse() {  # refuse <problem> <fix>
  R_RESULT=refused; R_CHANGE=""; R_EDITS=""; R_SECTION=""; R_POINTER=""; R_MOVES=""
  R_PROB="$1"; R_FIX="$2"; finish
}

if [ $CHECK -eq 1 ]; then
  BEFORE="--check runs before the commit, against HEAD as it was when the close was proposed"
fi

# --- reading: the working tree, or HEAD under --check -----------------------------

src() {  # src <path>: the file's contents
  if [ $CHECK -eq 1 ]; then git show "HEAD:$1" || die "git show failed reading $1 at HEAD"
  else cat "$1" || die "cat failed reading $1"; fi
}
has() {  # has <path>: exists, in the working tree or in HEAD
  if [ $CHECK -eq 1 ]; then git cat-file -e "HEAD:$1" 2>/dev/null; else [ -e "$1" ] || [ -L "$1" ]; fi
}
plan_dirs() {  # every directory under docs/plan/, one per line
  if [ $CHECK -eq 1 ]; then git ls-tree -r -d --name-only HEAD -- "$PD" || die "git ls-tree failed listing $PD at HEAD"
  else find "$PD" -type d || die "find failed listing $PD"; fi
}
status_src() {  # the first **Status** value of a file, as status_of reads it
  src "$1" | awk '/^\*\*Status\*\*:/ { sub(/^\*\*Status\*\*:[ \t]*/, ""); sub(/[ \t\r]+$/, ""); print; exit }' \
    || die "awk failed reading the status of $1"
}
lf() {  # a file with each line's trailing CR dropped
  awk '{ sub(/\r$/, ""); print }' "$1" || die "awk failed reading $1"
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
if [ $CHECK -eq 1 ] && ! git rev-parse -q --verify HEAD >/dev/null 2>&1; then
  violation "the repository has no commits, so there is no HEAD to check against" "$BEFORE"
  fail ""
fi

# --- the model and the layout -------------------------------------------------------

if has "$PD/DO.md" && has "$PD/TODO.md"; then
  violation "both $PD/DO.md and $PD/TODO.md exist, so which one is the root plan is ambiguous" \
    "keep the one the project's plans use, and move or remove the other (your call)"
  fail ""
fi
if has "$PD/DO.md"; then MODEL=DO.md
elif has "$PD/TODO.md"; then MODEL=TODO.md
else
  violation "there is no root plan, $PD/DO.md or $PD/TODO.md, so there is no revision to close" \
    "check you are in the right repository; a revision is opened with /master-plan"
  fail ""
fi
case "$MODEL" in TODO.md) OTHER=DO.md ;; *) OTHER=TODO.md ;; esac
ROOT_PLAN="$PD/$MODEL"; R_ROOT="$ROOT_PLAN"; REV="$PD/$LABEL/_$MODEL"; R_REV="$REV"

if [ $CHECK -eq 1 ]; then
  # HEAD's layout, as check_layout reads it: the first **Layout** line outside fences.
  v="$(src "$ROOT_PLAN" | awk '
    /^[ \t]*```/ { fence = !fence; next }
    !fence && /^\*\*Layout\*\*:/ { v = $0; sub(/^\*\*Layout\*\*:[ \t]*/, "", v); sub(/[ \t\r]+$/, "", v); print v; exit }
  ')" || die "awk failed reading the **Layout** header of $ROOT_PLAN at HEAD"
  if [ "$v" = revisions ]; then MLAYOUT=revisions; else MLAYOUT=legacy; fi
else
  master_files ""
fi
R_LAYOUT="$MLAYOUT"

# --- revisions: the stamp -------------------------------------------------------------

NOTOPEN="only an open revision ([~]) is closed; if this one is open, mark it [~] first (your call)"
IDX_N=""; IDX_LINE=""; ST_N=""
stamp() {
  local out mk v n rec IFS
  # The label's line under `## Revisions`, matched whole: the first word after the marker.
  out="$(src "$ROOT_PLAN" | L="$LABEL" awk '
    { sub(/\r$/, "") }
    /^[ \t]*```/ { fence = !fence; next }
    fence { next }
    /^## / { insec = ($0 ~ /^## Revisions[ \t]*$/); next }
    insec && /^- \[[ ~x!-]\] / { split(substr($0, 7), a, /[ \t]+/); if (a[1] == ENVIRON["L"]) { print NR "\t" $0; exit } }
  ')" || die "awk failed reading the revisions of $ROOT_PLAN"
  if [ -z "$out" ]; then
    if [ $CHECK -eq 1 ]; then
      violation "$ROOT_PLAN at HEAD lists no revision $LABEL" "$BEFORE"; fail ""
    fi
    refuse "$ROOT_PLAN lists no revision $LABEL" "check the label against the \`## Revisions\` lines"
  fi
  IDX_N="${out%%"$TAB"*}"; IDX_LINE="${out#*"$TAB"}"; mk="${IDX_LINE:3:1}"
  if [ "$mk" != "~" ]; then
    if [ $CHECK -eq 1 ]; then
      violation "$ROOT_PLAN:$IDX_N at HEAD marks revision $LABEL [$mk], not [~]" "$BEFORE"; fail ""
    fi
    case "$mk" in
      x) refuse "revision $LABEL is already closed: $ROOT_PLAN:$IDX_N marks it [x]" "nothing to do" ;;
      *) refuse "revision $LABEL is not open: $ROOT_PLAN:$IDX_N marks it [$mk]" "$NOTOPEN" ;;
    esac
  fi
  out="$(src "$REV" | awk '/^\*\*Status\*\*:/ { v = $0; sub(/^\*\*Status\*\*:[ \t]*/, "", v); sub(/[ \t\r]+$/, "", v); print NR "\t" v; exit }')" \
    || die "awk failed reading the status of $REV"
  if [ -z "$out" ]; then
    violation "$REV has no **Status** line, so it cannot be stamped closed" "add \`**Status**: open\` under its title, then run this again"
    fail ""
  fi
  ST_N="${out%%"$TAB"*}"; v="${out#*"$TAB"}"
  if [ "$v" != open ]; then
    if [ $CHECK -eq 1 ]; then
      violation "$REV:$ST_N at HEAD reads \`**Status**: $v\`, not open" "$BEFORE"; fail ""
    fi
    case "$v" in
      closed*) refuse "$REV:$ST_N is already stamped \`$v\`, but $ROOT_PLAN:$IDX_N marks the revision open" \
                 "mark $ROOT_PLAN:$IDX_N [x]: the revision has closed" ;;
      *)       refuse "$REV:$ST_N reads \`**Status**: $v\`, not \`open\`" "set it to \`**Status**: open\` if the revision is open (your call)" ;;
    esac
  fi
  # Open items at any indent, outside fences: the check /hitl-step makes before calling a
  # plan complete, so "closable" and "complete" cannot disagree.
  out="$(src "$REV" | awk "$OPEN_AWK")" || die "awk failed reading the items of $REV"
  n=0; v=""
  IFS="$NL"
  for rec in $out; do
    case "$rec" in
      OPEN"$TAB"*)
        rec="${rec#OPEN"$TAB"}"; n=$((n + 1))
        v="$v$NL$REV:${rec%%"$TAB"*} ${rec##*"$TAB"}" ;;
    esac
  done
  unset IFS
  if [ $n -gt 0 ]; then
    v="$(printf '%s' "$v" | awk '{ sub(/\r$/, ""); print }')" || die "awk failed listing open items"
    refuse "revision $LABEL still has $n unfinished item(s):$v" \
      "finish each, descope it ([-]), or move it to another revision; whether the revision is finished is your call"
  fi
  R_EDITS="$REV:$ST_N: **Status**: closed $DASH $DATE$NL$ROOT_PLAN:$IDX_N: - [x]${IDX_LINE:5}"
  R_CHANGE=stamp
}

# A branch plan inside the revision still stamped active: its branch may not have merged.
stamp_warnings() {
  local p s IFS="$NL"
  [ -d "$PD/$LABEL" ] || return 0
  for p in $(find "$PD/$LABEL" -type f \( -name "$MODEL" -o -name "$OTHER" \) | sort || die "find failed listing $PD/$LABEL"); do
    s="$(status_of "$p")"
    case "$s" in merged*) ;; *) warn "$p is stamped \`${s:-no status}\`: its branch may not have merged" ;; esac
  done
}

# --- legacy: the cut, the pointer and the moves ------------------------------------------

START=0; END=0; CLOSED=0; LASTPTR=0; LASTNB=0; DEFERRED=0; SUBTITLE=""
extract() {
  local out rec typ n val b flat seen="" opn=0 items="" IFS dirs s pf
  START="$(src "$ROOT_PLAN" | section_line /dev/stdin "$LABEL")"
  if [ -z "$START" ]; then
    if [ $CHECK -eq 1 ]; then
      violation "$ROOT_PLAN at HEAD has no section for revision $LABEL" "$BEFORE"; fail ""
    fi
    n="$(src "$ROOT_PLAN" | pointer_line /dev/stdin "$LABEL")"
    if [ -n "$n" ]; then
      refuse "revision $LABEL is already closed: $ROOT_PLAN:$n is its pointer" "nothing to do"
    fi
    refuse "$ROOT_PLAN has no \`## Subgoals $DASH revision $LABEL\` section" \
      "check the label; a bare \`## Subgoals\` heading carries none, and cannot be closed"
  fi
  # One pass for everything the cut needs. A line inside a fenced block, or a fence line,
  # is never a heading, an item or a backlink.
  out="$(src "$ROOT_PLAN" | S="$START" awk '
    BEGIN { s = ENVIRON["S"] + 0 }
    { sub(/\r$/, ""); f = fence; if ($0 ~ /^[ \t]*```/) { fence = !fence; f = 1 } }
    NR == s { insec = 1; t = $0; p = index(t, ": "); print "SUB\t" (p ? substr(t, p + 2) : ""); next }
    insec && !f && /^## / { insec = 0; print "END\t" NR - 1 }
    insec {
      if (!f && $0 ~ /^[ \t]*- \[[ ~!]\]( |$)/) print "OPEN\t" NR "\t" $0
      if (!f && $0 ~ /^[ \t]*> \*\*Branch:\*\*[ \t]+[^ \t]/) {
        b = $0; sub(/^[ \t]*> \*\*Branch:\*\*[ \t]+/, "", b); sub(/[ \t].*$/, "", b); print "BRANCH\t" NR "\t" b
      }
      next
    }
    !f && /^## / {
      incl = 0
      if ($0 ~ /^## Closed revisions[ \t]*$/ && !ch) { ch = NR; incl = 1; print "CLOSED\t" NR }
      if ($0 ~ /^## Deferred[ \t]*$/ && !dh) { dh = NR; print "DEFERRED\t" NR }
      next
    }
    incl && !f && index($0, "- **Revision ") == 1 { print "LASTPTR\t" NR }
    incl && $0 !~ /^[ \t]*$/ { print "LASTNB\t" NR }
    END { if (insec) print "END\t" NR }
  ')" || die "awk failed reading the sections of $ROOT_PLAN"
  IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; val="${rec#*"$TAB"}"; n="${val%%"$TAB"*}"
    case "$typ" in
      SUB)      SUBTITLE="$val" ;;
      END)      END="$n" ;;
      CLOSED)   CLOSED="$n" ;;
      DEFERRED) DEFERRED="$n" ;;
      LASTPTR)  LASTPTR="$n" ;;
      LASTNB)   LASTNB="$n" ;;
      OPEN)     opn=$((opn + 1)); items="$items$NL$ROOT_PLAN:$n ${val#*"$TAB"}" ;;
      BRANCH)
        b="${val#*"$TAB"}"
        case " $seen " in *" $b "*) ;; *) seen="${seen:+$seen }$b" ;; esac ;;
    esac
  done
  unset IFS
  R_SECTION="$ROOT_PLAN:$START-$END"
  if [ $opn -gt 0 ]; then
    if [ $CHECK -eq 1 ]; then
      violation "the section at HEAD has $opn unfinished item(s)" "$BEFORE"; fail ""
    fi
    refuse "revision $LABEL still has $opn unfinished item(s):$items" \
      "finish each, descope it ([-]), or move it to another revision; whether the revision is finished is your call"
  fi
  if has "$REV"; then
    if [ $CHECK -eq 1 ]; then
      violation "$REV already exists at HEAD" "$BEFORE"; fail ""
    fi
    refuse "$REV already exists, so revision $LABEL looks closed already" "nothing to do, or remove a stale $REV first (your call)"
  fi
  R_POINTER="- **Revision $LABEL**${SUBTITLE:+ $DASH $SUBTITLE} $DASH closed. See \`$REV\`."
  # The moves: each backlinked branch's plan directory, matched whole by its flattened name.
  dirs="$(plan_dirs)"
  for b in $seen; do
    flat="$(printf '%s' "$b" | tr / -)" || die "tr failed flattening $b"
    if has "$PD/$flat"; then
      # The command runs each move as printed, so a move is printed only for a plain name: a
      # backlink is text from the plan, and $( ) or ; in it would be run by the shell.
      case "$flat" in
        .|..|*[!A-Za-z0-9._+-]*)
          violation "the backlink \`$b\` names a plan directory that is not a plain name, so no move is printed for it" \
            "check the backlink; move the directory by hand if it is genuine (your call)"
          continue ;;
      esac
      if has "$PD/$LABEL/$flat"; then
        violation "both $PD/$flat and $PD/$LABEL/$flat exist, so one is a copy" \
          "compare them and remove the stale one (your call), then run this again"
        continue
      fi
      pf=""
      if has "$PD/$flat/$MODEL"; then pf="$PD/$flat/$MODEL"; elif has "$PD/$flat/$OTHER"; then pf="$PD/$flat/$OTHER"; fi
      s=""; [ -z "$pf" ] || s="$(status_src "$pf")"
      case "$s" in
        merged*) R_MOVES="${R_MOVES:+$R_MOVES$NL}git mv $PD/$flat $PD/$LABEL/$flat" ;;
        *) warn "$PD/$flat is not stamped merged (${s:-no status}), so it stays flat: file it by hand once it merges" ;;
      esac
    else
      if ! printf '%s\n' "$dirs" | F="$flat" awk '{ n = $0; sub(/.*\//, "", n) } n == ENVIRON["F"] { found = 1; exit } END { exit !found }'; then
        warn "no plan directory named $flat under $PD/, for the branch $b backlinked in the section"
      fi
    fi
  done
  if [ "$VIOL" -gt 0 ]; then fail ""; fi
  R_CHANGE=extract
}

case "$MLAYOUT" in
  none)      violation "there is no root plan, so there is no revision to close" "a revision is opened with /master-plan"; fail "" ;;
  revisions) [ -z "$RENDER" ] || usage "--render is for a legacy root plan; under a revisions index the close is two edits"
             stamp; [ $CHECK -eq 1 ] || stamp_warnings ;;
  legacy)    extract ;;
esac

# --- the files as closing writes them ---------------------------------------------------

# The section without its trailing blank lines: in the root plan they only separate it from
# the next heading, and tool output drops them, so a faithful Write of this render would
# never match. Blank lines inside it are held back and printed, as they were, at the next line.
render_archive() { src "$ROOT_PLAN" | S="$START" E="$END" awk 'NR >= ENVIRON["S"] + 0 && NR <= ENVIRON["E"] + 0 { sub(/\r$/, ""); if ($0 ~ /^[ \t]*$/) { held = held $0 "\n"; next } printf "%s", held; held = ""; print }' || die "awk failed rendering the archive"; }

render_root() {
  local after=0 blank=0 before=0 atend=0
  if [ "$CLOSED" -gt 0 ]; then
    if [ "$LASTPTR" -gt 0 ]; then after="$LASTPTR"
    elif [ "$LASTNB" -gt 0 ]; then after="$LASTNB"; blank=1
    else after="$CLOSED"; blank=1; fi
  elif [ "$DEFERRED" -gt 0 ]; then before="$DEFERRED"
  else atend=1; fi
  src "$ROOT_PLAN" | S="$START" E="$END" P="$R_POINTER" A="$after" B="$blank" D="$before" Z="$atend" awk '
    BEGIN { s = ENVIRON["S"] + 0; e = ENVIRON["E"] + 0; a = ENVIRON["A"] + 0; d = ENVIRON["D"] + 0; p = ENVIRON["P"] }
    { sub(/\r$/, "") }
    NR >= s && NR <= e { next }
    NR == d { if (prev != "") print ""; print "## Closed revisions"; print ""; print p; print "" }
    { print; prev = $0 }
    NR == a { if (ENVIRON["B"] == "1") print ""; print p }
    END { if (ENVIRON["Z"] == "1") { if (prev != "") print ""; print "## Closed revisions"; print ""; print p } }
  ' || die "awk failed rendering $ROOT_PLAN"
}

render() {
  case "$RENDER" in
    archive) render_archive ;;
    root)    render_root ;;
  esac
}

# --- the check: what HEAD says closing writes, against the working tree ------------------

replaced() {  # replaced <path> <line> <text>: HEAD's file with one line rewritten
  src "$1" | N="$2" T="$3" awk '{ sub(/\r$/, "") } NR == ENVIRON["N"] + 0 { print ENVIRON["T"]; next } { print }' \
    || die "awk failed rewriting $1"
}
same() {  # same <working-tree file>: stdin matches it, trailing CRs dropped on both sides
  local want
  want="$(cat; echo .)" || die "cat failed reading what closing writes"
  [ -f "$1" ] || return 1
  [ "$want" = "$(lf "$1"; echo .)" ]
}

if [ $CHECK -eq 1 ]; then
  case "$R_CHANGE" in
    stamp)
      replaced "$REV" "$ST_N" "**Status**: closed $DASH $DATE" | same "$REV" \
        || violation "$REV does not read as stamped: line $ST_N should be \`**Status**: closed $DASH $DATE\`, and nothing else should change" \
             "edit line $ST_N to that, and undo any other change"
      replaced "$ROOT_PLAN" "$IDX_N" "- [x]${IDX_LINE:5}" | same "$ROOT_PLAN" \
        || violation "$ROOT_PLAN does not read as stamped: line $IDX_N should be \`- [x]${IDX_LINE:5}\`, and nothing else should change" \
             "edit line $IDX_N to that, and undo any other change" ;;
    extract)
      render_archive | same "$REV" \
        || violation "$REV is not the section, verbatim" "write it again from \`$PROG $LABEL --date $DATE --render archive\`, run before the cut"
      render_root | same "$ROOT_PLAN" \
        || violation "$ROOT_PLAN is not the root plan with the section cut and the pointer added" \
             "write it again from \`$PROG $LABEL --date $DATE --render root\`, run before the cut"
      IFS="$NL"
      for m in $R_MOVES; do
        flat="${m##*/}"
        if [ -e "$PD/$flat" ] || [ ! -d "$PD/$LABEL/$flat" ]; then
          violation "$PD/$flat has not been moved into $PD/$LABEL/" "run: $m"
        fi
      done
      unset IFS ;;
  esac
  if [ "$VIOL" -gt 0 ]; then fail ""; fi
  R_RESULT=verified
  finish
fi

R_RESULT=proposed
finish
