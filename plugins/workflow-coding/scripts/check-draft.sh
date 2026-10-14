#!/usr/bin/env bash
# Check a revision's master plan twice: plan-drafter's reply before the user reviews it,
# for the draft's form, the trace's cover of its subgoals and, given the spec, that each
# tag names a part of it; and with --plan, the plan file as written, before the commit,
# for the form alone, since review edits, hand edits and a formatter's rewrite come after
# the first check.
#
# /master-plan writes the agent's reply, verbatim, to a file and runs this on it. The form
# is references/subdividing.md's, and subgoal blocks are read with lib/plan-rules.sh's
# SUBGOALS_AWK, the rule /new-branch and /smart-merge read a master plan by, so a draft
# that passes reads the same way to them. A tag that resolves names a real part of the
# spec; whether that part supports its subgoal is the review's judgement, not a rule's.
# A plan file has no trace: the trace numbers the draft as returned, and a review that
# merges, splits or reorders subgoals leaves its numbers pointing at the wrong ones.
#
# The rules, each broken one a problem: line with a fix: line. The draft is the fence's
# text in a reply, and the whole file with --plan, where only F1 to F6 apply:
#   S1 the reply's ## sections are Draft, Trace, Left out and Questions, in that order.
#      With none at the margin and ## Draft indented, the reply was copied inside the frame
#      Claude Code puts around a subagent's report, and is the session's to write again.
#   S2 ## Draft holds one ~~~markdown fence, closed; the draft is what it holds
#   F1 the draft's first line is `# Revision <label>`, the label --label gives if given
#   F2 **Status**: open, **Version**:, **Opened**: <a date> and **Spec**: come before the
#      first ## heading
#   F3 its ## headings are Preamble, Settled decisions and Subgoals, in that order
#   F4 no checkbox outside ## Subgoals: a settled decision is a plain bullet
#   F5 each subgoal is `- [ ] N.`, numbered from 1, in a two-line block whose second line
#      is `Scope: … Acceptance: …`; a blank line inside a subgoal ends its block early
#   F6 no `> **Branch:**` or `> **Done:**` line: later commands write those
#   T1 ## Trace has one `- N. <tag>; <tag>` line per subgoal, in order, no tag empty
#   T2 with --spec, each tag resolves: a "quoted phrase" occurs in the spec, whitespace
#      collapsed; §N names a heading numbered N; any other tag starts with a heading's
#      text. Headings inside fenced blocks do not count.
#
# With --spec, where: names the part of the spec each resolved tag points to, so that a
# subgoal in doubt is checked by reading that window alone: `N. <spec>:<from>-<to> <tag>`
# for a § or heading, its section up to the next heading at its level or above, less
# trailing blank lines; `N. <spec>:<line> <tag>` for a quoted phrase, the line it begins on.
# N is the subgoal the trace line tags. A reply whose only problems are tags that resolve
# nowhere is a question for the user, not a fresh reply, and its message says so.
#
# READ-ONLY. Writes nothing and runs no git; paths are taken as given. Of the library it
# uses die, violation, emit, need_file and SUBGOALS_AWK. Deterministic, Bash 3.2.
#
# Usage: check-draft.sh <reply> [--spec <path>] [--label <label>]
#        check-draft.sh --plan <plan> [--label <label>]
# Exit:  0 = clean. 1 = problems, or the file could not be checked (result: error).
#        2 = usage error, no report. 3 = a tool failed; message on stderr, no report.

set -euo pipefail
set -f
export LC_ALL=C
unset CDPATH

PROG=check-draft.sh
# The rules this script shares with the other plan scripts. A library that cannot be read
# is a broken install, which no report could explain.
LIB="$(dirname "$0")/lib/plan-rules.sh"
[ -r "$LIB" ] || { echo "$PROG: cannot read $LIB" >&2; exit 3; }
. "$LIB"
CR="$(printf '\r')"

usage() {
  [ $# -eq 0 ] || echo "error: $1" >&2
  echo "usage: $(basename "$0") <reply> [--spec <path>] [--label <label>]" >&2
  echo "       $(basename "$0") --plan <plan> [--label <label>]" >&2
  exit 2
}

# --- arguments ----------------------------------------------------------------

RF=""; NPOS=0; SPEC=""; LABEL=""; PLAN=0
pos() { NPOS=$((NPOS + 1)); RF="$1"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --plan)  PLAN=1; shift ;;
    --spec)  [ $# -ge 2 ] && [ -n "$2" ] || usage "--spec needs a path"; SPEC="$2"; shift 2 ;;
    --label) [ $# -ge 2 ] && [ -n "$2" ] || usage "--label needs a label"; LABEL="$2"; shift 2 ;;
    --) shift; while [ $# -gt 0 ]; do pos "$1"; shift; done ;;
    -?*) usage "unknown option '$1'" ;;
    *) pos "$1"; shift ;;
  esac
