"""Ticket regressions in disposable Git consumers.

Owner, MCP, manual-action and reviewer assertions are explicitly synthetic test
doubles. Local command/lock/Git behavior is real; no app, game, cloud review,
tracker access or authenticated human acceptance is claimed by this suite.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from safe_engine.project import EngineError, digest, file_hash, production_fingerprint
from safe_engine.storage import atomic_json, locked, read_json
from safe_engine.tickets import TicketStore, binding, parse_body, render_ticket, scope_digest, ticket_key
from safe_engine.workflow import DELEGATION, Workflow


BUNDLE = Path(__file__).resolve().parents[1]
SYNTHETIC = "Synthetic regression double; no live MCP, human, app or cloud acceptance"


class TicketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory ticket regression ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "consumer"
        self.root.mkdir()
        self.git("init", "-q")
        (self.root / ".gitignore").write_text(".factory/\n__pycache__/\n", encoding="utf-8")
        (self.root / "README.md").write_text("Synthetic fixture: preserve this sentence.\n", encoding="utf-8")
        self.commit("Synthetic committed fixture baseline")
        self.initial_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self.contract = self.make_contract()
        self.task = self.task_for(self.contract)
        self.profile = {"version": 2, "interface": "library", "checks": [],
                        "environment_inputs": [], "input_files": [], "protected_paths": [],
                        "test_paths": ["tests"], "review_scopes": [], "exposure": "local"}
        self.store = TicketStore(self.root)
        self.flow = Workflow(self.root, "alpha")
        self.artifact_count = 0
        self.activity = []
        self.last_observed_at = datetime.fromisoformat(self.initial_at)

    def git(self, *args, project=None):
        result = subprocess.run(["git", "-C", str(project or self.root), *args],
                                check=True, capture_output=True, text=True, encoding="utf-8")
        return result.stdout.strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("-c", "user.name=Synthetic Factory Fixture",
                 "-c", "user.email=fixture@example.invalid", "commit", "-qm", message)

    def make_contract(self, revision=1, dependencies=()):
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
        return self.confirm(result)

    def confirm(self, contract):
        contract["confirmation"] = {"revision": contract["revision"], "digest": scope_digest(contract),
            "actor": "Synthetic owner assertion double", "source": "synthetic:owner-confirmation",
            "statement": SYNTHETIC, "at": self.initial_at}
        return contract

    @staticmethod
    def task_for(contract):
        return {"request": contract["scope"]["original_request"], "acceptance": [
            {**item, "mode": "manual", "checks": []} for item in contract["scope"]["acceptance"]]}

    def fresh_observed_at(self):
        boundary = self.last_observed_at
        state_path = self.flow.directory / "state.json"
        if state_path.exists():
            boundary = max(boundary, datetime.fromisoformat(read_json(state_path)["updated_at"]))
        # Windows can repeat a clock tick; fresh fixtures wait rather than invent a future time.
        observed = datetime.now(timezone.utc)
        while observed <= boundary:
            time.sleep(0.001)
            observed = datetime.now(timezone.utc)
        self.last_observed_at = observed
        return observed.isoformat()

    def supplied(self, contract=None, key="alpha", number="101", activity=None, status="open"):
        observed = self.fresh_observed_at()
        return {"version": 1, "key": key,
            "identity": {"provider": "github", "workspace": "synthetic/ticket-fixture",
                         "id": number, "url": f"https://github.com/synthetic/ticket-fixture/issues/{number}"},
            "title": "Synthetic document fixture", "status": status, "observed_at": observed,
            "remote_updated_at": observed, "body": render_ticket(contract or self.contract),
            "complete": True, "transport": {"tool": SYNTHETIC, "source": "synthetic:full-capture"},
            "activity": deepcopy(self.activity if activity is None else activity)}

    def refresh(self, contract=None, **kwargs):
        supplied = self.supplied(contract, **kwargs)
        self.store.capture(supplied)
        return supplied

    def start(self):
        self.refresh()
        return self.flow.initialize(self.task, self.profile, session="synthetic:builder-alpha")

    def artifact(self, kind, flow=None):
        flow = flow or self.flow
        self.artifact_count += 1
        source = flow.directory / "inputs" / f"synthetic-{kind}-{self.artifact_count}.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"# Synthetic {kind} fixture\n{SYNTHETIC}. No actual method adherence asserted.\n",
                          encoding="utf-8")
        return flow.record(kind, source)

    def build(self):
        self.start()
        self.artifact("analysis")
        self.refresh()
        self.artifact("plan")

    def finish_manual(self):
        self.refresh()
        self.artifact("implementation")
        evidence = self.flow.directory / "synthetic-manual.txt"
        evidence.write_text(SYNTHETIC + ": synthetic action evidence fixture\n", encoding="utf-8")
        receipt = {"candidate": self.flow.status()["manual_candidate"], "observations": [
            {"criterion": item["id"], "device": "Synthetic text fixture device assertion",
             "action": SYNTHETIC, "result": "Synthetic sentence-preservation observation",
             "status": "PASS", "evidence": [evidence.relative_to(self.root).as_posix()]}
            for item in self.task["acceptance"]]}
        source = self.flow.directory / "synthetic-manual.json"
        atomic_json(source, receipt)
        self.flow.record("manual", source)
        return evidence

    def review_contract(self, task=None, profile=None):
        proposal = self.flow.contract_proposal(task or self.task, profile or self.profile)
        return {"verdict": "PASS", "independent": True, "reviewer": SYNTHETIC,
                "reason": "Synthetic contract-binding regression assessment only", "authority": SYNTHETIC,
                "old_digest": proposal["old_digest"], "new_digest": proposal["new_digest"]}

    def configure_check(self):
        folder = self.root / "tests"
        folder.mkdir(exist_ok=True)
        script = folder / "synthetic_check.py"
        script.write_text(
            "from pathlib import Path\nimport sys\n"
            "assert 'preserve this sentence' in Path('README.md').read_text()\n"
            "run = Path(sys.argv[1]); count = run / 'synthetic-check-count'\n"
            "count.write_text(str(int(count.read_text()) + 1) if count.exists() else '1')\n"
            "out = run / 'outputs' / 'synthetic-proof.txt'\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "out.write_text('Synthetic fixture check output; no product acceptance')\n"
            "print('Synthetic local document fixture check')\n", encoding="utf-8")
        task, profile = deepcopy(self.task), deepcopy(self.profile)
        profile["checks"] = [{"id": "document", "kind": "unit",
            "argv": ["{python}", "tests/synthetic_check.py", "{run}"], "timeout_seconds": 10,
            "artifacts": [".factory/runs/alpha/outputs/synthetic-proof.txt"]}]
        profile["protected_paths"] = ["tests/synthetic_check.py"]
        for item in task["acceptance"]:
            item.update(mode="mixed", checks=["document"])
        return task, profile

    def verified(self):
        self.build()
        evidence = self.finish_manual()
        self.task, self.profile = self.configure_check()
        self.flow.seal(self.task, self.profile, self.review_contract())
        self.artifact("batch")
        result = self.flow.check()
        self.assertTrue(result["checks_passed"])
        self.assertEqual(result["phase"], "review")
        return evidence

    def proof(self, evidence):
        ticket = self.flow.load()["ticket"]
        return {"revision": ticket["revision"], "scope_digest": ticket["scope_digest"], "criteria": [
            {"id": item["id"], "status": "PASS", "before": "Synthetic baseline sentence",
             "after": "Synthetic preserved sentence", "implementation": "README.md:1 synthetic fixture",
             "evidence": [{"path": evidence.relative_to(self.root).as_posix(), "sha256": file_hash(evidence)}],
             "deviations": []} for item in self.task["acceptance"]]}

    def record_proof(self, proof):
        source = self.flow.directory / "synthetic-proof.json"
        atomic_json(source, proof)
        return self.flow.ticket_proof(source)

    def local_review(self):
        report = {"verdict": "PASS", "summary": SYNTHETIC, "method_followed": True,
            "criteria": [{"id": item["id"], "status": "PASS", "evidence": SYNTHETIC}
                         for item in self.task["acceptance"]], "findings": []}

        def synthetic_reviewer(argv, cwd, timeout, log, stdin):
            self.assertIn("--ephemeral", argv)
            self.assertIn("read-only", argv)
            self.assertIn("Confirmed ticket:", stdin)
            self.assertIn("cannot authenticate", stdin)
            skills = BUNDLE / ".agents/skills"
            self.assertNotIn(str(BUNDLE / "AGENTS.md"), stdin)  # factory rules are not product methods
            for method in (skills / "analyze-start/SKILL.md", skills / "ticketing/SKILL.md",
                           skills / "deep-review/references/compliance.md", skills / "safe-engine/references/controller.md"):
                self.assertIn(str(method), stdin)
            self.assertIn(f'owner "owner", authority "{DELEGATION}"', stdin)
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(report), encoding="utf-8")
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(SYNTHETIC, encoding="utf-8")
            return {"passed": True, "exit_code": 0, "synthetic": True}

        with patch("safe_engine.workflow.shutil.which", return_value=sys.executable), \
                patch("safe_engine.workflow.run_command", side_effect=synthetic_reviewer) as reviewer:
            result = self.flow.review(10)
        self.assertEqual(reviewer.call_count, 1)
        return result

    def cli(self, *args, ticket="alpha"):
        argv = [sys.executable, "-m", "safe_engine", "--project", str(self.root)]
        if ticket is not None:
            argv += ["--ticket", ticket]
        return subprocess.run([*argv, *args], cwd=BUNDLE, capture_output=True,
                              text=True, encoding="utf-8", timeout=30)

    def test_canonical_projection_accepts_crlf_but_rejects_ignored_owner_edits(self):
        for folded in (True, False):
            body = render_ticket(self.contract, fold_contract=folded)
            with self.subTest(folded=folded):
                self.assertEqual(parse_body(body), self.contract)
                self.assertEqual(parse_body(body.replace("\n", "\r\n")), self.contract)
            for edited in (body.replace("Synthetic outcome", "Owner changed outcome", 1),
                           body + "Owner adds a new requirement\n", body + body):
                with self.subTest(folded=folded, edited=edited[:60]), self.assertRaises(EngineError):
                    parse_body(edited)

    def test_legacy_body_from_original_format_keeps_complete_history(self):
        contract = deepcopy(self.contract)
        contract["scope_history"] = [{"revision": 1, "owner_words": "Keep this reminder. Keep it."}]
        contract["scope"]["purpose"] = {"older_custom_metadata": True}
        scope = contract["scope"]
        legacy = (f"## Before\n\n{scope['before']}\n\n## After\n\n{scope['after']}\n\n"
                  "## Acceptance\n\n" + "\n".join(f"- {c['id']}: {c['text']}" for c in scope["acceptance"])
                  + "\n\n<!-- safe-engine-ticket:v1 -->\n```json\n"
                  + json.dumps(contract, indent=2, ensure_ascii=False)
                  + "\n```\n<!-- /safe-engine-ticket -->\n")
        folded = render_ticket(parse_body(legacy))
        self.assertEqual(parse_body(folded), contract)
        self.assertEqual(scope_digest(parse_body(legacy)), scope_digest(parse_body(folded)))
        self.assertIn('<details>', folded)
        self.assertIn('Keep this reminder. Keep it.', folded)
        for edited in (folded.replace('<details>', '<details open>'),
                       folded.replace('Full contract: owner input, journeys and history', 'Changed expectation'),
                       folded.replace('</details>', 'New owner requirement\n</details>')):
            with self.subTest(edited=edited[:60]), self.assertRaises(EngineError):
                parse_body(edited)

    def test_scope_must_have_a_journey_sourced_owner_input_and_unique_criteria(self):
        for field, value in (("journeys", []), ("owner_input", [{"text": SYNTHETIC}]),
                             ("dependencies", ["beta", "beta"]),
                             ("acceptance", self.contract["scope"]["acceptance"] * 2)):
            with self.subTest(field=field):
                changed = deepcopy(self.contract)
                changed["scope"][field] = value
                with self.assertRaises(EngineError):
                    render_ticket(changed)

    def visual_contract(self):
        contract = deepcopy(self.contract)
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
        contract["activity"] = [{"at": self.initial_at, "actor": SYNTHETIC,
            "what": "Synthetic inspection", "why": "Verify retained input",
            "result": "Synthetic planning; no live action"}]
        return self.confirm(contract)

    def test_visual_and_legacy_layouts_preserve_complete_confirmed_contract(self):
        contract = self.visual_contract()
        contract["scope_history"] = [{"owner_words": "Keep this reminder. Keep it."}]
        expected = scope_digest(contract)
        for layout in ("auto", "legacy"):
            for folded in (True, False):
                with self.subTest(layout=layout, folded=folded):
                    body = render_ticket(contract, layout=layout, fold_contract=folded)
                    self.assertEqual(parse_body(body.replace("\n", "\r\n")), contract)
                    self.assertEqual(scope_digest(parse_body(body)), expected)
                    self.assertEqual(binding({**self.supplied(contract),
                        "contract": parse_body(body)})["scope"], contract["scope"])

    def test_visual_prose_edits_cannot_change_or_hide_the_bound_record(self):
        contract = self.visual_contract()
        for folded in (True, False):
            body = render_ticket(contract, fold_contract=folded)
            for field in ("purpose", "goal", "context", "approach", "flow"):
                with self.subTest(folded=folded, field=field), self.assertRaises(EngineError):
                    parse_body(body.replace(contract["scope"][field], "Changed owner expectation", 1))
            for edited in (body.replace(contract["progress"], "Claimed merged", 1),
                           body.replace("Synthetic inspection", "Claimed review", 1),
                           body + "New requirement outside contract\n"):
                with self.subTest(folded=folded, edited=edited[:50]), self.assertRaises(EngineError):
                    parse_body(edited)

    def test_new_visual_scope_fields_require_exact_confirmation(self):
        contract = self.visual_contract()
        for field in ("purpose", "goal", "context", "approach", "flow", "optional"):
            changed = deepcopy(contract)
            changed["scope"][field] = ["Changed optional scope"] if field == "optional" else "Changed scope"
            with self.subTest(field=field):
                self.assertNotEqual(scope_digest(changed), scope_digest(contract))
                with self.assertRaises(EngineError):
                    binding({"contract": parse_body(render_ticket(changed)), "observed_at": self.initial_at})

    def test_visual_progress_activity_refresh_keeps_scope_and_prior_history(self):
        contract = self.visual_contract()
        self.refresh(contract)
        original = scope_digest(contract)
        changed = deepcopy(contract)
        changed["progress"] = "Synthetic final check; still no real PR"
        changed["activity"].append({"at": self.initial_at, "actor": SYNTHETIC,
            "what": "Synthetic result", "why": "Preserve history", "result": "Synthetic only"})
        self.refresh(changed)
        captured = self.store.get("alpha")
        self.assertEqual(captured["contract"], changed)
        self.assertEqual(scope_digest(captured["contract"]), original)
        self.assertEqual(captured["contract"]["activity"][0], contract["activity"][0])
        self.assertTrue(self.store.status("alpha")["valid"])

    def test_partial_or_invalid_visual_fields_do_not_silently_fall_back(self):
        contract = self.visual_contract()
        for field in ("purpose", "goal", "context", "approach"):
            changed = deepcopy(contract)
            del changed["scope"][field]
            with self.subTest(field=field), self.assertRaises(EngineError):
                render_ticket(changed, layout="legacy")
        for field, value in (("flow", []), ("optional", "not an array"), ("optional", [""])):
            changed = deepcopy(contract)
            changed["scope"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(EngineError):
                render_ticket(changed)
        for field, value in (("progress", ""), ("activity", {}), ("activity", [{}])):
            changed = deepcopy(contract)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(EngineError):
                render_ticket(changed)
        with self.assertRaises(EngineError):
            render_ticket(contract, layout="unknown")

    def test_reserved_or_escaping_keys_are_rejected_before_paths_are_created(self):
        for key in ("con", "prn", "aux", "nul", "com1", "lpt9", "Alpha", "../alpha", "a/b", "1alpha", "a" * 65):
            with self.subTest(key=key), self.assertRaises(EngineError):
                Workflow(self.root, key)
        self.assertEqual(ticket_key("document-fix-12"), "document-fix-12")
        self.assertFalse((self.root / ".factory").exists())

    def test_confirmation_must_bind_exact_revision_scope_and_observation(self):
        self.refresh()
        self.assertTrue(self.store.status("alpha")["confirmed"])
        for field, value in (("digest", "stale"), ("revision", 99), ("source", "")):
            with self.subTest(field=field):
                changed = deepcopy(self.contract)
                changed["confirmation"][field] = value
                self.refresh(changed)
                self.assertFalse(self.store.status("alpha")["confirmed"])
                with self.assertRaises(EngineError):
                    self.store.ready("alpha")
        changed = deepcopy(self.contract)
        changed.pop("confirmation")
        self.refresh(changed)
        self.assertFalse(self.store.status("alpha")["confirmed"])
        capture = self.supplied()
        capture["contract"] = deepcopy(self.contract)
        capture["observed_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        capture["contract"]["confirmation"]["at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(EngineError, "postdate"):
            binding(capture)

    def test_scope_revision_preserves_original_request_and_append_only_owner_input(self):
        self.refresh()
        for index, mutate in enumerate((lambda c: c["scope"].update(after="Synthetic changed outcome without revision"),
                       lambda c: c["scope"].update(original_request="Synthetic replaced original request"),
                       lambda c: c["scope"].update(owner_input=[{"text": "replacement", "source": "synthetic:2"}]))):
            changed = deepcopy(self.contract)
            mutate(changed)
            if index:
                changed["revision"] = 2  # Exercise preservation independently of the no-rewrite check.
            self.confirm(changed)
            with self.assertRaises(EngineError):
                self.refresh(changed)
            self.assertFalse(self.store.status("alpha")["valid"])
            self.refresh()
        changed = deepcopy(self.contract)
        changed["revision"] = 2
        changed["scope"]["after"] = "Synthetic owner revised the expected after"
        changed["scope"]["owner_input"].append({"text": SYNTHETIC + ": revision reason", "source": "synthetic:2"})
        self.confirm(changed)
        self.refresh(changed)
        self.assertEqual(self.store.status("alpha")["revision"], 2)
        with self.assertRaisesRegex(EngineError, "revision|rewrite"):
            self.refresh()

    def test_replayed_incomplete_or_bad_projection_refresh_invalidates_old_authority(self):
        initial = self.refresh()
        history = self.store.root / "history/alpha/000001.json"
        original_history = history.read_bytes()
        with self.assertRaisesRegex(EngineError, "replayed"):
            self.store.capture(initial)
        self.assertFalse(self.store.status("alpha")["valid"])
        for mutation in (lambda s: s.update(complete=False), lambda s: s.update(body=s["body"] + "unreconciled note")):
            self.refresh()
            changed = self.supplied()
            mutation(changed)
            with self.assertRaises(EngineError):
                self.store.capture(changed)
            with self.assertRaises(EngineError):
                self.store.ready("alpha")
        self.assertEqual(history.read_bytes(), original_history)
        self.refresh()
        self.assertTrue(self.store.ready("alpha")[0]["valid"])

    def test_failed_access_preserves_snapshot_history_until_successful_refresh(self):
        self.start()
        before = self.flow.load()
        history = self.store.root / "history/alpha/000001.json"
        preserved = history.read_bytes()
        self.store.failed("alpha", "Synthetic MCP timeout; no real network call")
        status = self.flow.status()
        self.assertFalse(status["ticket_current"])
        self.assertEqual(status["phase"], "analyze")
        self.assertEqual(self.flow.load(), before)
        with self.assertRaises(EngineError):
            self.artifact("analysis")
        self.assertEqual(history.read_bytes(), preserved)
        self.refresh()
        self.assertEqual(self.artifact("analysis")["phase"], "plan")

    def test_pending_activity_blocks_until_reconciled_and_cannot_disappear(self):
        self.activity = [{"id": "synthetic-comment-1", "at": self.initial_at,
            "author": "Synthetic owner assertion double", "text": SYNTHETIC + ": proposed scope change",
            "disposition": "pending"}]
        self.refresh()
        with self.assertRaisesRegex(EngineError, "unresolved"):
            self.store.ready("alpha")
        self.activity[0].update(disposition="resolved", reason="Synthetic owner kept scope; synthetic:decision-1")
        self.refresh()
        self.store.ready("alpha")
        with self.assertRaisesRegex(EngineError, "vanished"):
            self.refresh(activity=[])
        self.assertFalse(self.store.status("alpha")["valid"])
        self.refresh()
        self.assertEqual(len(self.store.get("alpha")["activity"]), 1)

    def test_cancelled_blocked_done_and_closed_tickets_cannot_resume_build(self):
        for lifecycle in ("cancelled", "blocked", "done"):
            with self.subTest(lifecycle=lifecycle):
                changed = deepcopy(self.contract)
                changed["lifecycle"] = lifecycle
                self.refresh(changed)
                with self.assertRaisesRegex(EngineError, "owner stop"):
                    self.store.ready("alpha")
        self.refresh(status="closed")
        with self.assertRaisesRegex(EngineError, "Closed"):
            self.store.ready("alpha")
        self.refresh()
        self.store.ready("alpha")

    def test_cache_loss_cannot_restart_numbering_or_duplicate_remote_identity(self):
        self.refresh()
        history = self.store.root / "history/alpha/000001.json"
        preserved = history.read_bytes()
        self.store.path("alpha").unlink()
        with self.assertRaisesRegex(EngineError, "cache is missing"):
            self.refresh()
        with self.assertRaisesRegex(EngineError, "already has a key"):
            self.refresh(key="alias")
        self.assertEqual(history.read_bytes(), preserved)
        self.assertFalse((self.store.root / "history/alias/000001.json").exists())

    def test_remote_identity_aliases_and_inconsistent_urls_do_not_create_new_lineage(self):
        self.refresh()
        alias = self.supplied(key="alias")
        alias["identity"]["workspace"] = "Synthetic/Ticket-Fixture"
        alias["identity"]["url"] = "https://github.com/Synthetic/Ticket-Fixture/issues/101"
        with self.assertRaisesRegex(EngineError, "already has a key"):
            self.store.capture(alias)
        for field, value in (("url", "https://github.com/synthetic/ticket-fixture/issues/101?alias=1"),
                             ("id", "0101"), ("url", "https://user:pass@github.com/synthetic/ticket-fixture/issues/101")):
            with self.subTest(field=field):
                supplied = self.supplied(key="other", number="102")
                supplied["identity"][field] = value
                with self.assertRaises(EngineError):
                    self.store.capture(supplied)

    def test_provider_neutral_capture_reports_asserted_access_limits(self):
        supplied = self.supplied()
        supplied["identity"] = {"provider": "jira", "workspace": "synthetic-workspace", "id": "DOC-101",
                                "url": "https://jira.example.invalid/browse/DOC-101"}
        status = self.store.capture(supplied)
        self.assertTrue(status["confirmed"])
        self.assertIn("not authenticated", status["freshness_limit"])
        record = self.store.get("alpha")
        original_scope, original_raw = status["scope_digest"], record["raw_digest"]
        changed = deepcopy(supplied)
        changed.update(observed_at=self.fresh_observed_at(), title="Synthetic title changed")
        self.store.capture(changed)
        self.assertEqual(self.store.status("alpha")["scope_digest"], original_scope)
        self.assertNotEqual(self.store.get("alpha")["raw_digest"], original_raw)

    def test_named_initialization_requires_v2_matching_scope_and_dedicated_session(self):
        self.refresh()
        with self.assertRaisesRegex(EngineError, "builder session"):
            self.flow.initialize(self.task, self.profile)
        for field in ("request", "acceptance"):
            changed = deepcopy(self.task)
            if field == "request":
                changed[field] = "Synthetic unrelated request"
            else:
                changed[field][0]["text"] = "Synthetic weaker criterion"
            with self.assertRaisesRegex(EngineError, "must match"):
                self.flow.initialize(changed, self.profile, session="synthetic:builder-alpha")
        with self.assertRaisesRegex(EngineError, "version 2"):
            self.flow.ticket_proposal(self.task, {"version": 1, "checks": []})
        self.assertFalse((self.flow.directory / "state.json").exists())
        result = self.flow.initialize(self.task, self.profile, session="synthetic:builder-alpha")
        self.assertEqual(Path(result["state"]), self.root / ".factory/runs/alpha/state.json")
        self.assertFalse((self.root / ".factory/state.json").exists())

    def test_phase_refresh_must_be_new_and_observed_after_saved_phase(self):
        self.start()
        self.refresh()  # New capture, but deliberately observed before the next saved phase.
        self.artifact("analysis")
        # `record plan` needs no new capture, so it succeeds on the stale one.
        self.assertEqual(self.artifact("plan")["phase"], "build")
        unchanged = self.flow.load()
        with self.assertRaisesRegex(EngineError, "after the saved phase"):
            self.artifact("implementation")  # Still observed before the saved plan phase.
        self.assertEqual(self.flow.load(), unchanged)
        self.refresh()
        self.assertEqual(self.artifact("implementation")["phase"], "manual")
        # Records-only repair and handoff keep the same rule: test_record_repairs
        # (ticket freshness) and test_full_ticket_cycle assert their "fresh capture" refusals.

    def test_plan_needs_no_new_capture_but_implementation_still_does(self):
        self.start()
        self.artifact("analysis")
        self.assertEqual(self.artifact("plan")["phase"], "build")
        before = self.flow.load()
        with self.assertRaisesRegex(EngineError, "new complete"):
            self.artifact("implementation")
        self.assertEqual(self.flow.load(), before)
        self.refresh()
        self.artifact("implementation")

    def test_testing_and_stage_skips_cannot_advance_unfinished_ticket(self):
        self.build()
        before = self.flow.load()
        with patch("safe_engine.workflow.run_command") as command:
            for action in (self.flow.check, lambda: self.artifact("batch"),
                           lambda: self.flow.feature_check(["document"], self.root / "README.md")):
                with self.assertRaises(EngineError):
                    action()
            command.assert_not_called()
        self.assertEqual(self.flow.load(), before)

    def test_manual_fingerprint_binds_scope_but_ordinary_refresh_does_not_invalidate_it(self):
        self.build()
        self.finish_manual()
        state = self.flow.load()
        original = state["manual_candidate"]
        self.refresh()
        self.assertEqual(production_fingerprint(self.root, self.profile, state["ticket"]), original)
        revised = deepcopy(state["ticket"])
        revised["scope"]["after"] = "Synthetic changed expected outcome"
        self.assertNotEqual(production_fingerprint(self.root, self.profile, revised), original)
        self.flow.require_manual(state)

    def test_full_ticket_cycle_runs_one_gate_requires_proof_and_fresh_handoff(self):
        self.build()
        evidence = self.finish_manual()
        manual_candidate = self.flow.status()["manual_candidate"]
        self.task, self.profile = self.configure_check()
        self.assertEqual(production_fingerprint(self.root, self.profile, self.flow.load()["ticket"]), manual_candidate)
        self.flow.seal(self.task, self.profile, self.review_contract())
        self.artifact("batch")
        self.assertEqual(self.flow.check()["phase"], "review")
        self.assertEqual((self.flow.directory / "synthetic-check-count").read_text(), "1")
        with self.assertRaises(EngineError):
            self.flow.check()
        with patch("safe_engine.workflow.run_command") as reviewer:
            with self.assertRaisesRegex(EngineError, "ticket-proof"):
                self.flow.review(10)
            reviewer.assert_not_called()
        self.record_proof(self.proof(evidence))
        self.assertEqual(self.local_review()["phase"], "ready")
        with self.assertRaisesRegex(EngineError, "new complete"):
            self.flow.handoff()
        self.refresh()
        result = self.flow.handoff()
        handoff = Path(result["handoff"]).read_text(encoding="utf-8")
        self.assertIn("Revision: 1", handoff)
        self.assertIn("not remote review", handoff)
        self.assertFalse(read_json(self.store.root / "claims.json")["alpha"]["active"])
        self.assertTrue(list((self.flow.directory / "ticket-observations").glob("*.json")))

    def test_ticket_proof_rejects_stale_unknown_missing_and_tampered_evidence(self):
        evidence = self.verified()
        valid = self.proof(evidence)
        mutations = [lambda p: p.update(scope_digest="stale"), lambda p: p.update(criteria=[]),
                     lambda p: p["criteria"][0].update(status="UNKNOWN"),
                     lambda p: p["criteria"][0]["evidence"][0].update(sha256="bad"),
                     lambda p: p["criteria"][0].pop("deviations"),
                     lambda p: p["criteria"][0].update(deviations=[{"change": "x", "reason": SYNTHETIC}])]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                changed = deepcopy(valid)
                mutate(changed)
                with self.assertRaises(EngineError):
                    self.record_proof(changed)
        self.record_proof(valid)
        evidence.write_text("Synthetic replaced evidence", encoding="utf-8")
        with self.assertRaisesRegex(EngineError, "Mapped ticket evidence changed"):
            self.flow.require_ticket_proof(self.flow.load())

    def test_scope_drift_invalidates_current_verdicts_without_destroying_saved_run(self):
        self.verified()
        original = self.flow.load()
        changed = deepcopy(self.contract)
        changed["revision"] = 2
        changed["scope"]["after"] = "Synthetic latest owner expectation changed"
        self.confirm(changed)
        self.refresh(changed)
        status = self.flow.status()
        self.assertFalse(status["ticket_current"])
        self.assertFalse(status["checks_current"])
        self.assertEqual(self.flow.load(), original)
        with self.assertRaises(EngineError):
            self.flow.require_checks(original)
        self.store.path("alpha").unlink()
        missing = self.flow.status()
        self.assertFalse(missing["ticket_current"])
        self.assertTrue(missing["ticket_error"])
        self.assertEqual(missing["phase"], "review")

    def test_reviewed_scope_amendment_preserves_history_and_restarts_analysis(self):
        self.verified()
        previous = self.flow.load()
        changed = deepcopy(self.contract)
        changed["revision"] = 2
        changed["scope"]["acceptance"][0]["text"] = "Synthetic owner revised the latest criterion"
        changed["scope"]["owner_input"].append({"text": SYNTHETIC + ": requested criterion revision", "source": "synthetic:2"})
        self.confirm(changed)
        self.refresh(changed)
        new_task = deepcopy(self.task)
        new_task["acceptance"][0]["text"] = changed["scope"]["acceptance"][0]["text"]
        review = self.review_contract(new_task, self.profile)
        with self.assertRaisesRegex(EngineError, "scope-change authority"):
            self.flow.amend(new_task, self.profile, review, "Synthetic owner revision")
        self.assertEqual(self.flow.load(), previous)
        review["acceptance_change_authority"] = SYNTHETIC + ": explicit scope-change authority"
        result = self.flow.amend(new_task, self.profile, review, "Synthetic owner revision")
        current = self.flow.load()
        self.assertEqual(result["phase"], "analyze")
        self.assertIsNone(current["checks"])
        self.assertIsNone(current["manual"])
        self.assertEqual(current["history"][:-1], previous["history"])
        self.assertEqual(current["contract_history"][-1]["ticket"], previous["ticket"])
        self.assertEqual(current["contract_history"][-1]["protected"], previous["protected"])
        self.assertEqual(current["original_task"], previous["original_task"])
        self.assertEqual(current["initial_fingerprint"], self.flow.current(current))
        self.assertFalse({"analysis", "plan", "implementation", "manual", "batch"} & set(current["artifacts"]))
        self.assertEqual(self.artifact("analysis")["phase"], "plan")

    def test_amendment_requires_exact_independent_review_and_cannot_revive_cancellation(self):
        self.build()
        review = self.review_contract()
        for field, value in (("old_digest", "stale"), ("new_digest", "stale"),
                             ("independent", False), ("authority", "")):
            with self.subTest(field=field):
                invalid = {**review, field: value}
                before = self.flow.load()
                with self.assertRaises(EngineError):
                    self.flow.amend(self.task, self.profile, invalid, "Synthetic amendment")
                self.assertEqual(self.flow.load(), before)
        self.flow.cancel("Synthetic local fixture cancellation only")
        with self.assertRaises(EngineError):
            self.flow.amend(self.task, self.profile, review, "Synthetic cannot revive cancellation")
        with self.assertRaises(EngineError):
            self.flow.initialize(self.task, self.profile, session="synthetic:new-session")
        self.assertEqual(self.flow.status()["phase"], "cancelled")

    def test_outputs_cannot_escape_into_another_ticket_namespace(self):
        self.refresh()
        profile = deepcopy(self.profile)
        profile["checks"] = [{"id": "document", "kind": "unit", "argv": ["{python}", "-c", "print('synthetic')"],
            "timeout_seconds": 10, "artifacts": [".factory/runs/beta/outputs/proof.txt"]}]
        with self.assertRaisesRegex(EngineError, "selected run"):
            self.flow.initialize(self.task, profile, session="synthetic:builder-alpha")
        self.assertFalse((self.flow.directory / "state.json").exists())
        with patch("safe_engine.workflow.run_command") as command:
            with self.assertRaisesRegex(EngineError, "escaped"):
                self.flow.execute_checks({"sequence": 1}, profile["checks"])
            command.assert_not_called()

    def test_claims_serialize_checkout_and_preserve_lineage_after_release(self):
        self.store.claim("alpha", "synthetic:run-1", self.flow.directory)
        path = self.store.root / "claims.json"
        claims = read_json(path)
        claims["alpha"]["expires_at"] = "2000-01-01T00:00:00+00:00"  # Synthetic stale legacy metadata; never permission to steal.
        atomic_json(path, claims)
        with self.assertRaisesRegex(EngineError, "Another ticket"):
            self.store.claim("beta", "synthetic:run-2", self.root / ".factory/runs/beta")
        with self.assertRaisesRegex(EngineError, "identity"):
            self.store.release("alpha", "synthetic:wrong-run")
        self.store.release("alpha", "synthetic:run-1")
        self.store.claim("beta", "synthetic:run-2", self.root / ".factory/runs/beta")
        with self.assertRaisesRegex(EngineError, "fresh-run bypass"):
            self.store.claim("alpha", "synthetic:new-run", self.flow.directory)
        self.assertEqual(read_json(path)["alpha"]["run_id"], "synthetic:run-1")

    def test_independent_worktrees_share_capture_and_allow_distinct_ticket_writers(self):
        self.refresh()
        second = self.root.parent / "second consumer"
        self.git("worktree", "add", "--detach", str(second), "HEAD")
        other_store = TicketStore(second)
        self.assertEqual(other_store.root, self.store.root)
        self.assertEqual(other_store.get("alpha"), self.store.get("alpha"))
        self.store.claim("alpha", "synthetic:run-alpha", self.flow.directory)
        other_store.claim("beta", "synthetic:run-beta", second / ".factory/runs/beta")
        with self.assertRaisesRegex(EngineError, "fresh-run bypass"):
            other_store.claim("alpha", "synthetic:duplicate-alpha", second / ".factory/runs/alpha")
        claims = read_json(self.store.root / "claims.json")
        self.assertTrue(claims["alpha"]["active"] and claims["beta"]["active"])

    def test_active_coordination_lock_refuses_second_claim_without_writing_it(self):
        with locked(self.store.root / "coordination"):
            with self.assertRaisesRegex(EngineError, "Another Safe Engine operation"):
                self.store.claim("alpha", "synthetic:run-alpha", self.flow.directory)
        self.assertFalse((self.store.root / "claims.json").exists())
        self.store.claim("alpha", "synthetic:run-alpha", self.flow.directory)

    def test_dependencies_need_confirmed_integrated_result_in_selected_baseline(self):
        self.contract = self.make_contract(dependencies=["beta"])
        dependency = self.make_contract()
        dependency["lifecycle"] = "done"
        self.refresh()
        self.refresh(dependency, key="beta", number="102", status="closed")
        with self.assertRaisesRegex(EngineError, "integrated commit"):
            self.store.dependencies("alpha")
        dependency["delivery"] = {"status": "integrated", "scope_digest": scope_digest(dependency),
            "commit": self.git("rev-parse", "HEAD"), "evidence": SYNTHETIC + ": dependency/cloud-review assertion only"}
        self.refresh(dependency, key="beta", number="102", status="closed")
        self.store.dependencies("alpha")
        # A saved synthetic boundary, rather than a same-clock-tick wall-time race.
        boundary = self.store.get("beta")["observed_at"]
        self.refresh()
        with self.assertRaisesRegex(EngineError, "after the saved phase"):
            self.store.dependencies("alpha", after=boundary)
        self.refresh(dependency, key="beta", number="102", status="closed")
        self.store.dependencies("alpha", after=boundary)
        changed = deepcopy(dependency)
        changed["delivery"]["scope_digest"] = "stale"
        self.refresh(changed, key="beta", number="102", status="closed")
        with self.assertRaisesRegex(EngineError, "accepted scope"):
            self.store.dependencies("alpha")
        self.refresh(dependency, key="beta", number="102", status="closed")
        self.git("checkout", "-qb", "synthetic-future")
        (self.root / "future.txt").write_text("Synthetic dependency future commit\n", encoding="utf-8")
        self.commit("Synthetic dependency not integrated into consumer")
        future = self.git("rev-parse", "HEAD")
        self.git("checkout", "--detach", "HEAD~1")
        changed["delivery"].update(scope_digest=scope_digest(dependency), commit=future)
        self.refresh(changed, key="beta", number="102", status="closed")
        with self.assertRaises(EngineError):
            self.store.dependencies("alpha")

    def test_dependency_cycles_and_stale_observations_block_before_build(self):
        self.contract = self.make_contract(dependencies=["beta"])
        dependency = self.make_contract(dependencies=["alpha"])
        self.refresh()
        self.refresh(dependency, key="beta", number="102")
        with self.assertRaisesRegex(EngineError, "cycle"):
            self.store.dependencies("alpha")
        self.contract = self.make_contract(dependencies=["alpha"])
        self.contract["revision"] = 2
        self.confirm(self.contract)
        self.refresh()
        with self.assertRaisesRegex(EngineError, "cycle"):
            self.store.dependencies("alpha")

    def test_failed_initial_state_save_releases_only_its_empty_reservation(self):
        self.refresh()
        with patch("safe_engine.workflow.save", side_effect=OSError("Synthetic first-save disk failure")):
            with self.assertRaises(OSError):
                self.flow.initialize(self.task, self.profile, session="synthetic:builder-alpha")
        self.assertNotIn("alpha", read_json(self.store.root / "claims.json"))
        self.assertFalse((self.flow.directory / "state.json").exists())
        self.flow.initialize(self.task, self.profile, session="synthetic:builder-alpha")
        self.assertEqual(self.flow.status()["phase"], "analyze")

    def test_failed_post_claim_observation_write_allows_retry_without_history_loss(self):
        self.refresh()
        capture = self.store.get("alpha")
        capture_bytes = self.store.path("alpha").read_bytes()
        ticket_history = {path.name: path.read_bytes()
                          for path in (self.store.root / "history/alpha").glob("*.json")}
        self.flow.directory.mkdir(parents=True, exist_ok=True)
        obstruction = self.flow.directory / "ticket-observations"
        obstruction.write_text(SYNTHETIC + ": intentional observation-directory obstruction", encoding="utf-8")
        preserved_obstruction = obstruction.read_bytes()

        # Real filesystem OSError occurs after the durable claim, before state/history save.
        with self.assertRaises(OSError):
            self.flow.initialize(self.task, self.profile, session="synthetic:failed-observation-builder")
        claims_path = self.store.root / "claims.json"
        self.assertTrue(claims_path.exists())
        self.assertEqual(read_json(claims_path), {})
        self.assertFalse((self.flow.directory / "state.json").exists())
        self.assertEqual(list((self.flow.directory / "history").glob("*.json")), [])
        self.assertEqual(obstruction.read_bytes(), preserved_obstruction)
        self.assertEqual(self.store.path("alpha").read_bytes(), capture_bytes)
        self.assertEqual({path.name: path.read_bytes()
                          for path in (self.store.root / "history/alpha").glob("*.json")}, ticket_history)

        obstruction.unlink()  # Remove only the disposable fixture's intentional obstruction.
        result = self.flow.initialize(self.task, self.profile, session="synthetic:retry-observation-builder")
        self.assertEqual(result["phase"], "analyze")
        state = self.flow.load()
        self.assertEqual(read_json(claims_path)["alpha"]["run_id"], state["run_id"])
        self.assertTrue(read_json(claims_path)["alpha"]["active"])
        self.assertEqual(read_json(self.flow.directory / "ticket-observations" /
                                   f"{capture['sequence']:06d}.json"), capture)
        first_history = self.flow.directory / "history/0001.json"
        first_history_bytes = first_history.read_bytes()
        self.assertEqual(read_json(first_history), state)
        self.artifact("analysis")
        self.assertEqual(self.flow.status()["phase"], "plan")
        self.assertEqual(first_history.read_bytes(), first_history_bytes)
        self.assertEqual(len(self.flow.load()["history"]), 2)
        self.assertEqual(self.store.path("alpha").read_bytes(), capture_bytes)
        self.assertEqual({path.name: path.read_bytes()
                          for path in (self.store.root / "history/alpha").glob("*.json")}, ticket_history)

    def test_missing_run_state_cannot_erase_saved_history_or_claim(self):
        self.start()
        history = self.flow.directory / "history/0001.json"
        preserved = history.read_bytes()
        self.flow.directory.joinpath("state.json").unlink()
        with self.assertRaisesRegex(EngineError, "preserved run history"):
            self.flow.initialize(self.task, self.profile, session="synthetic:replacement-builder")
        self.assertEqual(history.read_bytes(), preserved)

    def test_cli_failed_or_mismatched_import_invalidates_selected_ticket(self):
        self.refresh()
        source = self.root / ".factory/synthetic-capture.json"
        source.parent.mkdir(exist_ok=True)
        for content in ("not JSON", json.dumps(self.supplied(key="beta", number="102"))):
            with self.subTest(content=content[:25]):
                source.write_text(content, encoding="utf-8")
                result = self.cli("ticket-capture", "--source", str(source))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(self.store.status("alpha")["valid"])
                self.refresh()
        result = self.cli("ticket-refresh-failed", "--reason", "Synthetic failed access")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["valid"])

    def test_cli_named_selection_and_proposal_render_have_truthful_limits(self):
        source = self.root / ".factory/synthetic-contract.json"
        atomic_json(source, self.contract)
        result = self.cli("ticket-render", "--source", str(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = json.loads(result.stdout)
        self.assertFalse(rendered["remote_write"])
        self.assertEqual(rendered["scope_digest"], scope_digest(self.contract))
        self.assertFalse(self.store.path("alpha").exists())
        capture = self.root / ".factory/synthetic-capture.json"
        atomic_json(capture, self.supplied())
        result = self.cli("ticket-capture", "--source", str(capture))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not authenticated", json.loads(result.stdout)["freshness_limit"])
        task, profile = self.root / ".factory/task.json", self.root / ".factory/profile.json"
        atomic_json(task, self.task)
        atomic_json(profile, self.profile)
        result = self.cli("init", "--task", str(task), "--profile", str(profile), "--session", "synthetic:cli-builder")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["builder_session"], "synthetic:cli-builder")
        wrong = self.cli("status", ticket=None)
        self.assertEqual(wrong.returncode, 2)
        right = self.cli("status")
        self.assertEqual(right.returncode, 0, right.stderr)
        self.assertEqual(json.loads(right.stdout)["run_id"], self.flow.status()["run_id"])

    def test_unbound_v2_contract_and_runtime_path_remain_unchanged(self):
        legacy = Workflow(self.root)
        result = legacy.initialize(self.task, self.profile)
        state = legacy.load()
        self.assertEqual(state["schema_version"], 1)
        self.assertNotIn("ticket", state)
        self.assertEqual(state["contract_digest"], digest({"task": self.task, "profile": self.profile}))
        self.assertEqual(Path(result["state"]), self.root / ".factory/state.json")
        self.refresh()
        with self.assertRaisesRegex(EngineError, "legacy run"):
            self.flow.initialize(self.task, self.profile, session="synthetic:builder-alpha")
        self.assertEqual(legacy.load(), state)
        self.assertFalse((self.flow.directory / "state.json").exists())

    def test_legacy_v1_keeps_two_gates_and_no_ticket_contract(self):
        script = self.root / "synthetic_legacy_check.py"
        script.write_text("from pathlib import Path\nassert 'preserve this sentence' in Path('README.md').read_text()\n"
                          "p=Path('.factory/synthetic-v1-count')\n"
                          "p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n", encoding="utf-8")
        self.commit("Synthetic legacy configured check")
        profile = {"version": 1, "interface": "library", "checks": [{"id": "document", "kind": "unit",
            "argv": ["{python}", "synthetic_legacy_check.py"], "timeout_seconds": 10}],
            "protected_paths": ["synthetic_legacy_check.py"], "environment_inputs": [], "input_files": []}
        task = deepcopy(self.task)
        task["acceptance"][0] = {"id": "A1", "text": task["acceptance"][0]["text"], "checks": ["document"]}
        legacy = Workflow(self.root)
        legacy.initialize(task, profile)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind, legacy)
        self.assertEqual(legacy.check()["phase"], "improve")
        self.artifact("improvement", legacy)
        self.assertEqual(legacy.check()["phase"], "review")
        self.assertEqual((legacy.directory / "synthetic-v1-count").read_text(), "2")
        self.assertNotIn("ticket", legacy.load())
        self.assertNotIn("delivery_version", legacy.load())

    @unittest.skipUnless(os.name == "nt", "Real NTFS junction boundary")
    def test_junctions_cannot_redirect_named_run_or_ticket_history_writes(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        sentinel = outside / "preserve.txt"
        sentinel.write_text("Synthetic outside sentinel\n", encoding="utf-8")
        for link in (self.root / ".factory/runs/alpha", self.store.root / "history/alpha"):
            with self.subTest(link=str(link)):
                link.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                               check=True, capture_output=True)
                try:
                    with self.assertRaisesRegex(EngineError, "reparse"):
                        if ".factory" in link.parts:
                            Workflow(self.root, "alpha")
                        else:
                            self.refresh()
                    self.assertEqual(list(outside.iterdir()), [sentinel])
                    self.assertEqual(sentinel.read_text(encoding="utf-8"), "Synthetic outside sentinel\n")
                finally:
                    os.rmdir(link)  # Remove only the known fixture junction, never its target tree.


if __name__ == "__main__":
    unittest.main()
