"""Current, owner-visible picture evidence before a UI run's expensive proof."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import fast_design as evidence

VARIANTS = {(theme, device) for theme in ("light", "dark") for device in ("desktop", "phone")}
VIEWPORTS = {"desktop": [1280, 800], "phone": [390, 844]}


def enabled(run):
    """Only new UI runs use this checkpoint; old and non-UI runs retain their order."""
    return bool(run.get("show_first") and run.get("ui"))


def integer(value, name, low, high):
    """Reject ambiguous timer values before a run starts waiting."""
    evidence.require(type(value) is int and low <= value <= high, f"{name}: needs {low}..{high}")
    return value


def plan(data):
    """Freeze changed surfaces, the exact suite and the configured owner-response window."""
    evidence.require(type(data.get("version")) is int and data["version"] == 1, "Show plan version must be 1")
    surfaces = evidence.rows(data.get("surfaces"), "surfaces")
    suite = data.get("full_suite")
    evidence.require(isinstance(suite, list) and 0 < len(suite) <= 100, "full_suite needs an argv list")
    sizes = data.get("viewports", VIEWPORTS)
    evidence.require(isinstance(sizes, dict) and set(sizes) == set(VIEWPORTS), "viewports needs desktop and phone")
    for size in sizes.values():
        evidence.require(isinstance(size, list) and len(size) == 2
                         and all(type(n) is int and 0 < n <= 32768 for n in size), "Invalid planned viewport")
    evidence.require(sizes["desktop"][0] > sizes["phone"][0], "Phone viewport must be narrower than desktop")
    return {"surfaces": [{"id": key, "name": evidence.text(row.get("name"), "surface name")}
                         for key, row in surfaces.items()],
            "full_suite": [evidence.text(arg, "suite argument") for arg in suite], "viewports": sizes,
            "wait_minutes": integer(data.get("wait_minutes", 30), "wait_minutes", 0, 1440),
            "timeout_seconds": integer(data.get("timeout_seconds", 1800), "timeout_seconds", 1, 86400)}


def show_plan(run):
    """A missing plan is an explicit stop, not an empty screen inventory."""
    value = run.get("show", {}).get("plan")
    evidence.require(isinstance(value, dict), "Record show --plan before done plan")
    return value


def prepare(project, run, data):
    """Validate every reference/current variant; actual inspection remains a human obligation."""
    planned = show_plan(run)
    evidence.require(type(data.get("version")) is int and data["version"] == 1, "Show report version must be 1")
    candidate = evidence.candidate(project)
    evidence.require(data.get("candidate") == candidate, "Show candidate changed; capture the current source")
    screens = evidence.rows(data.get("screens"), "Show screens")
    expected = {(s["id"], *variant) for s in planned["surfaces"] for variant in VARIANTS}
    actual, captures = set(), []
    for key, row in screens.items():
        case = (row.get("surface"), row.get("theme"), row.get("device"))
        evidence.require(case in expected and case not in actual, f"{key}: unknown or duplicate surface variant")
        actual.add(case)
        evidence.require(row.get("viewport") == planned.get("viewports", VIEWPORTS)[case[2]],
                         f"{key}: use the planned device viewport")
        description = evidence.text(row.get("description"), "one-line change")
        evidence.require("\n" not in description and "\r" not in description, "Use a one-line change description")
        evidence.require(row.get("inspected") is True, f"{key}: inspect both images before Show")
        state = evidence.text(row.get("state"), "state")
        evidence.require(row.get("reference_state") == state, f"{key}: reference and capture states differ")
        captures.append({"id": key, "surface": case[0], "theme": case[1], "device": case[2],
                         "viewport": row.get("viewport"), "state": state, "description": description,
                         **{kind: evidence.image(project, row.get(kind), row.get("viewport"))
                            for kind in ("reference", "capture")}})
    evidence.require(actual == expected, "Show needs light/dark desktop/phone pairs for every planned surface")
    if run.get("design_port"):
        evidence.load(project, run)
        by_id = {s["id"]: s for s in captures}
        for reference in run["design"]["inventory"]["screens"]:
            current = by_id.get(reference["id"], {})
            evidence.require(all(current.get(k) == reference[k] for k in ("reference", "viewport", "theme", "state")),
                             f"{reference['id']}: Show must include the frozen design reference")
    return {"candidate": candidate, "screens": captures}


def markdown(project, report):
    """Produce a shareable side-by-side report; generating it is not delivery."""
    escape = lambda value: str(value).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
    lines = ["# Look: ready for your feedback", "", "These pictures are ready to inspect; final checks come next.", ""]
    for row in report["screens"]:
        label = escape(f"{row['surface']} · {row['theme']} · {row['device']}")
        lines += [f"## {label}", "", escape(row["description"]), "", "| Design | Current |", "|---|---|"]
        images = [f"![{kind}: {label}](<{(Path(project) / row[kind]['path']).resolve().as_posix()}>)"
                  for kind in ("reference", "capture")]
        lines += ["| " + " | ".join(images) + " |", ""]
    return "\n".join(lines)


def current(project, run):
    """Recheck source, all images and generated report before using a sharing claim."""
    report = run.get("show", {}).get("report")
    evidence.require(isinstance(report, dict), "Prepare the current Show report first")
    evidence.require(report["candidate"] == evidence.candidate(project), "Source changed; capture and share a fresh Show")
    for row in report["screens"]:
        for kind in ("reference", "capture"):
            evidence.require(evidence.image(project, row[kind]["path"], row["viewport"]) == row[kind],
                             "Show images changed; inspect and share a fresh Show")
    evidence.require(evidence.file_hash(evidence.local(project, report["path"])) == report["sha256"],
                     "Show report changed; prepare and share it again")
    return report


def publication(data):
    """Record actual sharing evidence; a local path alone cannot establish delivery."""
    evidence.require(data.get("channel") in ("chat", "tool", "url"), "Sharing channel must be chat, tool or url")
    source = evidence.text(data.get("source"), "actual sharing source")
    evidence.require(data.get("sent") is True and data.get("images_accessible") is True,
                     "Share the pictures and verify owner access before recording delivery")
    evidence.require(not source.startswith(("/", "\\", ".")) and not (len(source) > 1 and source[1] == ":"),
                     "A local path is not evidence the owner saw the report")
    if data["channel"] == "url":
        evidence.require(urlparse(source).scheme == "https" and bool(urlparse(source).hostname), "Sharing URL must be HTTPS")
    return {"channel": data["channel"], "source": source}


def reply(data, run):
    """Owner stops/changes block proof; explicit leave choices retain a follow-up and source."""
    action = data.get("action")
    evidence.require(action in ("proceed", "change", "stop"), "Reply action must be proceed, change or stop")
    result = {"action": action, **{key: evidence.text(data.get(key), f"owner reply {key}") for key in ("source", "quote")}}
    leaves = data.get("leave", [])
    evidence.require(isinstance(leaves, list), "leave must be a list")
    surfaces = {row["id"] for row in show_plan(run)["surfaces"]}
    for row in leaves:
        evidence.require(isinstance(row, dict) and row.get("surface") in surfaces, "Leave item needs a planned surface")
        evidence.text(row.get("description"), "leave description")
        link = urlparse(evidence.text(row.get("followup"), "Finishing touches follow-up"))
        evidence.require(link.scheme == "https" and bool(link.hostname), "Leave item needs its recorded follow-up URL")
    return {**result, "leave": leaves}


def ready_for_prove(project, run, at=None):
    """The one permission boundary for proof; elapsed time never means approval to merge."""
    current(project, run)
    shown = run["show"]
    shared = shown.get("shared")
    evidence.require(isinstance(shared, dict), "Share Show with the owner and record its actual delivery first")
    response = shown.get("reply")
    if response:
        evidence.require(response["action"] == "proceed", "Owner requested a stop/change; resolve it and share again")
        return "Owner reply recorded; continue to Prove. Merge still needs human authority."
    deadline = datetime.fromisoformat(shared["at"]) + timedelta(minutes=show_plan(run)["wait_minutes"])
    clock = datetime.fromisoformat(at) if at else datetime.now(timezone.utc)
    evidence.require(clock >= deadline, f"Waiting for owner reply until {deadline.isoformat()}; no proof yet")
    return "No owner reply by the configured deadline; continue to Prove. This is not approval or merge authority."


def problems(run, project, final=False):
    """Surface invalid plans/receipts in the existing gate without changing older runs."""
    if not enabled(run):
        return []
    try:
        ready_for_prove(project, run) if final else show_plan(run)
        return []
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Show: {error}"]


def notice(project, run):
    """A waiting/status message is not a failed record mutation."""
    try:
        return ready_for_prove(project, run)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return f"Show: {error}"


def completion_problems(run, project):
    """A known failed or interrupted suite cannot disappear behind a manual PASS line."""
    found = problems(run, project, final=True)
    proof = run.get("show", {}).get("proof")
    if enabled(run) and proof is not None:
        if not isinstance(proof, dict) or proof.get("passed") is not True:
            found.append("Show: declared suite failed or was interrupted; finish its correction before handoff")
        elif proof.get("candidate") != run["show"].get("report", {}).get("candidate"):
            found.append("Show: declared suite proof is stale; run prove --suite for the current source before handoff")
    return found


def suite_guard(command, run, project, dialect=None):
    """Match declared direct suite invocations using the existing parser, not a new shell classifier."""
    if not enabled(run):
        return None
    import fast_shell
    suite = run.get("show", {}).get("plan", {}).get("full_suite")
    if not suite:
        return None
    def normalized(words):
        first = fast_shell.program(words[0])
        return ["python" if first in ("python", "python3", "py") else first, *words[1:]]
    expected = normalized(suite)
    for mode in ([dialect] if dialect else ["bash", "windows"]):
        for cmd in fast_shell.pipelines(command, mode):
            if isinstance(cmd, fast_shell.Command) and not cmd.outer and normalized(cmd.words)[:len(expected)] == expected:
                return "; ".join(problems(run, project, final=True)) or None
    return None
