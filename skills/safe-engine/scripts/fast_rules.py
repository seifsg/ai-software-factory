"""Owner-only rules for the fast_gate.py destructive guard: structure-blind triggers over a command's judged text,
and the word-level readings (deletes, force_push) that fast_guard.py uses to prove a fired rule harmless.
"""
import fnmatch
from itertools import takewhile
import re

from fast_shell import CLIENTS, UNREADABLE, program


def word(names):
    """Regex for any of names as a whole command word (not part of a path, flag or file name)."""
    return rf"(?<![\w.-])(?:{names})(?:\.exe)?(?![\w.-])"


DELETERS = {"rm", "rmdir", "rd", "del", "erase", "ri", "remove-item"}
DOS = {"rmdir", "rd", "del", "erase"}  # cmd.exe takes /s flags
PROTECTED_NAMES = {"run.json", ".git", ".factory", "fast"}  # a find -name pattern must match none of these
LEDGER = re.compile(r"run\.json", re.I)  # the run's ledger: deleting it, even without -r, disables the gate
WILDCARD = re.compile(r"[*?[]")  # a pattern target may reach a protected path whatever its flags
MOVERS = {"mv", "move", "move-item", "mi", "ren", "rename", "rename-item", "rni"}
MOVE = re.compile(word("|".join(MOVERS)), re.I)
# never a shell move: their inline code is another language, whose "move" or 'mv' text is data (fast-run.md limits)
INTERPRETER = re.compile(r"py|python[\d.]*|pypy[\d.]*|node|nodejs|deno|bun|ruby|perl|php|lua")
PROTECTED_HINT = re.compile(r"\.git(?![\w-])|\.fact|run\.json|(?<![\w.-])fast(?![\w.-])", re.I)
PATH_TESTS = {"-path", "-ipath", "-wholename", "-iwholename", "-regex", "-iregex"}
NEGATIONS = ("-not", "!")
DELETE = re.compile(word("|".join(DELETERS | {"rimraf"})) + r"|(?<![\w-])-delete\b", re.I)
RECURSIVE_HINT = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*[rR][a-zA-Z]*(?::\S*)?|--recursive|/[sS](?:/\w)*)(?![\w-])|"
                            + word("rimraf|find"), re.I)
GIT, PUSH_WORD = re.compile(word("git"), re.I), re.compile(word("push"), re.I)
CLEAN, STASH = re.compile(word("clean"), re.I), re.compile(word("stash"), re.I)
IGNORED = re.compile(r"(?<![\w-])-[a-zA-Z]*[xX][a-zA-Z]*(?![\w-])")  # git clean -x/-X: also ignored files
ALL = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*a[a-zA-Z]*|--all)(?![\w-])")  # git stash -a/--all: also ignored files
FORCE = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*[fd][a-zA-Z]*|--force[\w-]*|--mirror|--delete|--prune)(?![\w-])|"
                   r"(?<!\S)[+:][^\s:]")
CLIENT = re.compile(word("|".join(CLIENTS)) + r"|\b(?:db|d1)\s+execute\b|\brails\s+db\b(?!:)", re.I)
WIPE = re.compile(r"(?:\b|(?<=-\w))(?:drop|truncate)\s+\w|\.drop\w*\s*\(", re.I)  # -e"DROP ..." reads -eDROP
TOKENS = re.compile(r"[^\s'\"=<>|;&()]+")  # whole words: linear scans, no backtracking
MIGRATE_PARTS = {"migrate", "migration", "migrations"}
DESTROY = re.compile(r"\bdropdb\b|\bdb:(?:drop|reset|purge|wipe)\b|\bmigrate(?::|\s+)(?:fresh|reset)\b|"
                     r"\becto\.(?:drop|reset)\b|(?:manage\.py|django-admin)\s+flush\b|\bsupabase\s+db\s+reset\b|"
                     r"--force-reset\b|\bschema:drop\b", re.I)
MIGRATE_TOOL = re.compile(r"\b(?:alembic|liquibase|flyway|dbmate|goose|drizzle-kit)\b|\bdb\s+(?:upgrade|push)\b|"
                          r"\bef\s+database\s+update\b", re.I)
