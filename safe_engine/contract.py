"""Contract proposal, sealing, amendment and ticket-criterion proof."""

from .acceptance import contract_candidate_digest, validate_contract_review
from .project import (EngineError, file_hash, inside, protected_inputs, reject_path_aliases, relative_input_path,
                      validate_profile, validate_task)
from .proof import proof_draft
from .storage import atomic_json, now, read_json


class ContractMixin:
    def contract_proposal(self, task, profile):
        """Read-only binding for an independent reviewer, not approval by this command."""
        state = self.load()
        draft = state.get("delivery_version") == 2 and not state["contract_sealed"]
        validate_profile(profile, draft=draft)
        validate_task(task, profile, draft=draft)
        protected = protected_inputs(self.project, profile)
        _, ticket = self.ticket_proposal(task, profile)
        return {"old_digest": state["contract_digest"],
                "new_digest": contract_candidate_digest(task, profile, protected, ticket),
                "protected": protected, "task": task, "profile": profile, "ticket": ticket}

    def seal(self, task, profile, review):
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "testing")
        if state.get("delivery_version") != 2 or state["contract_sealed"]:
            raise EngineError("Only a draft new-delivery contract can be sealed")
        if state.get("pending_operation"):
            raise EngineError("Reconcile the pending operation before sealing")
        self.integrity(state)
        self.require_manual(state)
        if not isinstance(profile, dict) or profile.get("version") != 2:
            raise EngineError("New delivery requires a version 2 profile")
        validate_profile(profile)
        validate_task(task, profile)
        # The final test contract cannot silently reclassify implementation as tests.
        for key in ("interface", "test_paths", "environment_inputs", "input_files", "review_scopes", "exposure"):
            if profile.get(key, []) != state["profile"].get(key, []):
                raise EngineError(f"Seal cannot change {key}; use a reviewed amendment")
        self.preserve_requirements(state["task"], task)
        proposal = self.contract_proposal(task, profile)
        validate_contract_review(review, proposal["old_digest"], proposal["new_digest"])
        self.require_manual({**state, "task": task, "profile": profile})
        self.save_contract(state, task, profile, proposal["protected"], review, "Sealed final acceptance")
        return self.status(state)

    @staticmethod
    def preserve_requirements(previous, proposed):
        if proposed.get("request") != previous["request"]:
            raise EngineError("Preserve the original request; a new product scope needs a new task")
        old = {item["id"]: item["text"] for item in previous["acceptance"]}
        new = {item["id"]: item["text"] for item in proposed.get("acceptance", [])}
        if old != new:
            raise EngineError("Preserve acceptance IDs/text; seal changes only evidence bindings")

    def save_contract(self, state, task, profile, protected, review, event, sealed=True, ticket=None):
        state["contract_history"].append({"task": state["task"], "profile": state["profile"],
            **({"ticket": state["ticket"]} if state.get("ticket") else {}),
            "protected": state["protected"], "digest": state["contract_digest"],
            "revision": state["contract_revision"], "review": review, "at": now()})
        state.update(task=task, profile=profile, protected=protected,
                     contract_digest=self.contract_digest(task, profile, ticket or state.get("ticket")),
                     contract_sealed=sealed, contract_revision=state["contract_revision"] + 1,
                     checks=None, review=None)
        if ticket is not None:
            state["ticket"] = ticket
        self.persist(state, event)

    def amend(self, task, profile, review, reason):
        state = self.load()
        if state.get("delivery_version") != 2 or state["phase"] == "cancelled" or (not self.ticket_key and state["phase"] in ("analyze", "plan")):
            raise EngineError("Amend a new-delivery build or final-stage contract; preserve cancelled runs")
        if state.get("pending_operation") or not reason.strip():
            raise EngineError("Amendment needs a reason and no pending operation")
        if not isinstance(profile, dict) or profile.get("version") != 2:
            raise EngineError("Amendment requires a version 2 profile")
        proposal = self.contract_proposal(task, profile)
        validate_contract_review(review, proposal["old_digest"], proposal["new_digest"])
        changed_scope = proposal["ticket"] != state.get("ticket")
        if self.ticket_key:
            store = self.store
            capture, _ = store.ready(self.ticket_key)
            store.dependencies(self.ticket_key)
            store.claim(self.ticket_key, state["run_id"], self.directory)
            if changed_scope:
                text_authority = review.get("acceptance_change_authority")
                if not isinstance(text_authority, str) or not text_authority.strip():
                    raise EngineError("Rebinding a ticket needs explicit owner scope-change authority in the review")
            state["ticket_observation"] = capture["sequence"]
            atomic_json(self.directory / "ticket-observations" / f"{capture['sequence']:06d}.json", capture)
        if task["request"] != state["original_task"]["request"]:
            raise EngineError("Amendment cannot replace the original request")
        old_criteria = {c["id"]: c["text"] for c in state["task"]["acceptance"]}
        new_criteria = {c["id"]: c["text"] for c in task["acceptance"]}
        authority = review.get("acceptance_change_authority")
        if old_criteria != new_criteria and (not isinstance(authority, str) or not authority.strip()):
            raise EngineError("Changed requirements need explicit acceptance_change_authority in the review")
        # A contract correction may repair protected tests; retain their prior hashes/history.
        for artifact in state["artifacts"].values():
            if file_hash(self.directory / artifact["path"]) != artifact["sha256"]:
                raise EngineError("Recorded evidence changed; preserve it before amendment")
        restart = changed_scope or state["phase"] in ("analyze", "plan")
        state["phase"] = "analyze" if restart else "build"
        state["manual"] = None
        for key in ("record_correction", "manual_candidate", "manual_receipts", "review_packet"):
            state.pop(key, None)
        for key in ("implementation", "manual", "batch", "improvement"):
            state["artifacts"].pop(key, None)
        if restart:
            for key in ("analysis", "plan"):
                state["artifacts"].pop(key, None)
            state["initial_fingerprint"] = self.current({**state, "task": task, "profile": profile,
                                                        "ticket": proposal["ticket"]})
        state["repairs_used"] += 1
        self.save_contract(state, task, profile, proposal["protected"], review, f"Reviewed amendment: {reason}",
                           sealed=state["contract_sealed"], ticket=proposal["ticket"])
        return self.status(state)

    def ticket_proof(self, source):
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "review")
        if not self.ticket_key:
            raise EngineError("Ticket proof requires a bound ticket run")
        proof = read_json(self.outside_inputs(source))
        if not isinstance(proof, dict):
            raise EngineError("Ticket proof must be a JSON object")
        ticket = state["ticket"]
        if proof.get("scope_digest") != ticket["scope_digest"] or proof.get("revision") != ticket["revision"]:
            raise EngineError("Proof must map the latest confirmed ticket revision/digest")
        expected = {c["id"] for c in ticket["scope"]["acceptance"]}
        rows = proof.get("criteria")
        if not isinstance(rows, list) or len(rows) != len(expected) or {row.get("id") for row in rows} != expected:
            raise EngineError("Map every latest ticket criterion exactly once")
        for row in rows:
            if row.get("status") != "PASS":
                raise EngineError("Unmet/unknown ticket expectations block acceptance")
            for field in ("before", "after", "implementation"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise EngineError(f"Ticket proof needs {field} per criterion")
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise EngineError("Ticket proof needs actual evidence files per criterion")
            for item in evidence:
                name = relative_input_path(item["path"], allow_factory=True)
                path = inside(self.project, name)
                reject_path_aliases(path, self.project)
                if file_hash(path) != item.get("sha256"):
                    raise EngineError("Ticket proof evidence hash differs")
            deviations = row.get("deviations")
            if not isinstance(deviations, list):
                raise EngineError("Declare deviations explicitly, including an empty array")
            for deviation in deviations:
                if any(not isinstance(deviation.get(f), str) or not deviation[f].strip()
                       for f in ("change", "reason", "authority")):
                    raise EngineError("Approved deviations need change/reason/owner authority")
        self.capture_artifact(state, "ticket-proof", source, self.current(state))
        self.persist(state, "Mapped latest confirmed ticket expectations to before/after evidence")
        return self.status(state)

    def require_ticket_proof(self, state):
        if not self.ticket_key:
            return
        artifact = state["artifacts"].get("ticket-proof")
        if not artifact or artifact["fingerprint"] != self.current(state):
            raise EngineError("Map current confirmed ticket criteria with ticket-proof before review/handoff")
        proof = read_json(self.directory / artifact["path"])
        for row in proof["criteria"]:
            for item in row["evidence"]:
                path = inside(self.project, item["path"])
                reject_path_aliases(path, self.project)
                if file_hash(path) != item["sha256"]:
                    raise EngineError("Mapped ticket evidence changed")

    def ticket_proof_draft(self, out):
        """Pre-fill ticket-proof from recorded receipts/checks; the agent writes before/after."""
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "review")
        if not self.ticket_key:
            raise EngineError("Ticket proof requires a bound ticket run")
        self.require_checks(state)
        draft = proof_draft(state, self.project)
        atomic_json(self.outside_inputs(out), draft)
        return {"draft": str(out), "complete": ["before", "after"],
                "unknown": [row["id"] for row in draft["criteria"] if row["status"] != "PASS"]}
