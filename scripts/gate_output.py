"""Bytes the Fast gate puts into an agent's context on one fixture change run.

Why: cards, record hints, hook context, deny and stop text repeat on every step. The same fixture at two
revisions shows whether a change made them smaller. Used by `token_report.py --gate`. Stdlib only.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

SKILL = "skills/safe-engine"  # the gate reads its VERSION beside scripts/
GATE = SKILL + "/scripts"
TICKETS = "**Ticket:** none (fixture)\n\n**Backlog:** none\n"


def scripts(root, rev, dest):
    """Use complete selected methods; an archived revision gets its own real local Git identity."""
    if not rev:
        return Path(root) / GATE
    tar = subprocess.run(("git", "-C", str(root), "-c", "core.autocrlf=false", "archive", "--format=tar", rev),
                         capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        archive.extractall(dest, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    origin = subprocess.check_output(("git", "-C", str(root), "remote", "get-url", "origin"), text=True).strip()
    origin = re.sub(r"(?<=//)[^@/]+@", "", origin)
    for args in (("init", "-q"), ("config", "core.autocrlf", "false"), ("remote", "add", "origin", origin),
                 ("add", "-A", "-f"), ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                                      "-c", "commit.gpgsign=false", "commit", "-qm", "Message fixture", "--no-verify")):
        subprocess.run(("git", "-C", str(dest), *args), capture_output=True, check=True)
    return dest / GATE


def field(out, *keys):
    """A nested field of a hook's JSON answer; '' when the hook said nothing."""
    data = json.loads(out) if out.strip() else {}
    for key in keys:
        data = data.get(key, {}) if isinstance(data, dict) else {}
    return data if isinstance(data, str) else ""


def shorten(text, path, tag):
    """text with path, in any case (the gate may lowercase it), replaced by tag: sizes then match on any machine."""
    return re.sub(re.escape(str(path)), tag, text, flags=re.I)


def messages(gate, tmp):
    """{message: text} from one fixture change run in a private gate home (start, hints, hooks, done, status),
    plus a product run's record hints."""
    project = tmp / "p"
    project.mkdir()
    subprocess.run(("git", "init", "-q", str(project)), check=True)
    env = {**os.environ, "SAFE_ENGINE_HOME": str(tmp / "h"), "HOME": str(tmp), "USERPROFILE": str(tmp),
           "SAFE_ENGINE_NO_UPDATE": "1", "PYTHONIOENCODING": "utf-8"}
    factory = Path(gate).resolve().parents[3]
    # Pin the measured checkout, not a remotely selected release. Only discovery is controlled;
    # receipt validation, current CLI startup, policies and every measured command remain real.
    probe = ("import sys;from pathlib import Path;sys.path.insert(0,sys.argv.pop(1));"
             "import fast_gate,resolve_bundle;root=Path(sys.argv.pop(1));"
             "hasattr(resolve_bundle,'select_for_project') or sys.exit('Message fixture requires a selection-capable revision');"
             "resolve_bundle.resolve_bundle=lambda *a,**k: resolve_bundle.inspect_bundle(root,entrypoint=k.get('entrypoint','safe-engine'));"
             "args=sys.argv[1:];project=Path(args[args.index('--project')+1]) if '--project' in args else None;"
             "resolve_bundle.select_for_project(project,root,None,fast_gate.HOME/'bundles','safe-engine') "
             "if args[:1]==['start'] and not (project/'.factory/entry-bundle.json').exists() else None;fast_gate.main()")

    def run(*args, stdin=None):
        done = subprocess.run((sys.executable, "-c", probe, str(Path(gate).parent), str(factory), *args), input=stdin, capture_output=True, text=True,
                              encoding="utf-8", env=env, cwd=project, check=args[0] != "hook")
        return done.stdout

    def hook(name, keys, **event):
        return field(run("hook", stdin=json.dumps({"hook_event_name": name, "cwd": str(project), "session_id": "s",
                                                   **event})), *keys)

    deny = ("hookSpecificOutput", "permissionDecisionReason")
    out = {"start": run("start", "--project", str(project), "--key", "fixture", "--kind", "change",
                        "--request", "Fix the footer typo")}
    selected = json.loads((project / ".factory/entry-bundle.json").read_text(encoding="utf-8"))
    started = json.loads((project / ".factory/fast/run.json").read_text(encoding="utf-8"))
    if started.get("bundle") != {"root": str(factory), "revision": selected["revision"]}:
        raise RuntimeError("Message fixture did not start the measured factory")
    record = project / ".factory" / "fast" / "work-record.md"
    text = record.read_text(encoding="utf-8")
    out["record hints"] = "\n".join(line for line in text.splitlines() if line.startswith("<!--"))
    out["hook context"] = hook("UserPromptSubmit", ("hookSpecificOutput", "additionalContext"), prompt="go")
    out["deny edit"] = hook("PreToolUse", deny, tool_name="Write", tool_input={"file_path": str(project / "a.py")})
    out["deny destructive"] = hook("PreToolUse", deny, tool_name="Bash", tool_input={"command": "git push --force"})
    out["stop"] = hook("Stop", ("reason",), stop_hook_active=False)
    record.write_text(text.replace("## Tickets\n", "## Tickets\n\n" + TICKETS, 1), encoding="utf-8")
    out["done"] = run("done", "tickets", "--project", str(project))
    out["status"] = run("status", "--project", str(project))
    product = tmp / "q"  # the largest hints: a product run with sign-in, every check its methods define
    product.mkdir()
    subprocess.run(("git", "init", "-q", str(product)), check=True)
    run("start", "--project", str(product), "--key", "fixture-product", "--kind", "product", "--auth", "--request", "A shop")
    hints = (product / ".factory" / "fast" / "work-record.md").read_text(encoding="utf-8").splitlines()
    out["product hints"] = "\n".join(line for line in hints if line.startswith("<!--"))
    for path, tag in sorted(((project, "<p>"), (factory, "<factory>"), (tmp, "<t>")),
                            key=lambda item: len(str(item[0])), reverse=True):
        out = {name: shorten(value, path, tag) for name, value in out.items()}
    return out


def measure(root, rev=None):
    """{message: bytes} for the gate at rev (default: the working tree); paths shortened so revisions compare."""
    tmp = Path(tempfile.mkdtemp()).resolve()
    try:
        texts = messages(scripts(root, rev, tmp / "src") / "fast_gate.py", tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, value in texts.items():
        if not value:
            raise RuntimeError(f"gate fixture: no '{name}' output at {rev or 'working tree'}")
    return {name: len(value.encode()) for name, value in texts.items()}
