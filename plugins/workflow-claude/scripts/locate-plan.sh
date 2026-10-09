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
# READ-ONLY. Writes nothing, temporary files included; runs only
# `git rev-parse --show-toplevel` and `git symbolic-ref`. Deterministic, Bash 3.2.
#
# Usage: locate-plan.sh <TODO.md|DO.md> [--goal <line>] [--branch <name>] [--] [path]
# Exit:  0 = report, result found/ask/none. 1 = report, result error.
#        2 = usage error, no report.

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

if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || [ -z "$ROOT" ]; then
  violation "the working directory is not inside a git repository" "run it from the repository"
  fail ""
fi
cd "$ROOT"
ROOTP="$(pwd -P)"
if [ $HAVE_BRANCH -eq 0 ]; then
  BRANCH="$(git symbolic-ref --short -q HEAD 2>/dev/null || true)"
fi

# --- helpers --------------------------------------------------------------------

list_named() {  # every file of that name under docs/plan/, sorted
  if [ -d "$PD" ]; then find "$PD" -type f -name "$1" | sort; fi
}

# A plan's status is the first **Status** line anywhere in it: the rule file-plans.sh
# applies, and the two readers must agree.
status_of() {
  awk '/^\*\*Status\*\*:/ { sub(/^\*\*Status\*\*:[ \t]*/, ""); sub(/[ \t\r]+$/, ""); print; exit }' "$1"
}

count_items() { if [ -z "$1" ]; then echo 0; else printf '%s\n' "$1" | awk 'END { print NR }'; fi; }

phys() {  # the physical absolute path of an existing file or directory
  local d
  if [ -d "$1" ]; then (cd "$1" && pwd -P)
  else d="$(cd "$(dirname "$1")" && pwd -P)"; printf '%s/%s\n' "${d%/}" "$(basename "$1")"; fi
}
relpath() {  # repository-relative form of a physical path; fails if outside
  case "$1" in
    "$ROOTP")   printf '' ;;
    "$ROOTP"/*) printf '%s' "${1#"$ROOTP"/}" ;;
    *)          return 1 ;;
  esac
}

# The **Layout** header, outside fenced code blocks. Sets LAYOUT_V; on a value that is
# unknown, or in the wrong place, records E8 and returns 1.
check_layout() {
  local f="$1" out n v
  LAYOUT_V=legacy
  out="$(awk '
    /^[ \t]*```/ { fence = !fence; next }
    !fence && /^\*\*Layout\*\*:/ { v = $0; sub(/^\*\*Layout\*\*:[ \t]*/, "", v); sub(/[ \t\r]+$/, "", v); print NR "\t" v; exit }
  ' "$f")"
  if [ -z "$out" ]; then return 0; fi
  n="${out%%"$TAB"*}"; v="${out#*"$TAB"}"
  case "$v" in
    legacy) return 0 ;;
    revisions) if [ "$f" = "$ROOT_PLAN" ]; then LAYOUT_V=revisions; return 0; fi ;;
    per-goal)  if [ "$f" != "$ROOT_PLAN" ]; then LAYOUT_V=per-goal; return 0; fi ;;
  esac
  violation "$f:$n has \`**Layout**: $v\`, which is not valid there" \
    "use \`revisions\` on $ROOT_PLAN only, and \`per-goal\` or \`legacy\` elsewhere"
  return 1
}

