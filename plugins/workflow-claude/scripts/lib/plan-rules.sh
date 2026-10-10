# Plan-convention rules shared by the plan scripts: locate-plan.sh, check-plan-index.sh
# and propose-branch-plan.sh. Sourced, never run. A rule that more than one of them
# applies is defined here once, because copies drift: a slug computed one way by the
# writer and another by the reader names a goal file the reader cannot find (E10).
#
# The caller, before sourcing, runs under `set -euo pipefail`, `set -f` and LC_ALL=C,
# and sets PROG (its name, for die's messages). Before calling anything here it sets
# MODEL and OTHER (TODO.md / DO.md), ROOT_PLAN ($PD/$MODEL), R_WARN, R_PROB, R_FIX and
# VIOL, and defines `fail <rung>`, which reports the violations collected so far in the
# caller's own report shape and exits. It also `cd`s to the repository root: every path
# here is repository-relative. SELECT_AWK takes the model as `-v todo=`, and a few
# functions read inputs their own comments name (FILES, CLAIMED, BAD).
#
# The contract is locate-plan-spec.md in the feat-plan-locator branch plan; the write
# side is per-goal-layout-spec.md in feat-per-goal-layout. Bash 3.2, BSD or GNU.

NL='
'
TAB="$(printf '\t')"
DASH='—'
PD=docs/plan

# --- failures and findings ------------------------------------------------------------

die() {  # die <message> [status]: a tool failed in a way the rules cannot explain
  local st=$? tool path   # $? is the failed command's, as `cmd || die "…"` leaves it
  if [ $# -ge 2 ]; then st="$2"; fi
  echo "$PROG: $1" >&2
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

# --- reading the repository -----------------------------------------------------------

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
      if ($0 ~ /^- \[.\] [0-9]+[a-z]? / || $0 ~ /^- \[.\] [0-9]+[a-z]?$/) {
        nn = $0; sub(/^- \[.\] /, "", nn); sub(/[ \t].*$/, "", nn); print "NUM\t" NR "\t" nn
        print "IDX\t" NR "\t" M[k] "\t" nn "\t" $0   # the whole index, for check-plan-index.sh
      }
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

# Every item line of a goal file, at any indent: SUB <line> <marker> <the line>.
GOALFILE_AWK='
  /^[ \t]*```/ { fence = !fence; next }
  fence { next }
  /^[ \t]*- \[[ ~x!-]\] / || /^[ \t]*- \[[ ~x!-]\]$/ { m = $0; sub(/^[ \t]*- \[/, "", m); print "SUB\t" NR "\t" substr(m, 1, 1) "\t" $0; next }
  /^[-*+][ \t]*\[(.|..)?\]/ { print "W6\t" NR "\t" $0 }
  /^\*\*Goal\*\*:/ && !g { g = 1; v = $0; sub(/^\*\*Goal\*\*:[ \t]*/, "", v); print "GOAL\t" substr(v, 2, 1) }'

# Every open item of a one-file plan, at any indent, outside fences, with the `## `
# heading it sits under: OPEN <line> <heading> <the line>, the heading empty above the
# first one. GOALS <n> counts its indent-0 items. W6 as above. check-plan-index.sh
# reports these for a legacy plan, where there is nothing to drift.
OPEN_AWK='
  /^[ \t]*```/ { fence = !fence; next }
  fence { next }
  /^## / { head = $0; next }
  /^[ \t]*- \[[ ~x!-]\] / || /^[ \t]*- \[[ ~x!-]\]$/ {
    if ($0 ~ /^-/) g++
    m = $0; sub(/^[ \t]*- \[/, "", m)
    if (substr(m, 1, 1) ~ /[ ~!]/) print "OPEN\t" NR "\t" head "\t" $0
    next
  }
  /^[-*+][ \t]*\[(.|..)?\]/ { print "W6\t" NR "\t" $0 }
  END { print "GOALS\t" g + 0 }'

# The subgoals of a master plan (a legacy one, or a revision's _F): one record per indent-0
# item outside fences, ITEM <line> <marker> <last line> <branches> <heading> <the line>.
# An item's block is its line and every following indented, non-blank line, up to the next
# indent-0 line, heading or blank line; the backlink goes after its last line. <branches>
# is every `> **Branch:**` value in the block, space-separated (a branch name has no
# space); <heading> is the `## ` heading the item sits under. /new-branch writes the
# backlink this reads, through propose-branch-plan.sh, and /smart-merge looks it up.
SUBGOALS_AWK='
  function flush() {
    if (cur) print "ITEM\t" cur "\t" mk "\t" last "\t" br "\t" head "\t" txt
    cur = 0
  }
  /^[ \t]*```/ { if (cur && /^[ \t]/) last = NR; else flush(); fence = !fence; next }
  fence { if (cur && /^[ \t]+[^ \t\r]/) last = NR; else flush(); next }
  /^## / { flush(); head = $0; sub(/[ \t\r]+$/, "", head); next }
  /^#/ { flush(); next }
  /^- \[[ ~x!-]\] / || /^- \[[ ~x!-]\]$/ { flush(); cur = NR; last = NR; mk = substr($0, 4, 1); br = ""; txt = $0; next }
  cur && /^[ \t]+[^ \t\r]/ {
    last = NR
    if ($0 ~ /^[ \t]+> \*\*Branch:\*\*[ \t]+[^ \t]/) {
      b = $0; sub(/^[ \t]+> \*\*Branch:\*\*[ \t]+/, "", b); sub(/[ \t\r].*$/, "", b)
      br = br (br == "" ? "" : " ") b
    }
    next
  }
  { flush() }
  END { flush() }'

w6() {  # w6 <file> <line> <text>
  warn "$1:$2 looks like an item but its marker is not one of [ ] [~] [x] [!] [-], so it was ignored: \`$3\`"
}

# --- goal files -----------------------------------------------------------------------

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
