"""Destructive-command guard for fast_gate.py hooks: which owner-only rule a shell command breaks in one run.

Rules fire on the whole judged text of a command, whatever its shell structure (fast_rules.py). This module may
only allow a fired rule, by proving it harmless command by command from the parse (fast_shell.py): anything it
cannot follow stays denied. The gate passes in its own path helpers.
"""
import fnmatch
import functools
import os
import re

import fast_rules as rules
import fast_shell as shell

BUDGET = 100  # delete targets proven per command; each costs a path lookup, and no agent names more
MOVES = 50  # directory changes followed per command; past it the directory counts as unknown
TREE = ("tree", "sweep")  # modes that remove the target and everything below it
SWEEP = ("a find under the whole project: name only files that cannot be .git, .factory, fast or run.json, or add "
         "-not -path './.git/*' -not -path './.factory/*'")


class Judge:
    """Judges commands for the run rooted at root. norm(path, base) and inside(child, parent) come from the gate;
    scratch() gives the run's own throwaway folder (fast_setup.scratch_path), where link-safe deletes pass."""

    def __init__(self, root, norm, inside, home=None, scratch=None):
        self.root, self.norm, self.inside, self.seen, self.budget = root, norm, inside, {}, BUDGET
        self.home, self.hint, self.scratch, self.alone = home, None, scratch, False
        if home:  # commands naming the gate home: its run files are guarded like .git
            names = {".safe-engine", "safe_engine_home", home, home.replace("\\", "/")}
            self.hint = re.compile("|".join(map(re.escape, names)), re.I)
        self.protected = {norm(os.path.join(root, *part)) for part in ((".factory",), (".factory", "fast"), (".git",),
                                                                       (".factory", "fast", "run.json"))}
        self.git = norm(os.path.join(root, ".git"))  # history: nothing inside it may go
        self.lock = norm(os.path.join(root, ".git", "index.lock"))  # a stale lock: removing it is routine

    def resolve(self, target, here):
        """Comparable path of target seen from here; None when a variable or here is unknown. Memoized per event."""
        key = (target, here)
        if key not in self.seen:
            self.seen[key] = self.locate(target, here)
        return self.seen[key]

    def locate(self, target, here):
        """resolve() without the memo."""
        path = re.sub(r"(?i)\$env:", "$", target)
        path = re.sub(r"\$GIT_TOPLEVEL\b", lambda _: self.root, path)
        path = re.sub(r"\$PWD\b", lambda _: here or "$?", path)  # $PWD is where this command runs
        path = os.path.expandvars(os.path.expanduser(path))
        if "$" in path or "`" in path or (here is None and not os.path.isabs(path)):
            return None
        return self.norm(path, here)

    def stray(self, target, here, mode, linksafe=False):
        """Why deleting target is refused, or None. mode "tree": the target and all below go, so the project root,
        root/* and the protected paths (.factory, .factory/fast, its run.json, .git) count; "below"/"below-git":
        only find matches below an inside start go, and from the root only when .git is excluded; "file": only the
        protected paths count. Nothing inside .git may go. linksafe: the delete is the command's only part and its
        deleter cannot follow a link, so with a plain target it may work inside the run's scratch folder."""
        head, tail = os.path.split(target)
        path = (head or ".") if mode in TREE and tail in ("*", ".*") else target
        try:
            full = self.resolve(path, here)
        except (OSError, ValueError):
            full = None
        if full is None:
            after = " after a directory change" if here is None else ""
            return None if mode == "file" else f"delete of a path that cannot be resolved{after} ({target})"
        if self.reaches(full, mode):
            return f"delete of a protected path ({target})"
        if mode == "file":
            return None
        if mode in TREE and full == self.root:
            return f"{SWEEP if mode == 'sweep' else 'recursive delete of the whole project'} ({target})"
        if self.inside(full, self.root):
            return None
        if self.own and self.inside(full, self.own):  # the run's scratch folder: its agents clean up there
            return None if linksafe else (
                f"recursive delete outside the project ({target}); in the run's scratch folder use rm -r (Bash, "
                "the path with / separators and no backslash or quote) or rd /s (no quote or space), with a plain "
                "literal path (no trailing slash, no wildcard mid-path), alone in its command")
        return f"recursive delete outside the project ({target})"

    def reaches(self, full, mode):
        """True when full, a path or a wildcard pattern, names a protected path, or (except for a plain file delete)
        anything inside .git or a protected folder a pattern's leading parts match. .git/index.lock may go."""
        if full == self.lock:
            return False
        if self.homeward(full):
            return True
        if not rules.WILDCARD.search(full):
            return (mode != "below" and full in self.protected) or (mode != "file" and self.inside(full, self.git))
        parts = full.split(os.sep)
        return fnmatch.fnmatch(self.root, full) or any(
            fnmatch.fnmatch(guarded, full if mode == "file" else os.sep.join(parts[:guarded.count(os.sep) + 1]))
            for guarded in self.protected)

    @functools.cached_property
    def own(self):
        """The run's scratch folder, resolved on first use (most commands delete nothing outside the project), and
        trusted only as a real folder: a link or junction put in its place would stretch the allowance to its target."""
        path = self.scratch() if self.scratch else None
        if path is None:
            return None
        full = self.norm(str(path))
        return full if full == os.path.join(self.norm(str(path.parent)), os.path.normcase(path.name)) else None

    @functools.cached_property
    def vault(self):
        """The gate home's run folders (registrations, run states), resolved on first use: most commands never ask."""
        return tuple(self.norm(os.path.join(self.home, part)) for part in ("active", "runs")) if self.home else ()

    def homeward(self, full):
        """True when full, a path or a wildcard pattern, is or reaches into the gate home's run folders."""
        if not rules.WILDCARD.search(full):
            return any(self.inside(full, folder) for folder in self.vault)
        parts = full.split(os.sep)
        return any(fnmatch.fnmatch(folder, os.sep.join(parts[:folder.count(os.sep) + 1])) for folder in self.vault)

    def moved(self, target, here):
        """Directory after a cd to target ('' is unknown); None once unknown."""
        try:
            return self.resolve(target, here) if target else None
        except (OSError, ValueError):
            return None

    def sql(self, commands, cwd):
        """Texts of the .sql files and `<` inputs the commands name: regular files only, first 1 MB each."""
        names = {name for cmd in commands for name in rules.sql_files(cmd.text)}
        names |= {target for cmd in commands for op, target in cmd.inputs if op == "<"}
        for name in names:
            try:
                path = self.resolve(name, cwd)
                if path and os.path.isfile(path):
                    with open(path, encoding="utf-8", errors="replace") as source:
                        yield source.read(1_000_000)
            except (OSError, ValueError):
                continue

    def proves(self, cmd, here, fired, dialect=None):
        """Why cmd is not proven harmless for the fired rules, or None."""
        literal = all(shell.literal(w) for w in cmd.words)
        if "delete" in fired and rules.DELETE.search(cmd.text):
            targets = rules.deletes(cmd.words) if literal and rules.deleter(cmd.words) else []
            if targets == []:  # an unreadable form, or a delete naming no literal target
                return f"recursive delete the hook cannot prove stays inside the project ({cmd.words[0]})"
            for path, mode in targets or []:
                self.budget -= 1
                safe = self.alone and rules.linksafe(cmd.words, dialect) and rules.plain(path, dialect)
                reason = self.stray(path, here, mode, safe) if self.budget >= 0 else (
                    f"recursive delete of more than {BUDGET} targets in one command")
                if reason:
                    return reason
        if "push" in fired and rules.PUSH_WORD.search(cmd.text) and rules.GIT.search(cmd.text):
            if not (literal and rules.pusher(cmd.words) and not rules.force_push(cmd.words)):
                return rules.TEXT["push"]
        if "migrate" in fired and rules.migrates(cmd.text) and rules.PROD.search(cmd.text):
            return rules.TEXT["migrate"]
        if "ignored" in fired and rules.GIT.search(cmd.text) and (
                rules.CLEAN.search(cmd.text) or rules.STASH.search(cmd.text)):
            if not literal or rules.loses_ignored(cmd.words):
                return rules.TEXT["ignored"]
        if "move" in fired and rules.MOVE.search(cmd.text) and not rules.INTERPRETER.fullmatch(
                shell.program(cmd.words[0])):
            return self.carries(cmd, here, literal)
        return None

    def carries(self, cmd, here, literal):
        """Why a move or rename is refused: an unreadable form, or a path that is or reaches a protected one."""
        paths = rules.moves(cmd.words) if literal else None
        for path in paths or [None]:
            try:
                full = path and self.resolve(path, here)
            except (OSError, ValueError):
                full = None
            if full is None or full == self.root or self.reaches(full, "tree"):
                return f"{rules.TEXT['move']} ({path or cmd.words[0]})"
        return None

    def rule(self, command, cwd, dialect=None):
        """The owner-only rule command breaks when run from cwd, or None. dialect "bash" or "windows" (PowerShell,
        cmd) says how the shell reads backslashes and quotes; unknown, both readings must prove the command."""
        for reading in [dialect] if dialect else ["bash", "windows"]:
            self.budget = BUDGET
            reason = self.reading(command, cwd, reading)
            if reason:
                return reason
        return None

    def reading(self, command, cwd, dialect):
        """rule() for one dialect. ( ) scopes restore the directory."""
        items = list(shell.pipelines(command, dialect))
        commands = [item for item in items if not isinstance(item, str)]
        text = "\n".join(cmd.text for cmd in commands)
        fired = rules.fired(text, lambda: self.sql(commands, cwd))
        self.alone = sum(not cmd.outer for cmd in commands) == 1  # no other part can make a link it runs through
        if self.hint and self.hint.search(text):  # deletes and moves naming the gate home must prove they miss it
            fired |= {"delete", "move"}
        if not fired:
            return None
        always = [rules.TEXT[name] for name in rules.ALWAYS if name in fired]
        if always:
            return always[0]
        if any(shell.UNCLEAR in cmd.text for cmd in commands):
            names = ", ".join(rules.TEXT[name] for name in sorted(fired))
            return (f"{names}, in a command the hook cannot follow (command substitution, a mid-command group or "
                    "a brace)")
        here, saved, changes = cwd, [], 0
        for item in items:
            if item == "(":
                saved.append(here)
                continue
            if item == ")":
                here = saved.pop() if saved else here
                continue
            target = shell.cd_target(item.words)
            changes += target is not None
            here = here if target is None else self.moved(target, here) if changes <= MOVES else None
            reason = None if item.outer else self.proves(item, here, fired, dialect)
            if reason:
                return reason
        return None
