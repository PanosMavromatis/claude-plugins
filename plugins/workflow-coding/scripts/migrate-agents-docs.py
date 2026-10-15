#!/usr/bin/env python3
"""Move a project's agent instructions into §4.3's layout, for /agents-docs-migrate.

  python3 -I migrate-agents-docs.py detect
  python3 -I migrate-agents-docs.py check <reply>
  python3 -I migrate-agents-docs.py apply <reply>
  python3 -I migrate-agents-docs.py verify <reply>

Run from the repository's root. Each mode reports in `key: value` lines, a key with several
items continuing on lines indented two spaces and `—` standing for none, `message:` last;
`problem:` and `fix:` pair up, line for line, on what stops the migration.

detect, check and verify are read-only; apply writes, and nothing here deletes. No mode reads
or writes through a symbolic link: a source, codex.md, guide, AGENTS.md, destination or drop file
with a link at any component of its path is a problem, since a repository being migrated may be
another's, and its table is written by an agent reading text it is told not to trust.

detect is read-only. Its targets are the root and each directory with a CLAUDE.md or with
dispatcher sources, docs/agents/<path>/{core,claude,codex}.md, found in git's list of tracked
and untracked, unignored files, so an ignored or vendored tree is never one. A CLAUDE.md is
read without its HTML comments: with no line left it is `empty`; with only @docs/agents/
imports, a `dispatcher`; with only `@AGENTS.md`, the `shim`; with anything else, `legacy`. An
AGENTS.md whose first line opens `<!-- Generated from` is `generated`, the old build's copy of
core.md; any other is `hand`. Each target is then in one state:
  legacy      (a) a legacy CLAUDE.md, and no dispatcher sources
  dispatcher  (b) dispatcher sources, or a dispatcher CLAUDE.md
  migrated    (c) neither, and an AGENTS.md
A legacy CLAUDE.md beside dispatcher sources is a problem, as is a codex.md beside the
codex-review/AGENTS.md it would become: either way, moving one would overwrite the other.

It reports, in this order:
  result    migrate (a target is legacy or dispatcher), migrated, none, or error
  targets   <path> <state> claude=<kind> agents=<kind>, `.` the root, the root first
  sources   what docs-classifier classifies: each legacy CLAUDE.md, each core.md and claude.md
  codex     each codex.md -> the codex-review/AGENTS.md it becomes, moved whole
  delete    what the destructive step removes once everything is moved: each legacy, dispatcher
            or empty CLAUDE.md of a target to migrate, and its core.md, claude.md and codex.md
  local     .claude/CLAUDE.md and each target's CLAUDE.local.md, found on disk since a
            CLAUDE.local.md is usually ignored: either switches native AGENTS.md off
  sizes     each migrated target's AGENTS.md, in lines and ≈ tokens (bytes × 3 / 7, the
            /memory-check estimate), marked over 200 lines or over ≈ 5,000 tokens
  warnings  what is odd but safe

check is read-only too. <reply> is docs-classifier's report, written to a file as returned. It
checks the table against detect's sources: each row four cells; its source named as detect names
it, `<file>:<start>-<end>` or `<file>:<n>`, in range and in order; its destination one of
AGENTS.md or <path>/AGENTS.md, docs/agents/[<path>/]<guide>/AGENTS.md,
docs/agents/_history/<area>.md, `drop: <file>[:<line>]` naming a file that is there, or
`drop: obsolete — <why>`, any <path> a target's; its flag `sure` or `unsure: <why>`; and every
non-blank line of every source in exactly one row. A table that fails is docs-classifier's to
redo. One that passes is planned as apply would write it, each row's lines verbatim but for its
relative links, which are re-expressed from the new folder, a link to a source being deleted
pointing where that source goes; a new guide or _history/ file opens `# <name>`, a generated
AGENTS.md is replaced and any other file appended to; and each AGENTS.md closes with
`## Guides and history`, one line per guide or history file of its target, naming the headings
its rows bring and nothing else, since AGENTS.md takes no agent's words. It reports:
  rows       how many, and how many docs-classifier flagged unsure
  writes     each file apply would write, how, its lines and ≈ tokens; an AGENTS.md marked over
             200 lines or ≈ 5,000 tokens
  unread     each new guide no agent of this plugin reads, with its ≈ tokens
  flags      the rule flags: obsolete drops, dated rows bound for an AGENTS.md, lines over
             2,000 characters, which Read cuts, and drops whose named file carries less than 80%
             of their five-word sequences
  drops      every duplicate drop, with the share of it its file carries
  repointed  each link pointed from a deleted source to where it goes

apply writes what check plans, after the user approves it, and deletes nothing. It writes only
over files git has committed, or none: a file it would write that git shows changed or untracked
stops it before it writes anything, which keeps it off the user's unsaved edits. A file it would
append to that already carries a row's text, as whole lines, stops it too: that is a run before
this one, which committing would hide from git. A generated AGENTS.md, which apply replaces,
carries its source's text by construction and is not counted. It reports wrote, each file with
how and its size, and repointed.

verify is read-only, and runs after apply and before the destructive step. Every row moved, and
each codex.md, must be found in its destination as apply writes it, links rewritten, as whole
lines, and as many times as rows put it there, so that a row written twice is a problem too;
every other row was dropped with a reason. Each relative link the move wrote is checked twice: a link that
resolved from its source and does not from where it was written was broken by the move, and
stops the destructive step; a link already dead in its source is listed under dead and does not.
A codex-review/AGENTS.md that opens with its codex.md, moved, is apply's own work, which detect
does not count as a clash. It reports:
  moved   how many rows and codex.md moves were found in their destinations
  drops   every dropped row, with the share of it its file carries, or why it is obsolete
  dead    each link already dead in its source
  delete    what the destructive step may remove, given only when nothing failed
  pointers  with delete, each line elsewhere that points at a file it removes: a Markdown link
            resolving to it, or its exact path where it has a folder, but not in docs/plan/ or an
            AGENTS.override.md; listed for the user to repoint, blocking nothing

Exit: 0, a report with no problem; 1, a report with problems; 2, a usage error and no report.
Python 3.8 or later, and the standard library only.
"""
import os
import re
import subprocess
import sys