# The open revisions of a root index. Sets OPEN_LIST and OPEN_N; records E5, E6 and E7
# for every violation and fails at <rung> if there were any.
index_open() {
  local idx="$1" rung="$2" out rec typ rest n val p IFS="$NL"
  OPEN_LIST=""; OPEN_N=0
  out="$(awk '
    /^[ \t]*```/ { fence = !fence; next }
    fence { next }
    /^## / { insec = ($0 ~ /^## Revisions[ \t\r]*$/); if (insec) sec = 1; next }
    insec && (/^[-*+][ \t]/ || /^[-*+]\[/ || /^[-*+]$/) {
      if ($0 ~ /^- \[[ ~x!-]\] /) {
        rest = substr($0, 7); split(rest, a, /[ \t]+/); lab = a[1]
        if (lab != "" && lab !~ /\// && lab !~ /^[#-]/) {
          if (substr($0, 4, 1) == "~") print "OPEN\t" NR "\t" lab
          next
        }
      }
      print "BAD\t" NR "\t" $0
    }
    END { if (!sec) print "NOSEC" }
  ' "$idx")"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
    case "$typ" in
      NOSEC) violation "$idx declares \`**Layout**: revisions\` but has no \`## Revisions\` section" \
               "add the section, or remove the header" ;;
      BAD)   violation "$idx:$n is not a revision line: \`$val\`" \
               "write it as \`- [m] <label> — <note>\`, with m one of the five markers" ;;
      OPEN)
        p="$PD/$val/_$MODEL"
        if [ -f "$p" ]; then
          OPEN_LIST="${OPEN_LIST:+$OPEN_LIST$NL}$p"; OPEN_N=$((OPEN_N + 1))
        elif [ -f "$PD/$val/_$OTHER" ]; then
          violation "revision $val is open at $idx:$n, but $p is missing ($PD/$val/_$OTHER exists)" \
            "restore it (git log -- $PD/$val/), or mark line $n [x] if the revision has closed"
        else
          violation "revision $val is open at $idx:$n, but $p is missing" \
            "restore it (git log -- $PD/$val/), or mark line $n [x] if the revision has closed"
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
    if (pergoal && !I[k] && $0 !~ /^- \[.\] [0-9]+[a-z]? / && $0 !~ /^- \[.\] [0-9]+[a-z]?$/)
      print "BADIDX\t" NR "\t" $0
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

resolved() {  # resolved <file> <rung> <kind>
  local f="$1" rung="$2" out rec typ rest n nn="" nnm="" gdir matches gm="" IFS="$NL"
  R_RESULT=found; R_RUNG="$rung"; R_PLAN="$f"; R_KIND="$3"
  if ! check_layout "$f"; then fail "$rung"; fi
  R_LAYOUT="$LAYOUT_V"
  R_STATUS="$(status_of "$f")"
  case "$R_STATUS" in
    '')              if [ "$3" = branch ]; then warn "$f has no **Status** line, so it counts as active"; fi ;;
    active|open)     ;;
    merged*)         if [ "$3" = branch ]; then warn "$f is stamped merged: the branch was probably reopened after merging"; fi ;;
    closed*)         ;;
    *)               warn "$f has the status '$R_STATUS', which is none of active, merged, open or closed" ;;
  esac
  R_LINES="$(awk 'END { print NR }' "$f")"

  local pg=0; if [ "$R_LAYOUT" = per-goal ]; then pg=1; fi
  out="$(awk -v todo="$TODO" -v goal="$GOAL" -v pergoal="$pg" "$SELECT_AWK" "$f")"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; n="${rest%%"$TAB"*}"
    case "$typ" in
      NEXT)    R_NEXT="$f:$n ${rest#*"$TAB"}" ;;
      SUB)     R_SUB="${R_SUB:+$R_SUB$NL}$f:$n" ;;
      BLK)     R_BLOCKED="${R_BLOCKED:+$R_BLOCKED$NL}$f:$n" ;;
      W6)      w6 "$f" "$n" "${rest#*"$TAB"}" ;;
      NN)      nn="$n"; nnm="${rest#*"$TAB"}" ;;
      BADIDX)  violation "$f:$n has no goal number: \`${rest#*"$TAB"}\`" "write it as \`- [ ] NN — <goal>\`" ;;
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
  if [ "$VIOL" -gt 0 ]; then fail "$rung"; fi

  if [ -n "$nn" ]; then
    case "$(dirname "$f")" in
      .) gdir="${MODEL%.md}" ;;
      *) gdir="$(dirname "$f")/${MODEL%.md}" ;;
    esac
    matches=""
    if [ -d "$gdir" ]; then matches="$(find "$gdir" -maxdepth 1 -type f -name "$nn-*.md" | sort)"; fi
    case "$(count_items "$matches")" in
      0) violation "goal $nn has no file matching $gdir/$nn-*.md" \
           "create it, or correct the number on ${R_NEXT%% *}"; fail "$rung" ;;
      1) R_GOALFILE="$matches" ;;
      *) violation "goal $nn matches several files:$NL$matches" "remove or renumber the stale copy"; fail "$rung" ;;
    esac
    out="$(awk "$GOALFILE_AWK" "$R_GOALFILE")"
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

rung1() {
  local p="$ARG_PATH" r1="" r2="" ok1=0 ok2=0 out=0 rel f o kind
  if [ -n "$p" ] && [ -e "$p" ]; then
    if r1="$(relpath "$(phys "$p")")"; then ok1=1; else out=1; fi
  fi
  case "$p" in
    /*) ;;
    *) if [ -n "$p" ] && [ -e "$PD/$p" ]; then
         if r2="$(relpath "$(phys "$PD/$p")")"; then ok2=1; else out=1; fi
       fi ;;
  esac
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
        violation "${rel:-.}/ holds no $MODEL" "name the plan file itself, or a directory holding $MODEL"
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
    if ! check_layout "$f"; then fail 1; fi
    if [ "$LAYOUT_V" = revisions ]; then
      warn "$f is the revisions index, not a plan; it was followed as rung 3 would"
      index_open "$f" 1
      case "$OPEN_N" in
        0) violation "$f is the revisions index and no revision in it is [~]" \
             "name a plan file, or mark the open revision [~]"; fail 1 ;;
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
    $0 != "" && $0 != ENVIRON["ROOT_PLAN"] { n = split($0, p, "/"); if (n >= 2 && p[n-1] == ENVIRON["NAME"]) print }'
}

nostatus_warnings() {  # W1 for every listed branch plan with no **Status** line
  local f IFS="$NL"
  for f in $1; do
    if [ -z "$(status_of "$f")" ]; then warn "$f has no **Status** line, so it counts as active"; fi
  done
}

rung2() {
  local m o
  if [ -z "$BRANCH" ]; then
    warn "no current branch (a detached HEAD: a rebase, a bisect or a CI checkout), so rung 2 was skipped"
    return 0
  fi
  NAME="${BRANCH//\//-}"
  m="$(by_name "$ALL_F")"
  case "$(count_items "$m")" in
    0) ;;
    1) resolved "$m" 2 branch ;;
    *) nostatus_warnings "$m"
       ask 2 "$m" "The plan for $BRANCH exists in several places; one is a stale copy, so choose which to use." ;;
  esac
  o="$(by_name "$(list_named "$OTHER")")"
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
  if ! check_layout "$ROOT_PLAN"; then fail 3; fi
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
  local f active="" merged="" na nm IFS="$NL"
  for f in $ALL_F; do
    if [ "$f" = "$ROOT_PLAN" ]; then continue; fi
    case "$(status_of "$f")" in
      merged*) merged="${merged:+$merged$NL}$f" ;;
      *)       active="${active:+$active$NL}$f" ;;
    esac
  done
  na="$(count_items "$active")"; nm="$(count_items "$merged")"
  if [ "$na" -eq 1 ]; then resolved "$active" 4 branch; fi
  if [ "$na" -gt 1 ]; then
    nostatus_warnings "$active"
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
ALL_F="$(list_named "$MODEL")"
rung2
rung3
rung4
rung5
R_RESULT=none
R_MSG="No $MODEL plan was found: none for the branch, none under $PD/, none at the root."
finish
