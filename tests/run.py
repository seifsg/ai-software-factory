"""Run the test suite in parallel: `python tests/run.py [--changed [BASE]] [--jobs N]`.

Same tests and assertions as `python -m unittest discover -s tests`, one test per pool task in warm worker
processes. Timing-sensitive classes run one at a time in their own process beside a pool that leaves cores free.
`--changed` runs only the modules a diff touches (against BASE, default origin/main, plus uncommitted files);
a file no rule maps runs everything. Python 3.9+, standard library only.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import unittest
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SERIAL = {"ParallelChecksTests", "HardeningTests", "CheckpointRepairs"}  # concurrency, locks, timeouts
SKILL_FILES = re.compile(r"\.agents|SKILL\.md|references/")  # tests that read the skill files themselves
PACKAGED = {"test_skill_distribution", "test_bundle_inputs"}  # bundle contents and resolvers
SOURCE_TREES = {"safe_engine", ".agents", "skills", "docs", "scripts"}  # safe_engine/bundle-inputs.json


def setup():
    """What `python -m unittest discover -s tests` gives each process: repo cwd, repo and tests importable."""
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT), str(TESTS)]
    if os.name == "nt":
        git = shutil.which("git")
        shells = next((parent / "bin" for parent in Path(git).resolve().parents
                       if all((parent / "bin" / name).is_file() for name in ("sh.exe", "bash.exe"))), None) if git else None
        if shells:
            # Prefer the installed Git shell over Windows' WSL launcher, only in test processes.
            paths = [str(shells), *os.environ.get("PATH", "").split(os.pathsep)]
            unique = {}
            for path in paths:
                unique.setdefault(os.path.normcase(os.path.normpath(path)), path)
            os.environ["PATH"] = os.pathsep.join(unique.values())


def flatten(suite):
    for item in suite:
        yield from flatten(item) if isinstance(item, unittest.TestSuite) else [item]


def run_one(test_id):
    """Run one test in this process: its id, problems (kind, traceback), skipped count and seconds."""
    started, result = time.perf_counter(), unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromName(test_id).run(result)
    problems = [("FAIL", trace) for _, trace in result.failures] + [("ERROR", trace) for _, trace in result.errors]
    problems += [("FAIL", "unexpected success") for _ in result.unexpectedSuccesses]  # as unittest counts it
    return test_id, problems, len(result.skipped), time.perf_counter() - started


def sources():
    return {path.stem: path.read_text(encoding="utf-8") for path in TESTS.glob("*.py") if path.name != "run.py"}


def importers(names, texts):
    """`names` plus every test helper or module that imports one of them, transitively."""
    found, grew = set(names), True
    while grew:
        grew = False
        for stem, text in texts.items():
            if stem not in found and any(re.search(rf"^(?:import|from) {n}\b", text, re.M) for n in found):
                found.add(stem)
                grew = True
    return found


def selected(base):
    """Test modules for the files changed against `base`, plus uncommitted and untracked ones; None means all."""
    def git(command, *args):
        out = subprocess.run(["git", "-C", str(ROOT), command, "-z", *args], capture_output=True, text=True,
                             encoding="utf-8", check=True).stdout
        return [name for name in out.split("\0") if name]
    files = set(git("diff", "--name-only", "--no-renames", f"{base}...HEAD")  # a rename lists both paths
                + git("diff", "--name-only", "--no-renames", "HEAD")
                + git("ls-files", "--others", "--exclude-standard"))
    texts, modules = sources(), set()
    for path in files:
        file = Path(path)
        if path.startswith("tests/"):
            hits = {file.stem} if file.stem in texts else set()  # the runner itself, or an unknown helper: all
        elif path.startswith((".agents/", "docs/", "skills/agents/")) or "/" not in path and path.endswith(".md"):
            hits = {stem for stem, text in texts.items() if SKILL_FILES.search(text)}
        elif path.startswith("safe_engine/"):
            hits = {stem for stem, text in texts.items() if "safe_engine" in text}
        else:  # modules naming this file or a sibling it may load (the gate loads its scripts by name)
            names = {file.stem} | ({p.stem for p in (ROOT / file.parent).glob("*.py")} if "/" in path else set())
            hits = {stem for stem, text in texts.items()
                    if any(re.search(rf"\b{re.escape(n)}\b", text) for n in names)}
        if not hits:
            return None  # nothing claims this file: run everything
        modules |= hits | (PACKAGED if file.parts[0] in SOURCE_TREES else set())
    return {m for m in importers(modules, texts) if m.startswith("test_")}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--changed", nargs="?", const="origin/main", metavar="BASE")
    parser.add_argument("--jobs", type=int, default=max(1, min((os.cpu_count() or 2) - 2, 16)))
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="backslashreplace")  # a failure trace with symbols must never crash the report
    setup()
    modules = selected(args.changed) if args.changed else None
    if modules is not None and not modules:
        print("No test module covers the changed files.")
        return 0
    tests = list(flatten(unittest.defaultTestLoader.discover(str(TESTS), top_level_dir=str(TESTS))))
    broken = [t for t in tests if t.id().startswith("unittest.loader.")]  # modules that failed to import
    tests = [t for t in tests if t not in broken and (modules is None or t.id().split(".")[0] in modules)]
    pooled = [t.id() for t in tests if t.id().split(".")[1] not in SERIAL]
    serial = [t.id() for t in tests if t.id().split(".")[1] in SERIAL]
    started, results = time.perf_counter(), []
    with ProcessPoolExecutor(max_workers=max(1, args.jobs), initializer=setup) as pool, \
            ProcessPoolExecutor(max_workers=1, initializer=setup) as lane:  # serial tests, in order
        futures = {lane.submit(run_one, test_id): test_id for test_id in serial}
        futures.update({pool.submit(run_one, test_id): test_id for test_id in pooled})
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as error:  # noqa: BLE001 - a crashed worker is a failed test, never a lost one
                results.append((futures[future], [("ERROR", f"worker failed: {error!r}")], 0, 0.0))
            print("F" if results[-1][1] else ".", end="", flush=True)
    for test in broken:
        result = unittest.TestResult()
        test.run(result)
        results.append((test.id(), [("ERROR", trace) for _, trace in result.errors], 0, 0.0))
    problems = [(test_id, kind, trace) for test_id, found, _, _ in results for kind, trace in found]
    for test_id, kind, trace in problems:
        print(f"\n{'=' * 70}\n{kind}: {test_id}\n{'-' * 70}\n{trace}")
    skipped = sum(item[2] for item in results)
    print(f"\nRan {len(results)} tests in {time.perf_counter() - started:.1f}s ({len(pooled)} pooled on "
          f"{args.jobs} workers, {len(serial)} serial){' in ' + str(len(modules)) + ' modules' if modules else ''}")
    print(f"FAILED ({len(problems)} problems, skipped={skipped})" if problems else f"OK (skipped={skipped})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
