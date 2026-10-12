"""Review round cap and the external reviewer packet route (speed work). Reviewer receipts are synthetic
doubles; commands, Git, hashes and state files are real."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from safe_engine.project import EngineError, file_hash
from safe_engine.storage import atomic_json, read_json
from safe_engine.workflow import EXTERNAL, REVIEW_ROUNDS
from speed_fixtures import BUNDLE, DOUBLE, REVIEWER_BINARIES, Base, report, finding, codex, command

PARTNER = "none (no stage reached)"  # the handoff's technical-partner decision


class ReviewRoundCapTests(Base):
    def test_capped_failed_reviews_then_refused_until_the_owner_extends(self):
        f = self.to_review()
        for round_number in (1, REVIEW_ROUNDS):  # real failed rounds; the middle ones only repeat the count
            if round_number > 1:
                self.set_state(f, failed_reviews=round_number - 1)
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
                                 "--rounds", "9", "--reason", "too many"], cwd=BUNDLE, capture_output=True, text=True, encoding="utf-8", timeout=30)
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
        self.assertIn("independence not verified", Path(f.flow.handoff(PARTNER)["handoff"]).read_text(encoding="utf-8"))

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
        for round_number in (1, REVIEW_ROUNDS):  # real failed rounds; the middle ones only repeat the count
            if round_number > 1:
                self.set_state(f, failed_reviews=round_number - 1)
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




if __name__ == "__main__":
    unittest.main()
