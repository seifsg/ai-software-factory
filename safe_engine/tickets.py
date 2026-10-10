"""Canonical remote tickets, imported observations and durable worktree ownership.

The host agent owns MCP reads/writes. Local records neither authenticate a human
nor prove a connector call occurred. They bind the supplied evidence, not the host.
"""

from datetime import datetime, timezone
import json
import re
from urllib.parse import urlsplit

from .project import EngineError, digest, git, git_dirs, reject_path_aliases
from .storage import atomic_json, locked, now, read_json


START = "<!-- safe-engine-ticket:v1 -->"
END = "<!-- /safe-engine-ticket -->"
WRITING_FIELDS = ("purpose", "goal", "context", "approach")
CHECKLIST_NOTE = "Ticked through the ticket contract; a box clicked here blocks the next import until re-rendered."
DONE_HEADINGS = ("Definition of done", "Done when")  # current, then the heading older bodies carry


def ticket_key(value):
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value) or value in reserved:
        raise EngineError("Ticket key needs lowercase letters/digits/hyphens; start with a letter")
    return value


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise EngineError(f"Ticket needs {name}")
    return value


def timestamp(value):
    try:
        # Python 3.9/3.10 parse only 3 or 6 fractional digits; pad 1-6 to six.
        value = re.sub(r"\.(\d{1,6})(?=[+-]|$)", lambda match: "." + match[1].ljust(6, "0"),
                       value.replace("Z", "+00:00"))
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
            raise ValueError()
        return parsed
    except (AttributeError, TypeError, ValueError) as error:
        raise EngineError("Ticket timestamps need a timezone and cannot be in the future") from error


def validate_contract(contract):
    if not isinstance(contract, dict) or type(contract.get("revision")) is not int or contract["revision"] < 1:
        raise EngineError("Ticket contract needs a positive revision")
    if contract.get("lifecycle") not in ("ready", "active", "blocked", "done", "cancelled"):
        raise EngineError("Ticket contract needs ready/active/blocked/done/cancelled lifecycle")
    scope = contract.get("scope")
    if not isinstance(scope, dict):
        raise EngineError("Ticket contract needs scope")
    for name in ("original_request", "before", "after", "completion"):
        text(scope.get(name), name)
    if contract.get("presentation") == "visual":
        for name in WRITING_FIELDS:
            text(scope.get(name), name)
        text(contract.get("progress"), "progress")
        activity = contract.get("activity", [])
        if not isinstance(activity, list):
            raise EngineError("Ticket activity must be a list")
        for item in activity:
            if not isinstance(item, dict):
                raise EngineError("Ticket activity needs dated actions and results")
            for name in ("at", "actor", "what", "why", "result"):
                text(item.get(name), f"activity {name}")
        if "flow" in scope:
            text(scope["flow"], "flow")
        if "optional" in scope and (not isinstance(scope["optional"], list)
                or any(not isinstance(v, str) or not v.strip() for v in scope["optional"])):
            raise EngineError("Ticket optional wants must be an explicit text array")
    inputs = scope.get("owner_input")
    if not isinstance(inputs, list) or not inputs:
        raise EngineError("Preserve owner input with its source")
    for item in inputs:
        if not isinstance(item, dict):
            raise EngineError("Owner input must include text and source")
        text(item.get("text"), "owner input text")
        text(item.get("source"), "owner input source")
    for name in ("journeys", "exclusions", "constraints", "dependencies"):
        values = scope.get(name)
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise EngineError(f"Ticket {name} must be an explicit text array")
        if name == "dependencies":
            for value in values:
                ticket_key(value)
            if len(set(values)) != len(values):
                raise EngineError("Duplicate ticket dependencies")
        if name == "journeys" and not values:
            raise EngineError("Ticket needs at least one owner-visible or enabling-contract journey")
    criteria = scope.get("acceptance")
    if not isinstance(criteria, list) or not criteria:
        raise EngineError("Ticket needs acceptance criteria")
    seen = set()
    for item in criteria:
        if not isinstance(item, dict):
            raise EngineError("Ticket criteria need id/text")
        identifier = text(item.get("id"), "criterion id")
        text(item.get("text"), "criterion text")
        if identifier in seen:
            raise EngineError("Duplicate ticket criterion")
        seen.add(identifier)
    if scope.get("epic") is not None:
        text(scope["epic"], "epic reference")
    if "checklist" in contract:
        validate_checklist(contract["checklist"])
    return contract