PROD = re.compile(r"(?<![A-Za-z0-9_])prod(?:uction)?(?![A-Za-z0-9])", re.I)  # a marker, not part of a name
DEFAULT_BRANCHES = {"main", "master"}
TEXT = {
    "unreadable": "a command the hook cannot read (encoded, or nested too deep)",
    "wipe": "DROP or TRUNCATE through a database client",
    "destroy": "a database-destroying command",
    "migrate": "migration aimed at production",
    "push": "force, mirror or prune push, or default-branch delete (allowed: --force-with-lease <remote> <branch> to a "
            "branch other than main or master)",
    "delete": "recursive delete",
    "ignored": "git clean -x/-X or git stash --all (they also remove the ignored .factory)",
    "move": "move or rename of a protected path (.git, .factory, its run.json, the project or the gate home's run files)",
}
ALWAYS = ("unreadable", "wipe", "destroy")  # no proof can allow these


def fired(text, sql):
    """Rules whose tokens appear anywhere in text, structure-blind. sql() yields referenced SQL file texts; it is
    called only when a database client appears without DROP or TRUNCATE in the text itself."""
    found = set()
    if UNREADABLE in text:
        found.add("unreadable")
    if DELETE.search(text) and (RECURSIVE_HINT.search(text) or LEDGER.search(text) or WILDCARD.search(text)):
        found.add("delete")
    if GIT.search(text) and ((CLEAN.search(text) and IGNORED.search(text)) or (STASH.search(text) and ALL.search(text))):
        found.add("ignored")
    if MOVE.search(text) and (PROTECTED_HINT.search(text) or WILDCARD.search(text)):
        found.add("move")
    if PUSH_WORD.search(text) and GIT.search(text) and FORCE.search(text):
        found.add("push")
    if CLIENT.search(text) and (WIPE.search(text) or any(WIPE.search(body) for body in sql())):
        found.add("wipe")
    if DESTROY.search(text):
        found.add("destroy")
    if migrates(text) and PROD.search(text):
        found.add("migrate")
    return found


def migrates(text):
    """True when text holds a migration word (migrate, db:migrate, ecto.migrate, migration:run, db:*) or tool."""
    for token in TOKENS.findall(text):
        lower = token.lower()
        if lower.startswith("db:") or MIGRATE_PARTS & set(re.split(r"[:./\\]", lower)):
            return True
    return bool(MIGRATE_TOOL.search(text))


def sql_files(text):
    """Words in text naming a .sql file (an attached -f prefix stripped)."""
    names = [token for token in TOKENS.findall(text) if token.lower().endswith(".sql")]
    return [re.sub(r"^-\w", "", name) if name.startswith("-") else name for name in names]


def recursive(flag):
    """True for a recursive delete flag: -r, -rfvi, --recursive, -Recurse (a prefix, or :$true), /s, /s/q."""
    base, _, value = flag.partition(":")
    lower = base.lower()
    return value.lower() != "$false" and (
        lower == "--recursive" or (lower.startswith("/") and "s" in lower.split("/"))
        or (len(lower) > 1 and "-recurse".startswith(lower)) or bool(re.fullmatch(r"-[fiIdv]*[rR][fiIrRdv]*", base)))


def named(words):
    """(pattern, case-folded) for each -name/-iname test of a find, None when one is negated."""
    found = []
    for i, w in enumerate(words[:-1]):
        if w in ("-name", "-iname"):
            if i and words[i - 1] in NEGATIONS:
                return None
            found.append((words[i + 1], w == "-iname"))
    return found


def widened(words):
    """True when a find has -o, or a -path/-regex test that is not negated (only exclusions are proven)."""
    return bool({"-o", "-or"} & set(words)) or any(
        w in PATH_TESTS and not (i and words[i - 1] in NEGATIONS) for i, w in enumerate(words))


def spared(words):
    """True when a find names files by patterns that cannot match a protected name (run.json, .git, .factory,
    fast), negates none of them, and nothing widens what it reaches."""
    patterns = named(words)
    return bool(patterns) and not widened(words) and not any(
        fnmatch.fnmatchcase(name, pattern.lower() if folded else pattern)
        for pattern, folded in patterns for name in PROTECTED_NAMES)


