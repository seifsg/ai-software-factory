"""Shell command analysis for fast_gate.py hooks: files a command writes, whether it scaffolds, and destructive rules.

Pure string analysis; callers resolve paths. Heredoc bodies, PowerShell here-strings, quoted text and
shell arithmetic never count as code, so ticket bodies with "->" or "npm install" pass. Quoted redirect
targets still count. Destructive rules read each pipeline's own words and input, and nested command strings.
"""
import base64
from collections import namedtuple
from itertools import takewhile
import re

HEREDOC = re.compile(r"(<<-?[ \t]*(['\"]?)(\w+)\2)([^\n]*)\n.*?^[ \t]*\3[ \t]*$", re.S | re.M)
HERESTRING = re.compile(r"@'.*?^'@|@\".*?^\"@", re.S | re.M)
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", re.S)
ARITHMETIC = re.compile(r"\(\(.*?\)\)|\[\[.*?\]\]", re.S)
TARGET = r"(\x00\d+\x00|[^\s;&|<>()'\"\x00]+)"
REDIRECT = re.compile(r"(?<![<>])[&\d]?>>?\|?[ \t]*" + TARGET + r"|\|[ \t]*tee\b(?:[ \t]+-a)?[ \t]+" + TARGET)
SCAFFOLD = re.compile(
    r"\b(?:(?:npm|pnpm|yarn|bun)\s+(?:create|init|install|i|add)\b|(?:npx|pnpx|bunx|pnpm\s+dlx)\s+(?:-\S+\s+)*"
    r"(?:create-|shadcn|@\S+/create)|cargo\s+(?:new|init|add)\b|dotnet\s+new\b|go\s+mod\s+init\b|"
    r"flutter\s+create\b|rails\s+new\b|django-admin\s+startproject\b|(?:pip|uv|poetry)\s+(?:install|add|init|new)\b)",
    re.I)
DISCARD = ("/dev/null", "nul", "$null")
PIPELINES = re.compile(r"\|\||&&|[;\n()]|(?<![<>])&(?!>)")
TOKEN = re.compile(r"\d*(?:<<<|<<|<|&?>>?)(?:&[\d-]|\|)?|[^\s<>]+")  # a redirect operator, or a word
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
ASSIGN = re.compile(r"\w+=")
NUMBER = re.compile(r"[\d.]+[smhd]?")
WRAPPERS = {"sudo", "doas", "env", "timeout", "time", "nice", "nohup", "command", "exec", "stdbuf", "ionice"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}
PWSH = {"pwsh", "powershell"}
CD = {"cd", "pushd", "popd", "chdir", "set-location", "sl"}
DELETERS = {"rm", "rmdir", "rd", "del", "erase", "ri", "remove-item"}
DOS = {"rmdir", "rd", "del", "erase"}  # cmd.exe takes /s flags
CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "mongosh", "mongo", "duckdb", "sqlplus",
           "clickhouse-client"}
WIPE = re.compile(r"\b(?:drop|truncate)\s+\w|\.drop\w*\s*\(", re.I)
DESTROY = re.compile(r"^dropdb\b|\bdb:(?:drop|reset)\b|\bmigrate\s+reset\b", re.I)
MIGRATE_WORD = re.compile(r"(?:[\w-]+[:.])*migrat(?:e|ions?)(?:[:.][\w-]+)*|db:[\w:-]+", re.I)
MIGRATE_TOOL = re.compile(r"\b(?:alembic|liquibase|flyway|dbmate|goose|drizzle-kit)\b|\bdb\s+(?:upgrade|push)\b|"
                          r"\bef\s+database\s+update\b", re.I)
PROD = re.compile(r"(?<![a-z])prod(?:uction)?(?![a-z])", re.I)
DEFAULT_BRANCHES = {"main", "master"}
ENCODED = "\x00encoded"  # stands in for a PowerShell -EncodedCommand the hook cannot read
PUSH = ("force-push, mirror push or default-branch delete (allowed: --force-with-lease <remote> <branch> to a "
        "branch other than main or master)")