MAX_LINES, MAX_TOKENS = 200, 5000
SOURCES = ("core.md", "claude.md")
GENERATED = "<!-- Generated from"
KNOWN_GUIDES = ("codex-review", "docs-sync", "pr-drafter")   # the guides an agent of this plugin reads
DATE = re.compile(r"20\d\d-\d\d-\d\d")
OVERLONG, SHINGLE, SHARE = 2000, 5, 80   # Read's line cut; words a sequence; % a duplicate must carry
POINTERS = "## Guides and history"
SRC = re.compile(r"(?P<f>[^:\s]+):(?P<a>\d+)(?:-(?P<b>\d+))?")   # a single line may be <file>:<n>
OBSOLETE = re.compile(r"drop: obsolete — \S.*")
DROP = re.compile(r"drop: (?P<f>[^\s:]+)(?::(?P<l>\d+))?")
HISTORY = re.compile(r"docs/agents/_history/(?P<a>[\w.-]+)\.md")
GUIDE = re.compile(r"docs/agents/(?:(?P<p>[\w./-]+)/)?(?P<g>[\w-]+)/AGENTS\.md")
TOP = re.compile(r"(?:(?P<p>[\w./-]+)/)?AGENTS\.md")
LINK = re.compile(r'(!?\[[^\]\n]*\]\()(<[^>\n]*>|[^)\s]+)((?:\s+"[^"\n]*")?\))')
REFDEF = re.compile(r"^( {0,3}\[[^\]\n]+\]:[ \t]*)(\S+)", re.M)


