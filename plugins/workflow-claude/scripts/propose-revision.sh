#!/usr/bin/env bash
# Propose opening a revision: whether the label may be opened, where its master plan goes,
# and the root plan as it would read once the revision is listed in it.
#
# /master-plan runs this before drafting, and again with --render for the root plan it
# writes. The root plan has one of three layouts. With none, a revisions index is created.
# A revisions index gains the line `- [~] <label> — <note>`. A legacy root plan with no
# revision open is converted to an index: a legacy close already left each closed revision
# at docs/plan/<label>/_<model>, so only the shape of each closed pointer changes. A legacy
# root plan with a revision still open is refused, since moving that section is a
# judgement. A label is matched whole and literally, under any marker, so a closed revision
# is never opened again.
#
# The contract is propose-revision-spec.md in the feat-master-plan branch plan (found by
# name under docs/plan/, like any plan).
#
# READ-ONLY. Writes nothing: --render prints the root plan, and /master-plan writes it. Of
# git it runs only `rev-parse --show-toplevel`, and the reads locate-plan.sh's E7 makes.
# Deterministic, Bash 3.2.
#
# Usage: propose-revision.sh <label> [--model DO.md|TODO.md] [--dry-run <path>]
#        propose-revision.sh <label> [--model DO.md|TODO.md] --render <note>
# Exit:  0 = report, result proposed; with --render, the root plan, printed.
#        1 = report, result refused or error; with --render, the report goes to stderr.
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=propose-revision.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"
CR="$(printf '\r')"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <label> [--model DO.md|TODO.md] [--dry-run <path> | --render <note>]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

LABEL=""; NLAB=0; MODEL_ARG=""; DRY=""; DRY_SET=0; NOTE=""; RENDER=0
lab() {
  NLAB=$((NLAB + 1))
  [ $NLAB -eq 1 ] || usage "one label only, got another: '$1'"
  LABEL="$1"
}
while [ $# -gt 0 ]; do
  case "$1" in
    --model)   [ $# -ge 2 ] || usage "--model needs DO.md or TODO.md"; MODEL_ARG="$2"; shift 2 ;;
    --dry-run) [ $# -ge 2 ] || usage "--dry-run needs a path"; DRY="$2"; DRY_SET=1; shift 2 ;;
    --render)  [ $# -ge 2 ] || usage "--render needs the new index line's note"; NOTE="$2"; RENDER=1; shift 2 ;;
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
case "$MODEL_ARG" in
  ''|TODO.md|DO.md) ;;
  *) usage "--model takes TODO.md or DO.md, got '$MODEL_ARG'" ;;
