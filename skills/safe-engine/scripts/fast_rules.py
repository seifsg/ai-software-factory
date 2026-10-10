"""Owner-only rules for the fast_gate.py destructive guard: structure-blind triggers over a command's judged text,
and the word-level readings (deletes, force_push) that fast_guard.py uses to prove a fired rule harmless.
"""
from itertools import takewhile
import re

from fast_shell import CLIENTS, UNREADABLE, program


def word(names):
    """Regex for any of names as a whole command word (not part of a path, flag or file name)."""
    return rf"(?<![\w.-])(?:{names})(?:\.exe)?(?![\w.-])"


DELETERS = {"rm", "rmdir", "rd", "del", "erase", "ri", "remove-item"}
DOS = {"rmdir", "rd", "del", "erase"}  # cmd.exe takes /s flags
FILTERS = {"-name", "-iname", "-path", "-ipath", "-wholename", "-regex", "-iregex", "-type", "-newer", "-mtime",
           "-mmin", "-atime", "-size", "-empty", "-user", "-perm"}  # a find with one removes matches, not the tree
DELETE = re.compile(word("|".join(DELETERS | {"rimraf"})) + r"|(?<![\w-])-delete\b", re.I)
RECURSIVE_HINT = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*[rR][a-zA-Z]*(?::\S*)?|--recursive|/[sS](?:/\w)*)(?![\w-])|"
                            + word("rimraf|find"), re.I)
GIT, PUSH_WORD = re.compile(word("git"), re.I), re.compile(word("push"), re.I)
FORCE = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*[fd][a-zA-Z]*|--force[\w-]*|--mirror|--delete)(?![\w-])|(?<!\S)[+:][^\s:]")
CLIENT = re.compile(word("|".join(CLIENTS)) + r"|\b(?:db|d1)\s+execute\b", re.I)
WIPE = re.compile(r"(?:\b|(?<=-\w))(?:drop|truncate)\s+\w|\.drop\w*\s*\(", re.I)  # -e"DROP ..." reads -eDROP
SQL_FILE = re.compile(r"[^\s'\"=<>|;&()]+\.sql\b", re.I)
DESTROY = re.compile(r"\bdropdb\b|\bdb:(?:drop|reset|purge|wipe)\b|\bmigrate(?::|\s+)(?:fresh|reset)\b|"
                     r"\becto\.(?:drop|reset)\b|(?:manage\.py|django-admin)\s+flush\b|\bsupabase\s+db\s+reset\b|"
                     r"--force-reset\b|\bschema:drop\b", re.I)
MIGRATE = re.compile(r"(?<![\w-])(?:[\w-]+[:.])*migrat(?:e|ions?)(?:[:.][\w-]+)*(?![\w-])|(?<![\w-])db:[\w:-]+|"
                     r"\b(?:alembic|liquibase|flyway|dbmate|goose|drizzle-kit)\b|\bdb\s+(?:upgrade|push)\b|"
                     r"\bef\s+database\s+update\b", re.I)
PROD = re.compile(r"(?<![A-Za-z0-9_])prod(?:uction)?(?![A-Za-z0-9])", re.I)  # a marker, not part of a name
DEFAULT_BRANCHES = {"main", "master"}
TEXT = {
    "unreadable": "a command the hook cannot read (encoded, or nested too deep)",
    "wipe": "DROP or TRUNCATE through a database client",
    "destroy": "a database-destroying command",
    "migrate": "migration aimed at production",
    "push": "force-push, mirror push or default-branch delete (allowed: --force-with-lease <remote> <branch> to a "
            "branch other than main or master)",
    "delete": "recursive delete",
}
ALWAYS = ("unreadable", "wipe", "destroy")  # no proof can allow these


def fired(text, sql):
    """Rules whose tokens appear anywhere in text, structure-blind. sql() yields referenced SQL file texts; it is
    called only when a database client appears without DROP or TRUNCATE in the text itself."""
    found = set()
    if UNREADABLE in text:
        found.add("unreadable")
    if DELETE.search(text) and RECURSIVE_HINT.search(text):
        found.add("delete")
    if PUSH_WORD.search(text) and GIT.search(text) and FORCE.search(text):
        found.add("push")
    if CLIENT.search(text) and (WIPE.search(text) or any(WIPE.search(body) for body in sql())):
        found.add("wipe")
    if DESTROY.search(text):
        found.add("destroy")
    if MIGRATE.search(text) and PROD.search(text):
        found.add("migrate")
    return found


def recursive(flag):
    """True for a recursive delete flag: -r, -rfvi, --recursive, -Recurse (a prefix, or :$true), /s, /s/q."""
    base, _, value = flag.partition(":")
    lower = base.lower()
    return value.lower() != "$false" and (
        lower == "--recursive" or (lower.startswith("/") and "s" in lower.split("/"))
        or (len(lower) > 1 and "-recurse".startswith(lower)) or bool(re.fullmatch(r"-[fiIdv]*[rR][fiIrRdv]*", base)))


def deletes(words):
    """(target, strict) pairs a recursive delete removes ([] when it names none), or None when the command is no
    recursive delete. strict: the target itself goes; a find with a filter removes only matches below its start."""
    name = program(words[0])
    if name == "git" and "rm" in words:
        words, name = words[words.index("rm"):], "rm"
    if name == "find":
        execs = [words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-exec", "-execdir", "-ok", "-okdir")]
        if "-delete" not in words and not any(program(w) in DELETERS | {"rimraf"} for w in execs):
            return None
        args = [w for w in words[1:] if w not in ("-H", "-L", "-P")]
        starts = list(takewhile(lambda w: not w.startswith(("-", "(", "!")), args))
        return [(start, not FILTERS & set(words)) for start in starts or ["."]]
    if name == "rimraf":
        return [(w, True) for w in words[1:] if not w.startswith("-")]
    if name not in DELETERS:
        return None
    flags = [w for w in words[1:] if w.startswith("-") or (name in DOS and re.fullmatch(r"(?:/\w)+", w))]
    if not any(recursive(flag) for flag in flags):
        return None
    joined = [f.split(":", 1)[1] for f in flags if re.match(r"(?i)-(?:path|literalpath|lp):.", f)]
    return [(w, True) for w in words[1:] if w not in flags] + [(w, True) for w in joined]


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
    removing = bool({"--delete", "-d"} & set(flags))
    if "--mirror" in flags or any(re.fullmatch(r"--force|-[a-zA-Z]*f[a-zA-Z]*", f) for f in flags):
        return True
    if any(ref.startswith("+") or (head in DEFAULT_BRANCHES and (removing or ref.startswith(":")))
           for ref, head in zip(refs, heads)):
        return True
    lease = any(f.startswith("--force-with-lease") for f in flags)
    return lease and (not refs or any(head in DEFAULT_BRANCHES | {"HEAD"} for head in heads))


def pusher(words):
    """True when force_push() can read this command (git ... push)."""
    return program(words[0]) == "git" and "push" in words
