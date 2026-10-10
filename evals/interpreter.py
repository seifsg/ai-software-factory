"""Interpreter guard: what check and harness children load must not change while agents run.

The runner records, before any agent starts, the files behind every module that real checks and harnesses load
(`catalog.loaded_modules`) and the folders they search. The guard hashes those files (sources and cached bytecode)
and the interpreter, and lists those folders and the interpreter's site folders.
"""
import hashlib
import json
import os
from pathlib import Path
import site
import sys
import sysconfig


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


def state(files, folders):
    """One digest of the recorded module files, the interpreter, and the listings of the searched and site
    folders."""
    hashes = {name: file_hash(name) for name in sorted({sys.executable, *files})}
    listings = {folder: listing(folder) for folder in sorted({*folders, *site_folders()})}
    return hashlib.sha256(json.dumps([hashes, listings], sort_keys=True).encode()).hexdigest()
