"""Run one rubric check in its own process: `python check.py <sample dir> <workdir> <item id>`, a token on stdin.

The check passes only when this process prints the token as its last line, after the check returned: a candidate
that exits early (even with code 0) or crashes fails. Python 3.9+, standard library only.
"""
import importlib.util
from pathlib import Path
import sys


def load_rubric(sample_dir):
    """The sample's rubric module: CHECKS maps item ids to check(workdir); KEEP names preserved-behavior items."""
    path = Path(sample_dir) / "rubric.py"
    if not path.is_file():
        raise ValueError(f"missing rubric: {path}")
    spec = importlib.util.spec_from_file_location(f"rubric_{path.parent.name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = getattr(module, "CHECKS", None)
    if not isinstance(checks, dict) or not checks or not all(callable(check) for check in checks.values()):
        raise ValueError(f"{path}: CHECKS must map item ids to functions")
    if not set(getattr(module, "KEEP", ())) <= set(checks):
        raise ValueError(f"{path}: KEEP names an item missing from CHECKS")
    return module


def main(argv):
    """Load the rubric before the workspace joins sys.path, run one check, then print the token."""
    if len(argv) != 3:
        print(__doc__.splitlines()[0], file=sys.stderr)
        return 2
    token = sys.stdin.readline().strip()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # rubrics import evals.rubric_tools
    sample_dir, workdir, item = argv
    try:
        check = load_rubric(sample_dir).CHECKS[item]  # rubric imports resolve before candidate files can shadow them
        sys.path.insert(0, str(Path(workdir).resolve()))  # candidate modules import by name
        check(Path(workdir))
    except BaseException as error:  # noqa: BLE001 - SystemExit from candidate code must not pass a check
        print(f"{type(error).__name__}: {error}".strip(), file=sys.stderr)
        return 1
    sys.stderr.flush()
    print(token, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
