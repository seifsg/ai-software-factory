"""PR-only rollout against live CLI fixtures, without replacing bundle or progress."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from test_fast_gate import GateHarness, GATE, LIGHT, PR_BODY, module
from bundle_fixtures import legacy_bundle, offline_gate


class PrPolicyTests(GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = self.root / "how-to-make-a-pr"
        shutil.copytree(GATE.parents[3] / ".agents/skills/how-to-make-a-pr", self.skill)
        self.method = self.skill / "SKILL.md"
        self.home = Path(self.env["SAFE_ENGINE_HOME"])
        self.bundle = legacy_bundle(self.root / "old-bundle")
        self.gate_command = offline_gate()
        (self.project / ".factory").mkdir()
        (self.project / ".factory/entry-bundle.json").write_text(json.dumps(self.bundle))

    def state(self):
        return next((self.home / "runs").glob("*.json"))

    def adopt(self, **kwargs):
        return self.gate("adopt-pr-proof", "--method", str(self.method), "--reason", "Owner: enable PR proof", **kwargs)

    def defaults(self, method=None, ok=True):
        result = subprocess.run([sys.executable, str(GATE), "adopt-pr-proof", "--new-runs", "--method",
                                 str(method or self.method), "--reason", "Owner: future runs"], env=self.env,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def ready(self, paused=False):
        """A pre-rollout run's completed work, as an older gate would have saved it."""
        self.start(kind="change")
        run = json.loads(self.state().read_text())
        run.pop("pr_instance", None)  # old runs predate per-start nonces
        run["done"] = {step: {"at": "fixture"} for step in ("tickets", "analysis", "plan", "build", "done-run")}
        run["paused"] = {"reason": "owner checkpoint", "at": "fixture"} if paused else None
        self.state().write_text(json.dumps(run))
        (self.project / ".factory/fast/work-record.md").write_text(LIGHT, encoding="utf-8")
        self.pr_body()
        return run

    def test_adoption_keeps_pause_progress_and_bundle_bytes(self):
        run = self.ready(paused=True)
        before = self.state().read_bytes()
        self.adopt()
        receipt = next((self.home / "pr-proof/runs").glob("*.json"))
        saved = receipt.read_bytes()
        self.adopt()
        self.assertEqual(saved, receipt.read_bytes())
        self.assertEqual(before, self.state().read_bytes())
        self.assertFalse(run["pr_demo"])
        message = json.dumps(self.hook({"hook_event_name": "UserPromptSubmit"}))
        self.assertIn("Visual/Journey", message)
        self.assertIn("owner checkpoint", message)
        self.assertIn("fast_gate.py", message)
        self.assertEqual(self.pre("Edit", file_path=str(receipt)), "deny")
        self.assertEqual(self.pre("Bash", command=f'python "{GATE}" adopt-pr-proof --project "{self.project}" '
                                 f'--method "{self.method}" --reason "Owner instruction"'), "allow")

    def test_new_defaults_do_not_upgrade_existing_runs_or_snapshots(self):
        self.start(kind="change")
        before = self.state().read_bytes()
        self.defaults()
        self.assertEqual(before, self.state().read_bytes())
        self.assertNotIn("PR proof:", self.gate("status"))
        self.gate("close", "--abandon", "fixture done")
        self.start(kind="change")
        run = json.loads(self.state().read_text())
        self.assertEqual((run["pr_proof"], run["pr_demo"], run["bundle"]["revision"]),
                         (True, True, self.bundle["revision"]))
        self.assertIn("new-run snapshot", self.adopt())
        second = self.root / "next-policy"
        shutil.copytree(self.skill, second)
        (second / "SKILL.md").write_text((second / "SKILL.md").read_text(encoding="utf-8") + "\nClarification.\n", encoding="utf-8")
        self.defaults(second / "SKILL.md")
        self.assertEqual(run, json.loads(self.state().read_text()))
        self.assertEqual(len(list((self.home / "pr-proof/defaults").glob("*.json"))), 2)

    def test_handoff_enforces_proof_without_persisting_overlay_flags(self):
        self.ready()
        self.adopt()
        body = self.project / ".factory/fast/pr-body.md"
        body.write_text(PR_BODY.replace("**Journey:** no (copy correction only)", "**Journey:** yes"), encoding="utf-8")
        self.assertIn("needs a '**Video:**'", self.gate("done", "handoff", "--offline", "fixture", ok=False))
        body.write_text(body.read_text(encoding="utf-8").replace("---", "**Video:** [Journey](https://example.com/demo.mp4)\n\n---"), encoding="utf-8")
        self.gate("done", "handoff", "--offline", "fixture")
        run = json.loads(self.state().read_text())
        self.assertFalse(run["pr_demo"])
        self.assertFalse(run["pr_proof"])
        self.assertEqual(len(run["done"]["handoff"]["pr_policy"]), 64)
        self.gate("close")

    def test_old_gate_or_racing_handoff_cannot_close(self):
        self.ready()
        self.adopt()
        run = json.loads(self.state().read_text())
        run["done"]["handoff"] = {"at": "old-gate"}
        self.state().write_text(json.dumps(run))
        self.assertIn("record handoff with the installed gate", self.gate("close", ok=False))
        self.assertIn("no recorded handoff", self.adopt(ok=False))
        self.gate("done", "handoff", "--offline", "fixture")
        self.gate("close")

    def test_reference_tamper_and_missing_source_fail_commands(self):
        self.ready()
        self.adopt()
        ref = self.skill / "references/pr-layout.md"
        ref.write_text(ref.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        self.assertIn("changed since adoption", self.gate("status", ok=False))
        self.assertIn("changed since adoption", self.gate("done", "handoff", "--offline", "fixture", ok=False))
        self.method.unlink()
        self.assertIn("existing absolute PR SKILL.md", self.gate("status", ok=False))
        self.gate("close", "--abandon", "owner ends fixture")

    def test_malformed_policy_is_not_silent_opt_out(self):
        self.start(kind="change")
        self.adopt()
        receipt = next((self.home / "pr-proof/runs").glob("*.json"))
        receipt.write_text("null")
        self.assertIn("null PR-proof receipt", self.gate("status", ok=False))
        self.assertIn("needs repair", json.dumps(self.hook({"hook_event_name": "UserPromptSubmit"})))
        self.gate("close", "--abandon", "owner ends fixture")
        for malformed in ("null", "[]", "false"):
            (self.home / "pr-proof/new-runs.json").write_text(malformed)
            self.assertIn("PR-proof policy", self.gate("start", "--key", "next", "--kind", "change", "--request", "new", ok=False))

    def test_adoption_is_bound_to_creation_identity(self):
        self.start(kind="change")
        self.adopt()
        policy = module("fast_pr_policy")
        run = json.loads(self.state().read_text())
        self.assertIsNotNone(policy.selected(self.home, run))
        run["pr_instance"] = "0" * 32 if run["pr_instance"] != "0" * 32 else "1" * 32
        self.assertIsNone(policy.selected(self.home, run))  # same key, project and second; a different start
        run["created"] += "-next"
        self.assertIsNone(policy.selected(self.home, run))


    def test_any_mode_can_read_and_verify_default_method(self):
        def lookup():
            return subprocess.run([sys.executable, str(GATE), "pr-proof-method"], env=self.env,
                                  capture_output=True, text=True, encoding="utf-8")
        self.assertIn("selected bundle method", lookup().stdout)
        self.defaults()
        self.assertEqual(lookup().stdout.splitlines()[0], str(self.method))
        self.assertRegex(lookup().stdout, r"SHA256: [0-9a-f]{64}")
        self.method.unlink()
        self.assertNotEqual(lookup().returncode, 0)


if __name__ == "__main__":
    unittest.main()