done
[ $NPOS -eq 1 ] && [ -n "$RF" ] || usage "give one file: the drafter's reply as written, or with --plan the plan file"
[ "$PLAN" -eq 0 ] || [ -z "$SPEC" ] || usage "--spec checks a reply's trace, and a plan file has none"
case "$LABEL" in *[[:space:]]*) usage "a label holds no whitespace, got '$LABEL'" ;; esac
if [ "$PLAN" -eq 1 ]; then INPUT=plan; WHAT="the plan"; else INPUT=reply; WHAT="the draft"; fi

# --- the report -----------------------------------------------------------------

R_RESULT=""; R_SUBS=""; R_TAGS=""; R_WHERE=""; R_WARN=""; R_PROB=""; R_FIX=""; R_MSG=""
VIOL=0

finish() {
  emit result "$R_RESULT";   emit input "$INPUT";       emit file "$RF"
  emit spec "$SPEC";         emit subgoals "$R_SUBS";   emit tags "$R_TAGS"
  emit where "$R_WHERE";     emit problem "$R_PROB";    emit fix "$R_FIX"
  emit message "$R_MSG"
  if [ "$R_RESULT" = clean ]; then exit 0; fi
  exit 1
}

fail() {  # fail <rung>: the file could not be checked; the rung is the library's, unused
  R_RESULT=error; R_SUBS=""; R_TAGS=""; R_WHERE=""
  R_MSG="The $INPUT could not be checked; see problem and fix."
  finish
}

readable() {  # readable <file> <what it should be>: E15's check, a missing file named as such
  if [ ! -e "$1" ]; then violation "$1 does not exist" "pass $2"; fail ""; fi
  if [ ! -f "$1" ]; then violation "$1 is not a file" "pass $2"; fail ""; fi
  need_file "$1" ""
}
if [ "$PLAN" -eq 1 ]; then readable "$RF" "the plan file as /master-plan wrote it"
else readable "$RF" "the file /master-plan wrote the drafter's reply to"; fi
if [ -n "$SPEC" ]; then readable "$SPEC" "the spec's path, as the draft's **Spec**: names it"; fi

HEADS=""; FO=""; FC=""; INFO=""; XF=""; UF=0; TNS=""; TGS=""; TBAD=""; NTAG=0; UN=0
TRACE=0; DRAFT=0; FR=""; FRAMED=0
if [ "$PLAN" -eq 1 ]; then
  # The whole file is the draft, as if fenced: line 1 opens it, a line past its last
  # closes it.
  FO=0; FC="$(awk 'END { print NR + 1 }' "$RF")" || die "awk failed counting the lines of $RF"
  DRAFT=1