def git(*args):
    """git's output in the current directory, or None if git fails."""
    r = subprocess.run(["git", *args], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def read(path):
    with open(path, "rb") as f:
        return f.read()


def join(p, name):
    return f"{p}/{name}" if p else name


def shown(p):
    return p or "."


def tokens(n):
    return n * 3 // 7


def link_in(path):
    """The first component of path, from the repository's root, that is a symbolic link, or
    None. Nothing here reads or writes through one: a link in a repository being migrated would
    carry a read or a write outside it, wherever the link points."""
    acc = ""
    for part in path.split("/"):
        acc = join(acc, part)
        if os.path.islink(acc):
            return acc
    return None


def outside(path):
    """Why path, as the table names it, is no plain repository path, or None: absolute, not in
    normal form, climbing out by .., or through a symbolic link. Normal form is required so that
    every check reads the very string the read or the write uses."""
    if os.path.isabs(path):
        return "is an absolute path"
    if os.path.normpath(path) != path:
        return f"is not in normal form, {os.path.normpath(path)}"
    if path == ".." or path.startswith("../"):
        return "climbs out of the repository"
    l = link_in(path)
    if l:
        return "is a symbolic link" if l == path else f"passes through the symbolic link {l}"
    return None


def linked(path, l):
    return f"{path} is a symbolic link" if l == path else f"{path} passes through the symbolic link {l}"


def claude_kind(path):
    """absent, empty, dispatcher, shim or legacy: what a CLAUDE.md holds, comments aside."""
    if not os.path.isfile(path):
        return "absent"
    text = re.sub(r"<!--.*?-->", "", read(path).decode("utf-8", "replace"), flags=re.S)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return "empty"
    if all(re.fullmatch(r"@docs/agents/\S+\.md", l) for l in lines):
        return "dispatcher"
    if all(l in ("@AGENTS.md", "@./AGENTS.md") for l in lines):
        return "shim"
    return "legacy"


def agents_kind(path):
    if not os.path.isfile(path):
        return "absent"
    return "generated" if read(path).startswith(GENERATED.encode()) else "hand"


def detect():
    """The detect report, as (key, value) pairs; whether it found a problem; and its targets,
    each a dict of its path, state, sources, codex.md and the guide that becomes, for check."""
    problems, fixes, warnings, tinfo, clashes = [], [], [], [], []
    top = git("rev-parse", "--show-toplevel")
    if top is None or os.path.realpath(top.strip()) != os.path.realpath(os.getcwd()):
        where = "not in a git repository" if top is None else f"in {os.getcwd()}, not at the root {top.strip()}"
        return [("result", "error"), ("problem", f"run {where}"),
                ("fix", "run it from the repository's root, the directory git rev-parse --show-toplevel names"),
                ("message", "Nothing was read: the targets are found from the repository's root.")], True, []
    listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if listed is None:
        return [("result", "error"), ("problem", "git ls-files failed in this repository"),
                ("fix", "run git ls-files here and repair what it reports, then run this again"),
                ("message", "Nothing was read: the targets come from git's list of files.")], True, []
    files = [f for f in listed.split("\0") if f]
    paths = {""}
    for f in files:
        d, name = os.path.split(f)
        if name == "CLAUDE.md" and d != ".claude" and not (d + "/").startswith("docs/agents/"):
            paths.add(d)
        elif name in SOURCES + ("codex.md",) and (d + "/").startswith("docs/agents/"):
            paths.add(d[len("docs/agents/"):])
    present = set(files)
    targets, tpaths, sources, codex, delete, local, sizes = [], [], [], [], [], [], []
    for p in sorted(paths, key=lambda x: (x != "", x)):
        cl, ag = join(p, "CLAUDE.md"), join(p, "AGENTS.md")
        ck, ak = claude_kind(cl), agents_kind(ag)
        src = [join("docs/agents/" + p if p else "docs/agents", s) for s in SOURCES]
        src = [s for s in src if s in present]
        cx = join("docs/agents/" + p if p else "docs/agents", "codex.md")
        cx = cx if cx in present else None
        if src or cx or ck == "dispatcher":
            state = "dispatcher"
            if ck == "legacy":
                beside = src + ([cx] if cx else [])
                problems.append(f"{cl} has prose beside the dispatcher's sources {', '.join(beside)}")
                fixes.append(f"move what {cl} says into {join(os.path.dirname(beside[0]), 'core.md')}, or move {cl} aside, and run this again")
        elif ck == "legacy":
            state = "legacy"
        elif ak != "absent":
            state = "migrated"
        else:
            continue
        targets.append(f"{shown(p)} {state} claude={ck} agents={ak}")
        tpaths.append(p)
        tinfo.append(dict(p=p, state=state, src=[], cx=None, guide=None))
        if state == "migrated":
            if ak == "generated":
                warnings.append(f"{ag} opens with the old build's header, but nothing builds it now: delete the header")
            b = read(ag)
            n = len(b.decode("utf-8", "replace").splitlines())
            over = [w for w, bad in ((f"over {MAX_LINES} lines", n > MAX_LINES),
                                     (f"over ≈{MAX_TOKENS:,} tokens", tokens(len(b)) > MAX_TOKENS)) if bad]
            sizes.append(f"{ag}: {n} lines, ≈{tokens(len(b)):,} tokens" + (" — " + ", ".join(over) if over else ""))
            continue
        sources += [cl] if state == "legacy" else src
        tinfo[-1]["src"] = [cl] if state == "legacy" else src
        if cx:
            guide = join(os.path.dirname(cx), "codex-review/AGENTS.md")
            tinfo[-1].update(cx=cx, guide=guide)
            codex.append(f"{cx} -> {guide}")
            if os.path.exists(guide):
                clashes.append((cx, guide))
        for p_ in tinfo[-1]["src"] + ([cx, tinfo[-1]["guide"]] if cx else []) + [ag]:
            l = link_in(p_)
            if l:
                problems.append(linked(p_, l))
                fixes.append(f"replace {l} with the file or folder it points to, or remove it, and run this again")
        # A dispatcher target's CLAUDE.md goes only if it holds no prose: prose there is a problem.
        gone = state == "legacy" or ck in ("dispatcher", "empty")
        delete += ([cl] if gone else []) + src + ([cx] if cx else [])
    # A guide that opens with its codex.md, moved, is apply's own work, as verify finds it.
    for cx, guide in clashes:
        mine = relink(read(cx).decode("utf-8", "replace"), cx, guide, moves(tinfo), [])
        if not read(guide).decode("utf-8", "replace").startswith(mine):
            problems.append(f"{cx} and {guide} both exist, and the move would overwrite the guide")
            fixes.append(f"fold what {cx} adds into {guide} and remove {cx}, or move {guide} aside, and run this again")
    # On disk, not from git: a CLAUDE.local.md is usually ignored, and is no less loaded for it.
    for f in [".claude/CLAUDE.md"] + [join(p, "CLAUDE.local.md") for p in tpaths]:
        if os.path.isfile(f):
            local.append(f)
    states = [t.split()[1] for t in targets]
    if problems:
        result, msg = "error", f"Cannot migrate: {len(problems)} problem{'s' if len(problems) > 1 else ''}, each with its fix."
    elif {"legacy", "dispatcher"} & set(states):
        n = sum(s != "migrated" for s in states)
        result = "migrate"
        msg = f"{n} target{'s' if n > 1 else ''} to migrate; " + (
            f"docs-classifier classifies the {len(sources)} source{'s' if len(sources) > 1 else ''}."
            if sources else "there is no source to classify.")
    elif targets:
        result, msg = "migrated", "Already migrated: nothing to move."
    else:
        result, msg = "none", "Nothing to migrate: no CLAUDE.md, no dispatcher source and no AGENTS.md."
    return [("result", result), ("targets", targets), ("sources", sources), ("codex", codex),
            ("delete", delete), ("local", local), ("sizes", sizes), ("warnings", warnings),
            ("problem", problems), ("fix", fixes), ("message", msg)], bool(problems), tinfo


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def share(text, path):
    """The % of text's 5-word sequences that path carries, case and punctuation aside."""
    w, t = words(text), words(read(path).decode("utf-8", "replace"))
    if len(w) < SHINGLE:
        return 100 if " ".join(w) in " ".join(t) else 0
    want = {tuple(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1)}
    have = {tuple(t[i:i + SHINGLE]) for i in range(len(t) - SHINGLE + 1)}
    return len(want & have) * 100 // len(want)


def heading(text):
    """The first of text's shallowest headings, or None."""
    hs = [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r"^(#{1,6})[ \t]+(.+)$", text, re.M)]
    return next(h for n, h in hs if n == min(n for n, _ in hs)) if hs else None


