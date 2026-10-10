"""Helpers for sample rubrics: run candidate code in a child process without a pipe a grandchild could hold."""
import subprocess
import sys
import tempfile


def text(handle):
    """Everything written to a temp file, decoded."""
    handle.seek(0)
    return handle.read().decode("utf-8", "replace")


def run_python(work, *args, timeout=30):
    """Run `python -B *args` in `work`; returns (exit code or None on timeout, stdout, stderr), read from files."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            code = subprocess.run([sys.executable, "-B", *args], cwd=work, stdin=subprocess.DEVNULL, stdout=out,
                                  stderr=err, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = None
        return code, text(out), text(err)
