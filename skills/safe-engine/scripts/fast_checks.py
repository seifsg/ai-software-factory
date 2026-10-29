"""Reasoned proof selection and immutable check inputs; old runs keep their contract."""
import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

import fast_design as evidence

require, text, digest = evidence.require, evidence.text, evidence.digest


def enabled(run):
    """Only methods advertising this contract require the new receipts."""
    return bool(run.get("check_selection"))


def criteria(body):
    """Use the same ticket layout as existing live coverage checks."""
    import fast_record as record
    return list(dict.fromkeys(record.CRITERION.findall(record.under(body, record.DEFINITION))))


def contract(body):
    """Checklist ticks and activity do not change a ticket's confirmed requirements."""
    import fast_record as record
    return digest(record.under(body, record.DEFINITION).strip())


def selection(data, run):
    """Freeze every listed ticket, its pasted text and its reasoned proof route."""
    require(set(data) <= {"version", "tickets", "none_reason"}, "Unknown checks plan fields")
    require(type(data.get("version")) is int and data["version"] == 1 and isinstance(data.get("tickets"), list),
            "Checks plan needs version 1 and tickets")
    tickets = {}
    for row in data["tickets"]:
        require(isinstance(row, dict), "Checks ticket must be an object")
        require(set(row) <= {"url", "body", "category", "reason", "hidden", "owner_request"},
                "Unknown checks ticket fields; ownership is computed by the gate")
        url = text(row.get("url"), "ticket URL")
        parsed = urlsplit(url)
        require(parsed.scheme == "https" and parsed.netloc and parsed.path not in ("", "/")
                and not parsed.query and not parsed.fragment, "Use a listed ticket URL")
        require(url not in tickets, "Duplicate checks ticket")
        body = row.get("body")
        require(isinstance(body, str) and 0 < len(body) <= 100000, "Paste the complete issue body (max 100000 characters)")
        ids = criteria(body)
        require(ids, "Pasted issue needs labelled definition-of-done criteria")
        category = row.get("category")
        require(category in ("visual-port", "logic", "data", "safety", "mixed"), "Unknown proof category")
        hidden = row.get("hidden", category != "visual-port")
        require(type(hidden) is bool, "hidden must be boolean")
        require(hidden or category in ("visual-port", "logic"), "Data, safety and mixed tickets keep hidden checks")
        if not hidden and category == "visual-port":
            require(run.get("design_port") and run.get("show_first"), "Visual-only proof needs design-port coverage and Show")
        if hidden and category == "visual-port":
            text(row.get("owner_request"), "owner request adding visual hidden checks")
        tickets[url] = {**row, "hidden": hidden, "criteria": ids, "contract": contract(body),
                        "reason": text(row.get("reason"), "selection reason")}
    require(set(tickets) == set(run.get("tickets", [])), "Checks plan must cover exactly the run's listed tickets")
    if not tickets:
        text(data.get("none_reason"), "reason no ticket is required")
    return {"version": 1, "tickets": tickets, "none_reason": data.get("none_reason")}


def wanted(run):
    """Frozen ownership keeps another run's epic integration proof with its owner."""
    epic = next(iter(run.get("tickets", [])), None) if run.get("kind") != "change" else None
    return {f"{url}#{cid}" for url, row in run.get("checks", {}).get("plan", {}).get("tickets", {}).items()
            if row["hidden"] and (url != epic or row.get("owed", True)) for cid in row["criteria"]}


def freeze_ownership(run):
    """Pin verified integration ownership after plan freezes this run's todo IDs."""
    import fast_record as record
    tickets = run.get("checks", {}).get("plan", {}).get("tickets", {})
    epic = next(iter(run.get("tickets", [])), None) if run.get("kind") != "change" else None
    for url, row in tickets.items():
        holders, odd = record.integration({"url": url, "body": row["body"]}) if url == epic else (set(), None)
        row["integration_todos"] = sorted(holders)
        row["integration_ambiguous"] = bool(odd)
        row["owed"] = url != epic or bool(odd or not holders or holders & set(run.get("todos", [])))


def argv(value, label):
    """Explicit argument vectors only; artifact prose never becomes shell code."""
    require(isinstance(value, list) and 0 < len(value) <= 100, f"{label} needs an argument vector")
    return [text(arg, label) for arg in value]


def files(project, names):
    """Input hashes bind checks and declared dependencies without reading assertions into a brief."""
    require(isinstance(names, list) and 0 < len(names) <= 1000, "Check files need 1..1000 paths")
    paths = [evidence.local(project, name) for name in names]
    require(len(set(paths)) == len(paths), "Duplicate check input")
    return {path.relative_to(Path(project).resolve()).as_posix(): evidence.file_hash(path) for path in paths}