def excludes(words, folder):
    """True when a find negates (-not, !) or prunes a -path test naming folder: the negation bound to that test."""
    return any(words[i] in ("-path", "-ipath", "-wholename") and folder in words[i + 1]
               and ((i and words[i - 1] in NEGATIONS) or words[i + 2:i + 3] == ["-prune"])
               for i in range(len(words) - 1))


def deletes(words):
    """(target, mode) for each path the command deletes ([] when it names none), or None when it deletes nothing.
    mode: "tree" (the path and all below it), "below" (a find proven to spare protected names), "sweep" (any other
    find: like tree) or "file" (a delete without recursion). PowerShell comma lists count item by item."""
    name = program(words[0])
    if name == "git" and "rm" in words:
        if "--cached" in words:
            return None  # only the index changes
        words, name = words[words.index("rm"):], "rm"
    if name == "find":
        execs = [words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-exec", "-execdir", "-ok", "-okdir")]
        if "-delete" not in words and not any(program(w) in DELETERS | {"rimraf"} for w in execs):
            return None
        args = [w for w in words[1:] if w not in ("-H", "-L", "-P")]
        starts = list(takewhile(lambda w: not w.startswith(("-", "(", "!")), args))
        fenced = bool(named(words)) and not {"-o", "-or"} & set(words) and excludes(words, ".git") and excludes(
            words, ".factory")
        mode = "below" if spared(words) or fenced else "sweep"
        return [(start, mode) for start in starts or ["."]]
    if name == "rimraf":
        targets, mode = [w for w in words[1:] if not w.startswith("-")], "tree"
    elif name in DELETERS:
        flags = [w for w in words[1:] if w.startswith("-") or (name in DOS and re.fullmatch(r"(?:/\w)+", w))]
        joined = [f.split(":", 1)[1] for f in flags if re.match(r"(?i)-(?:path|literalpath|lp):.", f)]
        flagged = set(flags)
        targets = [w for w in words[1:] if w not in flagged] + joined
        mode = "tree" if any(recursive(flag) for flag in flags) else "file"
    else:
        return None
    return [(part, mode) for target in targets for part in target.split(",") if part]


def deleter(words):
    """True when deletes() can read this command (the rm family, rimraf, find, git rm)."""
    name = program(words[0])
    return name in DELETERS | {"rimraf", "find"} or (name == "git" and "rm" in words)


def force_push(words):
    """True for a force, mirror or +ref push, a default-branch delete, or a lease push not naming a safe branch."""
    args = words[words.index("push") + 1:]
    flags = [a for a in args if a.startswith("-")]
    refs = [a for a in args if not a.startswith("-")][1:]  # first positional is the remote
    heads = [ref.split(":")[-1].removeprefix("refs/heads/") for ref in refs]
    removing = bool({"--delete", "-d"} & set(flags)) or ("--prune" in flags and bool(refs))
    if "--mirror" in flags or any(re.fullmatch(r"--force|-[a-zA-Z]*f[a-zA-Z]*", f) for f in flags):
        return True
    if "--prune" in flags and refs:
        return True  # deletes remote branches the refspec does not name
    if any(ref.startswith("+") or (head in DEFAULT_BRANCHES and (removing or ref.startswith(":")))
           for ref, head in zip(refs, heads)):
        return True
    lease = any(f.startswith("--force-with-lease") for f in flags)
    return lease and (not refs or any(head in DEFAULT_BRANCHES | {"HEAD"} for head in heads))


def loses_ignored(words):
    """True unless words are a git clean without -x/-X or a git stash without -a/--all (both keep .factory)."""
    verb = next((w for w in words if w in ("clean", "stash")), None)
    if program(words[0]) != "git" or not verb:
        return True
    flag = IGNORED if verb == "clean" else ALL
    return any(flag.fullmatch(w) for w in words[words.index(verb) + 1:])


def moves(words):
    """Paths a mv, Move-Item, ren or Rename-Item touches (sources and destination), or None for other commands."""
    if program(words[0]) not in MOVERS:
        return None
    return [part for w in words[1:] if not w.startswith("-") for part in w.split(",") if part]


def pusher(words):
    """True when force_push() can read this command (git ... push)."""
    return program(words[0]) == "git" and "push" in words
