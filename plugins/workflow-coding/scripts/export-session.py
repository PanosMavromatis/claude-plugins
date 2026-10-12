"""Render a Claude Code session log (JSONL) as readable Markdown, compactions included.

  python3 -I export-session.py <session> [<output.md> | <output dir>] [--subagents]

A session is named by the path of its log, by its id, or by the name /rename gave it. An
id or a name is looked up in this project's log directory, which Claude Code names after
the working directory, each character other than a letter or digit made `-`: an id is the
log's own name, and a name is matched against each `<uuid>/custom-title.json`. A renamed
session's log keeps every name it has had, so its records cannot say which one is
current; that file can.

Given a directory, or nothing, the export is named for the session: `<name>.md`, where
`<name>` is its /rename name, or its id if it was never renamed. The default directory is
~/claude-exports/<the working directory's name>/. The export goes outside the repository:
a path inside the git repository holding the working directory is refused.

/export writes only what is in context, so after a compaction it loses everything before
the summary. Claude Code's session log, ~/.claude/projects/<project-dir>/<session-uuid>.jsonl,
is append-only and survives compaction, so the whole conversation is rendered from it.

Output: the operator's messages, the assistant's visible replies, AskUserQuestion
questions and answers, slash commands run with their arguments, compaction summaries
(collapsed), and one-line entries for tool actions. Omitted: tool output, system
reminders, hidden reasoning and subagent sidechains. The title is the output file's name,
less `.md` and any `-full`.

With --subagents, each subagent's transcript, from `<uuid>/subagents/`, follows the call
that spawned it, collapsed; one whose call is not in the log goes in an appendix. A
subagent's own records are all sidechain records, so they are rendered without the filter
that drops sidechains from the main log. A subagent may hand its answer back as a
SubagentHandback call rather than as text; that call's message is rendered as its reply.

Beside <name>.md it keeps the raw record, which the Markdown leaves out: the log, byte for
byte, as <name>.jsonl, and the session's folder, `<uuid>/` (large tool outputs, subagent
transcripts, custom-title.json), as <name>.tar.gz, which unpacks into `<name>/`. A
session that was never renamed and spawned no subagent has no folder, and no archive. It
refuses to write <name>.jsonl over the log it reads, and creates the output directory.

Both files are read and written as UTF-8 whatever the locale, so an em dash is written
once, as itself."""
import glob, json, os, re, shutil, sys, tarfile

args = sys.argv[1:]
flags, pos = [a for a in args if a.startswith("--")], [a for a in args if not a.startswith("--")]
subagents = "--subagents" in flags
if not 1 <= len(pos) <= 2 or any(f != "--subagents" for f in flags):
    print("usage: export-session.py <session> [<output.md> | <output dir>] [--subagents]", file=sys.stderr)
    sys.exit(2)
arg, out_arg = pos[0], (pos[1] if len(pos) == 2 else None)
UUID = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"

def fail(msg):
    print(f"export-session.py: {msg}", file=sys.stderr)
    sys.exit(1)

def names(log):   # the session's current name: the one /rename left in <uuid>/custom-title.json
    try:
        with open(log.removesuffix(".jsonl") + "/custom-title.json", encoding="utf-8") as f: return {json.load(f).get("customTitle")}
    except (OSError, ValueError, AttributeError): return set()

if arg.endswith(".jsonl"):
    if not os.path.isfile(arg): fail(f"no such session log: {arg}")
    src = arg
else:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    d = os.path.join(base, "projects", re.sub(r"[^A-Za-z0-9]", "-", os.getcwd()))
    if not os.path.isdir(d): fail(f"no session log directory for this project: {d}")
    if re.fullmatch(UUID, arg) and os.path.isfile(os.path.join(d, arg + ".jsonl")):   # a session id
        hits = [os.path.join(d, arg + ".jsonl")]
    else:
        hits = [p for p in sorted(glob.glob(os.path.join(glob.escape(d), "*.jsonl"))) if arg in names(p)]
    if not hits: fail(f"no session named {arg!r} in {d}: a session's name is the one /rename gave it")
    if len(hits) > 1:
        fail(f"{len(hits)} sessions named {arg!r} in {d}: " + ", ".join(os.path.basename(p) for p in hits)
             + "; pass the log's path instead")
    src = hits[0]