def environment(names):
    """Store hashes, not environment secrets; PATH and interpreter resolution always count."""
    require(isinstance(names, list) and all(isinstance(n, str) and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", n)
                                         for n in names), "environment names must be variable names")
    return {name: digest(os.environ.get(name)) for name in sorted(set(names) | {"PATH", "PYTHONPATH", "NODE_PATH"})}


def executable(command, project):
    """Bind the actual executable, not only its spelling in PATH."""
    found = shutil.which(command[0]) or str(Path(project, command[0]))
    path = Path(found).resolve(strict=True)
    require(path.is_file(), "Check executable is missing")
    return {"path": str(path), "sha256": evidence.file_hash(path)}


def prepare(project, run, data):
    """A checker supplies contracts and procedures before build; runtime names arrive afterward."""
    require(isinstance(run.get("checks", {}).get("plan"), dict), "Record checks --plan first")
    require(type(data.get("version")) is int and data["version"] == 1, "Check set version must be 1")
    text(data.get("checker"), "independent checker identity/source")
    text(data.get("interface"), "Interface")
    text(data.get("ports"), "Ports")
    rows = data.get("checks")
    require(isinstance(rows, list) and len(rows) <= 10000, "Check set needs a bounded checks list")
    found = {}
    for row in rows:
        require(isinstance(row, dict), "Each check must be an object")
        key = text(row.get("criterion"), "criterion URL#ID")
        require(key not in found, "Duplicate criterion check")
        if row.get("manual"):
            text(row["manual"], "manual procedure")
        else:
            paths = files(project, row.get("files"))
            require(all(Path(p).suffix in (".py", ".js", ".mjs", ".cjs", ".json") for p in paths),
                    "Automatic syntax supports Python, JavaScript and JSON; other tools need a written manual check")
            command = argv(row.get("argv"), "check argv")
            primary = evidence.local(project, row["files"][0])
            require(any(Path(project, arg).resolve() == primary for arg in command[1:] if not arg.startswith('-')),
                    "Check argv must name its first declared source file")
            require(type(row.get("timeout_seconds")) is int and 1 <= row["timeout_seconds"] <= 3600,
                    "Check timeout must be 1..3600 seconds")
            environment(row.get("environment", []))
        found[key] = row
    require(set(found) == wanted(run), "Check set must cover exactly the selected hidden criteria")
    return {**data, "checks": found, "plan": digest(run["checks"]["plan"])}


def identity(project, prepared):
    """Recompute mutable inputs before parsing, execution and completion."""
    result, executables = {}, {}
    for key, row in prepared["checks"].items():
        if not row.get("manual") and row["argv"][0] not in executables:
            executables[row["argv"][0]] = executable(row["argv"], project)
        result[key] = {"manual": row["manual"]} if row.get("manual") else {
            "files": files(project, row["files"]), "argv": row["argv"],
            "environment": environment(row.get("environment", [])), "executable": executables[row["argv"][0]]}
    return digest({"prepared": prepared, "inputs": result})


def runtime(project, run, data):
    """Bind actual captured accessible names or a non-UI explanation to the candidate."""
    require(data.get("candidate") == evidence.candidate(project), "Runtime names are for a different candidate")
    text(data.get("source"), "runtime capture source")
    if run.get("ui"):
        path = evidence.local(project, data.get("path"))
        require(0 < path.stat().st_size <= evidence.LIMIT, "Runtime accessibility snapshot is empty or oversized")
        hashed = evidence.file_hash(path)
        require(not data.get("sha256") or data["sha256"] == hashed, "Runtime names changed; capture and run again")
        return {**data, "sha256": hashed}
    text(data.get("not_applicable"), "reason accessible names do not apply")
    return data


def problems(run, project, final=False):
    """Missing, mutated or failed proof is a blocker; manual assertions remain explicit evidence."""
    if not enabled(run):
        return []
    try:
        state = run.get("checks", {})
        require(isinstance(state.get("plan"), dict), "Record reasoned selection with checks --plan before plan")
        if not final:
            return []
        selected = wanted(run)
        if selected:
            prepared, result = state.get("prepared"), state.get("result")
            require(isinstance(prepared, dict) and isinstance(result, dict), "Checks have not run on the build")
            require(result.get("passed") is True, "Checks failed, were interrupted or are harness-invalid; inspect retained logs")
            require(result["inputs"] == identity(project, prepared), "Check files, commands or environment changed; prepare/run again")
            require(result["candidate"] == evidence.candidate(project), "Build changed; run checks again")
            for log in result["logs"]:
                require(evidence.file_hash(evidence.local(project, log["path"])) == log["sha256"], "Check log changed")
            runtime(project, run, state["runtime"])
        if any(not row["hidden"] and row["category"] == "visual-port" for row in state["plan"]["tickets"].values()):
            require(not evidence.problems(run, project, final=True), "Visual proof needs current complete independent likeness")
            import fast_show
            require(not fast_show.completion_problems(run, project), "Visual proof needs current Show")
            require(run.get("show", {}).get("proof", {}).get("passed") is True, "Visual proof needs the declared suite pass")
        if any(not row["hidden"] and row["category"] == "logic" for row in state["plan"]["tickets"].values()):
            import fast_show
            holder = run.get("show" if fast_show.enabled(run) else "suite", {})
            require(run.get("suite_policy") and holder.get("proof", {}).get("passed") is True
                    and not fast_show.completion_problems(run, project),
                    "Covered logic needs current passing planned validation")
        return []
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Checks: {error}"]