def relink(text, src, dst, moved, repointed, links=None):
    """text from src as it reads at dst. Each relative link, image and reference definition is
    re-expressed from dst's folder, anchor kept; a link to a source being deleted is pointed at
    where that source goes, and logged in repointed. URLs, #anchors, absolute paths, links out
    of the repository and code fences are left alone, and so is a link that keeps its folder.
    Each relative link in the repository is logged in links, if given, as it was and as it is."""
    def fix(url):
        bare = url[1:-1] if url.startswith("<") else url
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", bare) or bare.startswith(("#", "/")):
            return url
        path, mark, frag = bare.partition("#")
        to = os.path.normpath(os.path.join(os.path.dirname(src), path)) if path else ""
        if not path or to == ".." or to.startswith("../"):
            return url
        new = None
        if to in moved:
            repointed.append(f"{dst}: {url} -> {moved[to]}")
            to = moved[to]
        elif os.path.dirname(src) == os.path.dirname(dst):
            new = url
        if new is None:
            new = os.path.relpath(to, os.path.dirname(dst) or ".") + mark + frag
            new = f"<{new}>" if url.startswith("<") else new
        if links is not None:
            links.append((url, new))
        return new
    out, fence = [], False
    for line in text.splitlines(True):
        if re.match(r" {0,3}(```|~~~)", line):
            fence = not fence
        elif not fence:
            line = LINK.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), line)
            line = REFDEF.sub(lambda m: m.group(1) + fix(m.group(2)), line)
        out.append(line)
    return "".join(out)


def destination(dest, tpaths):
    """A row's destination as (kind, where), or (None, what is wrong with it)."""
    if OBSOLETE.fullmatch(dest):
        return "obsolete", None
    m = DROP.fullmatch(dest)
    why = outside(m["f"] if m else dest)
    if why:
        return None, f"names {m['f']}, which {why}" if m else why
    if m:
        p = m["f"]
        if not os.path.isfile(p):
            return None, f"names {m['f']}, which is not a file in this repository"
        if m["l"] and int(m["l"]) > len(read(p).splitlines()):
            return None, f"names line {m['l']} of {m['f']}, which is shorter"
        return "drop", p
    if HISTORY.fullmatch(dest):
        return "history", ""
    m = GUIDE.fullmatch(dest)
    if m and m["g"] != "_history":
        if (m["p"] or "") not in tpaths:
            return None, f"is a guide of {m['p']}, which is not a target"
        return "guide", m["p"] or ""
    m = TOP.fullmatch(dest)
    if m and not dest.startswith("docs/agents/"):
        if (m["p"] or "") not in tpaths:
            return None, f"is the AGENTS.md of {m['p']}, which is not a target"
        return "agents", m["p"] or ""
    return None, "is not one of the five forms docs-classifier's Output section gives"


def cells(line):
    """A table row's cells, a cell that is one code span unwrapped: `AGENTS.md` is AGENTS.md,
    and `needs` field keeps both its backticks."""
    out = []
    for c in line.strip().strip("|").split("|"):
        c = c.strip()
        out.append(c[1:-1].strip() if len(c) > 1 and c[0] == c[-1] == "`" and c.count("`") == 2 else c)
    return out