def validate_checklist(items):
    """Todo items outside the confirmed scope; a ticked item carries its proof."""
    if not isinstance(items, list):
        raise EngineError("Ticket checklist must be a list")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or type(item.get("done")) is not bool:
            raise EngineError("Checklist items need id, text and a done flag")
        identifier = text(item.get("id"), "checklist id")
        text(item.get("text"), "checklist text")
        if item["done"]:
            text(item.get("proof"), "checklist proof")
        if identifier in seen:
            raise EngineError("Duplicate checklist item")
        seen.add(identifier)


def checklist_lines(contract):
    """Task-list lines rendered from the contract, one per item."""
    def line(value):
        return " ".join(value.split())
    return "\n".join(f"- [{'x' if item['done'] else ' '}] {line(item['id'])} {line(item['text'])}"
                     + (f" Proof: {line(item['proof'])}" if item["done"] else "")
                     for item in contract.get("checklist", []))


def scope_digest(contract):
    return digest({"revision": contract["revision"], "scope": contract["scope"]})


def table_cell(value):
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("|", "\\|").replace("\n", "<br>")


def visual_projection(contract, done_heading=DONE_HEADINGS[0]):
    scope = contract["scope"]
    sections = [
        f"## 🎯 Purpose & goal\n\n- **Purpose:** {scope['purpose']}\n- **Goal:** {scope['goal']}",
        f"## 📍 Context\n\n{scope['context']}",
        ("## 🔧 What & why\n\n| Before | After |\n|---|---|\n"
         f"| {table_cell(scope['before'])} | {table_cell(scope['after'])} |\n\n"
         f"- **Approach:** {scope['approach']}"),
    ]
    journeys = "\n".join(f"- {value}" for value in scope["journeys"])
    flow = f"```text\n{scope['flow']}\n```\n\n" if "flow" in scope else ""
    sections.append(f"## 🔀 Journey\n\n{flow}{journeys}")
    criteria = "\n".join(f"- **{c['id']}:** {c['text']}" for c in scope["acceptance"])
    sections.append(f"## ✅ {done_heading}\n\n{criteria}")
    if contract.get("checklist"):
        sections.append(f"## ☑️ Checklist\n\n{CHECKLIST_NOTE}\n\n{checklist_lines(contract)}")
    guards = []
    for label, values in (("Keep", scope["constraints"]), ("Avoid / out", scope["exclusions"]),
                          ("Nice to have", scope.get("optional", [])), ("Depends on", scope["dependencies"])):
        guards.extend(f"- **{label}:** {value}" for value in values)
    guards.append(f"- **Finish:** {scope['completion']}")
    if scope.get("epic"):
        guards.append(f"- **Epic:** {scope['epic']}")
    sections.append("## 🧱 Scope & guardrails\n\n" + "\n".join(guards))
    sections.append(f"## 🚦 Progress\n\n{contract['progress']}")
    if contract.get("activity"):
        rows = []
        for item in contract["activity"]:
            rows.append(f"| {table_cell(item['at'])}<br>{table_cell(item['actor'])} | "
                        f"{table_cell(item['what'])}<br>**Reason:** {table_cell(item['why'])} | "
                        f"{table_cell(item['result'])} |")
        sections.append("## 📝 Activity\n\n| When / who | Change / reason | Result / next |\n|---|---|---|\n"
                        + "\n".join(rows))
    return "\n\n".join(sections) + "\n\n"


