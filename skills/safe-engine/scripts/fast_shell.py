"""Shell command analysis for fast_gate.py hooks: files a command writes, whether it scaffolds, and destructive rules.

Pure string analysis; callers resolve paths. Heredoc bodies, PowerShell here-strings, quoted text and
shell arithmetic never count as code, so ticket bodies with "->" or "npm install" pass. Quoted redirect
targets still count.
"""
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
SEPARATOR = re.compile(r"[;&|\n()]+")
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
PREFIX = re.compile(r"(?:sudo|command|nohup|env|\w+=\S*)$", re.I)  # words before the program
DELETERS = {"rm", "rmdir", "rd", "del", "erase", "ri", "remove-item"}
DOS = {"rmdir", "rd", "del", "erase"}  # cmd.exe takes /s flags
CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "mongosh", "mongo", "duckdb", "sqlplus",
           "clickhouse-client"}
WIPE = re.compile(r"\b(?:drop|truncate)\s+\w|\.drop\w*\s*\(", re.I)
MIGRATE_WORD = re.compile(r"(?:[\w-]+:)*migrat(?:e|ion)s?(?::[\w-]+)*", re.I)
MIGRATE_TOOL = re.compile(r"\b(?:alembic|liquibase|flyway|dbmate|goose|drizzle-kit)\b|\bef\s+database\s+update\b|"
                          r"\bsupabase\s+db\s+push\b", re.I)
PROD = re.compile(r"\bprod(?:uction)?\b", re.I)
DEFAULT_BRANCHES = {"main", "master"}


def mask(command):
    """(code, quotes): bodies and arithmetic removed, each quoted string replaced by a numbered placeholder."""
    quotes = []

    def keep(match):
        quotes.append(match.group(0)[1:-1])
        return f"\x00{len(quotes) - 1}\x00"

    text = HERESTRING.sub(" ", HEREDOC.sub(r"\1\4", command))
    return ARITHMETIC.sub(" ", QUOTED.sub(keep, text)), quotes


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
    """word with each quote placeholder back to its text."""
    return PLACEHOLDER.sub(lambda match: quotes[int(match.group(1))], word)


def scaffolds(command):
    """True when the command's code (not its quoted text or bodies) scaffolds or installs packages."""
    return bool(SCAFFOLD.search(mask(command)[0]))


def program(word):
    """Bare program name: no folder, no .exe, lower case."""
    return re.sub(r"\.exe$", "", re.split(r"[\\/]", word)[-1].lower())


def commands(command):
    """Words of each simple command, program first, quotes restored; quoted separators never split."""
    code, quotes = mask(command)
    for part in SEPARATOR.split(code):
        words = part.split()
        while words and PREFIX.match(words[0]):
            words.pop(0)
        if words:
            yield [unquote(word, quotes) for word in words]


def recursive(flag):
    """True for a recursive delete flag: -r, -rf, --recursive, -Recurse (or its prefix), /s."""
    flag = flag.lower()
    return (flag in ("--recursive", "/s") or (len(flag) > 1 and "-recurse".startswith(flag))
            or (bool(re.fullmatch(r"-[a-z]{1,3}", flag)) and "r" in flag))


def deletes(command):
    """Targets of each recursive delete (rm -r, Remove-Item -Recurse, rd /s). Callers resolve and judge them."""
    targets = []
    for words in commands(command):
        name = program(words[0])
        if name in DELETERS:
            flags = [w for w in words[1:] if w.startswith("-") or (name in DOS and re.fullmatch(r"/\w", w))]
            if any(recursive(flag) for flag in flags):
                targets += [w for w in words[1:] if w not in flags]
    return targets


def force_push(words):
    """True for git push --force, -f or +ref; --force-with-lease passes only to a named non-default branch."""
    if program(words[0]) != "git" or "push" not in words:
        return False
    args = words[words.index("push") + 1:]
    flags = [a for a in args if a.startswith("-")]
    refs = [a for a in args if not a.startswith("-")][1:]  # first positional is the remote
    if any(re.fullmatch(r"--force|-[a-zA-Z]*f[a-zA-Z]*", f) for f in flags) or any(r.startswith("+") for r in refs):
        return True
    lease = any(f.startswith("--force-with-lease") for f in flags)
    return lease and (not refs or any(r.split(":")[-1].removeprefix("refs/heads/") in DEFAULT_BRANCHES for r in refs))


def danger(command):
    """Name of the destructive rule the command breaks (force-push, database wipe, production migration), or None."""
    code = mask(command)[0]
    words = code.split()
    if any(force_push(parts) for parts in commands(command)):
        return "force-push (allowed: --force-with-lease <remote> <branch> to a non-default branch)"
    if any(program(w) in CLIENTS for w in words) and WIPE.search(command):
        return "DROP or TRUNCATE through a database client"
    if (any(MIGRATE_WORD.fullmatch(w) for w in words) or MIGRATE_TOOL.search(code)) and PROD.search(command):
        return "migration aimed at production"
    return None