def syntax_problems(run, project):
    """Authoring readiness needs syntax, never execution on an unfinished build."""
    if not wanted(run):
        return []
    try:
        state = run["checks"]
        require(state.get("syntax", {}).get("passed"), "Prepare syntactically valid hidden checks before done build")
        require(state["syntax"]["inputs"] == identity(project, state["prepared"]), "Checks changed; prepare them again")
        return []
    except (OSError, ValueError, TypeError, KeyError) as error:
        return [f"Checks: {error}"]


def refreshed(run, ticket):
    """Compare live requirements and semantic ownership; ignore progress edits."""
    row = run.get("checks", {}).get("plan", {}).get("tickets", {}).get(ticket["url"])
    if row is None or row["contract"] != contract(ticket["body"]):
        return "proof selection differs from current ticket criteria; revise the plan explicitly"
    if ticket["url"] == next(iter(run.get("tickets", [])), None) and run.get("kind") != "change":
        import fast_record as record
        holders, odd = record.integration(ticket)
        if (row.get("integration_todos") != sorted(holders)
                or row.get("integration_ambiguous") != bool(odd)):
            return "integration ownership differs from the frozen plan; reconfirm proof selection"
    return None


def verify_plan(run, ticket):
    """Verify the pasted ownership used by freeze against the current live ticket."""
    row = run["checks"]["plan"]["tickets"].get(ticket["url"])
    if row is None or row["contract"] != contract(ticket["body"]):
        return "proof selection differs from current ticket criteria; revise the plan explicitly"
    if ticket["url"] == next(iter(run.get("tickets", [])), None) and run.get("kind") != "change":
        import fast_record as record
        pasted, pasted_odd = record.integration({"url": ticket["url"], "body": row["body"]})
        holders, odd = record.integration(ticket)
        if pasted != holders or bool(pasted_odd) != bool(odd):
            return "pasted integration ownership differs from the live ticket; revise the plan"
    return None


def verdict_problems(run, body, record):
    """Every selected hidden criterion still needs its checker's explicit verdict."""
    import fast_briefs
    plan = run["checks"]["plan"]["tickets"]
    entry = r"(https://[^\s,]+#[A-Z]{1,3}\d+|#\d+[ \t]+[A-Z]{1,3}\d+):[ \t]*((?:PASS|FAIL|DEFERRED)(?:[ \t]+\([^()\n]*\))?)"
    line = re.compile(rf"{record.BULLET}{entry}(?:[ \t]*,[ \t]*{entry})*[ \t]*")
    entries, unreadable = [], []
    for raw_line in "\n".join(record.HIDDEN.findall(body)).splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        found = re.findall(entry, raw_line) if line.fullmatch(raw_line) else []
        if not found or any(value.startswith("DEFERRED") and not (run.get("briefs") and fast_briefs.DEFER.fullmatch(value))
                            for _, value in found):
            unreadable.append(raw_line)
            continue
        for key, value in found:
            if key.startswith("#"):
                number, cid = key[1:].split()
                matches = [f"{url}#{cid}" for url in plan if (record.ISSUE.fullmatch(url) or [None, None, None])[2] == number]
                if len(matches) != 1:
                    unreadable.append(raw_line)
                    continue
                key = matches[0]
            entries.append((key, value))
    problems = []
    if any(value.startswith("FAIL") for _, value in entries):
        problems.append("Hidden checks contain FAIL; fix the build and rerun")
    if len({key for key, _ in entries}) != len(entries):
        problems.append("Duplicate hidden-check verdict; keep one final entry per criterion")
    found = {key: value for key, value in entries}
    extra = sorted(set(found) - wanted(run))
    if extra:
        problems.append("Hidden-check verdict belongs outside this run: " + ", ".join(extra))
    missing = [key for key in wanted(run) if not found.get(key)]
    altered = [key for key, observation in run.get("checks", {}).get("observations", {}).items()
               if key in found and found[key].split(maxsplit=1)[0] != observation["verdict"]]
    return problems + [f"unreadable hidden-check entry: {line}; write '<ticket>#<ID>: <verdict>'" for line in unreadable] + (
        ["Manual verdict differs from recorded observation: " + ", ".join(altered)] if altered else []) + (
        ["Hidden criteria missing or failed: " + ", ".join(sorted(missing))] if missing else [])