esac
[ $DRY_SET -eq 0 ] || [ $RENDER -eq 0 ] || usage "--dry-run and --render are separate runs"
if [ $DRY_SET -eq 1 ]; then
  [ -n "$DRY" ] || usage "--dry-run needs a path"
  case "$DRY" in *"$NL"*|*"$TAB"*|*"$CR"*) usage "a dry-run path holds no newline, tab or carriage return" ;; esac
  case "/$DRY/" in */../*|*/./*) usage "give the dry-run path without . or .. components, got '$DRY'" ;; esac
fi
if [ $RENDER -eq 1 ]; then
  [ -n "$NOTE" ] || usage "the note is empty"
  case "$NOTE" in *"$NL"*|*"$TAB"*|*"$CR"*) usage "the note is one line, with no tab" ;; esac
fi

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_LAYOUT=""; R_ROOT=""; R_REV=""; R_PREV=""; R_CHANGE=""; R_OPEN=""
R_WARN=""; R_PROB=""; R_FIX=""; VIOL=0

report() {
  emit result "$R_RESULT";  emit layout "$R_LAYOUT";    emit root "$R_ROOT"
  emit revision "$R_REV";   emit previous "$R_PREV";    emit change "$R_CHANGE"
  emit open "$R_OPEN";      emit warnings "$R_WARN";    emit problem "$R_PROB"
  emit fix "$R_FIX"
}

finish() {  # print the report, or with --render the root plan, and exit
  if [ "$R_RESULT" = proposed ]; then
    if [ $RENDER -eq 1 ]; then render; else report; fi
    exit 0
  fi
  if [ $RENDER -eq 1 ]; then report >&2; else report; fi
  exit 1
}

fail() {  # fail <rung>: report every violation so far; the rung is the library's, unused
  R_RESULT=error; R_CHANGE=""; finish
}

refuse() {  # refuse <problem> <fix>
  R_RESULT=refused; R_CHANGE=""; R_PROB="$1"; R_FIX="$2"; finish
}

TAKEN="choose another label: a revision is never reopened, and a new one can say what it follows on from"

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
RP="$(pwd -P)" || die "cannot resolve the repository root $ROOT"

# --- the model: the root plan's file, or --model, or DO.md as /new-branch defaults ------

if [ -e "$PD/DO.md" ] && [ -e "$PD/TODO.md" ]; then
  violation "both $PD/DO.md and $PD/TODO.md exist, so which one is the root plan is ambiguous" \
    "keep the one the project's plans use, and move or remove the other (your call)"
  fail ""
fi
if [ -e "$PD/DO.md" ]; then MODEL=DO.md
elif [ -e "$PD/TODO.md" ]; then MODEL=TODO.md
else MODEL="${MODEL_ARG:-DO.md}"; fi
case "$MODEL" in TODO.md) OTHER=DO.md ;; *) OTHER=TODO.md ;; esac
ROOT_PLAN="$PD/$MODEL"; R_ROOT="$ROOT_PLAN"; R_REV="$PD/$LABEL/_$MODEL"
if [ -n "$MODEL_ARG" ] && [ "$MODEL_ARG" != "$MODEL" ]; then
  violation "--model $MODEL_ARG names the other file: the root plan is $ROOT_PLAN" \
    "leave --model out, or pass --model $MODEL"
  fail ""
fi

# --- the dry-run directory: outside docs/plan/, and holding neither file yet ---------
# Checked before the layout, since a dry run carries on past a refusal and needs a path.

if [ $DRY_SET -eq 1 ]; then
  case "$DRY" in /*) p="$DRY" ;; *) p="$RP/$DRY" ;; esac
  while [ "${p%/}" != "$p" ] && [ "$p" != / ]; do p="${p%/}"; done
  rest=""
  while [ "$p" != / ] && [ ! -e "$p" ] && [ ! -L "$p" ]; do rest="/${p##*/}$rest"; p="${p%/*}"; [ -n "$p" ] || p=/; done
  if [ ! -d "$p" ]; then
    violation "the dry-run path runs through a file that is not a directory" "give a directory, or a path that does not exist yet"
    fail ""
  fi
  canon="$(cd "$p" && pwd -P)" || die "cannot resolve the dry-run path"
  canon="${canon%/}$rest"
  case "$canon/" in
    "$RP/$PD/"*)
      violation "the dry-run path is inside $PD/, where its files would be read as plans" \
        "give a path outside $PD/, such as one in a scratch directory"
      fail "" ;;
  esac
  for f in "_$MODEL" "$MODEL"; do
    if [ -e "$canon/$f" ] || [ -L "$canon/$f" ]; then
      violation "the dry-run path already holds $f, which a dry run would overwrite" "remove it, or give another path"
    fi
  done
  if [ "$VIOL" -gt 0 ]; then fail ""; fi
fi

# --- the layout, and the refusals -------------------------------------------------

master_files ""
R_LAYOUT="$MLAYOUT"

taken_dir() {
  if [ -e "$PD/$LABEL" ] || [ -L "$PD/$LABEL" ]; then
    refuse "$PD/$LABEL already exists, so revision $LABEL has been opened before" "$TAKEN"
  fi
  return 0
}

previous() {  # previous <label>: its master plan, if it has one
  if [ -n "$1" ] && [ -f "$PD/$1/_$MODEL" ]; then R_PREV="$PD/$1/_$MODEL"; fi
  return 0
}

HEAD=0; LAST=0; STATUS=0; LAYLINE=0; PTRS=""
case "$MLAYOUT" in
  none)
    taken_dir
    R_CHANGE=create ;;

  revisions)
    # Every revision line under `## Revisions`, as index_open reads them: it has already
    # refused any that is malformed, so the label is the first word after the marker.
    out="$(awk '
      { sub(/\r$/, "") }
      /^[ \t]*```/ { fence = !fence; next }
      fence { next }
      /^## / { insec = ($0 ~ /^## Revisions[ \t]*$/); if (insec && !head) { head = NR; print "HEAD\t" NR }; next }
      insec && /^- \[[ ~x!-]\] / { split(substr($0, 7), a, /[ \t]+/); print "REV\t" NR "\t" a[1] }
    ' "$ROOT_PLAN")" || die "awk failed reading the revisions of $ROOT_PLAN"
    prev=""
    IFS="$NL"
    for rec in $out; do
      typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
      case "$typ" in
        HEAD) HEAD="$n" ;;
        REV)
          l="${rest#*"$TAB"}"
          if [ "$l" = "$LABEL" ]; then
            unset IFS; refuse "$ROOT_PLAN:$n already lists revision $LABEL" "$TAKEN"
          fi
          LAST="$n"; prev="$l" ;;
      esac
    done
    unset IFS
    taken_dir
    for p in $OPEN_LIST; do
      l="${p#"$PD"/}"; l="${l%/_"$MODEL"}"
      R_OPEN="${R_OPEN:+$R_OPEN, }$l"
    done
    if [ -n "$R_OPEN" ]; then
      warn "already open: $R_OPEN; with $LABEL open too, /new-branch and the step commands will ask which revision a branch belongs to"
    fi
    previous "$prev"
    R_CHANGE=append ;;

  legacy)
    n="$(section_line "$ROOT_PLAN" "$LABEL")"
    [ -z "$n" ] || refuse "$ROOT_PLAN:$n already has a section for revision $LABEL" "$TAKEN"
    n="$(pointer_line "$ROOT_PLAN" "$LABEL")"
    [ -z "$n" ] || refuse "$ROOT_PLAN:$n lists revision $LABEL as closed" "$TAKEN"
    taken_dir
    # What the conversion reads: the first **Status** and **Layout** lines, any section
    # still open, and each closed pointer under `## Closed revisions`, which must convert
    # to a line index_open accepts: a label, then nothing or ` — <note>`.
    out="$(awk '
      { sub(/\r$/, "") }
      /^[ \t]*```/ { fence = !fence; next }
      fence { next }
      /^\*\*Status\*\*:/ && !st { st = NR; print "STATUS\t" NR }
      /^\*\*Layout\*\*:/ && !ly { ly = NR; print "LAYOUT\t" NR }
      /^## / {
        if (!op && index($0, "## Subgoals") == 1) { op = 1; print "OPEN\t" NR "\t" $0 }
        insec = 0
        if ($0 ~ /^## Closed revisions[ \t]*$/ && !head) { head = NR; insec = 1; print "HEAD\t" NR }
        next
      }
      insec && index($0, "- **Revision ") == 1 {
        s = substr($0, 14); p = index(s, "**")
        lab = p > 1 ? substr(s, 1, p - 1) : ""; rest = p > 1 ? substr(s, p + 2) : ""
        r = rest; sub(/^[ \t]+/, "", r)
        if (lab == "" || lab ~ /[ \t\/]/ || lab ~ /^[#-]/ || index(lab, "—") || (rest != "" && (r == rest || index(r, "—") != 1)))
          print "BAD\t" NR "\t" $0
        else print "PTR\t" NR "\t" lab
      }
    ' "$ROOT_PLAN")" || die "awk failed reading the revisions of $ROOT_PLAN"
    prev=""; open=""
    IFS="$NL"
    for rec in $out; do
      typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
      case "$typ" in
        STATUS) STATUS="$n" ;;
        LAYOUT) LAYLINE="$n" ;;
        OPEN)   open="$n$TAB$val" ;;
        HEAD)   HEAD="$n" ;;
        PTR)    PTRS="${PTRS:+$PTRS }$n"; LAST="$n"; prev="$val" ;;
        BAD)    violation "$ROOT_PLAN:$n is a closed pointer that would not convert to an index line: \`$val\`" \
                  "write it as \`- **Revision <label>** — <note>\`, with a label holding no space or \`/\`" ;;
      esac
    done
    unset IFS
    if [ -n "$open" ]; then
      refuse "$ROOT_PLAN:${open%%"$TAB"*} has a section still open, \`${open#*"$TAB"}\`, which a revisions index has no place for" \
        "close that revision first (/close-revision), or convert the root plan to a revisions index by hand"
    fi
    if [ "$VIOL" -gt 0 ]; then fail ""; fi
    previous "$prev"
    R_CHANGE=convert ;;
esac
R_RESULT=proposed

# --- the root plan as it would read -------------------------------------------------

render() {
  local line="- [~] $LABEL $DASH $NOTE"
  case "$MLAYOUT" in
    none)
      printf '# Master plan\n\n**Layout**: revisions\n\n## Revisions\n\n%s\n' "$line" ;;
    revisions)
      NEWLINE="$line" HEAD="$HEAD" LAST="$LAST" awk '
        BEGIN { head = ENVIRON["HEAD"] + 0; last = ENVIRON["LAST"] + 0 }
        { sub(/\r$/, ""); print }
        last && NR == last { print ENVIRON["NEWLINE"] }
        !last && NR == head { print ""; print ENVIRON["NEWLINE"] }
      ' "$ROOT_PLAN" || die "awk failed rendering $ROOT_PLAN" ;;
    legacy)
      NEWLINE="$line" HEAD="$HEAD" LAST="$LAST" ST="$STATUS" LY="$LAYLINE" PTRS="$PTRS" awk '
        BEGIN {
          head = ENVIRON["HEAD"] + 0; last = ENVIRON["LAST"] + 0; st = ENVIRON["ST"] + 0; ly = ENVIRON["LY"] + 0
          n = split(ENVIRON["PTRS"], a, " "); for (i = 1; i <= n; i++) ptr[a[i]] = 1
        }
        { sub(/\r$/, "") }
        ly && NR == ly { print "**Layout**: revisions"; next }
        NR == head { print "## Revisions"; if (!last) { print ""; print ENVIRON["NEWLINE"] }; next }
        NR in ptr { s = substr($0, 14); p = index(s, "**"); print "- [x] " substr(s, 1, p - 1) substr(s, p + 2) }
        !(NR in ptr) { print }
        !ly && st && NR == st { print "**Layout**: revisions" }
        !ly && !st && NR == 1 { print ""; print "**Layout**: revisions" }
        last && NR == last { print ENVIRON["NEWLINE"] }
        { prior = $0 }
        END {
          if (!ly && !st && NR == 0) print "**Layout**: revisions"
          if (!head) { if (prior != "") print ""; print "## Revisions"; print ""; print ENVIRON["NEWLINE"] }
        }
      ' "$ROOT_PLAN" || die "awk failed rendering $ROOT_PLAN" ;;
  esac
}

finish