Command = namedtuple("Command", "words env inputs")  # program first; wrappers and assignments; (op, text) redirects in


def mask(command):
    """(code, quotes): heredoc bodies, here-strings and quoted strings become numbered placeholders; arithmetic goes."""
    quotes = []

    def hold(text):
        quotes.append(text)
        return f"\x00{len(quotes) - 1}\x00"

    text = HEREDOC.sub(lambda match: "<<" + hold(match.group(0).split("\n", 1)[1]) + match.group(4), command)
    text = HERESTRING.sub(lambda match: hold(match.group(0)[2:-2]), text)
    return ARITHMETIC.sub(" ", QUOTED.sub(lambda match: hold(match.group(0)[1:-1]), text)), quotes


def writes(command):
    """Target paths the command writes through redirects (> >> &> 1> >|) or a piped tee."""
    code, quotes = mask(command)
    names = []
    for first, second in REDIRECT.findall(code):
        name = unquote(first or second, quotes)
        if name and name[0] not in "&$" and name.lower() not in DISCARD:
            names.append(name)
    return names


def unquote(word, quotes):
    """word with each placeholder back to its text."""
    return PLACEHOLDER.sub(lambda match: quotes[int(match.group(1))], word)


def scaffolds(command):
    """True when the command's code (not its quoted text or bodies) scaffolds or installs packages."""
    return bool(SCAFFOLD.search(mask(command)[0]))


def program(word):
    """Bare program name: no folder, no .exe, lower case."""
    return re.sub(r"\.exe$", "", re.split(r"[\\/]", word)[-1].lower())


def parse(piece, quotes):
    """One simple command as a Command, redirects split off and wrappers (sudo -u x, timeout 10, env -i) skipped."""
    words, env, inputs = [], [], []
    tokens = iter(TOKEN.findall(piece))
    for token in tokens:
        if "<" not in token and ">" not in token:
            words.append(unquote(token, quotes))
            continue
        target = "" if re.search(r"&[\d-]$", token) else next(tokens, "")
        if "<" in token:
            inputs.append((token.lstrip("0123456789"), unquote(target, quotes)))
    while words and (ASSIGN.match(words[0]) or program(words[0]) in WRAPPERS):
        wrapper = program(words[0]) in WRAPPERS
        env.append(words.pop(0))
        while wrapper and words and (words[0].startswith("-") or NUMBER.fullmatch(words[0])):
            if words.pop(0) in ("-u", "-g", "-n", "-s", "-k") and words:
                words.pop(0)  # the option's value
    return Command(words, env, inputs) if words else None


def nested(words):
    """The command string a shell -c, eval, cmd /c or PowerShell -Command runs; ENCODED if unreadable; else None."""
    name, args = program(words[0]), words[1:]
    if name == "eval":
        return " ".join(args)
    for index, arg in enumerate(args):
        flag, rest = arg.lower(), args[index + 1:]
        if name in SHELLS and re.fullmatch(r"-[a-z]*c[a-z]*", flag):
            return rest[0] if rest else ""
        if (name == "cmd" and flag in ("/c", "/k")) or (
                name in PWSH and (flag == "-c" or (len(flag) > 3 and "-command".startswith(flag)))):
            return " ".join(rest)
        if name in PWSH and (flag in ("-e", "-ec") or (len(flag) > 3 and "-encodedcommand".startswith(flag))):
            try:
                return base64.b64decode(rest[0], validate=True).decode("utf-16-le")
            except (IndexError, ValueError):
                return ENCODED
    return None


def pipelines(command):
    """Each pipeline as its Commands, in order; a nested command string yields its own pipelines in its place."""
    code, quotes = mask(command)
    for part in PIPELINES.split(code):
        found = []
        for piece in part.split("|"):
            parsed = parse(piece, quotes)
            inner = parsed and nested(parsed.words)
            if inner == ENCODED:
                found.append(Command([ENCODED], [], []))
            elif inner is not None:
                yield from pipelines(inner)
            elif parsed:
                found.append(parsed)
        if found:
            yield found