if out_arg and out_arg.endswith(".md"):
    dst = out_arg
else:   # a directory, or the default one: the export is named for the session
    title = next(iter(names(src)), None)
    name = (title if isinstance(title, str) and title else os.path.basename(src).removesuffix(".jsonl")).replace("/", "-")
    out_dir = out_arg or os.path.join(os.path.expanduser("~"), "claude-exports", os.path.basename(os.getcwd()))
    dst = os.path.join(out_dir, name + ".md")

def repo_of(p):   # the git working tree holding p, if any
    p = os.path.realpath(p)
    while not os.path.exists(os.path.join(p, ".git")):
        if os.path.dirname(p) == p: return None
        p = os.path.dirname(p)
    return p
repo = repo_of(os.getcwd())
if repo and (os.path.realpath(os.path.dirname(os.path.abspath(dst))) + "/").startswith(repo + "/"):
    fail(f"{dst} is inside the repository {repo}: an export goes outside it")
base, folder = dst.removesuffix(".md"), src.removesuffix(".jsonl")
if os.path.exists(base + ".jsonl") and os.path.samefile(base + ".jsonl", src):
    fail(f"{base}.jsonl is the session log itself: write the export somewhere else")
REMINDER =re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
CMD = re.compile(r"<command-name>(.*?)</command-name>(?:.*?<command-args>(.*?)</command-args>)?", re.S)
LOCAL = re.compile(r"<local-command-(?:stdout|caveat)>.*?</local-command-(?:stdout|caveat)>", re.S)

def when(r):
    return r.get("timestamp", "")[:16].replace("T", " ") + " UTC"

def tool_line(b):
    name, i = b.get("name", ""), b.get("input", {}) or {}
    detail = (i.get("description") or i.get("file_path") or i.get("url") or i.get("query")
              or i.get("title") or i.get("action") or "")
    return f"- `{name}`" + (f": {str(detail)[:160]}" if detail else "")

def load(path):
    with open(path, encoding="utf-8") as log:
        lines = log.readlines()
    records = []
    for line in lines:
        try: records.append(json.loads(line))
        except Exception: continue
    return records