def render_ticket(contract, *, fold_contract=True, layout="auto", done_heading=DONE_HEADINGS[0]):
    """Readable projection and machine contract must agree; no ignored prose edits."""
    validate_contract(contract)
    scope = contract["scope"]
    if layout not in ("auto", "legacy"):
        raise EngineError("Ticket layout must be auto or legacy")
    if layout == "auto" and contract.get("presentation") == "visual":
        projection = visual_projection(contract, done_heading)
    else:
        criteria = "\n".join(f"- {c['id']}: {c['text']}" for c in scope["acceptance"])
        checklist = f"## Checklist\n\n{CHECKLIST_NOTE}\n\n{checklist_lines(contract)}\n\n" if contract.get("checklist") else ""
        projection = (f"## Before\n\n{scope['before']}\n\n## After\n\n{scope['after']}\n\n"
                      f"## Acceptance\n\n{criteria}\n\n{checklist}")
    payload = (f"{START}\n```json\n{json.dumps(contract, indent=2, ensure_ascii=False)}\n"
               f"```\n{END}\n")
    if fold_contract:
        payload = ("<details>\n<summary>Full contract: owner input, journeys and history</summary>\n\n"
                   f"{payload}\n</details>\n")
    return projection + payload


def parse_body(body):
    if isinstance(body, str):
        body = body.replace("\r\n", "\n")
    if not isinstance(body, str) or body.count(START) != 1 or body.count(END) != 1:
        raise EngineError("Remote body needs one Safe Engine ticket contract; reconcile raw owner edits first")
    payload = body.split(START)[1].split(END)[0].strip()
    if not payload.startswith("```json\n") or not payload.endswith("\n```"):
        raise EngineError("Ticket contract must be a fenced JSON block")
    contract = validate_contract(json.loads(payload[8:-4]))
    normalized = body.strip()
    if not any(normalized == render_ticket(contract, fold_contract=folded, layout=layout,
                                           done_heading=heading).strip()
               for layout in ("auto", "legacy") for folded in (True, False) for heading in DONE_HEADINGS):
        raise EngineError("Remote prose differs from the contract; reconcile and confirm changed expectations")
    return contract


def binding(capture):
    contract = capture["contract"]
    confirmation = contract.get("confirmation")
    expected = scope_digest(contract)
    if not isinstance(confirmation, dict) or confirmation.get("revision") != contract["revision"] or confirmation.get("digest") != expected:
        raise EngineError("Owner must confirm this exact ticket revision/digest before implementation")
    for name in ("actor", "source", "statement", "at"):
        text(confirmation.get(name), f"confirmation {name}")
    if timestamp(confirmation["at"]) > timestamp(capture["observed_at"]):
        raise EngineError("Owner confirmation cannot postdate the remote observation")
    return {"key": capture["key"], "identity": capture["identity"], "revision": contract["revision"],
            "scope_digest": expected, "confirmation": confirmation, "scope": contract["scope"]}