else
  # --- the reply: its sections, the draft's fence, the trace's lines ------------------
  # A `## ` line inside a fence is the fence's, not the reply's; a second fence under
  # ## Draft is reported at its opening line. Trace tags are split on `; ` outside double
  # quotes, curly quotes read as straight ones.

  out="$(awk '
    function tag(ln, n, s) {
      sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s)
      if (s == "") print "TE\t" ln; else print "TG\t" ln "\t" n "\t" s
    }
    { sub(/\r$/, "") }
    /^[ \t]+## Draft[ \t]*$/ && !fr { fr = NR; print "FR\t" NR }
    /^## / && !open && !extra { h = $0; sub(/[ \t]+$/, "", h); print "H\t" NR "\t" h; sec = h; next }
    sec == "## Draft" && /^~~~/ {
      if (!open && !done) {
        open = 1; info = $0; sub(/^~~~[ \t]*/, "", info); sub(/[ \t]+$/, "", info)
        print "FO\t" NR "\t" info; next
      }
      if (open && $0 ~ /^~~~[ \t]*$/) { open = 0; done = 1; print "FC\t" NR; next }
      if (!open) { if (!extra) print "XF\t" NR; extra = !extra; next }
    }
    open || extra { next }
    sec == "## Trace" && /[^ \t]/ {
      if (!match($0, /^- [0-9]+\.([ \t]|$)/)) { print "TX\t" NR "\t" $0; next }
      d = $0; sub(/^- /, "", d); sub(/\..*$/, "", d)
      print "TN\t" NR "\t" (d + 0)
      rest = substr($0, RLENGTH + 1); gsub(/“|”/, "\"", rest)
      t = ""; q = 0; m = length(rest)
      for (i = 1; i <= m; i++) {
        c = substr(rest, i, 1)
        if (c == "\"") q = !q
        if (!q && c == ";" && substr(rest, i + 1, 1) == " ") { tag(NR, d + 0, t); t = ""; i++; continue }
        t = t c
      }
      tag(NR, d + 0, t)
    }
    END { if (open) print "UF" }
  ' "$RF")" || die "awk failed reading $RF"

  IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; ln="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
    case "$typ" in
      H)  HEADS="${HEADS:+$HEADS$NL}$val" ;;
      FO) FO="$ln"; INFO="$val" ;;
      FC) FC="$ln" ;;
      XF) XF="${XF:+$XF$NL}$ln" ;;
      UF) UF=1 ;;
      FR) FR="$ln" ;;
      TN) TNS="${TNS:+$TNS$NL}$ln$TAB$val" ;;
      TG) TGS="${TGS:+$TGS$NL}$ln$TAB$val"; NTAG=$((NTAG + 1)) ;;
      TE|TX) TBAD="${TBAD:+$TBAD$NL}$rec" ;;   # reported with the trace, in reading order
    esac
  done
  unset IFS

  WANT="## Draft$NL## Trace$NL## Left out$NL## Questions"
  if [ -z "$HEADS" ] && [ -n "$FR" ]; then
    FRAMED=1
    violation "$RF:$FR has \`## Draft\` indented: the reply was copied inside the frame Claude Code puts around a subagent's report" \
      "write the reply again as plan-drafter returned it, without the hand-back note before it, the agentId and usage lines after it, or the indent on every line"
  elif [ "$HEADS" != "$WANT" ]; then
    got="$(printf '%s' "$HEADS" | awk 'BEGIN { ORS = "" } { print (NR == 1 ? "" : ", ") $0 }')" || die "awk failed listing the reply's sections"
    violation "the reply's sections are ${got:-none}, not ## Draft, ## Trace, ## Left out and ## Questions in that order" \
      "return the four sections, in that order, and nothing else"
  fi
  case "$NL$HEADS$NL" in *"$NL## Trace$NL"*) TRACE=1 ;; esac

  if [ -z "$FO" ]; then
    case "$NL$HEADS$NL" in
      *"$NL## Draft$NL"*) violation "## Draft holds no ~~~markdown fence" "put the whole plan file in one \`~~~markdown\` fence under ## Draft" ;;
    esac
  elif [ "$UF" -eq 1 ]; then
    violation "the draft's fence, opened at $RF:$FO, is never closed" "close it with a \`~~~\` line"
  else
    DRAFT=1
    [ "$INFO" = markdown ] || violation "$RF:$FO opens the draft's fence as \`~~~$INFO\`" "open it as \`~~~markdown\`"
  fi
  for ln in $XF; do
    violation "$RF:$ln opens a second fence under ## Draft" "keep the whole plan file in one fence"
  done
fi

# --- the draft --------------------------------------------------------------------
# Line numbers are the file's. Subgoal blocks come from SUBGOALS_AWK, run on the draft's
# lines alone, so a draft is read as /new-branch and /smart-merge will read the file.

N=""
if [ "$DRAFT" -eq 1 ] && [ "$FC" -eq $((FO + 1)) ]; then
  violation "$WHAT is empty" "write the whole plan file: \`# Revision <label>\`, its header and its three sections"
  DRAFT=0
