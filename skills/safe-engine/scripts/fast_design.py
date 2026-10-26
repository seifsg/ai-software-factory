"""Reference coverage and candidate-bound likeness evidence; no visual verdict is inferred."""
import hashlib
import json
from pathlib import Path
import struct

import fast_setup

LIMIT = 4 * 1024 * 1024
STATES = ("done", "partial", "missing", "cut")


def require(condition, message):
    """Reject malformed evidence where it enters."""
    if not condition:
        raise ValueError(message)


def text(value, label):
    """Names and evidence must be nonempty, bounded text."""
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= 2000, f"{label}: needs text")
    return value.strip()


def digest(value):
    """Stable identity of structured evidence."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    """Hash files incrementally; screenshots need not fit in memory."""
    hashed = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            hashed.update(chunk)
    return hashed.hexdigest()


def local(project, value):
    """Evidence stays inside the project and cannot traverse a linked directory."""
    root = Path(project).resolve()
    path = Path(text(value, "path"))
    path = path if path.is_absolute() else root / path
    require(path.resolve().is_relative_to(root), "Evidence path must stay inside the project")
    require(path.is_file(), f"Missing evidence: {value}")
    return path.resolve()


def read(path):
    """Read one bounded JSON object, never execute artifact content."""
    require(path.stat().st_size <= LIMIT, "Design artifact exceeds 4 MiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "Design artifact must be an object")
    return data


def rows(value, label):
    """Index distinct named rows without accepting an empty inventory."""
    require(isinstance(value, list) and 0 < len(value) <= 10000, f"{label}: needs 1..10000 rows")
    result = {}
    for row in value:
        require(isinstance(row, dict), f"{label}: every row must be an object")
        key = text(row.get("id"), f"{label} id")
        require(key not in result, f"{label}: duplicate id {key}")
        result[key] = row
    return result


def image(project, value, viewport, hash_image=True):
    """Validate a PNG capture's actual dimensions and retain its exact bytes' identity."""
    require(isinstance(viewport, list) and len(viewport) == 2
            and all(type(n) is int and 0 < n <= 32768 for n in viewport), "viewport: needs [width, height]")
    path = local(project, value)
    import fast_image
    fast_image.check(path)
    with path.open("rb") as source:
        header = source.read(24)
    require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR",
            f"{value}: use a PNG screenshot")
    require(list(struct.unpack(">II", header[16:24])) == viewport, f"{value}: screenshot size differs from viewport")
    return {"path": path.relative_to(Path(project).resolve()).as_posix(),
            "sha256": file_hash(path) if hash_image else None}


def inventory(project, data, hash_images=True):
    """Canonical screen/element identity excludes mutable statuses and approvals."""
    require(type(data.get("version")) is int and data["version"] == 1, "Design artifact version must be 1")
    screens, elements = rows(data.get("screens"), "screens"), rows(data.get("elements"), "elements")
    canonical = []
    for key, screen in screens.items():
        shot = image(project, screen.get("reference"), screen.get("viewport"), hash_images)
        canonical.append({"id": key, "reference": shot, "viewport": screen["viewport"],
                          "theme": text(screen.get("theme"), "theme"), "state": text(screen.get("state"), "state")})
    entries = []
    for key, element in elements.items():
        require(element.get("screen") in screens, f"{key}: screen is absent from inventory")
        entries.append({"id": key, "screen": element["screen"], "name": text(element.get("name"), f"{key} name")})
    require({e["screen"] for e in entries} == set(screens), "Every screen needs its design elements")
    return {"builder": text(data.get("builder"), "builder"), "screens": sorted(canonical, key=lambda x: x["id"]),
            "elements": sorted(entries, key=lambda x: x["id"])}


def statuses(data):
    """Validate owner decision records; their authenticity still needs human evidence review."""
    elements = rows(data.get("elements"), "elements")
    for key, item in elements.items():
        require(item.get("status") in STATES, f"{key}: status must be done, partial, missing or cut")
        if item["status"] == "cut":
            approval = item.get("approval")
            require(isinstance(approval, dict), f"{key}: cut needs the owner's recorded answer")
            for field in ("actor", "source", "quote"):
                text(approval.get(field), f"{key} owner approval {field}")
    return elements


def load(project, run, verify_images=True):
    """Compare the editable report with the immutable run inventory, including reference bytes."""
    frozen = run.get("design")
    require(isinstance(frozen, dict), "Record the reference inventory with design --input before plan")
    data = read(local(project, frozen["path"]))
    expected = frozen["inventory"]
    if not verify_images:
        expected = {**expected, "screens": [{**s, "reference": {**s["reference"], "sha256": None}}
                                           for s in expected["screens"]]}
    require(inventory(project, data, verify_images) == expected,
            "Design inventory or reference changed; preserve the original scope")
    statuses(data)
    return data


def candidate(project):
    """Hash source bytes, including dirty/untracked files; ignored runtime evidence is separate."""
    result = fast_setup.git(project, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    require(result is not None and result.returncode == 0, "Cannot identify the candidate: Git unavailable")
    names = result.stdout
    values = {}
    for name in sorted(set(names.rstrip("\0").split("\0")) - {""}):
        path = Path(project) / name
        require(not path.is_symlink(), f"Candidate symlink needs explicit review: {name}")
        require(not path.is_dir(), f"Candidate directory needs explicit review: {name}")
        values[name] = file_hash(path) if path.is_file() else None
    return digest(values)


def summary(data):
    """Report completed elements against the original denominator; cuts never inflate completion."""
    elements = statuses(data)
    counts = {state: sum(e["status"] == state for e in elements.values()) for state in STATES}
    return {**counts, "total": len(elements),
            "text": f"{counts['done']} of {len(elements)} design elements on screen; "
                    f"{counts['partial']} partial; {counts['missing']} missing; {counts['cut']} owner-approved cuts"}


def review_evidence(project, run, data, review):
    """Validate a fresh judge's matched captures and one explicit observation per element."""
    require(type(review.get("version")) is int and review["version"] == 1, "Review version must be 1")
    who = text(review.get("reviewer"), "reviewer")
    require(who != run["design"]["inventory"]["builder"] and review.get("independent") is True,
            "Likeness reviewer must be independent of the builder")
    require(review.get("candidate") == candidate(project), "Review candidate changed; capture and review the current source")
    screens = rows(review.get("screens"), "review screens")
    reference = {s["id"]: s for s in run["design"]["inventory"]["screens"]}
    require(set(screens) == set(reference), "Review must cover every reference screen")
    captures = {}
    for key, screen in screens.items():
        expected = reference[key]
        require(all(screen.get(field) == expected[field] for field in ("viewport", "theme", "state")),
                f"{key}: match the reference viewport, theme and state")
        captures[key] = image(project, screen.get("capture"), screen["viewport"])
    observations, elements = rows(review.get("elements"), "review elements"), statuses(data)
    require(set(observations) == set(elements), "Review must cover every original design element")
    for key, finding in observations.items():
        require(finding.get("status") == elements[key]["status"], f"{key}: review and coverage status disagree")
        differences = finding.get("differences")
        require(isinstance(differences, list) and all(isinstance(d, str) and d.strip() for d in differences),
                f"{key}: differences must be a list of descriptions")
        if finding["status"] == "done":
            require(not differences, f"{key}: unresolved likeness differences cannot be done")
        else:
            require(bool(differences), f"{key}: describe the missing element, layout, density or colour difference")
        text(finding.get("evidence"), f"{key} visual evidence")
    return {"reviewer": who, "candidate": review["candidate"], "coverage": digest(data), "captures": captures}


def final_problems(project, run):
    """Require complete, current evidence again at done-run, handoff and close."""
    try:
        data = load(project, run)
        incomplete = [key for key, row in statuses(data).items() if row["status"] not in ("done", "cut")]
        require(not incomplete, "Unresolved design elements: " + ", ".join(incomplete))
        receipt = run["design"].get("review")
        require(isinstance(receipt, dict), "Needs an independent likeness review: design --review")
        source = local(project, receipt["path"])
        require(file_hash(source) == receipt["sha256"], "Likeness review file changed; review again")
        evidence = review_evidence(project, run, data, read(source))
        require(evidence == receipt["evidence"], "Coverage or captures changed; review again")
        return []
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Design coverage: {error}"]


def problems(run, project, final=False):
    """Old/non-design runs retain their original checks."""
    if not run.get("design_port"):
        return []
    if final:
        return final_problems(project, run)
    try:
        load(project, run)
        return []
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Design coverage: {error}"]


def report(run):
    """Progress is cheap to read; malformed or altered inventory never becomes a percentage."""
    if not run.get("design_port"):
        return None
    try:
        return summary(load(run["project"], run, verify_images=False))["text"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return f"Design coverage unavailable: {error}"
