"""Rubric for the cli-tool sample: one check per requested item. Each raises on failure."""
from pathlib import Path
import subprocess
import sys
import tempfile

TEXT = "the cat\nThe dog the end\n"  # 2 lines, 6 words, 24 characters; "the" x3


def wordcount(work, *args):
    """Run the candidate tool on a fresh copy of TEXT; returns the finished process."""
    with tempfile.TemporaryDirectory() as tmp:
        sample = Path(tmp) / "sample.txt"
        sample.write_bytes(TEXT.encode("utf-8"))
        argv = [str(sample) if arg == "SAMPLE" else arg for arg in args]
        return subprocess.run([sys.executable, "wordcount.py", *argv], cwd=work, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=20)


def counts(work):
    """R1: prints `lines words chars`."""
    done = wordcount(work, "SAMPLE")
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr.strip()[-200:]}"
    assert done.stdout.splitlines()[:1] == ["2 6 24"], f"first line {done.stdout.splitlines()[:1]}"


def top(work):
    """R2: --top N lists the N most frequent words, ties alphabetical, lowercase."""
    done = wordcount(work, "--top", "2", "SAMPLE")
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr.strip()[-200:]}"
    assert done.stdout.splitlines()[1:] == ["the 3", "cat 1"], f"top lines {done.stdout.splitlines()[1:]}"


def missing(work):
    """R3: a missing file names it on stderr, no traceback, exit 2."""
    done = wordcount(work, "no-such-file.txt")
    assert done.returncode == 2, f"exit {done.returncode}"
    assert "no-such-file.txt" in done.stderr and "Traceback" not in done.stderr, done.stderr.strip()[-200:]


CHECKS = {"R1": counts, "R2": top, "R3": missing}