def parse(text, sources, tpaths):
    """docs-classifier's table as rows, with the problems and fixes that stop it."""
    probs, fixes = [], []
    def bad(p, f):
        probs.append(p)
        fixes.append(f)
    lines = text.split("\n")
    t = lines.index("## Table") if "## Table" in lines else -1
    n = lines.index("## Notes", t) if t >= 0 and "## Notes" in lines[t:] else -1
    if n < 0:
        if any(l.strip() == "## Table" for l in lines):
            bad("the reply was copied inside the frame Claude Code puts around a subagent's report",
                "write the report again alone, without the frame or its two-space indent, so that ## Table starts its line")
        else:
            bad("the reply has no ## Table followed by ## Notes", "ask docs-classifier again for the two sections its Output section gives")
        return [], probs, fixes
    table = [l for l in lines[t + 1:n] if l.startswith("|")]
    if len(table) < 2 or [c.lower() for c in cells(table[0])] != ["source", "destination", "what", "flag"]:
        bad("the table does not open with | source | destination | what | flag |",
            "ask docs-classifier again for its table in the form its Output section gives")
        return [], probs, fixes
    body = {s: read(s).decode("utf-8", "replace").splitlines(True) for s in sources}
    cover = {s: {} for s in sources}
    rows, last = [], {}
    again = "ask docs-classifier again, with this problem: line and its fix: line"
    for i, line in enumerate(table[2:], 1):
        c = cells(line)
        if len(c) != 4:
            bad(f"row {i} has {len(c)} cells: {line[:80]}", f"{again}: four cells to a row, no | inside a cell")
            continue
        src, dest, what, flag = c
        m = SRC.fullmatch(src)
        if not m or m["f"] not in body:
            bad(f"row {i} names {src}, which is not a range of a source", f"{again}: name each source as the prompt does, {', '.join(sources)}")
            continue
        f, a = m["f"], int(m["a"])
        b = int(m["b"]) if m["b"] else a
        if not 1 <= a <= b <= len(body[f]):
            bad(f"row {i}'s range {src} is not within {f}, which has {len(body[f])} lines", f"{again}: each range within its source")
            continue
        if a < last.get(f, 0):
            bad(f"row {i}, {src}, is out of source order", f"{again}: rows in source order")
        last[f] = a
        for k in range(a, b + 1):
            cover[f].setdefault(k, []).append(i)
        kind, where = destination(dest, tpaths)
        if kind is None:
            bad(f"row {i}'s destination {dest} {where}",
                f"replace the link with the file or folder it points to, or {again}: route the row elsewhere"
                if "symbolic link" in (where or "") else
                f"{again}: each destination one of the five forms, naming a target or a file that exists")
            continue
        if not (flag == "sure" or re.fullmatch(r"unsure: \S.*", flag)):
            bad(f"row {i}'s flag is {flag!r}", f"{again}: each flag sure, or unsure: and why")
        rows.append(dict(src=src, f=f, a=a, b=b, dest=dest, kind=kind, where=where, what=what, flag=flag,
                         text="".join(body[f][a - 1:b])))
    for f in sources:
        gaps = [k for k, l in enumerate(body[f], 1) if l.strip() and k not in cover[f]]
        twice = sorted(k for k, r in cover[f].items() if len(r) > 1)
        for what, ks in (("in no row", gaps), ("in two rows", twice)):
            if ks:
                bad(f"{f}: {len(ks)} non-blank line{'s' if len(ks) > 1 else ''} {what}, from line {ks[0]}",
                    f"{again}: every non-blank line of every source in exactly one row")
    return rows, probs, fixes


def occurrences(text, within):
    """How often text occurs in within as whole lines, repeats side by side counted each."""
    t = text.rstrip("\n")
    return sum(1 for _ in re.finditer("(?=" + re.escape("\n" + t + "\n") + ")", "\n" + within + "\n")) if t else 0


def owner(path):
    """The target whose AGENTS.md points at a guide or history file: the root for _history/."""
    if HISTORY.fullmatch(path):
        return ""
    gm = GUIDE.fullmatch(path)
    return (gm["p"] or "") if gm else None


def describe(items):
    seen = list(dict.fromkeys(i for i in items if i))
    return "; ".join(seen[:4] + ([f"and {len(seen) - 4} more"] if len(seen) > 4 else []))


def moves(tinfo):
    """Where each source being deleted goes: a core.md, claude.md or CLAUDE.md to its target's
    AGENTS.md, a codex.md to its codex-review/ guide."""
    moved = {}
    for t in tinfo:
        for s in t["src"]:
            moved[s] = join(t["p"], "AGENTS.md")
        if t["cx"]:
            moved[t["cx"]] = t["guide"]
    return moved


