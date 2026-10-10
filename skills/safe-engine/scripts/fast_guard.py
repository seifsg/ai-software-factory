"""Destructive-command guard for fast_gate.py hooks: which owner-only rule a shell command breaks in one run.

Rules fire on the whole judged text of a command, whatever its shell structure (fast_rules.py). This module may
only allow a fired rule, by proving it harmless command by command from the parse (fast_shell.py): anything it
cannot follow stays denied. The gate passes in its own path helpers.
"""
import os
import re

import fast_rules as rules
import fast_shell as shell

BUDGET = 200  # delete targets proven per command; each costs a path lookup, and no agent names more


class Judge:
    """Judges commands for the run rooted at root. norm(path, base) and inside(child, parent) come from the gate."""

    def __init__(self, root, norm, inside):
        self.root, self.norm, self.inside, self.seen, self.budget = root, norm, inside, {}, BUDGET
        self.protected = {norm(os.path.join(root, *part)) for part in ((".factory",), (".factory", "fast"), (".git",))}

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

    def stray(self, target, here, strict):
        """Why a recursive delete of target is refused, or None. strict: the target itself goes, so the project root,
        root/* and the protected folders (.factory, .factory/fast, .git) count too."""
        head, tail = os.path.split(target)
        path = (head or ".") if strict and tail in ("*", ".*") else target
        try:
            full = self.resolve(path, here)
        except (OSError, ValueError):
            full = None
        if full is None:
            after = " after a directory change" if here is None else ""
            return f"recursive delete of a path that cannot be resolved{after} ({target})"
        if strict and full in self.protected:
            return f"recursive delete of a protected folder ({target})"
        if strict and full == self.root:
            return f"recursive delete of the whole project ({target})"
        if not self.inside(full, self.root):
            return f"recursive delete outside the project ({target})"
        return None

    def moved(self, target, here):
        """Directory after a cd to target ('' is unknown); None once unknown."""
        try:
            return self.resolve(target, here) if target else None
        except (OSError, ValueError):
            return None

    def sql(self, commands, cwd):
        """Texts of the .sql files and `<` inputs the commands name: regular files only, first 1 MB each."""
        names = {name for cmd in commands for name in rules.SQL_FILE.findall(cmd.text)}
        names |= {target for cmd in commands for op, target in cmd.inputs if op == "<"}
        for name in names:
            name = re.sub(r"^-\w", "", name) if name.startswith("-") else name  # -fdrop.sql
            try:
                path = self.resolve(name, cwd)
                if path and os.path.isfile(path):
                    with open(path, encoding="utf-8", errors="replace") as source:
                        yield source.read(1_000_000)
            except (OSError, ValueError):
                continue

    def proves(self, cmd, here, fired):
        """Why cmd is not proven harmless for the fired rules, or None."""
        literal = all(shell.literal(w) for w in cmd.words)
        if "delete" in fired and rules.DELETE.search(cmd.text):
            targets = rules.deletes(cmd.words) if literal and rules.deleter(cmd.words) else []
            if targets == []:  # an unreadable form, or a recursive delete naming no literal target
                return f"recursive delete the hook cannot prove stays inside the project ({cmd.words[0]})"
            for path, strict in targets or []:
                self.budget -= 1
                reason = self.stray(path, here, strict) if self.budget >= 0 else (
                    f"recursive delete of more than {BUDGET} targets in one command")
                if reason:
                    return reason
        if "push" in fired and rules.PUSH_WORD.search(cmd.text) and rules.GIT.search(cmd.text):
            if not (literal and rules.pusher(cmd.words) and not rules.force_push(cmd.words)):
                return rules.TEXT["push"]
        if "migrate" in fired and rules.MIGRATE.search(cmd.text) and rules.PROD.search(cmd.text):
            return rules.TEXT["migrate"]
        return None

    def rule(self, command, cwd):
        """The owner-only rule command breaks when run from cwd, or None. ( ) scopes restore the directory."""
        items = list(shell.pipelines(command))
        commands = [item for item in items if not isinstance(item, str)]
        fired = rules.fired("\n".join(cmd.text for cmd in commands), lambda: self.sql(commands, cwd))
        if not fired:
            return None
        always = [rules.TEXT[name] for name in rules.ALWAYS if name in fired]
        if always:
            return always[0]
        if any(cmd.words[0] == shell.UNCLEAR for cmd in commands):
            names = ", ".join(rules.TEXT[name] for name in sorted(fired))
            return f"{names}, in a command the hook cannot follow (command substitution or a mid-command group)"
        here, saved = cwd, []
        for item in items:
            if item == "(":
                saved.append(here)
                continue
            if item == ")":
                here = saved.pop() if saved else here
                continue
            target = shell.cd_target(item.words)
            here = here if target is None else self.moved(target, here)
            reason = None if item.outer else self.proves(item, here, fired)
            if reason:
                return reason
        return None
