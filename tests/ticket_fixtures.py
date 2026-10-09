"""Synthetic ticket contracts shared by the ticket test modules; no live owner, tracker or review."""
from copy import deepcopy

from safe_engine.tickets import scope_digest


SYNTHETIC = "Synthetic regression double; no live MCP, human, app or cloud acceptance"


def confirm(contract, at):
    """Bind a synthetic owner confirmation to the contract's exact revision and scope."""
    contract["confirmation"] = {"revision": contract["revision"], "digest": scope_digest(contract),
        "actor": "Synthetic owner assertion double", "source": "synthetic:owner-confirmation",
        "statement": SYNTHETIC, "at": at}
    return contract


def base_contract(at, revision=1, dependencies=()):
    """Smallest confirmed contract the ticket rules accept."""
    result = {"revision": revision, "lifecycle": "ready", "scope": {
        "original_request": "Synthetic fixture request: preserve the document sentence",
        "owner_input": [{"text": SYNTHETIC, "source": "synthetic:owner-input-1"}],
        "before": "Synthetic baseline has a readable document sentence",
        "after": "Synthetic outcome preserves that sentence",
        "completion": "Synthetic checked local handoff only",
        "journeys": ["Synthetic reader opens the document and reads the unchanged sentence"],
        "exclusions": ["No app, game, external tracker or cloud review"],
        "constraints": [SYNTHETIC], "dependencies": list(dependencies),
        "epic": "synthetic:epic-document",
        "acceptance": [{"id": "A1", "text": "Synthetic fixture sentence remains readable"}]}}
    return confirm(result, at)


def visual_contract(contract, at):
    """The same contract in the visual ticket layout, with progress and activity."""
    contract = deepcopy(contract)
    contract["presentation"] = "visual"
    contract["scope"].update(
        purpose="Synthetic reader must retain the document",
        goal="Synthetic sentence survives unchanged",
        context="Synthetic source: README.md; no app observation",
        approach="Preserve the existing sentence; no new writer",
        before="Synthetic `left|right`\nKeep this reminder. Keep it.",
        flow="reader -> document -> unchanged sentence",
        optional=["Synthetic follow-up; not required"])
    contract["progress"] = "Synthetic fixture only; no real PR or review"
    contract["activity"] = [{"at": at, "actor": SYNTHETIC,
        "what": "Synthetic inspection", "why": "Verify retained input",
        "result": "Synthetic planning; no live action"}]
    return confirm(contract, at)