def plan(rows, tinfo):
    """What apply writes, {path: text} in the order first written; how each is written; the
    links re-pointed; and each new guide no agent of this plugin reads, with its ≈ tokens."""
    moved, repointed, chunks, how, about = moves(tinfo), [], {}, {}, {}
    def begin(path, title):
        if path in chunks:
            return
        top = not path.startswith("docs/agents/")
        if os.path.isfile(path) and not (top and agents_kind(path) == "generated"):
            chunks[path], how[path] = [read(path).decode("utf-8", "replace")], "appends"
        else:
            how[path] = "replaces the generated file" if os.path.isfile(path) else "new"
            chunks[path] = [f"# {title}\n"] if title else []
        about[path] = []
    for t in tinfo:
        if t["state"] != "migrated" and agents_kind(join(t["p"], "AGENTS.md")) == "generated":
            begin(join(t["p"], "AGENTS.md"), None)   # the old build's copy of core.md is replaced
        if t["cx"]:
            begin(t["guide"], None)
            text = read(t["cx"]).decode("utf-8", "replace")
            chunks[t["guide"]].append(relink(text, t["cx"], t["guide"], moved, repointed))
            about[t["guide"]].append(heading(text))
    for r in rows:
        if r["kind"] in ("drop", "obsolete"):
            continue
        gm, hm = GUIDE.fullmatch(r["dest"]), HISTORY.fullmatch(r["dest"])
        title = (gm["g"] if r["kind"] == "guide" and gm else
                 hm["a"] + " history" if r["kind"] == "history" and hm else None)
        begin(r["dest"], title)
        chunks[r["dest"]].append(relink(r["text"], r["f"], r["dest"], moved, repointed))
        about[r["dest"]].append(heading(r["text"]))   # never the what cell: AGENTS.md takes no agent's words
    for t in tinfo:
        home = join(t["p"], "AGENTS.md")
        mine = [p for p in list(chunks) if p.startswith("docs/agents/") and owner(p) == t["p"]]
        if mine:
            begin(home, None)
            chunks[home].append(POINTERS + "\n\n" + "".join(
                f"- `{p}`" + (f": {describe(about[p])}" if describe(about[p]) else "") + "\n" for p in mine))
    text = {p: "\n".join(c if c.endswith("\n") else c + "\n" for c in cs) for p, cs in chunks.items()}
    unread = [(p, tokens(len(text[p].encode()))) for p in text
              if (gm := GUIDE.fullmatch(p)) and gm["g"] not in KNOWN_GUIDES and how[p] == "new"]
    return text, how, repointed, unread


CHECK_KEYS = ("result", "input", "rows", "writes", "unread", "flags", "drops", "repointed", "problem", "fix", "message")


def prepare(reply, out, mode):
    """detect, then reply's table parsed against its sources: (tinfo, rows, None), or the report
    that stops mode here as the third."""
    report, bad, tinfo = detect()
    result = dict(report)["result"]
    if bad or result != "migrate":
        why = "detect reports problems" if bad else f"detect reports {result}: there is nothing to migrate"
        return [], [], out(result="error", input=reply, problem=[why], fix=["run detect, and act on its report first"],
                               message=f"The table was not read: {mode} works on a repository detect can migrate.")
    sources = [s for t in tinfo for s in t["src"]]
    try:
        text = read(reply).decode("utf-8", "replace")
    except OSError as e:
        return [], [], out(result="error", input=reply, problem=[f"cannot read {reply}: {e.strerror}"],
                               fix=["write docs-classifier's report to that file, then run this again"],
                               message="The table was not read.")
    rows, probs, fixes = parse(text, sources, [t["p"] for t in tinfo])
    if probs:
        framed = probs[0].startswith("the reply was copied")
        return [], [], out(result="problems", input=reply, problem=probs, fix=fixes, message=(
            "The reply was copied in its frame: write it again alone, and check it again." if framed else
            f"docs-classifier's table has {len(probs)} problem{'s' if len(probs) > 1 else ''}: ask it again, "
            "giving it each problem: line with its fix: line."))
    return tinfo, rows, None


