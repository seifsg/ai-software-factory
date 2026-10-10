"""Helpers for sample rubrics. Candidate code runs only in child process trees of its own; expected answers come
from the private reference solution, run in this process from memory; inputs are fresh and random per scoring."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import threading
import types

from evals.proc import Tree

HARNESS = None  # harness source; the check program sets it, else harness.py beside this file is read
RECORD = None  # folder where harness children list their loaded modules (interpreter guard probe only)
RANDOM = random.SystemRandom()  # operating system randomness: inputs no candidate can predict
PROGRAM_FLAGS = ("-E", "-s", "-S")  # candidate programs: no environment or site hooks, the host's own text
# defaults (so a missing encoding shows as it would for the owner), and their own folder on the path


def harness_source():
    """The harness program: as sent to the check child, else from beside this file."""
    return HARNESS or Path(__file__).with_name("harness.py").read_text(encoding="utf-8")


def text(handle):
    """Everything written to a temp file, decoded."""
    handle.seek(0)
    return handle.read().decode("utf-8", "replace")


def scratch():
    """A fresh folder in the run's temp, removed with the run folder after its leftover processes stop."""
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


def inheritable(write_fd):
    """(argument naming the pipe for the child, Popen options passing only that pipe)."""
    if os.name == "nt":
        import msvcrt
        handle = msvcrt.get_osfhandle(write_fd)
        os.set_handle_inheritable(handle, True)
        return str(handle), {"startupinfo": subprocess.STARTUPINFO(lpAttributeList={"handle_list": [handle]})}
    os.set_inheritable(write_fd, True)
    return str(write_fd), {"pass_fds": (write_fd,)}


def drain(read_fd, into):
    """Read a pipe to its end, then close it."""
    with os.fdopen(read_fd, "rb") as pipe:
        into.append(pipe.read())


def call(work, module, ops, timeout=30):
    """Run `ops` against the candidate's `module` in a harness tree; one [status, value] per op.

    The results come only from the harness's dedicated pipe and must be exactly one record from a clean exit.
    """
    ask = scratch() / "request.json"
    ask.write_text(json.dumps({"module": module, "ops": ops, "record": RECORD}), encoding="utf-8")
    read_fd, write_fd = os.pipe()
    received = []
    with tempfile.TemporaryFile() as log:
        try:
            handle, extra = inheritable(write_fd)
            tree = Tree([sys.executable, "-B", "-I", "-S", "-c", harness_source(), str(ask), handle], work, None,
                        False, subprocess.DEVNULL, log, log, **extra)
        finally:
            os.close(write_fd)  # the child holds the only write end now
        reader = threading.Thread(target=drain, args=(read_fd, received), daemon=True)
        reader.start()
        try:
            code = tree.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = None
        finally:
            tree.stop()
            reader.join(10)
        output = text(log)
    records = [line for line in b"".join(received).decode("utf-8", "replace").splitlines() if line.strip()]
    assert code == 0 and len(records) == 1, \
        f"harness gave {len(records)} result records (exit {code}): {output.strip()[-200:]}"
    results = json.loads(records[0])
    assert isinstance(results, list) and len(results) == len(ops), "malformed harness result"
    return results


def answers(source, module, ops):
    """Expected results for `ops`: the reference `source` loaded fresh in this process (never written to disk)."""
    functions = {"__name__": "evals_harness"}
    exec(compile(harness_source(), "harness", "exec"), functions)
    reference = types.ModuleType(module)
    exec(compile(source, module, "exec"), reference.__dict__)
    return [functions["outcome"](reference, item) for item in ops]


def run_program(source, args):
    """Run a reference program's source in this process with `args`: (exit code, stdout, stderr)."""
    out, err, argv = io.StringIO(), io.StringIO(), sys.argv
    sys.argv = ["program", *args]
    try:
        with redirect_stdout(out), redirect_stderr(err):
            exec(compile(source, "program", "exec"), {"__name__": "__main__"})
        code = 0
    except SystemExit as stop:
        code = stop.code if isinstance(stop.code, int) else int(stop.code is not None)
    finally:
        sys.argv = argv
    return code, out.getvalue(), err.getvalue()


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


def agree(work, module, source, ops, what):
    """Assert the candidate answers `ops` exactly as the reference `source` does."""
    for want, got, item in zip(answers(source, module, ops), call(work, module, ops), ops):
        assert want[0] == "ok", f"reference failed on {item}: {want}"  # the rubric's own inputs must be valid
        assert same(got, want), f"{what} {item[1:]}: expected {want[1]!r}, got {got}"
