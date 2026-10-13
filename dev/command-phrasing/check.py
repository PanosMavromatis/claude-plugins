"""Check that every workflow-coding command granting git says how to phrase a command so
allowed-tools matches it. Read-only.

  python3 -I check.py [<command.md> | <directory>]...

With no argument it checks the plugin's commands/. A command grants git when the
allowed-tools key in its frontmatter holds a Bash(git …) entry. Each such command must
carry, in its body, both fixed phrases the plugin's CLAUDE.md names under "Scoped
`allowed-tools`", each whole on one line: never `git -C <path>`, and every command alone.
Exit 0 when every command does, 1 naming each command and the phrase it lacks, 2 on a
usage error or when there is no command to check."""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMMANDS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "plugins", "workflow-coding", "commands")
PHRASES = ["never `git -C <path>`", "every command alone"]

def split(text):
    """The frontmatter's lines and the body's, or no frontmatter and every line."""
    lines = text.split("\n")
    if lines[0] == "---" and "---" in lines[1:]:
        end = lines.index("---", 1)
        return lines[1:end], lines[end + 1:]
    return [], lines

def allowed_tools(head):
    """The allowed-tools value: its own line, and any list items or indented lines under it."""
    for i, line in enumerate(head):
        if line.startswith("allowed-tools:"):
            value = [line]
            for more in head[i + 1:]:
                if not more.startswith((" ", "\t", "-")): break
                value.append(more)
            return " ".join(value)
    return ""

def usage(msg):
    print(f"check.py: {msg}", file=sys.stderr); sys.exit(2)

paths = []
for arg in sys.argv[1:] or [COMMANDS]:
    if os.path.isdir(arg): paths += sorted(glob.glob(os.path.join(arg, "*.md")))
    elif os.path.isfile(arg): paths.append(arg)
    else: usage(f"no such file or directory: {arg}")
if not paths: usage("no command files to check")

failing = 0
for path in paths:
    head, body = split(open(path, encoding="utf-8").read())
    name = os.path.basename(path)
    if "Bash(git " not in allowed_tools(head):
        print(f"skip  {name} (grants no git)"); continue
    lacks = [p for p in PHRASES if not any(p in line for line in body)]
    if lacks:
        print(f"FAIL  {name} lacks: {'; '.join(lacks)}"); failing += 1
    else: print(f"ok    {name}")
print(f"\n{failing} failing"); sys.exit(1 if failing else 0)
