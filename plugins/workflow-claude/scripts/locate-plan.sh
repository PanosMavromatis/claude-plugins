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

NL='
'
TAB="$(printf '\t')"
DASH='—'
PD=docs/plan

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <TODO.md|DO.md> [--goal <line>] [--branch <name>] [--] [path]" >&2
  exit 2
}

die() {  # die <message> [status]: a tool failed in a way the rules cannot explain
  local st=$? tool path   # $? is the failed command's, as `cmd || die "…"` leaves it
  if [ $# -ge 2 ]; then st="$2"; fi
  echo "locate-plan.sh: $1" >&2
  tool="${1%% *}"
  case "$tool" in
    awk|find|sort|git)   # name the binary that failed, so a broken PATH shows itself
      path="$(command -v "$tool" 2>/dev/null)" || path=""
      if [ "$st" -eq 127 ]; then
        echo "hint: $tool exited 127 (command not found)${path:+; the $tool first on PATH is $path}; check PATH" >&2
      elif [ -n "$path" ]; then
        echo "hint: the $tool first on PATH is $path, and it exited with status $st; check PATH, or that $tool" >&2
      else
        echo "hint: no $tool is on PATH; check PATH" >&2
      fi ;;
  esac
  exit 3
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

warn() { R_WARN="${R_WARN:+$R_WARN$NL}$1"; }
violation() {  # violation <problem> <fix>
  R_PROB="${R_PROB:+$R_PROB$NL}$1"; R_FIX="${R_FIX:+$R_FIX$NL}$2"; VIOL=$((VIOL + 1))
}

# A value with several items puts the first on the key line and each further one on
# a continuation line indented two spaces; an empty value is a dash.
emit() {
  local key="$1" val="$2" line first=1 IFS="$NL"
  if [ -z "$val" ]; then printf '%s: %s\n' "$key" "$DASH"; return 0; fi
  for line in $val; do
    if [ $first -eq 1 ]; then printf '%s: %s\n' "$key" "$line"; first=0
    else printf '  %s\n' "$line"; fi
  done
}

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

# E15: a file the rules need but cannot read. Checked before every read, because a failed
# read would otherwise pass as an empty answer wherever `set -e` does not reach.
need_file() {  # need_file <file> <rung>
  if [ ! -r "$1" ]; then violation "$1 cannot be read" "chmod u+r $1"; fail "$2"; fi
  return 0
}

# E15 for every directory under docs/plan/ that cannot be listed or entered: a plan inside
# one would be missing from rung 2's duplicate check and from rung 4, without notice.
scan_dirs() {
  local all d st=0 IFS="$NL"
  if [ ! -d "$PD" ]; then return 0; fi
  # find fails exactly when it meets such a directory; the loop names each one.
  if all="$(find "$PD" -type d 2>/dev/null)"; then :; else st=$?; fi
  for d in $all; do
    if [ ! -r "$d" ] || [ ! -x "$d" ]; then violation "$d/ cannot be entered or listed" "chmod u+rx $d"; fi
  done
  if [ "$VIOL" -gt 0 ]; then fail ""; fi
  if [ "$st" -ne 0 ]; then die "find failed under $PD with status $st"; fi
  return 0
}

list_named() {  # every file of that name under docs/plan/, sorted; scan_dirs runs first
  local out
  if [ ! -d "$PD" ]; then return 0; fi
  out="$(find "$PD" -type f -name "$1")" || die "find failed listing $1 under $PD"
  if [ -n "$out" ]; then printf '%s\n' "$out" | sort || die "sort failed"; fi
  return 0
}

# A plan's status is the first **Status** line anywhere in it: the rule file-plans.sh
# applies, and the two readers must agree.
status_of() {
  awk '/^\*\*Status\*\*:/ { sub(/^\*\*Status\*\*:[ \t]*/, ""); sub(/[ \t\r]+$/, ""); print; exit }' "$1" \
    || die "awk failed reading the status of $1"
}

count_items() {
  if [ -z "$1" ]; then echo 0; return 0; fi
  printf '%s\n' "$1" | awk 'END { print NR }' || die "awk failed counting a list"
}

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

# What git knows of a missing file: "head" if HEAD has it (deleted, not yet committed),
# else the commit that deleted it (12 hex), else nothing: never committed, so a fix must
# say create, not restore. HEAD's history only, since other branches are other work.
history_of() {  # history_of <path>
  local st sha
  if git rev-parse -q --verify HEAD >/dev/null 2>&1; then :; else
    st=$?; if [ "$st" -eq 1 ]; then return 0; fi   # no commits yet: nothing was committed
    die "git rev-parse --verify HEAD failed with status $st" "$st"
  fi
  if git cat-file -e "HEAD:$1" 2>/dev/null; then echo head; return 0; else st=$?; fi
  if [ "$st" -ne 128 ]; then die "git cat-file failed with status $st" "$st"; fi
  sha="$(git rev-list -n1 HEAD -- "$1")" || die "git rev-list failed reading the history of $1"
  if [ -n "$sha" ]; then printf '%s\n' "${sha:0:12}"; fi
  return 0
}

goal_dir() {  # the goal-file directory of a per-goal plan: TODO/ (or DO/) beside it
  case "$(dirname "$1")" in
    .) printf '%s' "${MODEL%.md}" ;;
    *) printf '%s/%s' "$(dirname "$1")" "${MODEL%.md}" ;;
  esac
}

