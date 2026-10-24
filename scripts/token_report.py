"""Print the method text each Fast run kind loads (bytes, estimated tokens), or the gate's output per message.

Why: input is the bill. One command measures it, so a trim is kept only when the count drops.
`--rev` measures any commit, `--against <rev>` compares it with the working tree, `--gate` measures gate output.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import gate_output

ROOT = Path(__file__).resolve().parents[1]
S = ".agents/skills/"
REF = S + "safe-engine/references/"
# Files a run reads by following its methods; conditional detail stays out.
BASE = (
    "skills/safe-engine/SKILL.md", S + "safe-engine/SKILL.md", REF + "fast-run.md",
    REF + "product-bar.md", REF + "sizes.md", REF + "work-record-sample.md",
    S + "ticketing/SKILL.md", S + "ticketing/references/ticket-layout.md",
    S + "ticketing/references/github.md", S + "get-ready-to-code/SKILL.md",
    S + "how-to-make-a-pr/SKILL.md", S + "how-to-make-a-pr/references/pr-layout.md",
    S + "how-to-make-a-pr/references/github.md", S + "how-to-make-a-pr/references/credit.md",
    REF + "delegate.md",  # routes, briefs and accepts every delegated job; every todo names its tier from it
)
NEW = (S + "research-market/SKILL.md", S + "analyze-start/SKILL.md")
KINDS = {
    "product, feature": BASE + NEW,
    "change": BASE,
    "+ui": (S + "ux-quality/",),
    "+data": (S + "database-schema/",),
    "+safe-check": (S + "deep-review/",),
    "+on demand": (  # detail behind pointers that name its situation: read only when it occurs
        REF + "work-record-sample.md", REF + "gate-details.md", REF + "cases.md", REF + "run-cases.md", S + "ticketing/references/safe-contract.md",
        S + "ticketing/references/unmerged-pr.md", S + "ticketing/references/epic-cases.md",
        S + "how-to-make-a-pr/references/pr-cases.md", S + "research-market/references/deep-research.md"),
    "all methods": (S, "skills/"),  # moved text still counts here: a move is not a cut
}
TOTAL_ONLY = {"all methods"}
# A kind skips a file only where its method says so at the measured revision (phrases, as the gate reads them).
SAMPLE = {REF + "work-record-sample.md": (REF + "fast-run.md", "A `done` refusal its message does not explain: the [sample]")}
SKIPS = {"product, feature": SAMPLE, "change": SAMPLE}


def git(*args, stdin=None):
    """Run git in the factory root; raise loudly on failure."""
    return subprocess.run(("git", "-C", str(ROOT)) + args, input=stdin, capture_output=True, check=True,
                          text=True, encoding="utf-8").stdout


def expand(paths, rev):
    """Folders ('/' suffix) become their .md files, sorted."""
    out = []
    for p in paths:
        if not p.endswith("/"):
            out.append(p)
        elif rev:
            out += sorted(f for f in git("ls-tree", "-r", "--name-only", rev, p).splitlines() if f.endswith(".md"))
        else:
            out += sorted(f.relative_to(ROOT).as_posix() for f in (ROOT / p).rglob("*.md"))
    return out


def sizes(paths, rev):
    """Bytes per path with LF line ends (git blob size); None when missing."""
    if not rev:
        return {p: len((ROOT / p).read_bytes().replace(b"\r\n", b"\n")) if (ROOT / p).is_file() else None for p in paths}
    found = git("cat-file", "--batch-check", stdin="".join(f"{rev}:{p}\n" for p in paths)).splitlines()
    cells = [line.split() for line in found]
    return {p: int(c[2]) if c[1:2] == ["blob"] else None for p, c in zip(paths, cells)}


def tok(n):
    """Estimated tokens: about 4 bytes each for English prose."""
    return (n + 3) // 4


def text(path, rev):
    """A method file's text at rev, or in the working tree."""
    return git("show", f"{rev}:{path}") if rev else (ROOT / path).read_text(encoding="utf-8")


def report(rev=None):
    """Rows per kind: (kind, [(path, bytes, None when missing, or 'skipped')], total bytes)."""
    rows = []
    for kind, paths in KINDS.items():
        skipped = {path for path, (method, phrase) in SKIPS.get(kind, {}).items() if phrase in text(method, rev)}
        got = sizes([path for path in expand(paths, rev) if path not in skipped], rev)
        rows.append((kind, list(got.items()) + [(path, "skipped") for path in sorted(skipped)],
                     sum(v or 0 for v in got.values())))
    return rows


def totals(rev, gate):
    """{row: bytes}: gate output per message (gate) or method load per kind, at rev or the working tree."""
    if gate:
        found = gate_output.measure(ROOT, rev)
        return {**found, "total": sum(found.values())}
    return {kind: total for kind, _, total in report(rev)}


def change(old, new):
    """'-23.4%' from old to new bytes; 'new' when old is missing."""
    return f"{(new - old) / old:+.1%}" if old else "new"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rev", help="measure this commit instead of the working tree")
    ap.add_argument("--against", metavar="REV", help="totals at REV beside --rev (or the working tree), with the change")
    ap.add_argument("--gate", action="store_true", help="gate output bytes per message on one fixture change run")
    ap.add_argument("--totals", action="store_true", help="one line per kind")
    a = ap.parse_args(argv)
    for rev in filter(None, (a.rev, a.against)):
        try:
            git("rev-parse", "--verify", rev + "^{commit}")
        except subprocess.CalledProcessError:
            ap.error(f"not a commit: {rev}")
    what, at = "Gate output" if a.gate else "Method load", a.rev or "working tree"
    if a.against:
        old, new = totals(a.against, a.gate), totals(a.rev, a.gate)
        print(f"{what} bytes: {a.against} -> {at}")
        for row, n in new.items():
            print(f"{row:16} {old.get(row, 0):>8,} -> {n:>8,}  {change(old.get(row), n)}")
    elif a.gate:
        print(f"{what} at {at} (bytes per message, one fixture change run)")
        for row, n in totals(a.rev, True).items():
            print(f"{row:16} {n:>8,}")
    else:
        print(f"{what} at {at} (bytes, ~tokens = bytes/4)")
        for kind, files, total in report(a.rev):
            print(f"{kind:16} {total:>8,} B ~{tok(total):>6,} tok")
            for p, n in [] if a.totals or kind in TOTAL_ONLY else files:
                print(f"  {'missing' if n is None else n if isinstance(n, str) else format(n, ','):>8}  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
