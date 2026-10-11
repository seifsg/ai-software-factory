"""Setup-only project MCP configuration: native read-only parsing and recoverable owned file updates."""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

LIMIT = 1048576
SERVER_PREFIX = "safe_engine_"
EVENTS = {"PreToolUse": "Bash|apply_patch", "Stop": None, "UserPromptSubmit": None, "SessionStart": None}


def digest(value):
    return hashlib.sha256(value).hexdigest() if value is not None else None


def content(path):
    try:
        with Path(path).open("rb") as stream:
            value = stream.read(LIMIT + 1)
    except FileNotFoundError:
        return None
    if len(value) > LIMIT:
        raise SystemExit("Project hook configuration exceeds the setup limit; preserve it and reduce it before retrying")
    return value


def replace(path, value):
    path = Path(path)
    if value is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".safe-engine-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        try:
            Path(name).unlink(missing_ok=True)
        except OSError:
            pass


def executable():
    value = os.environ.get("CODEX_EXECUTABLE") or shutil.which("codex")
    if not value or not Path(value).is_file():
        raise SystemExit("Project MCP hook setup needs the native Codex CLI. Put codex on PATH or set CODEX_EXECUTABLE to its executable, then retry; configuration was preserved")
    return str(Path(value).resolve())


def parse_toml(value, home, native=None):
    """Parse an opaque config in a private created user layer; never start a thread, model or copied MCP."""
    if len(value) > LIMIT:
        raise SystemExit("Generated project configuration exceeds the setup limit; original files were preserved")
    native = native or executable()
    temporary = Path(home) / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hook-config-", dir=temporary) as folder:
        root = Path(folder).resolve()
        assert root.is_relative_to(temporary.resolve())
        user = root / "home"
        codex = user / ".codex"
        codex.mkdir(parents=True)
        (codex / "config.toml").write_bytes(value)
        env = dict(os.environ, USERPROFILE=str(user), HOME=str(user), CODEX_HOME=str(codex),
                   SAFE_ENGINE_HOME=str(user / ".safe-engine"), GH_CONFIG_DIR=str(user / ".gh"))
        for key in ("USERPROFILE", "HOME", "CODEX_HOME", "SAFE_ENGINE_HOME", "GH_CONFIG_DIR"):
            path = Path(env[key]).resolve()
            assert path.is_relative_to(root)
            path.mkdir(parents=True, exist_ok=True)
        messages = queue.Queue(maxsize=8)
        process = subprocess.Popen([native, "app-server", "--stdio"], cwd=root, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        def receive():
            try:
                while True:
                    line = process.stdout.readline(4 * LIMIT + 1)
                    if not line:
                        return
                    if len(line) > 4 * LIMIT:
                        messages.put(None, timeout=1)
                        return
                    messages.put(json.loads(line), timeout=1)
            except (OSError, ValueError, queue.Full):
                try:
                    messages.put(None, timeout=1)
                except queue.Full:
                    pass

        reader = threading.Thread(target=receive, daemon=True)
        reader.start()

        def request(number, method, params):
            process.stdin.write((json.dumps({"id": number, "method": method, "params": params}) + "\n").encode())
            process.stdin.flush()
            # Each request is bounded even if the native process sends unrelated notifications.
            import time
            deadline = time.monotonic() + 15
            while True:
                message = messages.get(timeout=max(.01, deadline - time.monotonic()))
                if not isinstance(message, dict) or time.monotonic() > deadline:
                    raise ValueError("Unsupported parser response")
                if message.get("id") == number:
                    if "result" not in message:
                        raise ValueError("Configuration rejected")
                    return message["result"]

        try:
            request(1, "initialize", {"clientInfo": {"name": "safe-engine-hook-setup", "version": "1"}})
            process.stdin.write(b'{"method":"initialized"}\n')
            process.stdin.flush()
            result = request(2, "config/read", {"includeLayers": True})
            layer = next(item for item in result["layers"] if item["name"]["type"] == "user")
            parsed = layer["config"]
            if not isinstance(parsed, dict):
                raise ValueError("Invalid layer")
            return parsed
        except (OSError, ValueError, TypeError, KeyError, StopIteration, queue.Empty) as error:
            raise SystemExit("Native Codex could not parse project configuration. Repair malformed/unsupported TOML or the CLI, then retry; original files were preserved (" + type(error).__name__ + ")") from None
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # This exact private process owns no thread or run; EOF failed, so dispose only our child.
                process.terminate()
                process.wait(timeout=5)
            reader.join(timeout=1)
            process.stdout.close()


def handlers(identity):
    server = SERVER_PREFIX + identity
    result = {}
    for event in EVENTS:
        fields = {key: "${" + key + "}" for key in ("hook_event_name", "session_id", "cwd")}
        if event == "PreToolUse":
            fields.update({key: "${" + key + "}" for key in ("tool_name", "tool_input")})
        elif event == "Stop":
            fields["stop_hook_active"] = "${stop_hook_active}"
        result[event] = {"type": "mcp_tool", "server": server, "tool": "factory_hook", "input": {"event": fields}, "timeout": 30}
    return result


def block(identity, gate, home):
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    return ("\n# safe-engine project hooks begin " + identity + "\n[mcp_servers." + SERVER_PREFIX + identity + "]\n" +
            "command = " + quote(sys.executable) + "\nargs = [" + quote(Path(gate) / "fast_hook_server.py") + ", " + quote(identity) + "]\n" +
            "cwd = " + quote(Path(gate)) + "\nrequired = true\nstartup_timeout_sec = 10\ntool_timeout_sec = 30\n" +
            "enabled_tools = [\"factory_hook\"]\nenv = { SAFE_ENGINE_HOME = " + quote(home) + " }\n" +
            "# safe-engine project hooks end " + identity + "\n").encode("utf-8")


def encode(value):
    return base64.b64encode(value).decode("ascii") if value is not None else None


def decode(value):
    return base64.b64decode(value, validate=True) if value is not None else None


def save_receipt(path, data):
    encoded = (json.dumps(data, indent=2) + "\n").encode()
    if len(encoded) > 4 * LIMIT:
        raise SystemExit("Hook setup receipt exceeds the recovery limit; preserve the existing receipt/configuration and reduce it before retrying")
    replace(path, encoded)


def valid_receipt(saved):
    if not isinstance(saved, dict) or (saved and saved.get("version") not in (1, 2)):
        return False
    if saved.get("version") != 2:
        return True
    if (not isinstance(saved.get("project"), str) or not isinstance(saved.get("server"), str) or
            not isinstance(saved.get("removed"), bool) or saved.get("status") not in ("prepared", "configured", "removed") or
            not isinstance(saved.get("handlers"), dict) or not all(isinstance(value, dict) for value in saved["handlers"].values()) or
            not isinstance(saved.get("block"), (str, type(None))) or
            not isinstance(saved.get("server_config"), (dict, type(None)))):
        return False
    try:
        decode(saved.get("block"))
        if saved["status"] == "prepared":
            journal = saved.get("journal")
            if not isinstance(journal, list) or len(journal) != 2 or not isinstance(saved.get("previous"), dict):
                return False
            for item in journal:
                if (not isinstance(item, dict) or not isinstance(item.get("path"), str) or
                        "before" not in item or "before_hash" not in item or "after_hash" not in item or
                        not isinstance(item["before"], (str, type(None)))):
                    return False
                for key in ("before_hash", "after_hash"):
                    value = item[key]
                    if value is not None and (not isinstance(value, str) or len(value) != 64 or
                                               any(char not in "0123456789abcdef" for char in value)):
                        return False
                if digest(decode(item["before"])) != item["before_hash"]:
                    return False
    except (ValueError, TypeError):
        return False
    return True


def read_receipt(receipt, required=False):
    try:
        with Path(receipt).open("rb") as stream:
            raw = stream.read(4 * LIMIT + 1)
        if len(raw) > 4 * LIMIT:
            raise ValueError("Receipt limit")
        saved = json.loads(raw)
        if not valid_receipt(saved):
            raise ValueError("Receipt shape")
        return saved
    except FileNotFoundError:
        if required:
            raise SystemExit("Hook recovery receipt disappeared; preserve both configuration files and reconcile the paired backups before retrying") from None
        return {}
    except (OSError, ValueError, RecursionError):
        raise SystemExit("Hook setup receipt is unreadable or invalid; preserve it and reconcile the paired backups before retrying") from None


def recover(receipt, saved, paths, log, record):
    """Only roll back exact bytes we wrote; a concurrent owner edit is never a recovery target."""
    journal = saved.get("journal")
    if saved.get("status") != "prepared":
        return saved
    if not isinstance(journal, list) or len(journal) != len(paths) or any(not isinstance(item, dict) or
            item.get("path") != str(path) for item, path in zip(journal, paths)):
        raise SystemExit("Hook setup recovery receipt is invalid; preserve it and restore the paired backups before retrying")
    current = [content(path) for path in paths]
    if any(digest(value) not in (item["before_hash"], item["after_hash"]) for item, value in zip(journal, current)):
        record("hooks.recovery", status="owner_edit")
        raise SystemExit("Hook setup was interrupted and configuration changed afterward. Preserve your edits; reconcile both files with the private receipt/backups before retrying")
    if all(digest(value) == item["after_hash"] for item, value in zip(journal, current)):
        saved["status"] = "configured" if not saved["removed"] else "removed"
    else:
        originals = [decode(item["before"]) for item in journal]
        if any(digest(value) != item["before_hash"] for item, value in zip(journal, originals)):
                raise SystemExit("Hook recovery backup is invalid; preserve the receipt and repair the paired files before retrying")
        for item, path, value, before in zip(journal, paths, current, originals):
            if value != before:
                if content(path) != value:
                    raise SystemExit("Configuration changed during recovery; preserve your edits and retry after reconciling the receipt")
                replace(path, before)
        saved = saved.get("previous") or {}
    save_receipt(receipt, saved)
    record("hooks.recovery", status="recovered")
    return saved


def configure(base, gate, home, identity, remove, read_hooks, clean_groups, log, record):
    """Preflight, parse, stage and recover the two owned project configuration surfaces."""
    paths = (Path(base) / ".codex/hooks.json", Path(base) / ".codex/config.toml")
    receipts = Path(home) / "installations"
    receipt = receipts / ("codex-" + identity + ".json")
    saved = read_receipt(receipt)
    saved = recover(receipt, saved, paths, log, record)
    before = [content(path) for path in paths]
    data = read_hooks(paths[0], raw=before[0])  # validate exactly the bounded bytes covered by CAS
    native = executable()
    original = parse_toml(before[1] or b"", home, native)
    if not isinstance(original.get("mcp_servers", {}), dict):
        raise SystemExit("Project mcp_servers configuration is invalid; repair it before retrying; original files were preserved")
    server = SERVER_PREFIX + identity
    old_block = decode(saved.get("block")) if saved.get("version") == 2 and not saved.get("removed") else None
    desired = handlers(identity)
    previous_handlers = saved.get("handlers", {}) if old_block else {}
    toml = before[1] or b""
    if old_block:
        if (saved.get("project") != str(base) or saved.get("server") != server or not old_block or
                toml.count(old_block) != 1 or original.get("mcp_servers", {}).get(server) != saved.get("server_config")):
            raise SystemExit("Owned MCP configuration changed or its receipt is ambiguous; preserve edits and reconcile the exact managed block before retrying")
        candidate = toml.replace(old_block, b"", 1)
    else:
        if server in original.get("mcp_servers", {}) or ("# safe-engine project hooks begin " + identity).encode() in toml:
            raise SystemExit("Project MCP name/block already exists without verified ownership; preserve it and choose a clean configuration before retrying")
        candidate = toml
    events = data.setdefault("hooks", {})
    for event, groups in list(events.items()):
        kept = []
        for group in groups:
            remain = []
            for hook in group["hooks"]:
                if hook.get("server") == server and hook != previous_handlers.get(event):
                    raise SystemExit("An unrelated handler uses this MCP name; preserve it and reconcile the configuration before retrying")
                if hook != previous_handlers.get(event):
                    remain.append(hook)
            if remain:
                kept.append({**group, "hooks": remain})
        # Legacy command handlers remain conservatively identified by their complete existing shape.
        kept = clean_groups(kept)
        if kept:
            events[event] = kept
        else:
            events.pop(event, None)
    generated = None if remove else block(identity, gate, home)
    if generated:
        candidate += generated
        for event, hook in desired.items():
            events.setdefault(event, []).append({**({"matcher": EVENTS[event]} if EVENTS[event] else {}), "hooks": [hook]})
    parsed = parse_toml(candidate, home, native)
    expected = json.loads(json.dumps(original))
    expected.setdefault("mcp_servers", {}).pop(server, None)
    if not remove:
        expected["mcp_servers"][server] = parsed.get("mcp_servers", {}).get(server)
        if expected["mcp_servers"][server] is None:
            raise SystemExit("Native parser did not recognize the generated MCP configuration; original files were preserved")
    if not expected["mcp_servers"] and "mcp_servers" not in parsed:
        expected.pop("mcp_servers")
    if parsed != expected:
        raise SystemExit("Project config would change unrelated settings; original files were preserved")
    after = [None if remove and before[0] is None else (json.dumps(data, indent=2) + "\n").encode(),
             candidate if before[1] is not None or candidate else None]
    if any(value is not None and len(value) > LIMIT for value in after):
        raise SystemExit("Generated project configuration exceeds the setup limit; original files were preserved")
    for path, value in zip(paths, before):
        backup = receipts / ("codex-" + identity + (".hooks-backup.json" if path == paths[0] else ".config-backup.toml"))
        if value is not None and not backup.exists():
            replace(backup, value)
    current = {"version": 2, "project": str(base), "server": server, "removed": remove, "status": "prepared",
               "block": encode(generated), "handlers": {} if remove else desired,
               "server_config": None if remove else parsed["mcp_servers"][server], "previous": saved,
               "journal": [{"path": str(path), "before": encode(old), "before_hash": digest(old), "after_hash": digest(new)}
                           for path, old, new in zip(paths, before, after)]}
    if any(content(path) != value for path, value in zip(paths, before)):
        raise SystemExit("Configuration changed during setup; original files were preserved. Retry after your editor finishes")
    save_receipt(receipt, current)
    try:
        for path, old, new in zip(paths, before, after):
            if content(path) != old:
                raise OSError("Concurrent configuration change")
            if old != new:
                replace(path, new)
        current["status"] = "removed" if remove else "configured"
        current.pop("previous")
        current.pop("journal")
        save_receipt(receipt, current)
    except OSError:
        record("hooks.configure", status="write_failed")
        recover(receipt, read_receipt(receipt, required=True), paths, log, record)
        raise SystemExit("Paired hook setup did not finish; its writes were recovered. Retry after fixing write access; the private receipt/backups are available if recovery also fails") from None
    log("hooks.configured status=" + ("removed" if remove else "configured; review project and exact-hook trust, then open a fresh connection"))
    return [*paths, receipt]