def check(reply):
    """The check report, as (key, value) pairs, and whether it found a problem."""
    def out(**kw):
        return [(k, kw.get(k, [])) for k in CHECK_KEYS]
    tinfo, rows, stop = prepare(reply, out, "check")
    if stop:
        return stop, True
    sources = [s for t in tinfo for s in t["src"]]
    text, how, repointed, unread = plan(rows, tinfo)
    writes, flags, drops = [], [], []
    for p, t in text.items():
        n, k = len(t.splitlines()), tokens(len(t.encode()))
        over = [w for w, hit in ((f"over {MAX_LINES} lines", n > MAX_LINES), (f"over ≈{MAX_TOKENS:,} tokens", k > MAX_TOKENS))
                if hit and not p.startswith("docs/agents/") and os.path.basename(p) == "AGENTS.md"]
        writes.append(f"{p} ({how[p]}): {n} lines, ≈{k:,} tokens" + (" — " + ", ".join(over) if over else ""))
    for r in rows:
        kinds = (["obsolete"] if r["kind"] == "obsolete" else []) + \
                (["dated"] if r["kind"] == "agents" and DATE.search(r["text"]) else []) + \
                (["overlong"] if any(len(l.rstrip("\n")) > OVERLONG for l in r["text"].splitlines()) else [])
        if r["kind"] == "drop":
            pct = share(r["text"], r["where"])
            drops.append(f"{r['src']} -> {r['where']}: {pct}% found")
            kinds += [f"duplicate, {pct}% found"] if pct < SHARE else []
        if kinds:
            flags.append(f"{r['src']} -> {r['dest']}: {', '.join(kinds)}")
    unsure = sum(r["flag"] != "sure" for r in rows)
    lost = sum(k for _, k in unread)
    return out(result="clean", input=reply, rows=f"{len(rows)}, {unsure} flagged unsure by docs-classifier",
               writes=writes, unread=[f"{p}: ≈{k:,} tokens" for p, k in unread], flags=flags, drops=drops,
               repointed=repointed, message=(
                   f"The table covers every non-blank line of the {len(sources)} source{'s' if len(sources) > 1 else ''} "
                   f"in {len(rows)} row{'s' if len(rows) > 1 else ''}; {len(flags)} of them "
                   f"{'carries' if len(flags) == 1 else 'carry'} a rule flag, and ≈{lost:,} tokens go to guides "
                   "no agent reads.")), False


APPLY_KEYS = ("result", "input", "wrote", "repointed", "problem", "fix", "message")


def apply(reply):
    """Write what check plans, over files git has committed or that are not there, and report."""
    def out(**kw):
        return [(k, kw.get(k, [])) for k in APPLY_KEYS]
    tinfo, rows, stop = prepare(reply, out, "apply")
    if stop:
        return stop, True
    text, how, repointed, _ = plan(rows, tinfo)
    # Again, at the write: detect and check refuse a link already, and this is the last chance.
    links = [(p, l) for p in text for l in [link_in(p)] if l]
    if links:
        return out(result="problems", input=reply, problem=[linked(p, l) for p, l in links],
                   fix=[f"replace {l} with the file or folder it points to, or remove it, and run this again"
                        for _, l in links],
                   message="Nothing was written: apply writes through no symbolic link."), True
    status = git("status", "--porcelain", "-z", "--untracked-files=all", "--", *text)
    if status is None:
        return out(result="error", input=reply, problem=["git status failed in this repository"],
                   fix=["run git status here and repair what it reports, then run this again"],
                   message="Nothing was written."), True
    # A file apply wrote is uncommitted, so a second run stops here rather than append it again.
    dirty = sorted({e[3:] for e in status.split("\0") if len(e) > 3})
    if dirty:
        return out(result="problems", input=reply,
                   problem=[f"{p} has changes git has not committed: apply may have run already" for p in dirty],
                   fix=[f"commit {p}, or restore it with git restore, or remove it if untracked, then run this again"
                        for p in dirty],
                   message="Nothing was written: apply writes only over files git has committed, or none."), True
    # What a file already carries is the record of a run, whatever git says: committed between two
    # runs, a first run's writes look clean. A file apply replaces is the old build's copy of a
    # source, which carries the source's text by construction, and is not counted.
    mv, already = moves(tinfo), {}
    for r in rows:
        if r["kind"] not in ("drop", "obsolete") and how.get(r["dest"]) == "appends" and \
                occurrences(relink(r["text"], r["f"], r["dest"], mv, []), read(r["dest"]).decode("utf-8", "replace")):
            already.setdefault(r["dest"], []).append(r["src"])
    for t in tinfo:
        if t["cx"] and os.path.isfile(t["guide"]) and read(t["guide"]).decode("utf-8", "replace").startswith(
                relink(read(t["cx"]).decode("utf-8", "replace"), t["cx"], t["guide"], mv, [])):
            already.setdefault(t["guide"], []).append(t["cx"])
    if already:
        return out(result="problems", input=reply,
                   problem=[f"{d} already carries {describe(ls)}: apply has run already" for d, ls in already.items()],
                   fix=["go on to verify, or restore what apply wrote and start again"] * len(already),
                   message="Nothing was written: apply has run already."), True
    wrote = []
    for p, t in text.items():
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "wb") as f:
            f.write(t.encode("utf-8"))
        wrote.append(f"{p} ({how[p]}): {len(t.splitlines())} lines, ≈{tokens(len(t.encode())):,} tokens")
    return out(result="written", input=reply, wrote=wrote, repointed=repointed,
               message=f"Wrote {len(wrote)} file{'s' if len(wrote) > 1 else ''} and deleted nothing: "
                       "run verify before the destructive step."), False


VERIFY_KEYS = ("result", "input", "moved", "drops", "dead", "delete", "pointers", "problem", "fix", "message")


