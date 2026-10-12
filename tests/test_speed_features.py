"""Regressions for the speed work: parallel checks, cheap ticket refresh, proof drafts,
handoff tables, carried manual QA, review cap and external reviewer, plus hardening.

Reviewer, owner and manual receipts are explicit synthetic doubles. Commands, Git,
locks, hashes and state files are real; no product, tracker or cloud acceptance is claimed.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import test_tickets as tickets
import test_workflow as legacy
from safe_engine.acceptance import carried_observation
from safe_engine.project import EngineError, file_hash, git, production_fingerprint, rescan, snapshot, validate_profile
from safe_engine.proof import proof_draft
from safe_engine.storage import atomic_json, read_json
from safe_engine.tickets import timestamp
from safe_engine.workflow import Workflow
from speed_fixtures import BUNDLE, RENDEZVOUS, PAUSE, Base, report, finding, deferral, script, command

PARTNER = "none (test owner is a developer)"  # the handoff's technical-partner decision


class ParallelChecksTests(Base):
    def manual_done(self):
        f = self.fixture()
        f.start_build()
        f.finish_manual()
        return f

    def test_profile_accepts_only_an_explicit_boolean(self):
        base = {"version": 2, "interface": "library", "checks": [], "environment_inputs": [],
                "input_files": [], "protected_paths": []}
        for value in (True, False):
            validate_profile({**base, "parallel_checks": value}, draft=True)
        for value in ("true", 1, 0, None, [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(EngineError, "parallel_checks"):
                validate_profile({**base, "parallel_checks": value}, draft=True)

    def test_two_checks_run_concurrently_with_their_own_logs(self):
        f = self.manual_done()
        script(f, "rendezvous.py", RENDEZVOUS)
        pair = [command("alpha", "rendezvous.py", ".factory/rv-a", ".factory/rv-b"),
                command("beta", "rendezvous.py", ".factory/rv-b", ".factory/rv-a")]
        # Each check waits for the other's marker, so only a concurrent run can pass.
        state = {"sequence": 7, "profile": {"parallel_checks": True}}
        results = f.flow.execute_checks(state, pair)
        self.assertEqual([r["id"] for r in results], ["alpha", "beta"])
        self.assertTrue(all(r["passed"] for r in results), results)
        self.assertEqual(len({r["log"] for r in results}), 2)
        for result in results:
            self.assertTrue(Path(result["log"]).is_file())
            self.assertEqual(file_hash(Path(result["log"])), result["log_sha256"])

    def test_full_batch_keeps_outputs_per_check_and_serial_default_does_not_overlap(self):
        for parallel, overlap in ((True, True), (False, False), (None, False)):
            with self.subTest(parallel=parallel):
                f = self.manual_done()
                script(f, "pause.py", PAUSE)
                self.seal_with(f, [command(name, "pause.py", f".factory/outputs/{name}.txt",
                                           artifacts=[f".factory/outputs/{name}.txt"]) for name in ("alpha", "beta")],
                               parallel)
                result = f.flow.check()
                self.assertTrue(result["checks_passed"], result)
                first, second = result["results"]
                self.assertEqual([len(r["artifacts"]) for r in (first, second)], [1, 1])
                self.assertNotEqual(first["artifacts"][0]["path"], second["artifacts"][0]["path"])
                gap = (datetime.fromisoformat(second["started_at"]) - datetime.fromisoformat(first["started_at"])).total_seconds()
                # Each command pauses 0.4s: concurrent starts are close, serial starts a full pause apart.
                self.assertTrue(gap < 0.2 if overlap else gap > 0.3, gap)

    def test_one_failing_check_fails_the_whole_batch(self):
        f = self.manual_done()
        script(f, "pass.py", "import time\ntime.sleep(0.2)\n")
        script(f, "fail.py", "import sys\nsys.exit(3)\n")
        self.seal_with(f, [command("good", "pass.py"), command("bad", "fail.py")], True)
        result = f.flow.check()
        self.assertFalse(result["checks_passed"])
        self.assertEqual({r["id"]: r["passed"] for r in result["results"]}, {"good": True, "bad": False})
        self.assertTrue(all(Path(r["log"]).is_file() for r in result["results"]))
        self.assertEqual(result["phase"], "verify")
        with self.assertRaisesRegex(EngineError, "require correction"):
            f.flow.check()

    def test_input_mutation_during_checks_rejects_serial_and_parallel(self):
        edit = "from pathlib import Path\nPath('README.md').write_text('edited by a check\\n')\n"
        for parallel in (False, True):
            with self.subTest(parallel=parallel):
                f = self.manual_done()
                script(f, "pass.py", "import time\ntime.sleep(0.2)\n")
                script(f, "edit.py", edit)
                self.seal_with(f, [command("good", "pass.py"), command("edit", "edit.py")], parallel)
                with snapshot():  # As the CLI runs it: scans are memoized unless the check phase forgets them.
                    result = f.flow.check()
                self.assertFalse(result["checks_passed"])
                self.assertTrue(all(r["passed"] for r in result["results"]))  # Both exit 0.
                self.assertFalse(f.flow.load()["checks"]["inputs_unchanged"])


class SnapshotSoundnessTests(Base):
    def test_edit_between_two_commands_changes_the_fingerprint(self):
        f = self.fixture()
        f.flow.initialize(f.task, f.profile)
        with snapshot():
            before = production_fingerprint(f.root, f.profile)
        (f.root / "README.md").write_text("edited between commands\n", encoding="utf-8")
        with snapshot():
            self.assertNotEqual(production_fingerprint(f.root, f.profile), before)
        with snapshot():
            self.assertNotEqual(f.flow.current(f.flow.load()), f.flow.load()["initial_fingerprint"])

    def test_scan_is_shared_within_a_command_until_rescan_forgets_it(self):
        f = self.fixture()
        with snapshot():
            first = production_fingerprint(f.root, f.profile)
            (f.root / "README.md").write_text("edited mid-command\n", encoding="utf-8")
            self.assertEqual(production_fingerprint(f.root, f.profile), first)  # Memoized scan.
            rescan()
            self.assertNotEqual(production_fingerprint(f.root, f.profile), first)
        self.assertNotEqual(production_fingerprint(f.root, f.profile), first)  # No scope: always fresh.

    def test_nested_snapshots_reuse_the_outer_scope(self):
        f = self.fixture()
        with snapshot():
            first = production_fingerprint(f.root, f.profile)
            with snapshot():
                (f.root / "README.md").write_text("edited in nested scope\n", encoding="utf-8")
                self.assertEqual(production_fingerprint(f.root, f.profile), first)
        self.assertNotEqual(production_fingerprint(f.root, f.profile), first)


class UnchangedCaptureTests(Base):
    def observation(self, f, **override):
        previous = f.store.get("alpha")
        value = {"version": 1, "unchanged": True, "key": "alpha", "observed_at": f.fresh_observed_at(),
                 "remote_updated_at": previous["remote_updated_at"], "status": previous["status"],
                 "transport": {"tool": tickets.SYNTHETIC, "source": "synthetic:unchanged"}}
        value.update(override)
        return value

    def planned(self):
        f = self.ticket_fixture()
        f.start()
        f.artifact("analysis")
        f.artifact("plan")
        return f

    def test_matching_updated_at_and_status_count_as_a_fresh_observation(self):
        f = self.planned()
        full = f.store.get("alpha")
        with self.assertRaisesRegex(EngineError, "new complete"):
            f.artifact("implementation")
        status = f.store.unchanged(self.observation(f))
        self.assertTrue(status["valid"] and status["confirmed"])
        record = f.store.get("alpha")
        self.assertEqual((record["sequence"], record["unchanged_from"]), (full["sequence"] + 1, full["sequence"]))
        self.assertEqual((record["body"], record["activity"], record["contract"]),
                         (full["body"], full["activity"], full["contract"]))
        self.assertTrue((f.store.root / f"history/alpha/{record['sequence']:06d}.json").exists())
        self.assertEqual(f.artifact("implementation")["phase"], "manual")
        self.assertTrue((f.flow.directory / "ticket-observations" / f"{record['sequence']:06d}.json").exists())

    def test_changed_updated_at_or_status_invalidates_and_needs_a_full_capture(self):
        f = self.planned()
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        for override in ({"remote_updated_at": past}, {"status": "closed"}):
            with self.subTest(override=override):
                with self.assertRaisesRegex(EngineError, "changed"):
                    f.store.unchanged(self.observation(f, **override))
                self.assertFalse(f.store.status("alpha")["valid"])
                with self.assertRaises(EngineError):
                    f.artifact("implementation")
                with self.assertRaisesRegex(EngineError, "complete capture|invalid|Invalid"):
                    f.store.unchanged(self.observation(f))
                f.refresh()  # The complete capture restores authority.
                f.store.ready("alpha")

    def test_unchanged_needs_a_prior_valid_capture_the_marker_and_a_newer_observation(self):
        f = self.ticket_fixture()
        with self.assertRaisesRegex(EngineError, "No current capture"):
            f.store.unchanged({**self.observation_for_missing(f)})
        f.refresh()
        for override in ({"unchanged": False}, {"version": 2}, {"transport": None}, {"transport": {"tool": "x"}},
                         {"observed_at": "2000-01-01T00:00:00+00:00"}, {"observed_at": "not a time"}):
            with self.subTest(override=override), self.assertRaises(EngineError):
                f.store.unchanged(self.observation(f, **override))
            f.refresh()
        record = f.store.get("alpha")
        with self.assertRaisesRegex(EngineError, "replayed"):  # Same instant as the capture itself.
            f.store.unchanged(self.observation(f, observed_at=record["observed_at"]))

    @staticmethod
    def observation_for_missing(f):
        now = f.fresh_observed_at()
        return {"version": 1, "unchanged": True, "key": "alpha", "observed_at": now, "remote_updated_at": now,
                "status": "open", "transport": {"tool": tickets.SYNTHETIC, "source": "synthetic:unchanged"}}

    def test_cli_unchanged_flag_records_a_numbered_observation_and_rejects_mismatch(self):
        f = self.ticket_fixture()
        f.refresh()
        source = f.root / ".factory/synthetic-observation.json"
        source.parent.mkdir(exist_ok=True)
        atomic_json(source, self.observation(f))
        result = f.cli("ticket-capture", "--unchanged", "--source", str(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(f.store.get("alpha")["sequence"], 2)
        atomic_json(source, self.observation(f, status="closed"))
        result = f.cli("ticket-capture", "--unchanged", "--source", str(source))
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(f.cli("ticket-status").stdout)["valid"])


class ProofDraftAndHandoffTests(Base):
    def test_draft_is_prefilled_from_receipt_checks_and_changes_then_round_trips(self):
        f = self.ticket_fixture()
        evidence = f.verified()
        out = f.flow.directory / "synthetic-draft.json"
        result = f.flow.ticket_proof_draft(out)
        self.assertEqual((result["complete"], result["unknown"]), (["before", "after"], []))
        draft, state = read_json(out), f.flow.load()
        self.assertEqual((draft["revision"], draft["scope_digest"]),
                         (state["ticket"]["revision"], state["ticket"]["scope_digest"]))
        row = draft["criteria"][0]
        self.assertEqual((row["id"], row["status"], row["before"], row["after"], row["deviations"]),
                         ("A1", "PASS", "", "", []))
        self.assertTrue(row["implementation"].startswith("Changed: "))
        self.assertIn("tests/synthetic_check.py", row["implementation"])
        mapped = {item["path"]: item["sha256"] for item in row["evidence"]}
        manual = evidence.relative_to(f.root).as_posix()
        check = state["checks"]["results"][0]
        log = Path(check["log"]).relative_to(f.root).as_posix()
        output = Path(check["artifacts"][0]["path"]).relative_to(f.root).as_posix()
        self.assertEqual(mapped[manual], file_hash(evidence))
        self.assertEqual((mapped[log], mapped[output]), (check["log_sha256"], check["artifacts"][0]["sha256"]))
        with self.assertRaises(EngineError):  # before/after are the agent's to write.
            f.record_proof(draft)
        row.update(before="Synthetic baseline", after="Synthetic outcome")
        self.assertEqual(f.record_proof(draft)["phase"], "review")
        self.assertEqual(f.local_review()["phase"], "ready")

    def test_proof_that_changes_while_recorded_is_refused(self):
        f = self.ticket_fixture()
        f.verified()
        out = f.flow.directory / "synthetic-draft.json"
        f.flow.ticket_proof_draft(out)
        draft = read_json(out)
        draft["criteria"][0].update(before="Synthetic baseline", after="Synthetic outcome")
        original = type(f.flow).capture_artifact

        def swap(flow, state, kind, source, current):
            atomic_json(Path(source), {**draft, "revision": draft["revision"] + 1})
            return original(flow, state, kind, source, current)
        with patch.object(type(f.flow), "capture_artifact", swap), \
                self.assertRaisesRegex(EngineError, "changed while it was recorded"):
            f.record_proof(draft)
        self.assertNotIn("ticket-proof", f.flow.load()["artifacts"])

    def test_status_is_unknown_when_receipt_or_checks_do_not_support_the_criterion(self):
        f = self.ticket_fixture()
        f.verified()
        state = f.flow.load()
        self.assertEqual(proof_draft(state, f.root)["criteria"][0]["status"], "PASS")
        failed = deepcopy(state)
        failed["checks"]["results"][0]["passed"] = False
        unobserved = deepcopy(state)
        unobserved["manual"]["observations"] = []
        empty = deepcopy(state)
        empty["manual"]["observations"] = []
        empty["task"]["acceptance"][0].update(mode="automated", checks=[])
        for name, changed in (("failed check", failed), ("no manual observation", unobserved), ("no evidence", empty)):
            with self.subTest(name):
                self.assertEqual(proof_draft(changed, f.root)["criteria"][0]["status"], "UNKNOWN")

    def test_draft_needs_review_phase_a_bound_ticket_and_writes_nothing_otherwise(self):
        f = self.ticket_fixture()
        f.build()
        out = f.flow.directory / "early-draft.json"
        with self.assertRaises(EngineError):
            f.flow.ticket_proof_draft(out)
        self.assertFalse(out.exists())
        plain = self.to_review()
        with self.assertRaisesRegex(EngineError, "bound ticket"):
            plain.flow.ticket_proof_draft(plain.root / ".factory/plain-draft.json")

    def test_draft_path_must_be_under_the_run_directory_or_outside_the_project(self):
        f = self.ticket_fixture()
        f.verified()
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        for inside in (f.root / "draft.json", f.root / ".factory/draft.json", f.root / "tests/draft.json",
                       f.root / ".factory/runs/beta/draft.json"):
            with self.subTest(path=str(inside.relative_to(f.root))), self.assertRaisesRegex(EngineError, "Use a path under"):
                f.flow.ticket_proof_draft(inside)
            self.assertFalse(inside.exists())
        for allowed in (f.flow.directory / "nested-draft.json", Path(outside.name) / "draft.json"):
            f.flow.ticket_proof_draft(allowed)
            self.assertTrue(allowed.is_file())
        result = f.cli("ticket-proof-draft", "--out", str(f.root / "refused.json"))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((f.root / "refused.json").exists())

    def test_cli_writes_the_draft(self):
        f = self.ticket_fixture()
        f.verified()
        out = f.flow.directory / "cli-draft.json"
        result = f.cli("ticket-proof-draft", "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["unknown"], [])
        self.assertEqual(read_json(out)["criteria"][0]["status"], "PASS")

    def test_ticket_handoff_has_the_criterion_table_from_the_proof(self):
        f = self.ticket_fixture()
        evidence = f.verified()
        proof = f.proof(evidence)
        f.record_proof(proof)
        f.local_review()
        f.refresh()
        with self.assertRaisesRegex(EngineError, "Write the ticket's checklist"):  # new runs need one
            f.flow.handoff(PARTNER)
        state = f.flow.load()
        state.pop("checklist_required")  # a run started before the rule keeps working without one
        atomic_json(f.flow.directory / "state.json", state)
        text = Path(f.flow.handoff(PARTNER)["handoff"]).read_text(encoding="utf-8")
        sha = proof["criteria"][0]["evidence"][0]["sha256"][:12]
        for expected in ("## Criterion → change → proof → gap", "| Criterion | Change | Proof | Gap |",
                         "| A1: Synthetic fixture sentence remains readable | README.md:1 synthetic fixture |",
                         "Before: Synthetic baseline sentence", "After: Synthetic preserved sentence",
                         f"`{evidence.relative_to(f.root).as_posix()}` ({sha})", "| None recorded |", "(codex)"):
            self.assertIn(expected, text)

    def test_plain_handoff_maps_recorded_implementation_and_lists_deferred_findings(self):
        f = self.to_review()
        low = finding("LOW", "accepted-deferral", deferral())
        self.assertEqual(self.codex_review(f, report(findings=[low]))["phase"], "ready")
        text = Path(f.flow.handoff(PARTNER)["handoff"]).read_text(encoding="utf-8")
        self.assertIn("| A1: Criterion A1 holds | Recorded implementation: artifacts/", text)
        self.assertIn("manual-evidence.txt", text)
        self.assertIn("## Deferred findings", text)
        self.assertIn("- LOW README.md:1: Synthetic finding (accepted-deferral; synthetic:followup-1)", text)

    def test_clean_review_has_no_deferred_section(self):
        f = self.to_review()
        self.codex_review(f, report())
        self.assertNotIn("## Deferred findings", Path(f.flow.handoff(PARTNER)["handoff"]).read_text(encoding="utf-8"))

    def test_handoff_records_the_technical_partner_decision(self):
        f = self.to_review()
        self.codex_review(f, report())
        for value in (None, "", "maybe later", "none", "none ()", "offered (a (b))"):
            with self.subTest(value=value), self.assertRaisesRegex(EngineError, "technical-partner decision"):
                f.flow.handoff(value)
        text = Path(f.flow.handoff("offered (go-live, upkeep)")["handoff"]).read_text(encoding="utf-8")
        self.assertIn("Technical partner: offered (go-live, upkeep)", text)

    def test_runs_started_before_the_partner_rule_hand_off_without_it(self):
        f = self.to_review()
        self.codex_review(f, report())
        state = f.flow.load()
        state.pop("partner_required")
        atomic_json(f.flow.directory / "state.json", state)
        self.assertNotIn("Technical partner", Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8"))


class OwnerDelegationTests(Base):
    def blocks(self, severity, exception, exposure="local", scopes=()):
        state = {"delivery_version": 2, "profile": {"exposure": exposure, "review_scopes": list(scopes)}}
        return Workflow.finding_blocks(finding(severity, "accepted-deferral", exception), state)

    def test_low_and_local_medium_defer_but_exposed_medium_high_and_foreign_owner_block(self):
        self.assertFalse(self.blocks("LOW", deferral()))
        self.assertFalse(self.blocks("MEDIUM", deferral()))
        self.assertFalse(self.blocks("LOW", deferral(), exposure="production"))
        self.assertTrue(self.blocks("MEDIUM", deferral(), exposure="public"))
        self.assertTrue(self.blocks("MEDIUM", deferral(), scopes=["release"]))
        self.assertTrue(self.blocks("HIGH", deferral()))
        self.assertTrue(self.blocks("LOW", deferral(owner="Someone else")))
        self.assertFalse(self.blocks("MEDIUM", deferral(authority="Other real authority")))


class CarriedManualQaTests(Base):
    def record(self, f, fresh, carried=None, tag="m", status="PASS"):
        evidence = f.root / ".factory" / f"evidence-{tag}.txt"
        evidence.write_text(f"Synthetic observation {tag}; no product QA claimed.\n", encoding="utf-8")
        observations = [{"criterion": i, "device": "fixture", "action": "Synthetic action", "result": "Synthetic result",
                         "status": "PASS", "evidence": [f".factory/evidence-{tag}.txt"]} for i in fresh]
        observations += [{"criterion": i, "status": status, "carried": {"receipt_sha256": sha, "reason": reason}}
                         for i, (sha, reason) in (carried or {}).items()]
        receipt = {"candidate": f.flow.status()["manual_candidate"], "observations": observations}
        path = f.root / ".factory" / f"receipt-{tag}.json"
        atomic_json(path, receipt)
        return f.flow.record("manual", path)

    def repaired(self):
        f = self.fixture(("A1", "A2"))
        f.start_build()
        f.artifact("implementation")
        self.record(f, ["A1", "A2"], tag="one")
        sha = f.flow.load()["artifacts"]["manual"]["sha256"]
        f.flow.repair("Synthetic fix touching A1 only")
        f.artifact("implementation")
        return f, sha

    def test_prior_receipt_pass_can_be_carried_while_one_criterion_is_fresh(self):
        f, sha = self.repaired()
        self.assertEqual(f.flow.status()["prior_manual_receipts"],
                         [{"receipt_sha256": sha, "passed": ["A1", "A2"]}])
        self.assertEqual(self.record(f, ["A1"], {"A2": (sha, "A2 unaffected by the fix")}, tag="two")["phase"], "testing")
        observations = {o["criterion"]: o for o in f.flow.load()["manual"]["observations"]}
        self.assertEqual(observations["A2"]["carried"], {"receipt_sha256": sha, "reason": "A2 unaffected by the fix"})
        self.assertEqual(observations["A2"]["evidence"][0]["path"], ".factory/evidence-one.txt")
        self.assertNotIn("carried", observations["A1"])
        f.flow.require_manual(f.flow.load())
        (f.root / ".factory/evidence-one.txt").write_text("tampered", encoding="utf-8")  # Carried hashes are rechecked.
        with self.assertRaisesRegex(EngineError, "Manual evidence changed"):
            f.flow.seal(f.task, f.profile, f.review_double())

    def test_carry_is_rejected_for_unknown_receipt_non_pass_all_carried_and_blank_claims(self):
        f, sha = self.repaired()
        cases = {"unknown receipt": dict(fresh=["A1"], carried={"A2": ("0" * 64, "reason")}, match="prior receipt"),
                 "every criterion carried": dict(fresh=[], carried={"A1": (sha, "r"), "A2": (sha, "r")}, match="freshly observed"),
                 "not a PASS": dict(fresh=["A1"], carried={"A2": (sha, "r")}, status="FAIL", match="only a PASS"),
                 "blank reason": dict(fresh=["A1"], carried={"A2": (sha, " ")}, match="receipt_sha256 and reason"),
                 "blank hash": dict(fresh=["A1"], carried={"A2": ("", "reason")}, match="receipt_sha256 and reason")}
        before = f.flow.load()
        for name, case in cases.items():
            with self.subTest(name), self.assertRaisesRegex(EngineError, case.pop("match")):
                self.record(f, case.pop("fresh"), case.pop("carried"), tag="bad", **case)
            self.assertEqual(f.flow.load(), before)
        self.assertEqual(self.record(f, ["A1"], {"A2": (sha, "ok")}, tag="good")["phase"], "testing")

    def test_prior_receipt_must_contain_that_criterion_as_a_pass(self):
        prior = [{"sha256": "h1", "observations": [{"criterion": "A1", "status": "FAIL"},
                                                    {"criterion": "A3", "status": "PASS", "evidence": []}]}]
        claim = {"receipt_sha256": "h1", "reason": "unaffected"}
        for identifier in ("A1", "A2"):  # FAIL in the receipt; absent from the receipt.
            with self.subTest(identifier=identifier), self.assertRaisesRegex(EngineError, "prior receipt"):
                carried_observation(identifier, claim, prior)
        with self.assertRaisesRegex(EngineError, "prior receipt"):
            carried_observation("A3", {**claim, "receipt_sha256": "other"}, prior)  # Names another receipt.
        self.assertEqual(carried_observation("A3", claim, prior)["carried"], claim)

    def test_a_carry_before_any_repair_has_no_history(self):
        f = self.fixture(("A1", "A2"))
        f.start_build()
        f.artifact("implementation")
        self.assertEqual(f.flow.status()["prior_manual_receipts"], [])
        with self.assertRaisesRegex(EngineError, "prior receipt"):
            self.record(f, ["A1"], {"A2": ("a" * 64, "no history")})

    def test_amendment_clears_the_archive_so_old_receipts_cannot_be_carried(self):
        f, sha = self.repaired()
        self.record(f, ["A1"], {"A2": (sha, "ok")}, tag="two")
        f.flow.repair("Second repair")
        self.assertEqual(len(f.flow.status()["prior_manual_receipts"]), 2)
        f.flow.amend(f.task, f.profile, f.review_double(), "Synthetic reviewed amendment")
        self.assertEqual(f.flow.status()["prior_manual_receipts"], [])
        self.assertNotIn("manual_receipts", f.flow.load())
        f.artifact("implementation")
        with self.assertRaisesRegex(EngineError, "prior receipt"):
            self.record(f, ["A1"], {"A2": (sha, "stale")}, tag="three")


class HardeningTests(Base):
    def test_v1_runs_reject_v2_stages_as_engine_errors(self):
        f = legacy.WorkflowTests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.tearDown)
        f.start()
        source = f.root / ".factory/v1-stage.md"
        source.parent.mkdir(exist_ok=True)
        source.write_text("# stage\nSynthetic artifact long enough to count as substantive.\n", encoding="utf-8")
        before = f.flow.load()
        for kind in ("implementation", "manual", "bogus"):
            with self.subTest(kind=kind), self.assertRaisesRegex(EngineError, "version 2 stage"):
                f.flow.record(kind, source)
        self.assertEqual(f.flow.load(), before)

    def test_status_and_other_commands_create_nothing_without_a_saved_run(self):
        f = self.fixture()
        for ticket in (None, "alpha"):
            for name in ("status", "check", "handoff", "cancel"):
                with self.subTest(ticket=ticket, command=name):
                    argv = [sys.executable, "-m", "safe_engine", "--project", str(f.root)]
                    argv += ["--ticket", ticket] if ticket else []
                    argv += [name, "--reason", "x"] if name == "cancel" else [name]
                    result = subprocess.run(argv, cwd=BUNDLE, capture_output=True, text=True, encoding="utf-8", timeout=30)
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn("No saved run", result.stderr)
                    self.assertFalse((f.root / ".factory").exists())
        with self.assertRaises(EngineError):
            Workflow(f.root).status()
        self.assertFalse((f.root / ".factory").exists())

    def test_status_takes_no_lock_while_another_operation_holds_it(self):
        from safe_engine.storage import locked
        f = self.fixture()
        f.flow.initialize(f.task, f.profile)
        with locked(f.flow.directory):
            result = subprocess.run([sys.executable, "-m", "safe_engine", "--project", str(f.root), "status"],
                                    cwd=BUNDLE, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["phase"], "analyze")

    def test_git_timeout_becomes_an_engine_error(self):
        f = self.fixture()
        with patch("safe_engine.project.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaisesRegex(EngineError, "timed out"):
                git(f.root, "status", "--porcelain")

    def test_timestamps_accept_one_to_six_fractional_digits_and_z_on_old_pythons(self):
        for digits in ("", ".1", ".12", ".123", ".1234", ".12345", ".123456"):
            for zone in ("Z", "+00:00", "-00:00", "+02:00"):
                with self.subTest(value=f"2020-01-02T03:04:05{digits}{zone}"):
                    parsed = timestamp(f"2020-01-02T03:04:05{digits}{zone}")
                    self.assertEqual(parsed.microsecond, int(digits[1:].ljust(6, "0")))
                    self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(timestamp("2020-01-02T03:04:05.5Z"), timestamp("2020-01-02T03:04:05.500000+00:00"))
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        for bad in ("2020-01-02T03:04:05", "2020-01-02T03:04:05.1", "not a time", "", None, 5, future):
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                timestamp(bad)


if __name__ == "__main__":
    unittest.main()