def cd_target(words):
    """Where cd, pushd, chdir or Set-Location goes: its path, '~' with none, '' when unknown; None if not a cd."""
    name = program(words[0])
    if name not in CD:
        return None
    args = [w for w in words[1:] if not (w.startswith("-") and len(w) > 1) and w.lower() != "/d"]
    return "" if name == "popd" or "-" in args else (args[0] if args else "~")


def recursive(flag):
    """True for a recursive delete flag: -r, -rfvi, --recursive, -Recurse (a prefix, or :$true), /s."""
    base, _, value = flag.partition(":")
    lower = base.lower()
    return value.lower() != "$false" and (
        lower in ("--recursive", "/s") or (len(lower) > 1 and "-recurse".startswith(lower))
        or bool(re.fullmatch(r"-[fiIdv]*[rR][fiIrRdv]*", base)))


def deletes(words):
    """(target, strict) for each path the command deletes recursively. strict: the target itself goes (rm -r,
    Remove-Item -Recurse, rd /s); not strict: matches below a find start path go (find -delete, -exec rm)."""
    name = program(words[0])
    if name == "find":
        execs = [words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-exec", "-execdir", "-ok", "-okdir")]
        if "-delete" in words or any(program(w) in DELETERS for w in execs):
            starts = list(takewhile(lambda w: not w.startswith(("-", "(", "!")), words[1:]))
            return [(start, False) for start in starts or ["."]]
    elif name in DELETERS:
        flags = [w for w in words[1:] if w.startswith("-") or (name in DOS and re.fullmatch(r"/\w", w))]
        if any(recursive(flag) for flag in flags):
            return [(w, True) for w in words[1:] if w not in flags]
    return []


def force_push(words):
    """True for a force, mirror or +ref push, a default-branch delete, or a lease push not naming a safe branch."""
    if program(words[0]) != "git" or "push" not in words:
        return False
    args = words[words.index("push") + 1:]
    flags = [a for a in args if a.startswith("-")]
    refs = [a for a in args if not a.startswith("-")][1:]  # first positional is the remote
    heads = [ref.split(":")[-1].removeprefix("refs/heads/") for ref in refs]
    removing = bool({"--delete", "-d"} & set(flags))
    if "--mirror" in flags or any(re.fullmatch(r"--force|-[a-zA-Z]*f[a-zA-Z]*", f) for f in flags):
        return True
    if any(ref.startswith("+") or (head in DEFAULT_BRANCHES and (removing or ref.startswith(":")))
           for ref, head in zip(refs, heads)):
        return True
    lease = any(f.startswith("--force-with-lease") for f in flags)
    return lease and (not refs or any(head in DEFAULT_BRANCHES | {"HEAD"} for head in heads))


def danger(pipeline, read):
    """Destructive rule one pipeline breaks, or None. read(name) returns a `< file` input's text."""
    for cmd in pipeline:
        if cmd.words[0] == ENCODED:
            return "a PowerShell encoded command the hook cannot read"
        text = " ".join([program(cmd.words[0])] + cmd.words[1:])
        if force_push(cmd.words):
            return PUSH
        if DESTROY.search(text):
            return "a database-destroying command"
        migrates = any(MIGRATE_WORD.fullmatch(w) for w in cmd.words) or MIGRATE_TOOL.search(text)
        if migrates and PROD.search(" ".join(cmd.env + [text])):
            return "migration aimed at production"
    if any(program(w) in CLIENTS for cmd in pipeline for w in cmd.words):
        sql = [w for cmd in pipeline for w in cmd.words]
        sql += [read(text) if op == "<" else text for cmd in pipeline for op, text in cmd.inputs]
        if WIPE.search("\n".join(sql)):
            return "DROP or TRUNCATE through a database client"
    return None