def pointers(gone):
    """Each line of the repository's text files, but for the files the destructive step deletes,
    that points at one of them: a Markdown link resolving to it, or its exact path where it has a
    folder, since a bare CLAUDE.md in prose names the idea far more often than the file. Two kinds
    of file are not the user's live text and are skipped: docs/plan/, records of past work no one
    rewrites, and each AGENTS.override.md, which the build after the delete replaces. Listed for
    the user, who decides where each should point now; nothing here blocks."""
    listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard") or ""
    paths = [g for g in gone if "/" in g]
    found = []
    for f in sorted(p for p in listed.split("\0") if p and p not in gone and not outside(p)
                    and not p.startswith("docs/plan/") and os.path.basename(p) != "AGENTS.override.md"):
        try:
            b = read(f)
        except OSError:
            continue
        if b"\0" in b:   # binary
            continue
        for n, line in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
            hits = [g for g in paths if re.search(r"(?<![\w./-])" + re.escape(g) + r"(?![\w-])", line)]
            if f.endswith(".md"):
                for url in [m.group(2) for m in LINK.finditer(line)] + [m.group(2) for m in REFDEF.finditer(line)]:
                    bare = url[1:-1] if url.startswith("<") else url
                    if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", bare) and not bare.startswith(("#", "/")) and \
                            target(f, url) in gone:
                        hits.append(target(f, url))
            if hits:
                found.append(f"{f}:{n}: {', '.join(sorted(set(hits)))}")
    return found


def target(base, url):
    """Where a relative link in the file base points, in the repository."""
    bare = url[1:-1] if url.startswith("<") else url
    return os.path.normpath(os.path.join(os.path.dirname(base), bare.partition("#")[0]))


def verify(reply):
    """Check, after apply and before the destructive step, that every row and codex.md is in
    its destination, its links rewritten as apply rewrites them, and that the move broke no link."""
    def out(**kw):
        return [(k, kw.get(k, [])) for k in VERIFY_KEYS]
    tinfo, rows, stop = prepare(reply, out, "verify")
    if stop:
        return stop, True
    mv = moves(tinfo)
    items = [(r["src"], r["f"], r["text"], r["dest"]) for r in rows if r["kind"] not in ("drop", "obsolete")]
    items += [(t["cx"], t["cx"], read(t["cx"]).decode("utf-8", "replace"), t["guide"]) for t in tinfo if t["cx"]]
    probs, fixes, dead, found = [], [], [], 0
    wants = [(relink(text, src, dest, mv, []), dest) for _, src, text, dest in items]
    for label, src, text, dest in items:
        links = []
        want = relink(text, src, dest, mv, [], links)
        have = read(dest).decode("utf-8", "replace") if os.path.isfile(dest) else None
        n = occurrences(want, have) if have is not None else 0
        if not n:
            probs.append(f"{label}: its text is not in {dest}" + (", which is not there" if have is None else ""))
            fixes.append("run apply on this reply; if it ran, restore what it wrote, and run it again")
            continue
        if n > wants.count((want, dest)):   # more than the rows that carry the same text there
            probs.append(f"{label}: its text is in {dest} {n} times")
            fixes.append("restore what apply wrote, and run apply once")
        found += 1
        for old, new in links:
            if not os.path.exists(target(src, old)):
                dead.append(f"{label}: {old}, already dead in {src}")
            elif not os.path.exists(target(dest, new)):
                probs.append(f"{label}: {old} resolves in {src}, but {new} does not in {dest}")
                fixes.append(f"restore what apply wrote; then point the link elsewhere in {src}, or route a row "
                             f"to {target(dest, new)}, and start again")
    drops = [f"{r['src']} -> {r['where']}: {share(r['text'], r['where'])}% found" if r["kind"] == "drop"
             else f"{r['src']} -> {r['dest']}" for r in rows if r["kind"] in ("drop", "obsolete")]
    moved = f"{found} of {len(items)} rows and codex.md moves found in their destinations"
    if probs:
        return out(result="problems", input=reply, moved=moved, drops=drops, dead=dead, problem=probs, fix=fixes,
                   message=f"The destructive step is not offered: {len(probs)} problem{'s' if len(probs) > 1 else ''}, "
                           "each with its fix."), True
    delete = dict(detect()[0])["delete"]
    return out(result="clean", input=reply, moved=moved, drops=drops, dead=dead, delete=delete, pointers=pointers(delete),
               message="Every non-blank line of every source is moved or dropped with a reason, and the move broke "
                       f"no link: the destructive step may remove the {len(delete)} file{'s' if len(delete) > 1 else ''} "
                       "under delete:."), False


def emit(report):
    for key, value in report:
        items = value if isinstance(value, list) else [value]
        print(f"{key}: {items[0] if items else '—'}")
        for v in items[1:]:
            print(f"  {v}")


def main(argv):
    if argv[1:] == ["detect"]:
        report, bad, _ = detect()
    elif len(argv) == 3 and argv[1] in ("check", "apply", "verify"):
        report, bad = {"check": check, "apply": apply, "verify": verify}[argv[1]](argv[2])
    else:
        print("usage: migrate-agents-docs.py detect | check <reply> | apply <reply> | verify <reply>", file=sys.stderr)
        return 2
    emit(report)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
