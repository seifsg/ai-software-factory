"""Interpreter guard: what check and harness children load must not change while agents run.

A probe child, started like a check child (-I -S -B), imports every module the check program, the rubric tools,
the harness and the rubrics use, and reports the files behind them and the folders Python searches. The guard
hashes those files (sources and cached bytecode) and the interpreter, and lists those folders and the site folders.
"""
import hashlib
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import sysconfig

MODULES = ["ast", "functools", "importlib", "io", "json", "os", "pathlib", "secrets", "signal", "subprocess", "sys",
           "tempfile", "threading", "types", "unittest", "wsgiref.util"]
MODULES += ["ctypes.wintypes"] if os.name == "nt" else []  # the job object, Windows only
PROBE = ("import json, sys\n"
         "for name in {names!r}:\n"
         "    __import__(name)\n"
         "files = {{getattr(m, a, None) or ''\n"
         "         for m in list(sys.modules.values()) for a in ('__file__', '__cached__')}}\n"
         "print(json.dumps({{'files': sorted(f for f in files if f), 'path': sys.path}}))\n")


def file_hash(path):
    """SHA-256 of a file, or 'missing'."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "missing"


def listing(folder):
    """The names directly in `folder`, or none."""
    try:
        return sorted(os.listdir(folder))
    except OSError:
        return []


def site_folders():
    """Where site hooks (.pth files, sitecustomize, packages) would live for this interpreter."""
    paths = sysconfig.get_paths()
    found = {paths["purelib"], paths["platlib"], site.getusersitepackages()}
    return found | set(site.getsitepackages() if hasattr(site, "getsitepackages") else [])


def state():
    """One digest of everything a check child could load; RuntimeError when the probe itself fails."""
    try:
        done = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", PROBE.format(names=MODULES)],
                              capture_output=True, text=True, timeout=120)
        seen = json.loads(done.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as error:
        raise RuntimeError(f"the interpreter probe failed: {error}") from error
    if done.returncode:
        raise RuntimeError(f"the interpreter probe failed: {done.stderr.strip()[-300:]}")
    files = {name: file_hash(name) for name in [sys.executable, *seen["files"]]}
    folders = {folder: listing(folder) for folder in sorted({*seen["path"], *site_folders()})}
    return hashlib.sha256(json.dumps([files, folders], sort_keys=True).encode()).hexdigest()
