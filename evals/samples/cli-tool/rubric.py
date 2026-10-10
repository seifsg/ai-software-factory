"""Rubric for the cli-tool sample: one check per requested item. Each raises on failure."""
from evals.rubric_tools import run_python, scratch

TEXT = "the cat\nThe dog the end\n"  # 2 lines, 6 words, 24 characters; "the" x3


def wordcount(work, *args):
    """Run the candidate tool on a fresh copy of TEXT; returns (exit code, stdout, stderr)."""
    sample = scratch() / "sample.txt"
    sample.write_bytes(TEXT.encode("utf-8"))
    return run_python(work, "wordcount.py", *(str(sample) if arg == "SAMPLE" else arg for arg in args))


def counts(work):
    """R1: prints `lines words chars`."""
    code, out, err = wordcount(work, "SAMPLE")
    assert code == 0, f"exit {code}: {err.strip()[-200:]}"
    assert out.splitlines()[:1] == ["2 6 24"], f"first line {out.splitlines()[:1]}"


def top(work):
    """R2: --top N lists the N most frequent words, ties alphabetical, lowercase."""
    code, out, err = wordcount(work, "--top", "2", "SAMPLE")
    assert code == 0, f"exit {code}: {err.strip()[-200:]}"
    assert out.splitlines()[1:] == ["the 3", "cat 1"], f"top lines {out.splitlines()[1:]}"


def missing(work):
    """R3: a missing file names it on stderr, no traceback, exit 2."""
    code, _, err = wordcount(work, "no-such-file.txt")
    assert code == 2, f"exit {code}"
    assert "no-such-file.txt" in err and "Traceback" not in err, err.strip()[-200:]


CHECKS = {"R1": counts, "R2": top, "R3": missing}
