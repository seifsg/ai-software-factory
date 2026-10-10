"""Destructive-command guard for fast_gate.py hooks: which owner-only rule a shell command breaks in one run.

fast_shell.py parses commands and names the rules; this module follows the directory each command runs in
and judges delete targets against the run's project. The gate passes in its own path helpers.
"""
import os
import re

import fast_shell as shell


class Judge:
    """Judges commands for the run rooted at root. norm(path, base) and inside(child, parent) come from the gate."""

    def __init__(self, root, norm, inside):
        self.root, self.norm, self.inside = root, norm, inside
        self.factory = norm(os.path.join(root, ".factory"))

    def resolve(self, target, here):
        """Comparable path of target seen from here; None when a variable or here is unknown."""
        path = re.sub(r"(?i)\$env:", "$", target)
        path = re.sub(r"\$GIT_TOPLEVEL\b", lambda _: self.root, path)
        path = re.sub(r"\$PWD\b", lambda _: here or "$?", path)  # $PWD is where this command runs
        path = os.path.expandvars(os.path.expanduser(path))
        if "$" in path or (here is None and not os.path.isabs(path)):
            return None
        return self.norm(path, here)

    def stray(self, target, here, strict):
        """Why a recursive delete of target is refused, or None. strict: the target itself goes, so the project root,
        root/* and the run's .factory folder count too."""
        head, tail = os.path.split(target)
        path = (head or ".") if strict and tail in ("*", ".*") else target
        try:
            full = self.resolve(path, here)
        except (OSError, ValueError):
            return None  # unparsable path: fail open
        if full is None:
            after = " after a directory change" if here is None else ""
            return f"recursive delete of a path that cannot be resolved{after} ({target})"
        if strict and full == self.factory:
            return f"recursive delete of the run's .factory folder ({target})"
        if (strict and full == self.root) or not self.inside(full, self.root):
            return f"recursive delete outside the project ({target})"
        return None

    def moved(self, target, here):
        """Directory after a cd to target ('' is unknown); None once unknown."""
        try:
            return self.resolve(target, here) if target else None
        except (OSError, ValueError):
            return None

    def peek(self, name, here):
        """Text of a `< file` or `-f file` input (first 1 MB); empty when unknown or unreadable."""
        try:
            with open(self.resolve(name, here), encoding="utf-8", errors="replace") as source:
                return source.read(1_000_000)
        except (OSError, TypeError, ValueError):
            return ""

    def pipeline(self, commands, here):
        """(rule or None, directory after) for one pipeline run from here."""
        rule = shell.danger(commands, lambda name: self.peek(name, here))
        for cmd in commands:
            target = shell.cd_target(cmd.words)
            here = here if target is None else self.moved(target, here)
            for path, strict in shell.deletes(cmd.words):
                rule = rule or self.stray(path, here, strict)
        return rule, here

    def rule(self, command, cwd):
        """The owner-only rule command breaks when run from cwd, or None. A ( ) scope restores the directory."""
        here, saved = cwd, []
        for item in shell.pipelines(command):
            if item == "(":
                saved.append(here)
            elif item == ")":
                here = saved.pop() if saved else here
            else:
                found, here = self.pipeline(item, here)
                if found:
                    return found
        return None
