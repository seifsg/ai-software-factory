"""Owner-selected PR proof rules, independent of a run's bundle and progress.

Immutable receipts avoid racing the live ledger's writer. Only new starts snapshot the default;
existing runs use an identity-bound sidecar. Hooks read metadata; commands verify the whole skill.
"""
import hashlib
import json
from pathlib import Path
import stat

import fast_ledger as ledger


def identity(run):
    """A project may reuse a key: its creation time keeps adoption on the intended run."""
    if any(not isinstance(run.get(key), str) or not run[key] for key in ("project", "key", "created")):
        raise ValueError("run has no stable project/key/created identity")
    instance = run.get("pr_instance")
    if instance is not None and (not isinstance(instance, str) or len(instance) != 32
                                 or any(c not in "0123456789abcdef" for c in instance)):
        raise ValueError("malformed run instance")
    return {"project": ledger.norm(run["project"]), "key": run["key"], "created": run["created"], "instance": instance}


def receipt_path(home, run):
    key = hashlib.sha256(json.dumps(identity(run), sort_keys=True).encode()).hexdigest()
    return Path(home) / "pr-proof" / "runs" / (key + ".json")


def source_digest(method):
    """Hash paths and bytes, including references; reject links that could change outside the skill."""
    method = Path(method)
    if not method.is_absolute() or method.name != "SKILL.md" or not method.is_file():
        raise ValueError("--method must name an existing absolute PR SKILL.md")
    text = method.read_text(encoding="utf-8")
    if not all(marker in text for marker in ("**Visual:**", "**Journey:**")):
        raise ValueError("PR method does not define Visual and Journey proof")
    root, digest = method.parent, hashlib.sha256()
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("PR method folder must not contain links or reparse points")
        if path.is_file():
            data = path.read_bytes()
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest()


def read(path):
    """Absent is optional; unreadable or malformed policy never silently disables enforcement."""
    try:
        value = ledger.load(path)
        if value is None:
            raise ValueError(f"null PR-proof receipt: {path}")
        return value
    except FileNotFoundError:
        return None


def validate(policy, expected=None, verify=False):
    fields = {"version", "method", "digest", "reason", "at", "run"}
    if (not isinstance(policy, dict) or set(policy) != fields or type(policy["version"]) is not int or policy["version"] != 1
            or any(not isinstance(policy[key], str) or not policy[key].strip()
                   for key in ("method", "digest", "reason", "at"))
            or len(policy["digest"]) != 64 or any(c not in "0123456789abcdef" for c in policy["digest"])
            or not Path(policy["method"]).is_absolute() or policy["run"] != expected):
        raise ValueError("malformed PR-proof receipt or mismatched run identity")
    if verify and source_digest(policy["method"]) != policy["digest"]:
        raise ValueError("PR method changed since adoption; restore its recorded contents before continuing")
    return policy


def selected(home, run, verify=False):
    """A new run's snapshot wins; older runs can only receive their exact identity's sidecar."""
    if "pr_policy" in run:
        return validate(run["pr_policy"], verify=verify)
    # A lost or historical run without a creation time cannot have an adoption receipt.
    if not run.get("created"):
        return None
    policy = read(receipt_path(home, run))
    return validate(policy, identity(run), verify) if policy is not None else None


def failure(error):
    raise SystemExit(f"PR-proof policy: {error}") from error


def start(home):
    """Apply an explicitly configured default before the new run's first ledger write."""
    try:
        policy = read(Path(home) / "pr-proof" / "new-runs.json")
        return {"pr_policy": validate(policy, verify=True), "pr_proof": True, "pr_demo": True} if policy is not None else {}
    except (OSError, ValueError, TypeError) as error:
        failure(error)


def effective(home, run):
    """The handoff checker sees flags on a copy; adoption never writes live progress or pauses."""
    try:
        policy = selected(home, run, verify=True)
        return {**run, "pr_proof": True, "pr_demo": True, "pr_policy": policy} if policy else run
    except (OSError, ValueError, TypeError) as error:
        failure(error)


def method(home):
    """Every mode can discover and verify the owner's selected PR method without changing a run."""
    policy = start(home).get("pr_policy")
    print(f"{policy['method']}\nSHA256: {policy['digest']}" if policy else "No PR policy override; use selected bundle method.")


def notice(home, run, strict=False):
    """Prompt hooks only read one small receipt; source hashing belongs to commands."""
    try:
        policy = selected(home, run, verify=strict)
        return (f"PR proof: read {policy['method']}; Visual/Journey declarations and required media apply. "
                f"Use {Path(__file__).with_name('fast_gate.py')} for handoff; "
                "the other bundle rules and pause remain unchanged.") if policy else ""
    except (OSError, ValueError, TypeError) as error:
        if strict:
            failure(error)
        return f"PR-proof policy needs repair before handoff: {error}"


def close(home, run):
    """A handoff racing adoption, or recorded by an older gate, cannot count as the new proof check."""
    checked = effective(home, run)
    policy = checked.get("pr_policy")
    if policy and run["done"].get("handoff", {}).get("pr_policy") != policy["digest"]:
        raise SystemExit("PR-proof policy: record handoff with the installed gate before closing")


def default(home, path, policy, previous):
    """Explicit default changes retain prior selections; existing run snapshots never change."""
    if previous is not None:
        validate(previous)  # a changed old source does not block selecting a repaired default
    for entry in [policy] + ([previous] if previous is not None else []):
        key = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        try:
            ledger.save(Path(home) / "pr-proof" / "defaults" / (key + ".json"), entry, new=True)
        except FileExistsError:
            pass  # content-addressed history is already retained
    ledger.save(path, policy)


def adopt(args, gate):
    """Record only authorized PR-policy selection; never overwrite the active run's state."""
    try:
        if not args.reason.strip():
            raise ValueError("--reason must record the owner's authority and source")
        project, run = (None, None) if args.new_runs else gate.open_run(args.project)
        if run and (not gate.well_formed(run) or "handoff" in run["done"]):
            raise ValueError("adoption needs an open run with no recorded handoff")
        policy = {"version": 1, "method": str(Path(args.method).absolute()), "digest": source_digest(args.method),
                  "reason": args.reason.strip(), "at": gate.now(), "run": identity(run) if run else None}
        path = receipt_path(gate.HOME, run) if run else gate.HOME / "pr-proof" / "new-runs.json"
        previous = selected(gate.HOME, run, verify=True) if run else read(path)
        if run is None:
            default(gate.HOME, path, policy, previous)
        elif previous is not None:
            if (previous["method"], previous["digest"]) != (policy["method"], policy["digest"]):
                raise ValueError("a different immutable PR policy is already selected; preserve it for reviewed migration")
        else:
            try:
                ledger.save(path, policy, new=True)
            except FileExistsError:
                previous = validate(read(path), policy["run"], verify=True)
                if (previous["method"], previous["digest"]) != (policy["method"], policy["digest"]):
                    raise ValueError("another adoption selected a different PR policy")
        if run:
            current = gate.home_run(project)
            if current.get("closed") or identity(current) != identity(run) or "handoff" in current["done"]:
                raise ValueError("run changed during adoption; inspect its status; a fresh installed-gate handoff is required")
        gate.log("pr-proof.adopt", project=str(project) if project else None, method=policy["method"], digest=policy["digest"])
        location = "new-run snapshot in " + str(gate.state_path(project)) if run and "pr_policy" in run else str(path)
        print(f"PR proof {'for new runs' if run is None else 'for ' + run['key']}: {location}\nMethod: {policy['method']}")
    except (OSError, ValueError, TypeError) as error:
        failure(error)