# Goal files name a goal by number and slug: lowercase, runs of anything else as one `-`,
# at most 40 characters. A title is an index line's text after its marker and number.
SLUG_AWK='
  function slug(s) {
    s = tolower(s); gsub(/[^a-z0-9]+/, "-", s); sub(/^-+/, "", s); sub(/-+$/, "", s)
    if (40 < length(s)) { s = substr(s, 1, 40); sub(/-+$/, "", s) }
    return s == "" ? "goal" : s
  }
  function title(s) {
    sub(/^[ \t]*- \[.\][ \t]*/, "", s); sub(/^[0-9]+[a-z]?([ \t]+|$)/, "", s)
    sub(/^(—|-|:)[ \t]*/, "", s); sub(/[ \t\r]+$/, "", s)
    return s
  }
  function num(s) { sub(/^0+/, "", s); return s == "" || s ~ /^[a-z]/ ? "0" s : s }'

# The **Layout** header, outside fenced code blocks. Sets LAYOUT_V; on a value that is
# unknown, or in the wrong place, records E8 and returns 1.
check_layout() {  # check_layout <file> <rung>; called as a condition, so check everything here
  local f="$1" out n v
  LAYOUT_V=legacy
  need_file "$f" "$2"
  out="$(awk '
    /^[ \t]*```/ { fence = !fence; next }
    !fence && /^\*\*Layout\*\*:/ { v = $0; sub(/^\*\*Layout\*\*:[ \t]*/, "", v); sub(/[ \t\r]+$/, "", v); print NR "\t" v; exit }
  ' "$f")" || die "awk failed reading the **Layout** header of $f"
  if [ -z "$out" ]; then return 0; fi
  n="${out%%"$TAB"*}"; v="${out#*"$TAB"}"
  case "$v" in
    legacy) return 0 ;;
    revisions) if [ "$f" = "$ROOT_PLAN" ]; then LAYOUT_V=revisions; return 0; fi ;;
    per-goal)  if [ "$f" != "$ROOT_PLAN" ]; then LAYOUT_V=per-goal; return 0; fi ;;
  esac
  layout_fix "$f" "$n" "$v"
  violation "$f:$n has \`**Layout**: $v\`, which is not valid there" "$LFIX"
  return 1
}

# E8's fix, from what the file shows. The root plan: a `## Revisions` heading means it is
# an index with the header misspelt; otherwise nothing justifies a header there. A branch
# plan: numbered items or goal files mean it is per-goal; otherwise it never was.
layout_fix() {  # layout_fix <file> <line> <value>; sets LFIX
  local f="$1" n="$2" v="$3" ev g gf=""
  if [ "$f" = "$ROOT_PLAN" ]; then
    ev="$(awk '/^[ \t]*```/ { fence = !fence; next } !fence && /^## Revisions[ \t\r]*$/ { print "y"; exit }' "$f")" \
      || die "awk failed looking for a Revisions section in $f"
    if [ -n "$ev" ]; then
      LFIX="correct line $n to \`**Layout**: revisions\`: the file has a \`## Revisions\` section, so it is the revisions index"
    else
      LFIX="remove line $n: $f takes only \`revisions\`, for an index with a \`## Revisions\` section, and it has none"
    fi
    return 0
  fi
  ev="$(awk '
    /^[ \t]*```/ { fence = !fence; next }
    fence { next }
    /^- \[[ ~x!-]\]( |$)/ { k++; if ($0 ~ /^- \[.\] [0-9]+[a-z]?( |$)/) m++ }
    END { if (0 < k && m == k) print "y" }' "$f")" || die "awk failed reading the items of $f"
  g="$(goal_dir "$f")"
  if [ -d "$g" ] && [ -r "$g" ] && [ -x "$g" ]; then
    gf="$(find "$g" -maxdepth 1 -type f -name '[0-9]*-*.md' | sort)" || die "find failed listing $g"
  fi
  if [ -n "$ev" ] && [ -n "$gf" ]; then
    LFIX="correct line $n to \`**Layout**: per-goal\`: every item is numbered and $g/ holds goal files"
  elif [ -n "$gf" ]; then
    LFIX="correct line $n to \`**Layout**: per-goal\`: $g/ holds goal files"
  elif [ -n "$ev" ]; then
    LFIX="correct line $n to \`**Layout**: per-goal\`: every item is numbered (its goal files then go in $g/)"
  else
    LFIX="remove line $n: the items are unnumbered and there is no $g/, so the plan was never per-goal"
  fi
}

# The open revisions of a root index. Sets OPEN_LIST and OPEN_N; records E5, E6 and E7
# for every violation and fails at <rung> if there were any.
index_open() {
  local idx="$1" rung="$2" out rec typ rest n val p o mk canon hist close fx IFS="$NL"
  OPEN_LIST=""; OPEN_N=0
  need_file "$idx" "$rung"
  # A revision line is `- [m] <label>`, then the end of the line or ` — <note>`; a label
  # has no space, no `/`, no `—`, and does not start with `#` or `-`. A line that breaks
  # this is printed with the canonical form it most likely meant, for E6's fix.
  out="$(awk '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t\r]+$/, "", s); return s }
    function canon(s,   mk, p, lab, note) {
      sub(/\r$/, "", s); sub(/^[-*+][ \t]*/, "", s)
      if (s !~ /^\[.\]/) return "\t"
      mk = substr(s, 2, 1); s = trim(substr(s, 4))
      p = index(s, "—")
      if (p) { lab = trim(substr(s, 1, p - 1)); note = trim(substr(s, p + length("—"))) } else { lab = s; note = "" }
      gsub(/[ \t]+/, "-", lab); gsub(/\t/, " ", note)
      if (lab == "" || lab ~ /\// || lab ~ /^[#-]/) return mk "\t"
      return mk "\t- [" mk "] " lab (note != "" ? " — " note : "")
    }
    /^[ \t]*```/ { fence = !fence; next }
    fence { next }
    /^\*\*Layout\*\*:/ && !hl { hl = NR }
    /^#/ {
      t = $0; sub(/^#+[ \t]*/, "", t)
      if ($0 !~ /^## Revisions[ \t\r]*$/ && tolower(t) ~ /^revisions?([^a-z]|$)/ && !near) near = NR "\t" $0
    }
    /^## / { insec = ($0 ~ /^## Revisions[ \t\r]*$/); if (insec) sec = 1; next }
    insec && (/^[-*+][ \t]/ || /^[-*+]\[/ || /^[-*+]$/) {
      if ($0 ~ /^- \[[ ~x!-]\] /) {
        rest = substr($0, 7); split(rest, a, /[ \t]+/); lab = a[1]
        after = trim(substr(rest, length(lab) + 1))
        if (lab != "" && lab !~ /\// && lab !~ /^[#-]/ && index(lab, "—") == 0 && (after == "" || index(after, "—") == 1)) {
          if (substr($0, 4, 1) == "~") print "OPEN\t" NR "\t" lab
          next
        }
      }
      print "BAD\t" NR "\t" canon($0) "\t" $0
    }
    END { if (!sec) print "NOSEC\t" hl "\t" near }
  ' "$idx")" || die "awk failed reading the revisions index $idx"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
    case "$typ" in
      NOSEC)
        # val is "<near-miss line>\t<its text>", or empty
        if [ -n "$val" ]; then
          fx="rename line ${val%%"$TAB"*}, \`${val#*"$TAB"}\`, to \`## Revisions\`"
        else
          fx="remove line $n (\`**Layout**: revisions\`), or add a \`## Revisions\` section listing the revisions"
        fi
        violation "$idx declares \`**Layout**: revisions\` (line $n) but has no \`## Revisions\` section" "$fx" ;;
      BAD)
        # val is "<marker>\t<canonical form>\t<the line>"
        mk="${val%%"$TAB"*}"; val="${val#*"$TAB"}"; canon="${val%%"$TAB"*}"; val="${val#*"$TAB"}"
        case "$mk" in
          ''|*[!\ ~x!-]*)
            if [ -n "$canon" ]; then
              fx="its marker [$mk] is not one of [ ] [~] [x] [!] [-]; choose one (your call) and write it as \`${canon/\[$mk\]/[m]}\`"
            else
              fx="write it as \`- [m] <label> — <note>\`, with m one of [ ] [~] [x] [!] [-]"
            fi ;;
          *)
            if [ -n "$canon" ]; then
              fx="write line $n as \`$canon\`"
              p="${canon#- \[?\] }"; p="${p%% — *}"
              if [ "$mk" = "~" ] && [ ! -f "$PD/$p/_$MODEL" ]; then
                fx="$fx; revision $p is then open, so it also needs $PD/$p/_$MODEL"
              fi
              case "$val" in *"$p"*) ;; *) fx="$fx (a label has no spaces; the label is your call)" ;; esac
            else
              fx="write it as \`- [m] <label> — <note>\`: a label is non-empty, with no space or \`/\`, and does not start with \`#\` or \`-\`"
            fi ;;
        esac
        violation "$idx:$n is not a revision line: \`$val\`" "$fx" ;;
      OPEN)
        p="$PD/$val/_$MODEL"; o="$PD/$val/_$OTHER"
        if [ -f "$p" ]; then
          OPEN_LIST="${OPEN_LIST:+$OPEN_LIST$NL}$p"; OPEN_N=$((OPEN_N + 1))
          continue
        fi
        hist="$(history_of "$p")" || exit 3
        close="or mark line $n [x] if the revision has closed"
        case "$hist" in
          head) fx="restore it: git checkout HEAD -- $p (it is deleted but the deletion is not committed); $close" ;;
          '')   if [ -f "$o" ]; then
                  fx="$p was never committed, so there is nothing to restore: git mv $o $p if that file is this revision's plan; $close"
                else
                  fx="$p was never committed, so there is nothing to restore: create it; $close"
                fi ;;
          *)    fx="restore it: git checkout $hist^ -- $p (it was deleted in $hist); $close" ;;
        esac
        if [ -f "$o" ]; then
          violation "revision $val is open at $idx:$n, but $p is missing ($o exists)" "$fx"
        else
          violation "revision $val is open at $idx:$n, but $p is missing" "$fx"
        fi ;;
    esac
  done
  if [ "$VIOL" -gt 0 ]; then fail "$rung"; fi
  return 0
}

# Item lines outside fenced code blocks, and the selection rules of both models.
SELECT_AWK='
  function item(s) { return s ~ /^[ \t]*- \[[ ~x!-]\] / || s ~ /^[ \t]*- \[[ ~x!-]\]$/ }
  /^[ \t]*```/ { fence = !fence; next }
  fence { next }
  /^## / { k++; T[k] = "H"; L[k] = NR; next }
  item($0) {
    k++; T[k] = "I"; L[k] = NR; X[k] = $0; I[k] = ($0 ~ /^[ \t]/) ? 1 : 0
    m = $0; sub(/^[ \t]*- \[/, "", m); M[k] = substr(m, 1, 1)
    if (pergoal && !I[k]) {
      if ($0 ~ /^- \[.\] [0-9]+[a-z]? / || $0 ~ /^- \[.\] [0-9]+[a-z]?$/) { nn = $0; sub(/^- \[.\] /, "", nn); sub(/[ \t].*$/, "", nn); print "NUM\t" NR "\t" nn }
      else print "BADIDX\t" NR "\t" $0
    }
    next
  }
  /^[-*+][ \t]*\[(.|..)?\]/ { print "W6\t" NR "\t" $0 }
  END {
    sel = 0
    if (goal > 0) {
      for (j = 1; j <= k; j++) if (T[j] == "I" && L[j] == goal) sel = j
      if (!sel || (todo && I[sel])) { print "GOALERR"; exit }
    } else if (todo) {
      for (j = 1; j <= k && !sel; j++) if (T[j] == "I" && !I[j] && M[j] == "~") sel = j
      for (j = 1; j <= k && !sel; j++) if (T[j] == "I" && !I[j] && M[j] == " ") sel = j
    } else {
      for (j = 1; j <= k && !sel; j++) if (T[j] == "I" && M[j] == " ") sel = j
    }
    if (sel) {
      print "NEXT\t" L[sel] "\t" X[sel]
      if (pergoal) { nn = X[sel]; sub(/^- \[.\] /, "", nn); sub(/[ \t].*$/, "", nn); print "NN\t" nn "\t" M[sel] }
      else if (todo) for (j = sel + 1; j <= k; j++) { if (T[j] == "H" || !I[j]) break; print "SUB\t" L[j] }
    }
    for (j = 1; j <= k; j++) if (T[j] == "I" && !I[j] && M[j] == "!") print "BLK\t" L[j]
  }'

# Every item line of a goal file, at any indent.
GOALFILE_AWK='
  /^[ \t]*```/ { fence = !fence; next }
  fence { next }
  /^[ \t]*- \[[ ~x!-]\] / || /^[ \t]*- \[[ ~x!-]\]$/ { print "SUB\t" NR; next }
  /^[-*+][ \t]*\[(.|..)?\]/ { print "W6\t" NR "\t" $0 }
  /^\*\*Goal\*\*:/ && !g { g = 1; v = $0; sub(/^\*\*Goal\*\*:[ \t]*/, "", v); print "GOAL\t" substr(v, 2, 1) }'

w6() {  # w6 <file> <line> <text>
  warn "$1:$2 looks like an item but its marker is not one of [ ] [~] [x] [!] [-], so it was ignored: \`$3\`"
}

# --- reading the resolved plan ----------------------------------------------------

goal_dir_ok() {  # goal_dir_ok <dir> <rung>: E15 for a goal directory that cannot be listed
  if [ -d "$1" ] && { [ ! -r "$1" ] || [ ! -x "$1" ]; }; then
    violation "$1/ cannot be entered or listed" "chmod u+rx $1"; fail "$2"
  fi
  return 0
}
goal_files() {  # goal_files <dir>: every file directly in it, sorted; run goal_dir_ok first
  if [ -d "$1" ]; then find "$1" -maxdepth 1 -type f | sort || die "find failed listing $1"; fi
  return 0
}

# E9's fixes, one per unnumbered index line: give it the number of an unclaimed goal file
# whose slug matches its title, else the next free number and the goal file to create.
e9_fixes() {  # e9_fixes <goal dir>; reads BAD ("<line>\t<text>" each), CLAIMED, FILES
  BAD="$BAD" CLAIMED="$CLAIMED" FILES="$FILES" GDIR="$1" awk "$SLUG_AWK"'
    function id_of(s) { return match(s, /^[0-9]+[a-z]?/) ? substr(s, 1, RLENGTH) : "" }
    function see(id) { if (max < id + 0) max = id + 0; match(id, /^[0-9]+/); if (w < RLENGTH) w = RLENGTH }
    BEGIN {
      w = 2; g = ENVIRON["GDIR"]
      n = split(ENVIRON["CLAIMED"], C, "\n"); for (i = 1; i <= n; i++) if (C[i] != "") { claimed[num(C[i])] = 1; see(C[i]) }
      n = split(ENVIRON["FILES"], F, "\n")
      for (i = 1; i <= n; i++) {
        b = F[i]; sub(/.*\//, "", b); id = id_of(b)
        if (id == "" || substr(b, length(id) + 1, 1) != "-" || b !~ /\.md$/) continue
        see(id)
        if (!(num(id) in claimed)) { u++; U[u] = b; US[u] = substr(b, length(id) + 2, length(b) - length(id) - 4) }
      }
      n = split(ENVIRON["BAD"], B, "\n")
      for (i = 1; i <= n; i++) {
        if (B[i] == "") continue
        line = B[i]; sub(/\t.*/, "", line); text = substr(B[i], length(line) + 2)
        mk = substr(text, 4, 1); t = title(text); s = slug(t); fix = ""
        for (j = 1; j <= u; j++) if (!used[j] && US[j] == s) {
          used[j] = 1; id = id_of(U[j])
          fix = "number it " id " to match its goal file " g "/" U[j] ": `- [" mk "] " id " — " t "`"; break
        }
        if (fix == "") {
          max++; id = sprintf("%0" w "d", max)
          fix = "number it " id ", the next free number, and create " g "/" id "-" s ".md: `- [" mk "] " id " — " t "`"
          left = ""; for (j = 1; j <= u; j++) if (!used[j]) left = left (left == "" ? "" : ", ") g "/" U[j]
          if (left != "") fix = fix "; no index line claims " left ", which may be this goal'"'"'s file"
        }
        print line "\t" fix "\t" text
      }
    }' </dev/null || die "awk failed working out goal numbers for $1"
}

# E10's fix: a file carrying goal NN's number in another form is probably its goal file;
# otherwise name the file to create, from the index line's title.
e10_fix() {  # e10_fix <goal dir> <NN> <index line text>; reads FILES
  FILES="$FILES" GDIR="$1" NN="$2" LINE="$3" awk "$SLUG_AWK"'
    BEGIN {
      g = ENVIRON["GDIR"]; nn = ENVIRON["NN"]; want = num(nn); s = slug(title(ENVIRON["LINE"]))
      n = split(ENVIRON["FILES"], F, "\n")
      for (i = 1; i <= n; i++) {
        b = F[i]; sub(/.*\//, "", b)
        if (!match(b, /^[0-9]+[a-z]?/)) continue
        id = substr(b, 1, RLENGTH); after = substr(b, RLENGTH + 1)
        if (num(id) != want || after ~ /^[a-z0-9]/) continue
        rest = after; sub(/^[-_. \t]+/, "", rest); sub(/\.[A-Za-z0-9]+$/, "", rest)
        k++; N[k] = b; T[k] = nn "-" (rest == "" ? s : slug(rest)) ".md"
      }
      if (k == 1) print "goal " nn "'"'"'s file is there under another name: git mv " g "/" N[1] " " g "/" T[1]
      else if (1 < k) { l = ""; for (i = 1; i <= k; i++) l = l (1 < i ? ", " : "") g "/" N[i]
        print "these carry goal " nn "'"'"'s number in another form: " l "; git mv the right one to " g "/" nn "-" s ".md" }
      else print "create " g "/" nn "-" s ".md"
    }' </dev/null || die "awk failed working out the goal file for $2"
}

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
