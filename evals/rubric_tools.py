"""Helpers for sample rubrics: candidate code runs only in child process trees of its own, output through files."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from evals.proc import Tree

HARNESS = None  # harness source; the check program sets it, else harness.py beside this file is read
PROGRAM_FLAGS = ("-E", "-s", "-S")  # candidate programs: no environment hooks, no site; their own folder stays


def text(handle):
    """Everything written to a temp file, decoded."""
    handle.seek(0)
    return handle.read().decode("utf-8", "replace")


def scratch():
    """A fresh folder in the run's temp. The run folder's removal cleans it, after its leftover processes are
    stopped, so a candidate process still holding it cannot fail the check."""
    return Path(tempfile.mkdtemp())


def run_python(work, *args, timeout=30, flags=PROGRAM_FLAGS):
    """Run `python -B *flags *args` in `work` as its own tree, stopped when it ends: (exit code, stdout, stderr)."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        tree = Tree([sys.executable, "-B", *flags, *args], work, None, False, subprocess.DEVNULL, out, err)
        try:
            code = tree.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = None
        finally:
            tree.stop()  # candidate leftovers die with the program
        return code, text(out), text(err)


def op(name, *args, **kwargs):
    """An operation calling module attribute `name` with plain-data arguments."""
    return ["call", name, list(args), kwargs]


def request(method, path, body=None, query=""):
    """An operation sending one request to the module's WSGI `app`; a str body is sent as is, else as JSON."""
    raw = body if isinstance(body, str) else "" if body is None else json.dumps(body)
    return ["wsgi", "app", method, path, raw, query]


def tests(source):
    """An operation running a unittest module's source against the candidate: {run, failures, errors}."""
    return ["tests", "", source]


def call(work, module, ops, timeout=30):
    """Run `ops` against the candidate's `module` in a separate harness tree; one [status, value] per op."""
    source = HARNESS or Path(__file__).with_name("harness.py").read_text(encoding="utf-8")
    ask = scratch() / "request.json"
    ask.write_text(json.dumps({"module": module, "ops": ops}), encoding="utf-8")
    code, out, err = run_python(work, "-c", source, str(ask), timeout=timeout, flags=("-I", "-S"))
    answers = [line[len("RESULT "):] for line in out.splitlines() if line.startswith("RESULT ")]
    assert answers, f"candidate code ended without a result (exit {code}): {err.strip()[-200:]}"
    results = json.loads(answers[-1])
    assert isinstance(results, list) and len(results) == len(ops), "malformed harness result"
    return results


def same(actual, expected):
    """Equal with exactly the same types, all the way down (an always-equal object or True for 1 fails)."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is list:
        return len(actual) == len(expected) and all(map(same, actual, expected))
    if type(expected) is dict:
        return actual.keys() == expected.keys() and all(same(actual[key], expected[key]) for key in expected)
    return actual == expected


def expect(result, expected, what):
    """Assert one harness result succeeded with exactly `expected`."""
    assert result[0] == "ok" and same(result[1], expected), f"{what}: got {result}"
