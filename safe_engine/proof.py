"""Criterion proof drafts and PR-ready handoff tables from recorded evidence; never a PASS by itself."""

from pathlib import Path

from .project import git
from .tickets import table_cell


def relative(project, path):
    return Path(path).relative_to(project).as_posix()


def criterion_evidence(state, project, criterion):
    """Recorded manual evidence plus linked check logs/outputs, with their recorded hashes."""
    items = [item for observation in (state.get("manual") or {}).get("observations", [])
             if observation["criterion"] == criterion["id"] for item in observation["evidence"]]
    results = {result["id"]: result for result in (state.get("checks") or {}).get("results", [])}
    for identifier in criterion.get("checks", []):
        result = results.get(identifier)
        if result:
            items.append({"path": relative(project, result["log"]), "sha256": result["log_sha256"]})
            items += [{"path": relative(project, item["path"]), "sha256": item["sha256"]}
                      for item in result.get("artifacts", [])]
    return list({item["path"]: item for item in items}.values())


def criterion_supported(state, criterion):
    results = {result["id"]: result for result in (state.get("checks") or {}).get("results", [])}
    observed = {o["criterion"] for o in (state.get("manual") or {}).get("observations", [])}
    manual_needed = criterion.get("mode", "automated") in ("manual", "mixed")
    return ((not manual_needed or criterion["id"] in observed)
            and all(results.get(identifier, {}).get("passed") for identifier in criterion.get("checks", [])))


def changed_files(project, base):
    tracked = git(project, "diff", "--name-only", "-z", base, "--").split("\0")
    untracked = git(project, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({name for name in tracked + untracked if name and not name.startswith(".factory/")})


def proof_draft(state, project):
    ticket = state["ticket"]
    changed = changed_files(project, state["base_commit"])
    summary = ", ".join(changed[:20]) + (f" (+{len(changed) - 20} more)" if len(changed) > 20 else "")
    rows = []
    for criterion in state["task"]["acceptance"]:
        evidence = criterion_evidence(state, project, criterion)
        rows.append({"id": criterion["id"],
                     "status": "PASS" if evidence and criterion_supported(state, criterion) else "UNKNOWN",
                     "before": "", "after": "", "implementation": f"Changed: {summary or 'none'}",
                     "evidence": evidence, "deviations": []})
    return {"revision": ticket["revision"], "scope_digest": ticket["scope_digest"], "criteria": rows}


def handoff_table(state, project, proof=None):
    """Markdown rows a PR verification section can paste."""
    mapped = {row["id"]: row for row in (proof or {}).get("criteria", [])}
    implementation = next((state["artifacts"][kind]["path"] for kind in ("implementation", "improvement", "batch")
                           if kind in state["artifacts"]), None)
    lines = ["| Criterion | Change | Proof | Gap |", "|---|---|---|---|"]
    for criterion in state["task"]["acceptance"]:
        row = mapped.get(criterion["id"], {})
        evidence = row.get("evidence") or criterion_evidence(state, project, criterion)
        change = row.get("implementation") or (f"Recorded implementation: {implementation}" if implementation else "Not mapped")
        proof_cell = "<br>".join(([f"Before: {table_cell(row['before'])}", f"After: {table_cell(row['after'])}"] if row else [])
                                 + [f"`{table_cell(item['path'])}` ({item['sha256'][:12]})" for item in evidence])
        gaps = "; ".join(f"{d['change']} ({d['reason']}; {d['authority']})" for d in row.get("deviations", []))
        gap = gaps or ("None recorded" if evidence else "No mapped evidence")
        lines.append(f"| {table_cell(criterion['id'] + ': ' + criterion['text'])} | {table_cell(change)} "
                     f"| {proof_cell or 'None'} | {table_cell(gap)} |")
    return lines


def deferred_findings(report):
    """Nonblocking review findings stay visible in the handoff with their follow-up."""
    parked_output = []
    if any("worth" in finding for finding in report.get("findings", [])):
        from .worth import parked, parked_lines
        lines = parked_lines(report)
        links = sorted({item["destination"] for item in parked(report)})
        if lines:
            parked_output = ["", "## Finishing touches", "", *lines, "", "Follow-ups: " + ", ".join(links)]
        report = {**report, "findings": [finding for finding in report["findings"]
                                        if finding.get("disposition") != "accepted-deferral"]}
    rows = [f"- {f['severity']} {f['location']}: {f['description']} ({f.get('disposition')}; "
            f"{(f.get('exception') or {}).get('destination') or (f.get('exception') or {}).get('revisit', 'no follow-up')})"
            for f in report.get("findings", []) if f.get("disposition") in ("accepted-deferral", "before-exposure")
            or f.get("severity") == "LOW"]
    return parked_output + (["", "## Deferred findings", "", *rows] if rows else [])
