"""Immutable helper generations; terminal receipts outrank stale host observations."""
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import uuid

import fast_ledger as ledger
import fast_hosts as hosts

LIMIT, BYTES = 256, 16384
TOKEN = re.compile(r"[0-9a-f]{32}")
FIELDS = {"version", "coordinator", "job", "name", "kind", "host", "wakeup", "source", "observed_at", "expires_at"}
IDENTITY = {"run", "coordinator", "job", "generation"}
TERMINAL = {"completed", "failed", "cancelled"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def word(value, name, limit=240):
    require(isinstance(value, str) and not any(ord(c) < 32 for c in value),
            f"{name}: supply bounded, nonempty single-line text")
    value = value.strip()
    require(0 < len(value) <= limit, f"{name}: supply bounded, nonempty single-line text")
    return value


def storable(value):
    """Check the exact ledger encoding before creating an immutable receipt."""
    require(len((json.dumps(value, indent=2) + "\n").encode("utf-8")) <= BYTES,
            "Wait receipt would exceed the read limit")
    return value


def instant(value):
    """Only explicit timezone timestamps can define the observation's finite lifetime."""
    parsed = datetime.fromisoformat(word(value, "timestamp", 40).replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Timestamp needs an explicit timezone")
    return parsed.timestamp()


def clock():
    return datetime.now(timezone.utc).timestamp()


def read(path):
    with Path(path).open("rb") as source:
        raw = source.read(BYTES + 1)
    require(len(raw) <= BYTES, "Wait receipt is too large")
    data = json.loads(raw.decode("utf-8-sig"))
    require(isinstance(data, dict), "Wait input must be an object")
    return data


def location(home, run):
    """Names derive from the current protected run, never a supplied destination path."""
    require(not run.get("lost") and TOKEN.fullmatch(str(run.get("pr_instance"))),
            "Wait needs a readable current run with its unique instance")
    key = hashlib.sha256(ledger.norm(run["project"]).encode()).hexdigest()[:24]
    return Path(home) / "waits" / key / run["pr_instance"]


def registration(data, current=None):
    require(set(data) == FIELDS and type(data.get("version")) is int and data["version"] == 1,
            "Wait registration needs exactly the documented version 1 fields")
    data = dict(data)
    for name in ("coordinator", "job", "name", "host", "wakeup", "source", "observed_at", "expires_at"):
        data[name] = word(data[name], name, 120 if name == "name" else 40 if name.endswith("_at") else 240)
    require(data["kind"] in ("helper", "job"), "Only finite helpers or jobs can be registered")
    require(data["wakeup"] in ("native-subagent-result", "none"), "Unknown completion route")
    observed, expires = instant(data["observed_at"]), instant(data["expires_at"])
    require(0 < expires - observed <= 86400, "Wait lifetime must be positive and at most 24 hours")
    if current is not None:
        require(current - 300 <= observed <= current and expires > current,
                "Observe the running job now; timestamps cannot be future, stale or expired")
    return data


def entries(directory):
    paths = list(itertools.islice(directory.glob("*.pending.json"), LIMIT + 1))
    require(len(paths) <= LIMIT, "Too many wait receipts; inspect this run before continuing")
    return sorted(paths)


def pending(path, run):
    value = read(path)
    require(set(value) == FIELDS | {"run", "generation", "created"}, "Invalid stored wait fields")
    registration({key: value[key] for key in FIELDS})
    require(value["run"] == run["pr_instance"] and TOKEN.fullmatch(str(value["generation"]))
            and path.name == value["generation"] + ".pending.json", "Wait belongs to another run or generation")
    instant(value["created"])
    return value


def completion(data, item):
    require(set(data) == IDENTITY | {"version", "status", "source"}
            and type(data.get("version")) is int and data["version"] == 1, "Invalid completion fields")
    require(all(data[key] == item[key] for key in IDENTITY), "Completion identity does not match this helper generation")
    require(data["status"] in TERMINAL, "Completion must be completed, failed or cancelled")
    return {**data, "source": word(data["source"], "completion source")}


def terminal(directory, item, include_at=False):
    path = directory / (item["generation"] + ".terminal.json")
    if not path.exists():
        return None
    value = read(path)
    require("at" in value, "Completion timestamp missing")
    at = instant(value["at"])
    result = completion({key: value[key] for key in value if key != "at"}, item)
    return {**result, "at": at} if include_at else result


def add(home, run, data):
    """Caller holds the selection lock: duplicate jobs cannot acquire competing pending generations."""
    data = registration(data, clock())
    directory = location(home, run)
    found = entries(directory)
    require(len(found) < LIMIT, "This run reached 256 wait generations; finish it before starting another")
    for path in found:
        item = pending(path, run)
        if item["coordinator"] == data["coordinator"] and item["job"] == data["job"]:
            require(terminal(directory, item) is not None, "Job already registered; finish its generation before reuse")
    value = {**data, "run": run["pr_instance"], "generation": uuid.uuid4().hex,
             "created": datetime.now(timezone.utc).isoformat()}
    ledger.save(directory / (value["generation"] + ".pending.json"), storable(value), new=True)
    try:
        import fast_metrics
        fast_metrics.safe(
            "emit_wait",
            run["project"],
            run["key"],
            "start",
            "helper",
            event_id=f"wait-{value['generation']}",
            job=value.get("job"),
            name=value.get("name"),
        )
    except Exception:
        pass
    return {key: value[key] for key in IDENTITY}


def finish(home, run, data):
    """Append a terminal receipt only; callbacks never rewrite coordinator run state."""
    token = data.get("generation")
    require(isinstance(token, str) and TOKEN.fullmatch(token), "Invalid completion generation")
    directory = location(home, run)
    item = pending(directory / (token + ".pending.json"), run)
    value = completion(data, item)
    path = directory / (token + ".terminal.json")
    finished_at = datetime.now(timezone.utc).isoformat()
    try:
        ledger.save(path, storable({**value, "at": finished_at}), new=True)
    except FileExistsError:
        require(terminal(directory, item) == value, "Conflicting completion; original terminal result retained")
    try:
        import fast_metrics
        created = instant(item["created"])
        ended = instant(finished_at)
        duration = max(0.0, (ended - created).total_seconds())
        fast_metrics.safe(
            "emit_wait",
            run["project"],
            run["key"],
            "finish",
            "helper",
            event_id=f"wait-{token}-end",
            parent_id=f"wait-{token}",
            status=value["status"],
            duration_seconds=round(duration, 3),
        )
    except Exception:
        pass
    return value["status"]


def state(home, run, session=None, observations=None):
    """A bad, stale or unsupported observation cannot grant a quiet wait."""
    result = {"recorded": False, "pending": [], "finished": [], "problems": [], "latest_completed_at": None}
    if run.get("closed") or run.get("paused"):
        return result
    try:
        directory = location(home, run)
        result["recorded"] = directory.exists()
        current = clock()
        for path in entries(directory):
            item = pending(path, run)
            if session is not None and item["coordinator"] != session:
                continue
            done = terminal(directory, item, include_at=True)
            if done is not None:
                result["finished"].append(f"{item['name']} ({done['status']})")
                result["latest_completed_at"] = max(result["latest_completed_at"] or done["at"], done["at"])
            elif any(isinstance(seen, dict) and seen.get("id") == item["job"]
                     and (not seen.get("run") or seen.get("observer") or seen.get("persistent")
                          or seen.get("type") not in hosts.WAKERS)
                     for seen in (observations or [])):
                result["problems"].append(f"{item['name']}: host reports no finite running helper; reconcile its completion")
            elif not instant(item["created"]) <= current < instant(item["expires_at"]):
                result["problems"].append(f"{item['name']}: observation expired or clock moved backward")
            elif not hosts.completion_route(item["host"], item["kind"], item["wakeup"]):
                result["problems"].append(f"{item['name']}: no supported completion wakeup; use the host wait tool")
            else:
                result["pending"].append(item["name"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["problems"].append(f"Wait state unknown: {error}")
    return result


def suppress_report(waiting, report):
    """Hide directions while work is pending or until a newer report follows completion."""
    if waiting["pending"] or waiting["problems"]:
        return True
    completed = waiting["latest_completed_at"]
    if completed is None:
        return False
    try:
        return instant((report or {}).get("at")) <= completed
    except (ValueError, TypeError):
        return True


def describe(value):
    prefix = "Waiting on helpers: " + ", ".join(value["pending"]) if value["pending"] else "No pending helpers."
    return "\n".join([prefix, *value["problems"], *(["Reported: " + ", ".join(value["finished"])] if value["finished"] else [])])


def blocked(event, runs, session, gate):
    """Every owned unfinished run must have its own eligible wait; old host observations stay legacy-only."""
    waiting = []
    for _, _, run in runs:
        if run.get("paused") or run.get("closed"):
            continue
        value = state(gate.HOME, run, session, event.get("observations"))
        explicit = run.get("wait_receipts") or value["recorded"]
        if (not run.get("lost") and session and explicit and value["pending"] and not value["problems"]):
            waiting.extend(value["pending"])
            continue
        if not explicit and not run.get("lost") and event.get("waiting"):
            waiting.append("host-reported background work")
            continue
        return run
    if waiting:
        event["wait_message"] = "Waiting on helpers: " + ", ".join(dict.fromkeys(waiting)) + ". Completion results resume the work."
        gate.log("hook.wait_stop", pending=waiting)
    return None
