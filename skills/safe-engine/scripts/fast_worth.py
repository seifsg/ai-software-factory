"""Worth-it assessments shared by review and repair; priority never waives quality or owner authority."""
import re


FIELDS = {"notice", "harm", "minutes", "required", "reason"}
SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
DISPOSITIONS = {"blocking", "before-exposure", "accepted-deferral"}


def text(value):
    """Require a real single-line explanation; records remain readable and cannot inject report rows."""
    return isinstance(value, str) and bool(value.strip()) and not re.search(r"[\r\n\x00]", value)


def assess(finding):
    """Derive a score and action from bounded inputs, keeping unknown estimates explicit."""
    if not isinstance(finding, dict) or finding.get("severity") not in SEVERITIES:
        raise ValueError("Each finding needs LOW, MEDIUM, HIGH or CRITICAL severity")
    if finding.get("disposition") not in DISPOSITIONS:
        raise ValueError("Each finding needs blocking, before-exposure or accepted-deferral disposition")
    if not all(text(finding.get(key)) for key in ("location", "description")):
        raise ValueError("Each finding needs a single-line location/source and plain description")
    worth = finding.get("worth")
    if not isinstance(worth, dict) or set(worth) != FIELDS:
        raise ValueError("Worth needs notice, harm, minutes, required and reason")
    for key, limit in (("notice", 2), ("harm", 3)):
        if type(worth[key]) is not int or not 0 <= worth[key] <= limit:
            raise ValueError(f"Worth {key} must be an integer from 0 to {limit}")
    minutes = worth["minutes"]
    if minutes is not None and (type(minutes) is not int or minutes < 0):
        raise ValueError("Worth minutes must be a nonnegative integer or null for unknown")
    if type(worth["required"]) is not bool or not text(worth["reason"]):
        raise ValueError("Worth needs a boolean required and a single-line reason")
    cost = None if minutes is None else 2 if minutes < 15 else 1 if minutes < 60 else 0
    score = None if cost is None else worth["notice"] + worth["harm"] + cost
    mandatory = (worth["required"] or worth["harm"] == 3 or finding["severity"] in ("HIGH", "CRITICAL")
                 or finding["disposition"] == "blocking" or finding.get("evidence_status") in ("missing", "challenged"))
    action = ("do-now" if mandatory else "estimate" if score is None else "do-now"
              if score >= 5 or score >= 3 and minutes < 60 else "finishing-touches")
    return {"score": score, "cost": cost, "mandatory": mandatory, "action": action}


def rows(report):
    """Validate a whole finding report and its one existing follow-up destination; never write the tracker."""
    if not isinstance(report, dict) or not isinstance(report.get("findings"), list):
        raise ValueError("Report needs a findings list (empty for a clean check)")
    result, destinations = [], set()
    for number, finding in enumerate(report["findings"], 1):
        row = {"id": f"F{number}", **assess(finding), "finding": finding}
        if finding["disposition"] == "accepted-deferral":
            exception = finding.get("exception")
            if row["mandatory"]:
                raise ValueError(f"{row['id']}: required, harmful, high-severity or unverified work cannot be parked")
            if not isinstance(exception, dict) or not all(text(exception.get(key)) for key in
                    ("owner", "reason", "scope", "revisit", "authority", "destination")):
                raise ValueError(f"{row['id']}: parking needs owner, reason, scope, revisit, authority and destination")
            destinations.add(exception["destination"])
        result.append(row)
    if len(destinations) > 1:
        raise ValueError("Use the epic's one existing follow-ups ticket for every parked finding")
    return result


def select(report, selected, finishing=None):
    """Reject optional low-value selections, including mixed rounds; explicit finishing authority permits them."""
    assessed = rows(report)
    if (not isinstance(selected, list) or not selected or any(not isinstance(key, str) for key in selected)
            or len(set(selected)) != len(selected)):
        raise ValueError("Select each finding once with --finding F1 (report order)")
    known = {row["id"]: row for row in assessed}
    if any(not isinstance(key, str) or key not in known for key in selected):
        raise ValueError("Selected finding is absent from this report; use F1, F2 in report order")
    if finishing is not None and not text(finishing):
        raise ValueError("Finishing authority needs the owner's exact instruction and source")
    picked = [known[key] for key in selected]
    for row in picked:
        if row["action"] == "estimate":
            raise ValueError(f"{row['id']}: estimate optional work before selecting a fix round")
        if row["action"] == "finishing-touches" and not finishing:
            raise ValueError(f"{row['id']}: optional score {row['score']}/7 waits for an authorized finishing batch")
        if row["action"] == "finishing-touches" and row["finding"]["disposition"] != "accepted-deferral":
            raise ValueError(f"{row['id']}: finishing work needs its authorized entry in the existing follow-ups ticket")
    return {"selected": selected, "finishing_authority": finishing, "assessments": assessed,
            "parked": parked(report)}


def parked(report):
    """Plain owner-facing parked facts; identifiers and destinations remain in separate structured fields."""
    return [{"description": row["finding"]["description"], "score": row["score"],
             "reason": row["finding"]["exception"]["reason"],
             "destination": row["finding"]["exception"]["destination"],
             "source": row["finding"]["location"]}
            for row in rows(report) if row["finding"]["disposition"] == "accepted-deferral"]


def parked_lines(report):
    """Format only owner-visible facts; callers retain links separately, never claim unknown cost is free."""
    return [f"Parked: {item['description']} (worth it {str(item['score']) + '/7' if item['score'] is not None else 'unknown'}). "
            f"{item['reason']}" for item in parked(report)]


def reconcile(report, rounds, *, completed=True):
    """Account for every finding; completing a batch also settles every selected obligation."""
    owed = {(receipt["sha256"], row["id"]): row["finding"]
            for receipt in rounds for row in rows(receipt["report"])}
    selected = {(receipt["sha256"], number) for receipt in rounds for number in receipt["selected"]}
    current = {row["id"]: row["finding"] for row in rows(report)}
    covered = set()
    for group, fields in (("resolved", ("evidence",)), ("retained", ("current_finding",)),
                          ("cancelled", ("owner", "authority", "reason"))):
        entries = report.get(group, [])
        required = {"report_sha256", "finding", *fields}
        if not isinstance(entries, list):
            raise ValueError(f"{group} must be a list")
        for item in entries:
            if not isinstance(item, dict) or set(item) != required or not all(text(item[key]) for key in required):
                raise ValueError(f"{group} entries need " + ", ".join(sorted(required)))
            key = (item["report_sha256"], item["finding"])
            if key not in owed or key in covered:
                raise ValueError("Reconcile each recorded report/finding once; foreign or duplicate entries refused")
            if group == "retained" and completed and key in selected:
                raise ValueError("Selected findings need resolution evidence or owner cancellation before completion")
            if group == "retained" and current.get(item["current_finding"]) != owed[key]:
                raise ValueError("Retained entries must point to the unchanged finding in this report")
            covered.add(key)
    if owed.keys() - covered:
        missing = ", ".join(f"{number} from {digest}" for digest, number in sorted(owed.keys() - covered))
        raise ValueError("Reconcile every recorded finding: retain, resolve with evidence, or record owner cancellation: " + missing)