class TicketStore:
    def __init__(self, project):
        self.project = project
        self.common = git_dirs(project)[1]
        self.root = self.common / "safe-engine" / "tickets"
        reject_path_aliases(self.root, self.common)

    def path(self, key):
        path = self.root / "captures" / f"{ticket_key(key)}.json"
        reject_path_aliases(path, self.common)
        return path

    def get(self, key):
        return read_json(self.path(key))

    def failed(self, key, reason):
        path = self.path(key)
        if path.exists():
            with locked(self.root / "coordination"):
                capture = read_json(path)
                capture.update(valid=False, refresh_error=text(reason, "refresh failure reason"))
                atomic_json(path, capture)

    def capture(self, supplied):
        key = ticket_key(supplied.get("key"))
        try:
            if supplied.get("version") != 1 or supplied.get("complete") is not True:
                raise EngineError("Capture requires the complete remote body and paginated activity")
            identity = supplied.get("identity")
            if not isinstance(identity, dict) or set(identity) != {"provider", "workspace", "id", "url"}:
                raise EngineError("Ticket needs provider/workspace/id/url")
            for name in ("provider", "workspace", "id", "url"):
                text(identity.get(name), f"identity {name}")
            url = urlsplit(identity["url"])
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise EngineError("Ticket URL must use HTTPS")
            if identity["provider"] == "github" and (url.hostname != "github.com"
                    or url.path != f"/{identity['workspace']}/issues/{identity['id']}"
                    or not re.fullmatch(r"[1-9][0-9]*", identity["id"]) or url.query or url.fragment):
                raise EngineError("GitHub identity must name its actual repository issue URL")
            observed = timestamp(supplied.get("observed_at"))
            updated = timestamp(supplied.get("remote_updated_at"))
            if updated > observed:
                raise EngineError("Observe the remote ticket after its last update")
            transport = supplied.get("transport")
            if not isinstance(transport, dict):
                raise EngineError("Capture needs actual tool and source provenance")
            text(transport.get("tool"), "transport tool")
            text(transport.get("source"), "transport source")
            text(supplied.get("title"), "remote title")
            text(supplied.get("status"), "remote status")
            contract = parse_body(supplied.get("body"))
            activity = supplied.get("activity")
            if not isinstance(activity, list):
                raise EngineError("Capture all activity, including an explicit empty array")
            pending, ids = [], set()
            for item in activity:
                if not isinstance(item, dict):
                    raise EngineError("Activity needs id/at/author/text/disposition")
                identifier = text(item.get("id"), "activity id")
                if identifier in ids:
                    raise EngineError("Duplicate activity id")
                ids.add(identifier)
                for name in ("author", "text"):
                    text(item.get(name), f"activity {name}")
                if timestamp(item.get("at")) > observed:
                    raise EngineError("Activity is newer than the observation")
                if item.get("disposition") not in ("non-scope", "resolved", "pending"):
                    raise EngineError("Classify every activity entry; unreviewed scope stays pending")
                if item["disposition"] == "pending":
                    pending.append(identifier)
                else:
                    text(item.get("reason"), "activity disposition reason/source")
            with locked(self.root / "coordination"):
                path = self.path(key)
                previous = read_json(path) if path.exists() else None
                history = self.root / "history" / key
                reject_path_aliases(history, self.common)
                if previous is None and history.exists() and any(history.glob("*.json")):
                    raise EngineError("Current ticket cache is missing; recover its preserved history before capture")
                if previous:
                    if previous["identity"] != identity:
                        raise EngineError("Ticket identity is immutable; do not reuse its key")
                    if observed <= timestamp(previous["observed_at"]) or updated < timestamp(previous["remote_updated_at"]):
                        raise EngineError("Older/replayed remote observations cannot replace the current snapshot")
                    old = previous["contract"]
                    if contract["scope"]["original_request"] != old["scope"]["original_request"]:
                        raise EngineError("Preserve the original owner request")
                    if contract["revision"] < old["revision"] or (scope_digest(contract) != scope_digest(old) and contract["revision"] == old["revision"]):
                        raise EngineError("Scope changes need a new revision; never rewrite one")
                    old_inputs = old["scope"]["owner_input"]
                    if contract["scope"]["owner_input"][:len(old_inputs)] != old_inputs:
                        raise EngineError("Append owner changes; preserve original/superseded input")
                    if not {item["id"] for item in previous["activity"]} <= ids:
                        raise EngineError("Activity vanished; reconcile deleted entries with preserved tracker history")
                index_path = self.root / "identity-index.json"
                reject_path_aliases(index_path, self.common)
                index = read_json(index_path) if index_path.exists() else {}
                identity_id = digest({k: identity[k].casefold() for k in ("provider", "workspace", "id")})
                if index.get(identity_id, key) != key:
                    raise EngineError("This remote ticket already has a key; resume its lineage")
                for other in (self.root / "captures").glob("*.json"):
                    reject_path_aliases(other, self.common)
                    other_capture = read_json(other)
                    if other.stem != key and all(other_capture["identity"][k].casefold() == identity[k].casefold() for k in ("provider", "workspace", "id")):
                        raise EngineError("This remote ticket already has a key; resume its lineage")
                sequence = previous["sequence"] + 1 if previous else 1
                record = {**supplied, "contract": contract, "pending": pending,
                          "sequence": sequence, "valid": True, "captured_at": now(),
                          "raw_digest": digest({name: supplied[name] for name in ("body", "activity", "title", "status", "identity")})}
                self.history_path(key, sequence)
                index[identity_id] = key
                atomic_json(index_path, index)
                return self.append(key, record)
        except (EngineError, ValueError, KeyError, TypeError) as error:
            self.failed(key, str(error))
            raise EngineError(str(error)) from error

    def unchanged(self, supplied):
        """Cheap refresh: remote updated_at/status equal the current capture's; any change needs a full capture."""
        key = ticket_key(supplied.get("key"))
        try:
            if supplied.get("version") != 1 or supplied.get("unchanged") is not True:
                raise EngineError("Unchanged observation needs version 1 and unchanged: true")
            observed = timestamp(supplied.get("observed_at"))
            updated = timestamp(supplied.get("remote_updated_at"))
            transport = supplied.get("transport")
            if not isinstance(transport, dict):
                raise EngineError("Observation needs actual tool and source provenance")
            text(transport.get("tool"), "transport tool")
            text(transport.get("source"), "transport source")
            with locked(self.root / "coordination"):
                if not self.path(key).exists():
                    raise EngineError("No current capture; import a complete capture first")
                previous = read_json(self.path(key))
                if not previous["valid"] or previous["pending"]:
                    raise EngineError("Invalid or pending captures need a complete capture")
                if updated != timestamp(previous["remote_updated_at"]) or supplied.get("status") != previous["status"]:
                    raise EngineError("Remote ticket changed since its capture; import a complete capture")
                if observed <= timestamp(previous["observed_at"]):
                    raise EngineError("Older/replayed remote observations cannot replace the current snapshot")
                sequence = previous["sequence"] + 1
                return self.append(key, {**previous, "observed_at": supplied["observed_at"], "transport": transport,
                                         "sequence": sequence, "captured_at": now(),
                                         "unchanged_from": previous["sequence"]})
        except (EngineError, ValueError, KeyError, TypeError) as error:
            self.failed(key, str(error))
            raise EngineError(str(error)) from error

    def history_path(self, key, sequence):
        path = self.root / "history" / key / f"{sequence:06d}.json"
        reject_path_aliases(path, self.common)
        if path.exists():
            raise EngineError("Preserve numbered ticket history; reconcile sequence before importing")
        return path

    def append(self, key, record):
        """Numbered immutable history, then the current snapshot; the caller holds the lock."""
        atomic_json(self.history_path(key, record["sequence"]), record)
        atomic_json(self.path(key), record)
        return self.status(key)

    def status(self, key):
        record = self.get(key)
        try:
            confirmed = binding(record)
        except EngineError:
            confirmed = None
        return {"key": key, "identity": record["identity"], "revision": record["contract"]["revision"],
                "scope_digest": scope_digest(record["contract"]), "confirmed": bool(confirmed),
                "valid": record["valid"], "pending": record["pending"], "sequence": record["sequence"],
                "lifecycle": record["contract"]["lifecycle"], "remote_status": record["status"],
                "observed_at": record["observed_at"], "refresh_error": record.get("refresh_error"),
                "freshness_limit": "Imported MCP evidence, not authenticated live access or owner identity"}

    def ready(self, key, dependency=False):
        record = self.get(key)
        if not record["valid"] or record["pending"]:
            raise EngineError("Refresh/reconcile the canonical ticket; unresolved owner activity blocks progression")
        if record["contract"]["lifecycle"] not in (("ready", "active", "done") if dependency else ("ready", "active")):
            raise EngineError("Canonical ticket is blocked/cancelled/done; preserve its history and owner stop")
        if not dependency and record["identity"]["provider"] == "github" and record["status"] != "open":
            raise EngineError("Closed GitHub tickets cannot silently resume implementation")
        return record, binding(record)

    def dependencies(self, key, visiting=None, after=None, dependency=False):
        visiting = set() if visiting is None else visiting
        if key in visiting:
            raise EngineError("Ticket dependency cycle")
        record, _ = self.ready(key, dependency=dependency)
        if after is not None and timestamp(record["observed_at"]) <= timestamp(after):
            raise EngineError("Refresh ticket/dependency observations after the saved phase boundary")
        for dependency in record["contract"]["scope"]["dependencies"]:
            self.dependencies(dependency, visiting | {key}, after=after, dependency=True)
            item, accepted = self.ready(dependency, dependency=True)
            delivery = item["contract"].get("delivery")
            if (not isinstance(delivery, dict) or delivery.get("status") != "integrated"
                    or delivery.get("scope_digest") != accepted["scope_digest"]
                    or not re.fullmatch(r"[0-9a-f]{40}", delivery.get("commit", ""))):
                raise EngineError(f"Dependency {dependency} needs accepted scope and integrated commit, not closed status")
            text(delivery.get("evidence"), "dependency acceptance/cloud-review evidence")
            try:
                git(self.project, "merge-base", "--is-ancestor", delivery["commit"], "HEAD")
            except EngineError as error:  # name the commit; "Git command failed" told the builder nothing
                if str(error) != "Git command failed":  # not a plain "no": missing object, timeout
                    raise EngineError(f"Dependency {dependency}: cannot check delivered commit {delivery['commit']} "
                                      f"({error}); fetch it, then rerun") from error
                raise EngineError(f"Dependency {dependency}: delivered commit {delivery['commit']} is not in this "
                                  "branch's history; branch from it or merge it (several dependencies: merge each), "
                                  "then rerun") from error

    def claim(self, key, run_id, directory):
        """Durable lineage and one active writer per physical checkout; no time expiry."""
        with locked(self.root / "coordination"):
            path = self.root / "claims.json"
            reject_path_aliases(path, self.common)
            claims = read_json(path) if path.exists() else {}
            owner = {"project": str(self.project), "directory": str(directory), "run_id": run_id}
            previous = claims.get(key)
            if previous and any(previous.get(k) != v for k, v in owner.items()):
                raise EngineError("This ticket already owns a run; preserve/resume its history, never fresh-run bypass")
            for other, claim in claims.items():
                if other != key and claim.get("active") and claim["project"] == str(self.project):
                    raise EngineError("Another ticket owns this checkout; use another worktree or finish/release it")
            claims[key] = {**owner, "active": True}
            atomic_json(path, claims)

    def release(self, key, run_id):
        with locked(self.root / "coordination"):
            path = self.root / "claims.json"
            reject_path_aliases(path, self.common)
            claims = read_json(path)
            if claims.get(key, {}).get("run_id") != run_id:
                raise EngineError("Ticket writer identity changed")
            claims[key]["active"] = False
            atomic_json(path, claims)

    def abandon_empty_reservation(self, key, run_id, directory):
        """Only an unsuccessful first save with no state/history may undo its own claim."""
        with locked(self.root / "coordination"):
            path = self.root / "claims.json"
            reject_path_aliases(path, self.common)
            claims = read_json(path)
            if (claims.get(key, {}).get("run_id") == run_id and not (directory / "state.json").exists()
                    and not any((directory / "history").glob("*.json"))):
                del claims[key]
                atomic_json(path, claims)

    def block_legacy_writer(self):
        if any((self.project / ".factory/runs").glob("*/state.json")):
            raise EngineError("This checkout contains ticket runs; use --ticket or an independent legacy worktree")
        path = self.root / "claims.json"
        if path.exists():
            claims = read_json(path)
            if any(c.get("active") and c["project"] == str(self.project) for c in claims.values()):
                raise EngineError("A ticket owns this checkout; resume it with --ticket")
