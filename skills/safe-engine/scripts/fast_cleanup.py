"""Explicit owner-authorized cleanup of obsolete temp fixtures; never a general guard exception."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid

LIMIT = 100_000


def parser(sub, common):
    """Register the preview/execute command without growing the gate's argument wiring."""
    cmd = sub.add_parser("cleanup-temp", parents=[common], help="Preview owner-named obsolete temp folders")
    cmd.add_argument("--path", action="append", required=True, help="Exact absolute direct child of system temp")
    cmd.add_argument("--reason", required=True, help="Owner instruction and source authorizing these exact folders")
    cmd.add_argument("--expect", help="Execute only if the fresh inventory matches this preview SHA256")


def plain(path):
    """Reject links, junctions and special nodes without following them."""
    info = path.lstat()
    if (stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))):
        raise ValueError(f"Link or special node refused: {path}")
    return info


def overlaps(a, b):
    """Protect both a project itself and a temp ancestor containing it."""
    return a == b or a in b.parents or b in a.parents


def inventory(paths, temp, protected):
    """Bounded metadata snapshot of exact roots; no contents or link traversal."""
    temp = Path(os.path.abspath(temp))
    for ancestor in (temp, *temp.parents):
        plain(ancestor)
    if temp.resolve() != temp:
        raise ValueError(f"Use the canonical temp folder: {temp.resolve()}")
    roots = []
    for value in paths:
        path = Path(value)
        if not path.is_absolute() or ".." in path.parts or path.parent != temp:
            raise ValueError(f"Name an exact absolute direct child of {temp}: {value}")
        if any(overlaps(path, Path(p).resolve()) for p in protected):
            raise ValueError(f"Protected project or factory overlap: {path}")
        if not stat.S_ISDIR(plain(path).st_mode) or path in roots:
            raise ValueError(f"Not a unique directory: {path}")
        if path.resolve() != path:
            raise ValueError(f"Use the canonical folder path: {path.resolve()}")
        roots.append(path)
    if not 1 <= len(roots) <= 32:
        raise ValueError("Name between 1 and 32 exact folders")
    rows, summaries = [], []
    for root in sorted(roots):
        stack, count, size = [root], 0, 0
        while stack:
            path = stack.pop()
            info = plain(path)
            rows.append((str(path), info.st_dev, info.st_ino, info.st_mode, info.st_size,
                         info.st_mtime_ns, info.st_ctime_ns))
            count += 1
            if len(rows) > LIMIT:
                raise ValueError(f"Inventory exceeds {LIMIT} entries; use a smaller explicit batch")
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(path) as entries:
                    for entry in entries:
                        stack.append(Path(entry.path))
                        if len(stack) + len(rows) > LIMIT:
                            raise ValueError(f"Inventory exceeds {LIMIT} entries")
            else:
                size += info.st_size
        summaries.append({"path": str(root), "entries": count, "bytes": size})
    digest = hashlib.sha256(json.dumps(sorted(rows), separators=(",", ":")).encode()).hexdigest()
    return {"sha256": digest, "folders": summaries}


def run(args, gate):
    """Preview first; a matching fresh snapshot enables audited, non-following removal."""
    project, run_state = gate.open_run(args.project)
    if not args.reason.strip() or len(args.reason) > 2000:
        gate.fail("Supply a concise owner instruction and its source in --reason")
    protected = [gate.HOME, project] + [item[2]["project"] for item in gate.active_runs()]
    receipt = gate.HOME / "cleanup" / f"{uuid.uuid4().hex}.json"
    report = {"project": str(project), "run": run_state["key"], "reason": args.reason, "time": gate.now()}
    try:
        report.update(inventory(args.path, tempfile.gettempdir(), protected))
        report["status"] = "preview"
        if args.expect:
            if args.expect != report["sha256"]:
                raise ValueError("Inventory changed or wrong digest; inspect a fresh preview before retrying")
            report["status"] = "started"
        gate.save(receipt, report, new=True)  # no deletion when the initial audit cannot be saved
        if args.expect:
            left = []
            for folder in report["folders"]:
                gate.sibling("fast_setup").remove(Path(folder["path"]), left)
            report["remaining"] = [f["path"] for f in report["folders"] if os.path.lexists(f["path"])]
            report["errors"] = left[:32]
            report["status"] = "partial" if left or report["remaining"] else "removed"
            gate.save(receipt, report)
        gate.log("cleanup." + report["status"], receipt=str(receipt), folders=len(args.path))
        print(json.dumps({**report, "receipt": str(receipt)}, indent=2))
        if report["status"] == "partial":
            gate.fail("Cleanup incomplete; inspect receipt and remaining folders before a fresh preview")
    except (OSError, ValueError) as error:
        gate.fail(f"Cleanup stopped: {error}. Inspect targets; receipt if created: {receipt}")
