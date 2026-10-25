"""Owner-reviewed stale Git baseline recovery; original state and proof obligations survive."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import fast_record as record


def parser(sub, common):
    """Expose a preview first, then an explicit digest-bound application."""
    command = sub.add_parser("recover-baseline", parents=[common], help=__doc__)
    command.add_argument("--base", required=True, help="Full upstream commit SHA preceding owned work")
    command.add_argument("--upstream", required=True, help="Full refs/remotes/<remote>/<branch> name")
    command.add_argument("--reason", required=True, help="Owner authority and reason for recovery")
    command.add_argument("--expect", help="Apply only the reviewed preview SHA256")


def git(project, *args):
    """Fail closed when provenance cannot be read."""
    value = record.git(project, *args)
    if value is None:
        raise ValueError("Cannot verify Git evidence: " + " ".join(args))
    return value.strip()


def sha(value):
    """Hash exact structured evidence without publishing file contents."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def preview(project, run, args):
    """Validate ancestry and start snapshots, binding every input consumed by apply."""
    if run.get("closed") or not run.get("paused") or any(step in run["done"] for step in ("done-run", "handoff")):
        raise ValueError("Recovery needs a paused open run before done-run")
    old = run.get("base")
    if not isinstance(old, str) or not record.HEX.fullmatch(old) or run.get("baseline_recovery"):
        raise ValueError("Needs an original Git baseline with no previous recovery")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", args.base) or args.base == old:
        raise ValueError("Name a different full commit SHA")
    if not args.reason.strip():
        raise ValueError("Record owner authority and recovery reason")
    if not args.upstream.startswith("refs/remotes/") or git(project, "check-ref-format", args.upstream):
        raise ValueError("Name a full remote-tracking upstream ref")
    base = git(project, "rev-parse", "--verify", args.base + "^{commit}")
    head = git(project, "rev-parse", "--verify", "HEAD")
    upstream = git(project, "rev-parse", "--verify", args.upstream + "^{commit}")
    for ancestor, child in ((old, base), (base, head), (base, upstream)):
        if git(project, "merge-base", ancestor, child) != ancestor:
            raise ValueError("Baseline must descend from start and precede HEAD and upstream")
    excluded = git(project, "log", "--format=%H %ct", old + ".." + base).splitlines()
    started = datetime.fromisoformat(run["created"]).timestamp()
    if not excluded or any(int(line.split()[1]) >= started for line in excluded):
        raise ValueError("Excluded commits must predate run start; owned work cannot become baseline")
    seen = run.get("ui_seen")
    if not isinstance(seen, dict) or any(record.digest(Path(project) / name) != mark for name, mark in seen.items()):
        raise ValueError("Start UI snapshot changed or is unavailable; preserve it and review manually")
    dirty = git(project, "diff", "--binary", "HEAD")
    untracked = git(project, "ls-files", "--others", "--exclude-standard").splitlines()
    return {"original_base": old, "base": base, "head": head, "upstream": args.upstream,
            "upstream_head": upstream, "excluded_commits": excluded,
            "excluded_paths": git(project, "diff", "--name-only", old, base).splitlines(),
            "remaining_ui": record.ui_files({**run, "base": base}, project),
            "run_sha256": sha(run), "dirty_sha256": sha(dirty),
            "index_sha256": sha(git(project, "diff", "--cached", "--binary", "HEAD")),
            "untracked_ui": {name: record.digest(Path(project) / name) for name in untracked if record.UI_FILE.search(name)},
            "reason": args.reason.strip()}


def recover(args, gate):
    """Save one audited correction through the gate, without changing progress or pause."""
    try:
        project, run = gate.open_run(args.project)
        evidence = preview(project, run, args)
        digest = sha(evidence)
        if args.expect:
            if args.expect != digest:
                raise ValueError("Preview changed; review a fresh preview before applying")
            if sha(gate.home_run(project)) != evidence["run_sha256"]:
                raise ValueError("Run changed during recovery; preview again")
            run["baseline_recovery"] = {**evidence, "sha256": digest, "at": gate.now()}
            gate.put(project, run)
            gate.log("run.baseline_recovered", key=run["key"], original=run["base"], base=args.base, digest=digest)
        print(json.dumps({"status": "applied" if args.expect else "preview", "sha256": digest, **evidence}, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as error:
        gate.fail("Baseline recovery refused: " + str(error))
