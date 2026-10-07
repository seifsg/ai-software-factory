"""Regressions for the speed work: parallel checks, cheap ticket refresh, proof drafts,
handoff tables, carried manual QA, review cap and external reviewer, plus hardening.

Reviewer, owner and manual receipts are explicit synthetic doubles. Commands, Git,
locks, hashes and state files are real; no product, tracker or cloud acceptance is claimed.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_delivery_v2 as v2
import test_tickets as tickets
import test_workflow as legacy
from safe_engine.acceptance import carried_observation
from safe_engine.project import (EngineError, file_hash, git, production_fingerprint, rescan,
                                 snapshot, validate_profile)
from safe_engine.proof import proof_draft
from safe_engine.storage import atomic_json, read_json
from safe_engine.tickets import timestamp
from safe_engine.workflow import DELEGATION, EXTERNAL, REVIEW_ROUNDS, Workflow

BUNDLE = Path(__file__).resolve().parents[1]
DOUBLE = "Synthetic double; no actual independent acceptance"
REAL_WHICH = shutil.which


def report(verdict="PASS", findings=()):
    return {"verdict": verdict, "summary": DOUBLE, "method_followed": True,
            "criteria": [{"id": "A1", "status": "PASS", "evidence": DOUBLE}], "findings": list(findings)}


def finding(severity="HIGH", disposition="blocking", exception=None):
    return {"severity": severity, "location": "README.md:1", "description": "Synthetic finding",
            "disposition": disposition, "exception": exception, "layer": "product",
            "evidence_status": "valid", "evidence": DOUBLE, "action": "Synthetic action"}


def deferral(owner="owner", authority=DELEGATION):
    return {"owner": owner, "reason": "Synthetic reason", "scope": "local", "revisit": "Before release",
            "authority": authority, "destination": "synthetic:followup-1"}


REVIEWER_BINARIES = {"codex", "claude", "agent", "cursor-agent"}


def codex(present):
    """Make shutil.which see (or not see) a Codex CLI and no other reviewer agent; other lookups stay real."""
    return patch("shutil.which", side_effect=lambda name, *a, **k: sys.executable if name == "codex" and present
                 else None if name in REVIEWER_BINARIES else REAL_WHICH(name, *a, **k))


class Base(unittest.TestCase):
    def fixture(self, ids=("A1",)):
        """A disposable v2 consumer whose criteria are all manual."""
        f = v2.DeliveryV2Tests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.task["acceptance"] = [{"id": i, "text": f"Criterion {i} holds", "mode": "manual", "checks": []}
                                for i in ids]
        return f

    def ticket_fixture(self):
        f = tickets.TicketTests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        return f

    def seal_with(self, f, checks=(), parallel=None):
        """Seal the final contract (optionally with real checks) and record the batch."""
        task, profile = deepcopy(f.task), deepcopy(f.profile)
        if checks:
            profile.update(protected_paths=sorted({"tests/" + c["script"] for c in checks}),
                           checks=[{k: v for k, v in c.items() if k != "script"} for c in checks])
            task["acceptance"][0].update(mode="mixed", checks=[c["id"] for c in checks])
        if parallel is not None:
            profile["parallel_checks"] = parallel
        f.task, f.profile = task, profile
        f.flow.seal(task, profile, f.review_double(task, profile))
        f.artifact("batch")

    def to_review(self, ids=("A1",)):
        f = self.fixture(ids)
        f.start_build()
        f.finish_manual()
        self.seal_with(f)
        self.assertTrue(f.flow.check()["checks_passed"])
        return f

    def codex_review(self, f, body):
        def double(argv, cwd, timeout, log, stdin):
            atomic_json(Path(argv[argv.index("--output-last-message") + 1]), body)
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(DOUBLE, encoding="utf-8")
            return {"passed": True, "synthetic": DOUBLE}
        with codex(True), patch("safe_engine.workflow.run_command", side_effect=double):
            return f.flow.review(10)

    def redo(self, f):
        """One full correction cycle back to the review phase."""
        f.flow.repair("Synthetic correction")
        f.finish_manual()
        f.artifact("batch")
        self.assertTrue(f.flow.check()["checks_passed"])

    def set_state(self, f, **values):
        state = f.flow.load()
        state.update(values)
        atomic_json(f.flow.directory / "state.json", state)


def script(f, name, body):
    folder = f.root / "tests"
    folder.mkdir(exist_ok=True)
    (folder / name).write_text(body, encoding="utf-8")


def command(identifier, name, *args, artifacts=()):
    return {"id": identifier, "kind": "unit", "script": name, "timeout_seconds": 30,
            "argv": ["{python}", f"tests/{name}", *args], "artifacts": list(artifacts)}


RENDEZVOUS = ("import sys, time\nfrom pathlib import Path\n"
              "mine, other = Path(sys.argv[1]), Path(sys.argv[2])\nmine.write_text('x')\n"
              "end = time.time() + 12\n"
              "while time.time() < end:\n    if other.exists(): sys.exit(0)\n    time.sleep(0.02)\nsys.exit(1)\n")
PAUSE = ("import sys, time\nfrom pathlib import Path\ntime.sleep(0.4)\n"
         "Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)\nPath(sys.argv[1]).write_text('out')\n")


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
        text = Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8")
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
        text = Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8")
        self.assertIn("| A1: Criterion A1 holds | Recorded implementation: artifacts/", text)
        self.assertIn("manual-evidence.txt", text)
        self.assertIn("## Deferred findings", text)
        self.assertIn("- LOW README.md:1: Synthetic finding (accepted-deferral; synthetic:followup-1)", text)

    def test_clean_review_has_no_deferred_section(self):
        f = self.to_review()
        self.codex_review(f, report())
        self.assertNotIn("## Deferred findings", Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8"))


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


class ReviewRoundCapTests(Base):
    def test_capped_failed_reviews_then_refused_until_the_owner_extends(self):
        f = self.to_review()
        for round_number in range(1, REVIEW_ROUNDS + 1):
            if round_number > 1:
                self.redo(f)
            self.assertEqual(self.codex_review(f, report("FAIL", [finding()]))["phase"], "review")
            self.assertEqual(f.flow.status()["failed_reviews"], round_number)
        self.redo(f)
        with codex(True), patch("safe_engine.workflow.run_command") as reviewer:
            with self.assertRaisesRegex(EngineError, "round cap"):
                f.flow.review(10)
            with self.assertRaisesRegex(EngineError, "round cap"):
                f.flow.review_packet(f.root / ".factory/capped-packet.md")
            reviewer.assert_not_called()
        self.assertFalse((f.root / ".factory/capped-packet.md").exists())
        status = f.flow.extend_reviews(2, "The owner decided two more rounds")
        self.assertEqual((status["failed_reviews"], status["review_rounds"]), (REVIEW_ROUNDS, REVIEW_ROUNDS + 2))
        self.assertIn("The owner decided two more rounds", f.flow.load()["history"][-1]["event"])
        self.assertEqual(self.codex_review(f, report())["phase"], "ready")

    def test_extension_grants_exactly_the_requested_extra_rounds(self):
        f = self.to_review()
        self.set_state(f, failed_reviews=REVIEW_ROUNDS)
        f.flow.extend_reviews(1, "One more")
        self.assertEqual(self.codex_review(f, report("FAIL", [finding()]))["phase"], "review")
        self.redo(f)
        with codex(True), self.assertRaisesRegex(EngineError, "round cap"):
            f.flow.review(10)

    def test_an_early_extension_never_lowers_the_cap(self):
        f = self.fixture()
        f.flow.initialize(f.task, f.profile)
        self.assertEqual(f.flow.extend_reviews(1, "Extended before any review failed")["review_rounds"], REVIEW_ROUNDS + 1)

    def test_invalid_extensions_are_rejected_without_changing_the_run(self):
        f = self.to_review()
        before = f.flow.load()
        for rounds in (0, 4, -1, True, "2", 1.5, None):
            with self.subTest(rounds=rounds), self.assertRaises(EngineError):
                f.flow.extend_reviews(rounds, "reason")
        for reason in ("", "  ", None, 5):
            with self.subTest(reason=reason), self.assertRaises(EngineError):
                f.flow.extend_reviews(1, reason)
        self.assertEqual(f.flow.load(), before)
        for rounds in (1, 3):
            f.flow.extend_reviews(rounds, "boundary values are valid")
        result = subprocess.run([sys.executable, "-m", "safe_engine", "--project", str(f.root), "extend-reviews",
                                 "--rounds", "9", "--reason", "too many"], cwd=BUNDLE, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        f.flow.cancel("Synthetic cancellation")
        with self.assertRaisesRegex(EngineError, "Cancelled"):
            f.flow.extend_reviews(1, "reason")


class ExternalReviewerTests(Base):
    def packet(self, f, name="packet.md"):
        with codex(False):
            return f.flow.review_packet(f.flow.directory / name)

    def external(self, f, body, reviewer="host/agent-1/model-x", present=False, nonce=True):
        """Submit body as a host subagent's report; nonce=True adds the current packet's nonce to its summary."""
        if nonce and isinstance(body, dict) and f.flow.load().get("review_packet"):
            body = {**body, "summary": f"{f.flow.load()['review_packet']['nonce']} {body.get('summary', DOUBLE)}"}
        path = f.flow.directory / "external-report.json"
        atomic_json(path, body)
        with codex(present), patch("safe_engine.workflow.run_command") as launched:
            try:
                return f.flow.review(None, str(path), reviewer)
            finally:
                launched.assert_not_called()

    def test_packet_then_report_is_accepted_and_recorded_as_external(self):
        f = self.to_review()
        status = self.packet(f)
        packet = (f.flow.directory / "packet.md").read_text(encoding="utf-8")
        nonce = f.flow.load()["review_packet"]["nonce"]
        for expected in ("Return only JSON matching the schema", "review-schema-v2.json", nonce,
                         "Carried manual PASSes must be justified"):
            self.assertIn(expected, packet)
        self.assertEqual(status["review_packet"]["sha256"], file_hash(f.flow.directory / "packet.md"))
        self.assertEqual(self.external(f, report())["phase"], "ready")
        execution = f.flow.load()["review"]["execution"]
        self.assertEqual((execution["kind"], execution["reviewer"], execution["note"]),
                         ("external", "host/agent-1/model-x", EXTERNAL))
        self.assertEqual(execution["packet_sha256"], status["review_packet"]["sha256"])
        self.assertEqual(f.flow.status()["review_execution"], f"host/agent-1/model-x: {EXTERNAL}")
        self.assertIsNone(f.flow.status()["review_packet"])
        self.assertIn(nonce, read_json(f.flow.load()["review"]["report"])["summary"])
        self.assertIn("independence not verified", Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8"))

    def test_report_must_carry_this_packets_nonce(self):
        f = self.to_review()
        self.packet(f)
        old = f.flow.load()["review_packet"]["nonce"]
        before = f.flow.load()
        for name, summary in (("no nonce", DOUBLE), ("empty summary", ""), ("guessed nonce", "0" * 32 + " " + DOUBLE)):
            with self.subTest(name), self.assertRaisesRegex(EngineError, "nonce"):
                self.external(f, report() | {"summary": summary}, nonce=False)
        with self.assertRaisesRegex(EngineError, "nonce"):  # Missing summary entirely.
            self.external(f, {k: v for k, v in report().items() if k != "summary"}, nonce=False)
        self.assertEqual(f.flow.load(), before)
        self.packet(f, "second.md")  # Reissue: the first packet's nonce is now foreign.
        self.assertNotEqual(f.flow.load()["review_packet"]["nonce"], old)
        with self.assertRaisesRegex(EngineError, "nonce"):
            self.external(f, report() | {"summary": f"{old} {DOUBLE}"}, nonce=False)
        self.assertEqual(self.external(f, report())["phase"], "ready")

    def test_extension_keeps_the_open_packet_usable(self):
        f = self.to_review()
        self.packet(f)
        for _ in range(REVIEW_ROUNDS - 1):
            self.packet(f)
        with self.assertRaisesRegex(EngineError, "round cap"):
            self.packet(f)
        self.assertEqual(f.flow.extend_reviews(1, "Owner: one more round")["review_rounds"], REVIEW_ROUNDS + 1)
        self.assertEqual(self.external(f, report())["phase"], "ready")
        self.assertEqual(f.flow.status()["failed_reviews"], REVIEW_ROUNDS - 1)

    def test_extension_never_revives_a_stale_packet(self):
        f = self.to_review()
        self.packet(f)
        self.set_state(f, review_packet={**f.flow.load()["review_packet"], "records": "stale"})
        f.flow.extend_reviews(1, "Owner: one more round")
        with self.assertRaisesRegex(EngineError, "changed since the review packet"):
            self.external(f, report())

    def test_records_change_stales_the_packet_but_cap_bookkeeping_does_not(self):
        f = self.to_review()
        self.packet(f)
        self.set_state(f, contract_revision=f.flow.load().get("contract_revision", 0) + 1)
        with self.assertRaisesRegex(EngineError, "changed since the review packet"):
            self.external(f, report())
        self.packet(f, "second.md")
        self.set_state(f, failed_reviews=1, review_rounds=5)
        self.assertEqual(self.external(f, report())["phase"], "ready")

    def test_reserved_run_files_are_refused(self):
        f = self.to_review()
        for name in ("state.json", "lock", "history/x.json", "review-0009.json", "outputs/p.md",
                     "Review-0099.json", "OUTPUTS/p.md"):
            with self.subTest(name), self.assertRaisesRegex(EngineError, "reserved"):
                self.packet(f, name)

    def test_reserved_names_include_the_entry_bundle_and_legacy_runs_folder(self):
        f = self.to_review()
        for name in ("entry-bundle.json", "Entry-Bundle.json", "runs", "runs/x.md", "RUNS/x.md"):
            with self.subTest(name), self.assertRaisesRegex(EngineError, "reserved"):
                self.packet(f, name)

    @unittest.skipUnless(os.name == "nt", "Windows drops trailing spaces and dots from path parts")
    def test_trailing_space_and_extended_length_paths_are_refused(self):
        f = self.to_review()
        run, root = f.flow.directory, f.root
        for path, pattern in ((run / "state.json ", "reserved"), (run / "state.json.", "reserved"),
                              (root / "src /a.json", "space or dot|extended-length|Use a path under"),
                              (Path("\\\\?\\" + str(root / "x.json")), "extended-length|Use a path under"),
                              (Path("\\\\?\\" + str(run / "nul")), "extended-length|not a file")):  # 3.9 drops the prefix
            with self.subTest(path=str(path)), self.assertRaisesRegex(EngineError, pattern):
                self.packet(f, str(path))
        for path in (run / "history /x.json", run / "outputs /x.md", run / "logs./x.md"):
            with self.subTest(path=str(path)), self.assertRaisesRegex(EngineError, "reserved|space or dot|extended-length"):
                self.packet(f, str(path))
        self.assertFalse((run / "history" / "x.json").exists() or (run / "outputs").exists()
                         or (run / "logs").exists())  # nothing written, no empty reserved folder created
        self.assertFalse((root / "src").exists())

    @unittest.skipUnless(os.name == "nt", "Windows trailing-space folders")
    def test_a_real_trailing_space_folder_is_refused_not_mapped(self):
        f = self.to_review()
        real = Path("\\\\?\\" + str(f.flow.directory / "p "))
        os.mkdir(real)
        self.addCleanup(os.rmdir, real)
        (f.flow.directory / "p").mkdir()
        with self.assertRaisesRegex(EngineError, "space or dot"):
            f.flow.outside_inputs(str(f.flow.directory / "p " / "x.json"))

    def test_symlinked_packet_file_refuses_the_report(self):
        f = self.to_review()
        self.packet(f)
        issued = f.flow.directory / "packet.md"
        copy = f.flow.directory / "copy.md"
        copy.write_bytes(issued.read_bytes())
        issued.unlink()
        try:
            os.symlink(copy, issued)
        except (OSError, NotImplementedError):  # no symlink rights: exercise the same branch through is_symlink
            copy.replace(issued)
            real = Path.is_symlink
            patcher = patch.object(Path, "is_symlink", lambda p: p == issued or real(p))
            patcher.start()
            self.addCleanup(patcher.stop)
        with self.assertRaisesRegex(EngineError, "Review packet changed or missing"):
            self.external(f, report())

    @unittest.skipUnless(os.name == "nt", "Windows extended-length namespaces")
    def test_unresolvable_extended_length_path_is_an_engine_error(self):
        f = self.to_review()
        with self.assertRaises(EngineError):
            self.packet(f, r"\\?\GLOBALROOT\x")

    def test_edited_or_deleted_packet_file_refuses_the_report(self):
        f = self.to_review()
        issued = f.flow.directory / "packet.md"
        for name, damage in (("edited", lambda: issued.write_text("tampered", encoding="utf-8")),
                             ("deleted", issued.unlink)):
            with self.subTest(name):
                self.packet(f)
                damage()
                with self.assertRaisesRegex(EngineError, "Review packet changed or missing"):
                    self.external(f, report())
                self.assertIsNotNone(f.flow.load()["review_packet"])
        self.packet(f)  # A fresh packet restores the route.
        self.assertEqual(self.external(f, report())["phase"], "ready")

    def test_legacy_packet_without_records_falls_back_to_the_sequence_check(self):
        f = self.to_review()
        for name, offset, accepted in (("different sequence", 5, False), ("matching sequence", 0, True)):
            with self.subTest(name):
                self.packet(f)
                legacy_packet = {k: v for k, v in f.flow.load()["review_packet"].items() if k != "records"}
                legacy_packet["sequence"] += offset
                self.set_state(f, review_packet=legacy_packet)
                if accepted:
                    self.assertEqual(self.external(f, report())["phase"], "ready")
                else:
                    with self.assertRaisesRegex(EngineError, "changed since the review packet"):
                        self.external(f, report())

    def test_patching_workflow_seams_reaches_the_mixin_modules(self):
        f = self.to_review()
        with patch("safe_engine.workflow.shutil.which", return_value=None) as which:
            with self.assertRaisesRegex(EngineError, "review-packet"):
                f.flow.review(10)  # review.py asked the patched lookup, not the real PATH
        self.assertEqual({call.args[0] for call in which.call_args_list}, REVIEWER_BINARIES)  # every preset probed
        with patch("safe_engine.workflow.save") as saved:
            self.packet(f)
        saved.assert_called_once()  # persist() in review.py resolves save through workflow
        def double(argv, cwd, timeout, log):
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(DOUBLE, encoding="utf-8")
            return {"passed": True, "synthetic": DOUBLE}
        with patch("safe_engine.workflow.run_command", side_effect=double) as launched:
            results = f.flow.execute_checks({"sequence": 7}, [command("alpha", "seam.py")])
        launched.assert_called_once()  # checks.py launches through workflow.run_command
        self.assertEqual([r["id"] for r in results], ["alpha"])

    def test_reissuing_an_unsubmitted_packet_counts_as_a_failed_review_and_can_hit_the_cap(self):
        f = self.to_review()
        self.packet(f)
        self.assertEqual(f.flow.status()["failed_reviews"], 0)
        for expected in range(1, REVIEW_ROUNDS):
            self.packet(f)
            self.assertEqual(f.flow.status()["failed_reviews"], expected)
        before = f.flow.load()
        refused = f.flow.directory / "over-cap-packet.md"
        with self.assertRaisesRegex(EngineError, "round cap"):
            self.packet(f, refused.name)
        self.assertFalse(refused.exists())
        self.assertEqual(f.flow.load(), before)  # The refused reissue saved nothing.
        self.assertEqual(self.external(f, report())["phase"], "ready")  # The last packet still works.

    def test_packet_and_report_paths_stay_under_the_run_directory_or_outside_the_project(self):
        f = self.to_review()
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        before = f.flow.load()
        for inside in (f.root / "packet.md", f.root / "tests/packet.md", f.root / "README.md.packet"):
            with self.subTest(packet=inside.name), codex(False), self.assertRaisesRegex(EngineError, "Use a path under"):
                f.flow.review_packet(inside)
            self.assertFalse(inside.exists())
        self.assertEqual(f.flow.load(), before)
        self.packet(f)
        nonce = f.flow.load()["review_packet"]["nonce"]
        body = report() | {"summary": f"{nonce} {DOUBLE}"}
        misplaced = f.root / "report.json"  # Not created: a file here would itself change the inputs.
        with codex(False), self.assertRaisesRegex(EngineError, "Use a path under"):
            f.flow.review(None, str(misplaced), "host/agent")
        self.assertIsNotNone(f.flow.load().get("review_packet"))
        elsewhere = Path(outside.name) / "report.json"
        atomic_json(elsewhere, body)
        with codex(False):
            self.assertEqual(f.flow.review(None, str(elsewhere), "host/agent")["phase"], "ready")
        again = self.to_review()
        with codex(False):
            again.flow.review_packet(Path(outside.name) / "packet.md")
        self.assertTrue((Path(outside.name) / "packet.md").is_file())

    def test_packet_report_is_accepted_even_with_a_reviewer_agent_installed(self):
        f = self.to_review()  # no agent is privileged; the packet route always stays open
        self.packet(f)
        self.assertEqual(self.external(f, report(), present=True)["phase"], "ready")

    def test_report_needs_a_packet_a_reviewer_identity_and_the_schema(self):
        f = self.to_review()
        with self.assertRaisesRegex(EngineError, "review-packet first"):
            self.external(f, report())
        self.packet(f)
        before = f.flow.load()
        with self.assertRaisesRegex(EngineError, "--reviewer"):
            self.external(f, report(), reviewer=" ")
        with codex(False), self.assertRaisesRegex(EngineError, "--report"):
            f.flow.review(None, None, "host/agent")
        broken = {"verdict": "MAYBE", "summary": DOUBLE, "method_followed": True, "criteria": [], "findings": [],
                  "extra": 1}
        missing = {k: v for k, v in report().items() if k != "findings"}
        loose = report(findings=[{**finding("LOW"), "surprise": 1}])
        for name, body in (("enum and extra key", broken), ("missing key", missing), ("extra finding key", loose)):
            with self.subTest(name), self.assertRaisesRegex(EngineError, "schema"):
                self.external(f, body)
        self.assertEqual(f.flow.load(), before)
        self.assertEqual(self.external(f, report())["phase"], "ready")  # The packet survived the rejections.

    def test_non_object_report_is_an_engine_error(self):
        f = self.to_review()
        self.packet(f)
        with self.assertRaises(EngineError):
            self.external(f, [])

    def test_report_is_rejected_when_inputs_or_records_changed_since_the_packet(self):
        f = self.to_review()
        self.packet(f)
        packet = f.flow.load()["review_packet"]
        self.set_state(f, review_packet={**packet, "records": "stale"})  # Records changed.
        with self.assertRaisesRegex(EngineError, "changed since the review packet"):
            self.external(f, report())
        self.packet(f, "second.md")
        packet = f.flow.load()["review_packet"]
        self.set_state(f, review_packet={**packet, "fingerprint": "stale"})  # Inputs changed.
        with self.assertRaisesRegex(EngineError, "changed since the review packet"):
            self.external(f, report())
        self.packet(f, "third.md")
        (f.root / "tests").mkdir(exist_ok=True)
        (f.root / "tests/extra.py").write_text("# changed after the packet\n", encoding="utf-8")
        with self.assertRaises(EngineError):  # Candidate evidence is stale too.
            self.external(f, report())

    def test_repair_discards_the_packet(self):
        f = self.to_review()
        self.packet(f)
        f.flow.repair("Synthetic correction")
        self.assertNotIn("review_packet", f.flow.load())

    def test_failed_external_reviews_count_toward_the_cap_and_packets_stop(self):
        f = self.to_review()
        for round_number in range(1, REVIEW_ROUNDS + 1):
            if round_number > 1:
                self.redo(f)
            self.packet(f)
            self.assertEqual(self.external(f, report("FAIL", [finding()]))["phase"], "review")
            self.assertEqual(f.flow.status()["failed_reviews"], round_number)
        self.redo(f)
        with codex(False):
            with self.assertRaisesRegex(EngineError, "round cap"):
                f.flow.review_packet(f.flow.directory / "over-cap.md")
            with self.assertRaisesRegex(EngineError, "round cap"):
                f.flow.review(None, str(f.flow.directory / "external-report.json"), "host/agent")
        self.assertFalse((f.flow.directory / "over-cap.md").exists())

    def test_without_any_agent_or_report_review_points_to_the_packet_route(self):
        f = self.to_review()
        with codex(False), self.assertRaisesRegex(EngineError, "review-packet"):
            f.flow.review(10)


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
                    result = subprocess.run(argv, cwd=BUNDLE, capture_output=True, text=True, timeout=30)
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
                                    cwd=BUNDLE, capture_output=True, text=True, timeout=30)
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