def render(records, h="##", op="Operator", cl="Claude", side=False, subs=None):
    """The Markdown blocks for a log's records. A subagent's log is rendered with h="###",
    its own labels, and side=True; subs maps a spawning call's id to its subagent."""
    out, pending_tools, ask_ids = [], [], {}
    def flush_tools():
        if pending_tools:
            out.append("<details><summary>Actions (" + str(len(pending_tools)) + ")</summary>\n\n"
                       + "\n".join(pending_tools) + "\n\n</details>\n")
            pending_tools.clear()
    for r in records:
        t = r.get("type")
        if t not in ("user", "assistant") or r.get("isMeta") or (r.get("isSidechain") and not side): continue
        content = r.get("message", {}).get("content")
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
        if t == "assistant":
            for b in blocks:
                if b.get("type") == "text" and b["text"].strip():
                    flush_tools()
                    out.append(f"{h} {cl} — {when(r)}\n\n{b['text'].strip()}\n")
                elif b.get("type") == "tool_use":
                    handback = (b.get("input") or {}).get("message") if b.get("name") == "SubagentHandback" else None
                    if isinstance(handback, str) and handback.strip():   # a subagent's answer, sent as a call
                        flush_tools()
                        out.append(f"{h} {cl} — {when(r)}\n\n{handback.strip()}\n")
                    elif b.get("name") == "AskUserQuestion":
                        flush_tools()
                        qs = (b.get("input") or {}).get("questions", [])
                        txt = "\n".join(f"- **{q.get('question')}** Options: "
                                        + "; ".join(o.get("label", "") for o in q.get("options", []))
                                        for q in qs)
                        out.append(f"{h} {cl} asks — {when(r)}\n\n{txt}\n")
                        ask_ids[b.get("id")] = True
                    else:
                        pending_tools.append(tool_line(b))
                        if subs and b.get("id") in subs:
                            flush_tools()
                            out.append(subagent(subs.pop(b.get("id"))))
            continue
        # user
        if r.get("isCompactSummary"):
            flush_tools()
            text = blocks[0].get("text", "") if blocks else ""
            out.append(f"{h} Compaction summary — {when(r)}\n\n<details><summary>Summary the session "
                       f"continued from</summary>\n\n{text.strip()}\n\n</details>\n")
            continue
        for b in blocks:
            if b.get("type") == "tool_result":
                if b.get("tool_use_id") in ask_ids:
                    c = b.get("content")
                    c = c if isinstance(c, str) else " ".join(x.get("text", "") for x in (c or []) if isinstance(x, dict))
                    flush_tools()
                    out.append(f"{h} {op} answers — {when(r)}\n\n{c.strip()}\n")
                continue
            if b.get("type") != "text": continue
            text = REMINDER.sub("", b["text"])
            m = CMD.search(text)
            if m:
                flush_tools()
                args = (m.group(2) or "").strip()
                out.append(f"{h} {op} ran `{m.group(1)}` — {when(r)}\n" + (f"\n{args}\n" if args else ""))
                continue
            text = LOCAL.sub("", text).strip()
            if not text or text.startswith("[Request interrupted"):
                if text: out.append(f"*{text}*\n")
                continue
            flush_tools()
            out.append(f"{h} {op} — {when(r)}\n\n{text}\n")
    flush_tools()
    return out

def subagent(s):   # one subagent's transcript, collapsed
    blocks = render(load(s["log"]), "###", "Prompt", "Subagent", side=True)
    n = sum(1 for x in blocks if x.startswith("### Subagent —"))
    return (f"<details><summary>Subagent {s['type']} — {s['desc']} ({n} replies)</summary>\n\n"
            + "\n".join(blocks) + "\n</details>\n")

subs = {}
if subagents:
    for m in sorted(glob.glob(os.path.join(glob.escape(src.removesuffix(".jsonl")), "subagents", "*.meta.json"))):
        try:
            with open(m, encoding="utf-8") as f: meta = json.load(f)
        except (OSError, ValueError): continue
        log = m.removesuffix(".meta.json") + ".jsonl"
        if os.path.isfile(log):
            subs[meta.get("toolUseId") or log] = dict(log=log, type=meta.get("agentType", "agent"),
                                                      desc=meta.get("description", ""))
found = len(subs)

out = [f"# Session {os.path.basename(dst).removesuffix('.md').removesuffix('-full')} — full transcript\n\nRendered from the Claude Code session log "
       f"`{src.split('/')[-1]}`. It contains the operator's messages, the assistant's visible replies, "
       "the operator's answers to multiple-choice questions, compaction summaries, and one-line "
       "entries for tool actions. It omits tool output, system reminders and hidden reasoning.\n"]
out += render(load(src), subs=subs)
if subs:   # subagents whose spawning call the log does not hold
    out.append("## Subagents whose call is not in the log\n")
    out += [subagent(s) for s in subs.values()]
os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
with open(dst, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
shutil.copyfile(src, base + ".jsonl")   # the raw log: tool output, reasoning and token counts
archived = os.path.isdir(folder)
if archived:   # large tool outputs and subagent transcripts live only here
    with tarfile.open(base + ".tar.gz", "w:gz") as t:
        t.add(folder, arcname=os.path.basename(base))
print(dst, sum(1 for s in out if s.startswith("## Operator —")), "operator messages,",
      sum(1 for s in out if s.startswith("## Claude —")), "assistant replies,",
      sum(1 for s in out if s.startswith("## Compaction")), "compactions"
      + (f", {found} subagents" if subagents else "")
      + ", raw log copied" + (", session folder archived" if archived else ", no session folder"))
