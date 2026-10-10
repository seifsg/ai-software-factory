"""Rubric for the cli-tool sample: one check per requested item. Each raises on failure.

The candidate program runs as its own process on a fixed text and on a fresh random text; the reference program
(REFERENCE, run in this process) gives the expected output for the random text.
"""
from evals.rubric_tools import RANDOM, run_program, run_python, scratch

TEXT = "the cat\nThe dog the end\n"  # 2 lines, 6 words, 24 characters; "the" x3
WORDS = ("the", "cat", "dog", "end", "sun", "moon", "a", "tree", "sky")
SPACES = (" ", "  ", "\t")


def random_text():
    """A few lines of random words in random case, separated by random whitespace."""
    lines = []
    for _ in range(RANDOM.randint(1, 6)):
        words = [RANDOM.choice((str.lower, str.upper, str.title))(RANDOM.choice(WORDS))
                 for _ in range(RANDOM.randint(0, 7))]
        lines.append("".join(word + RANDOM.choice(SPACES) for word in words).rstrip())
    return "\n".join(lines) + RANDOM.choice(("", "\n"))


def wordcount(work, text, *args):
    """Run the candidate tool on a file holding `text`: (exit code, stdout, stderr, the file's path)."""
    sample = scratch() / "sample.txt"
    sample.write_bytes(text.encode("utf-8"))
    argv = [str(sample) if arg == "SAMPLE" else arg for arg in args]
    return (*run_python(work, "wordcount.py", *argv), argv)


def matches(work, *args):
    """Assert the candidate's output on a random text equals the reference's; returns nothing."""
    code, out, err, argv = wordcount(work, random_text(), *args)
    want = run_program(REFERENCE["wordcount.py"], argv)  # noqa: F821 - provided by the check program
    expected, got = (want[0], want[1].splitlines()), (code, out.splitlines())  # line endings vary by platform
    assert got == expected, f"random text: expected {expected}, got {got} {err[-200:]}"


def counts(work):
    """R1: prints `lines words chars`."""
    code, out, err, _ = wordcount(work, TEXT, "SAMPLE")
    assert code == 0, f"exit {code}: {err.strip()[-200:]}"
    assert out.splitlines()[:1] == ["2 6 24"], f"first line {out.splitlines()[:1]}"
    matches(work, "SAMPLE")


def top(work):
    """R2: --top N lists the N most frequent words, ties alphabetical, lowercase."""
    code, out, err, _ = wordcount(work, TEXT, "--top", "2", "SAMPLE")
    assert code == 0, f"exit {code}: {err.strip()[-200:]}"
    assert out.splitlines()[1:] == ["the 3", "cat 1"], f"top lines {out.splitlines()[1:]}"
    matches(work, "--top", str(RANDOM.randint(1, 6)), "SAMPLE")


def missing(work):
    """R3: a missing file names it on stderr, no traceback, exit 2."""
    name = f"no-such-{RANDOM.getrandbits(32):08x}.txt"
    code, _, err = run_python(work, "wordcount.py", name)
    assert code == 2, f"exit {code}"
    assert name in err and "Traceback" not in err, err.strip()[-200:]


CHECKS = {"R1": counts, "R2": top, "R3": missing}