fi
if [ "$DRAFT" -eq 1 ]; then
  out="$(awk -v fo="$FO" -v fc="$FC" '
    NR <= fo || fc <= NR { next }
    { sub(/\r$/, "") }
    NR == fo + 1 { print "L1\t" NR "\t" $0 }
    /^[ \t]*```/ { fence = !fence; next }
    fence { next }
    /^## / { if (!hd) hd = NR; h = $0; sub(/[ \t]+$/, "", h); print "DH\t" NR "\t" h; next }
    !hd && /^\*\*(Status|Version|Opened|Spec)\*\*:/ {
      k = $0; sub(/^\*\*/, "", k); sub(/\*\*:.*$/, "", k)
      v = $0; sub(/^\*\*[A-Za-z]+\*\*:[ \t]*/, "", v); sub(/[ \t]+$/, "", v)
      print "HD\t" NR "\t" k "\t" v
    }
    /^[ \t]*> \*\*(Branch|Done):\*\*/ { print "BD\t" NR }
    /^[ \t]+Scope: .*Acceptance: / { print "SA\t" NR }
  ' "$RF")" || die "awk failed reading the draft in $RF"

  DHS=""; SAS=""; BDS=""; ST=""; VE=""; OP=""; SP=""
  IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; ln="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
    case "$typ" in
      L1)
        if [ -n "$LABEL" ]; then
          [ "$val" = "# Revision $LABEL" ] || violation "$RF:$ln, $WHAT's first line, reads \`$val\`, not \`# Revision $LABEL\`" "begin $WHAT \`# Revision $LABEL\`"
        else
          case "$val" in
            "# Revision "*[[:space:]]*|"# Revision ") violation "$RF:$ln, $WHAT's first line, reads \`$val\`, not \`# Revision <label>\`" "begin $WHAT \`# Revision <label>\`, with the revision's label" ;;
            "# Revision "?*) ;;
            *) violation "$RF:$ln, $WHAT's first line, reads \`$val\`, not \`# Revision <label>\`" "begin $WHAT \`# Revision <label>\`, with the revision's label" ;;
          esac
        fi ;;
      DH) DHS="${DHS:+$DHS$NL}$val" ;;
      HD)
        k="${val%%"$TAB"*}"; v="${val#*"$TAB"}"
        case "$k" in
          Status)  ST=1
                   [ "$v" = open ] || violation "$RF:$ln has \`**Status**: $v\`; a revision opens \`open\`" "write \`**Status**: open\`" ;;
          Version) VE=1
                   [ -n "$v" ] || violation "$RF:$ln has an empty \`**Version**:\`" "state the version each package reaches, or \`—\` if the spec names none" ;;
          Opened)  OP=1
                   case "$v" in
                     [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
                     *) violation "$RF:$ln has \`**Opened**: $v\`, not a date" "write the date the revision opens, as YYYY-MM-DD" ;;
                   esac ;;
          Spec)    SP=1
                   [ -n "$v" ] || violation "$RF:$ln has an empty \`**Spec**:\`" "name the spec: its path, \`pasted\` or \`conversation\`" ;;
        esac ;;
      BD) BDS="${BDS:+$BDS$NL}$ln" ;;                        # reported after the subgoals
      SA) SAS="${SAS:+$SAS$NL}$ln" ;;
    esac
  done
  unset IFS
  for k in Status Version Opened Spec; do
    case "$k" in Status) v="$ST" ;; Version) v="$VE" ;; Opened) v="$OP" ;; Spec) v="$SP" ;; esac
    [ -n "$v" ] || violation "$WHAT has no \`**$k**:\` line before its first ## heading" "add it to the header, in the order Status, Version, Opened, Spec"
  done
  if [ "$DHS" != "## Preamble$NL## Settled decisions$NL## Subgoals" ]; then
    got="$(printf '%s' "$DHS" | awk 'BEGIN { ORS = "" } { print (NR == 1 ? "" : ", ") $0 }')" || die "awk failed listing the draft's headings"
    violation "$WHAT's ## headings are ${got:-none}, not ## Preamble, ## Settled decisions and ## Subgoals in that order" \
      "use subdividing.md's three sections, in that order, and no others"
  fi

  items="$(awk -v fo="$FO" -v fc="$FC" '
    NR <= fo || fc <= NR { next }
  '"$SUBGOALS_AWK" "$RF")" || die "awk failed reading the subgoals in $RF"
  k=0
  IFS="$NL"
  for rec in $items; do
    r="${rec#ITEM"$TAB"}"
    ln="${r%%"$TAB"*}"; r="${r#*"$TAB"}"
    r="${r#*"$TAB"}"                                       # the marker: the line says it
    last="${r%%"$TAB"*}"; r="${r#*"$TAB"}"
    r="${r#*"$TAB"}"                                       # branches: F6 reports them
    hd="${r%%"$TAB"*}"; txt="${r#*"$TAB"}"; txt="${txt%"$CR"}"
    if [ "$hd" != "## Subgoals" ]; then
      violation "$RF:$ln is a checkbox under ${hd:-no heading}, outside ## Subgoals: \`$txt\`" \
        "write it as a plain \`- \` bullet: the plan scripts count every \`- [ ] \` line at the margin as a subgoal"
      continue
    fi
    k=$((k + 1))
    case "$txt" in
      "- [ ] $k. "?*) ;;
      *) violation "$RF:$ln reads \`$txt\`, where subgoal $k should begin \`- [ ] $k. \`" "number the subgoals from 1, in order, each \`- [ ] N. <what the branch delivers>\`" ;;
    esac
    if [ "$last" -eq "$ln" ]; then
      violation "subgoal $k, at $RF:$ln, has no \`Scope: … Acceptance: …\` line in its block" \
        "put that line directly under it, indented two spaces, with no blank line between"
    elif [ "$last" -ne $((ln + 1)) ]; then
      violation "subgoal $k, at $RF:$ln, runs to line $last: a subgoal is two lines" "write its scope and acceptance as one \`Scope: … Acceptance: …\` line"
    else
      case "$NL$SAS$NL" in
        *"$NL$((ln + 1))$NL"*) ;;
        *) violation "$RF:$((ln + 1)) is not \`Scope: … Acceptance: …\`" "write subgoal $k's second line as \`Scope: <what it touches>. Acceptance: <the check>.\`" ;;
      esac
    fi
  done
  unset IFS
  for ln in $BDS; do
    violation "$RF:$ln is a \`> **Branch:**\` or \`> **Done:**\` line" "remove it: /new-branch and /smart-merge write those, once the revision is committed"
  done
  N="$k"
  if [ "$N" -eq 0 ]; then
    case "$NL$DHS$NL" in
      *"$NL## Subgoals$NL"*) violation "$WHAT has no subgoals under ## Subgoals" "subdivide the spec into subgoals, each \`- [ ] N. …\` with its \`Scope: … Acceptance: …\` line" ;;
    esac
  fi
fi
R_SUBS="$N"

# --- the trace: one line per subgoal, in order --------------------------------------

IFS="$NL"
for rec in $TBAD; do
  typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; ln="${rest%%"$TAB"*}"; val="${rest#*"$TAB"}"
  case "$typ" in
    TE) violation "$RF:$ln has an empty tag" "tag the subgoal with the spec item it carries, or drop the empty tag" ;;
    TX) violation "$RF:$ln is not a trace line: \`$val\`" "write each trace line as \`- N. <tag>\`, with \`; \` between tags" ;;
  esac
done
unset IFS
if [ "$TRACE" -eq 1 ] && [ -n "$N" ]; then
  e=1
  IFS="$NL"
  for rec in $TNS; do
    ln="${rec%%"$TAB"*}"; n="${rec#*"$TAB"}"
    if [ "$n" -eq "$e" ] && [ "$e" -le "$N" ]; then e=$((e + 1)); continue; fi
    if [ "$N" -lt "$n" ] || [ "$n" -eq 0 ]; then
      violation "$RF:$ln traces subgoal $n, which the draft does not have" "trace only the draft's subgoals, 1 to $N"
    else
      violation "$RF:$ln traces subgoal $n where subgoal $e is next" "give each subgoal one trace line, in the draft's order"
    fi
  done
  unset IFS
  if [ "$e" -le "$N" ]; then
    if [ "$e" -eq "$N" ]; then miss="subgoal $N has"; else miss="subgoals $e to $N have"; fi
    violation "$miss no trace line" "tag each subgoal with the spec item it carries, one line each"
  fi
fi

# --- the tags, against the spec ---------------------------------------------------

if [ "$PLAN" -eq 1 ]; then
  R_TAGS=""                                                # a plan file has no trace
elif [ -z "$SPEC" ]; then
  R_TAGS="$NTAG, not checked: no spec given"
else
  # all is the spec on one line, whitespace collapsed, so a phrase wrapped across lines is
  # found; cs[k] is where line cl[k] starts in it, so a match maps back to its line. A
  # heading's section runs to the next heading at its level or above, or to the end.
  out="$(TAGS="$TGS" awk '
    function sect(j,    k, e) {
      e = NR
      for (k = j + 1; k <= nh; k++) if (hv[k] <= hv[j]) { e = hl[k] - 1; break }
      return hl[j] "-" nb[e]
    }
    function ok(g,    p, j, x, k, rest, c) {
      if (substr(g, 1, 1) == "\"") {
        p = substr(g, 2); j = index(p, "\""); if (!j) return 0
        p = substr(p, 1, j - 1); gsub(/[ \t]+/, " ", p); sub(/^ /, "", p); sub(/ $/, "", p)
        if (p == "" || !(x = index(all, p))) return 0
        for (k = 1; k < nc && cs[k + 1] < x; k++) ;
        at = cl[k]; return 1
      }
      if (index(g, "§") == 1) {
        rest = substr(g, length("§") + 1)
        if (!match(rest, /^[0-9]+(\.[0-9]+)*/)) return 0
        rest = substr(rest, 1, RLENGTH)
        for (j = 1; j <= nh; j++) if (hn[j] == rest) { at = sect(j); return 1 }
        return 0
      }
      for (j = 1; j <= nh; j++)
        if (index(g, hs[j]) == 1) {
          c = substr(g, length(hs[j]) + 1, 1)
          if (c == "" || c !~ /[A-Za-z0-9]/) { at = sect(j); return 1 }
        }
      return 0
    }
    {
      sub(/\r$/, ""); s = $0; gsub(/[ \t]+/, " ", s); sub(/^ /, "", s); sub(/ $/, "", s)
      if (s != "") { cs[++nc] = length(all) + 1; cl[nc] = NR; all = all " " s; last = NR }
      nb[NR] = last                                        # the last line, to here, not blank
    }
    /^[ \t]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    /^#+[ \t]/ {
      h = $0; sub(/^#+[ \t]+/, "", h); sub(/[ \t]+$/, "", h)
      if (h != "") {
        hs[++nh] = h; hl[nh] = NR; v = $0; sub(/[ \t].*$/, "", v); hv[nh] = length(v)
        hn[nh] = match(h, /^[0-9]+(\.[0-9]+)*/) ? substr(h, 1, RLENGTH) : ""
      }
    }
    END {
      n = split(ENVIRON["TAGS"], L, "\n"); r = 0; t = 0
      for (i = 1; i <= n; i++) {
        if (L[i] == "") continue
        t++; ln = L[i]; sub(/\t.*$/, "", ln); sg = L[i]; sub(/^[^\t]*\t/, "", sg)
        g = sg; sub(/^[^\t]*\t/, "", g); sub(/\t.*$/, "", sg)
        if (ok(g)) { r++; print "W\t" sg "\t" at "\t" g } else print "U\t" ln "\t" g
      }
      print "N\t" r "\t" t
    }
  ' "$SPEC")" || die "awk failed reading $SPEC"
  IFS="$NL"
  for rec in $out; do
    typ="${rec%%"$TAB"*}"; rest="${rec#*"$TAB"}"; a="${rest%%"$TAB"*}"; b="${rest#*"$TAB"}"
    case "$typ" in
      U) UN=$((UN + 1))
         violation "$RF:$a has the tag \`$b\`, which names nothing in $SPEC" \
           "tag with a heading or § as $SPEC writes it, or a phrase copied from it verbatim; a subgoal no part of the spec supports is a question, not a subgoal" ;;
      W) R_WHERE="${R_WHERE:+$R_WHERE$NL}$a. $SPEC:${b%%"$TAB"*} ${b#*"$TAB"}" ;;
      N) R_TAGS="$a of $b resolve" ;;
    esac
  done
  unset IFS
fi

# --- the verdict ----------------------------------------------------------------------

if [ "$VIOL" -eq 0 ]; then
  R_RESULT=clean
  if [ "$PLAN" -eq 1 ]; then
    R_MSG="The plan has subdividing.md's form, with $N subgoals."
  else
    if [ -n "$SPEC" ]; then how="every tag names a part of $SPEC"; else how="its tags were not checked against a spec"; fi
    R_MSG="The draft has subdividing.md's form and its trace covers its $N subgoals; $how."
  fi
else
  R_RESULT=problems
  if [ "$VIOL" -eq 1 ]; then many="1 problem"; else many="$VIOL problems"; fi
  if [ "$PLAN" -eq 1 ]; then R_MSG="$many: correct the plan file, then check it again before the commit."
  elif [ "$FRAMED" -eq 1 ]; then R_MSG="$many: write the reply file again without the frame around plan-drafter's report, then check it again."
  elif [ "$UN" -eq "$VIOL" ]; then R_MSG="$many in tags alone: ask the user, for each tag that names nothing in $SPEC, whether the spec supports its subgoal."
  else R_MSG="$many: ask plan-drafter once for a fresh reply, naming each."; fi
fi
finish
