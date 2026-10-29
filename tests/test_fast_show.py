"""Show gates real proof on current, complete pictures and retains candidate-bound passes."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from png_fixtures import png

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/safe-engine/scripts"
sys.path.insert(0, str(SCRIPTS))
import fast_design as evidence
import fast_install
import fast_ledger as ledger
import fast_record
import fast_show as show
import fast_show_command as show_command
from safe_engine import suite_queue


class ShowPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"version": 1, "surfaces": [{"id": "home", "name": "Home"}],
                     "full_suite": ["python", "tests/run.py"],
                     "viewports": {"desktop": [64, 32], "phone": [48, 32]}}

    def test_default_plan_freezes_only_light_desktop(self):
        self.plan.pop("viewports")
        planned = show.plan(self.plan)
        self.assertEqual(planned["variants"], [{"theme": "light", "device": "desktop"}])
        self.assertEqual(planned["comparison"], "before")

    def test_invalid_planned_variants_comparison_and_geometry(self):
        invalid = [{"variants": value} for value in (None, [], {}, [None],
                   [{"theme": "light"}], [{"theme": "light", "device": "tablet"}],
                   [{"theme": "sepia", "device": "desktop"}], [{"theme": [], "device": "desktop"}],
                   [{"theme": "light", "device": "desktop", "extra": True}],
                   [{"theme": "light", "device": "desktop"}] * 2)]
        invalid += [{"comparison": value} for value in (None, "after", [])]
        invalid += [{"viewports": value} for value in (None, {}, {"phone": [48, 32]},
                    {"desktop": [64, 32], "tablet": [48, 32]}, {"desktop": [True, 32]},
                    {"desktop": [64, 0]}, {"desktop": [64]},
                    {"desktop": [48, 32], "phone": [64, 32]})]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                show.plan({**self.plan, **fields})
        self.assertEqual(show.plan({**self.plan, "viewports": {"desktop": [64, 32]}})["viewports"],
                         {"desktop": [64, 32]})


class ShowFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        cache_home = patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.home / "cache-home"))
        cache_home.start()
        self.addCleanup(cache_home.stop)
        self.project = self.home / "project"
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        (self.project / ".gitignore").write_text(".factory/\n")
        (self.project / "source.txt").write_text("candidate A\n")
        (self.project / ".factory/fast").mkdir(parents=True)
        for device, width in (("desktop", 64), ("phone", 48)):
            png(self.project / f".factory/{device}.png", width)
        self.plan = {"version": 1, "surfaces": [{"id": "home", "name": "Home"}],
                     "full_suite": [sys.executable, "-c", "from pathlib import Path; "
                        "p=Path('.factory/invocations'); p.write_text(p.read_text()+'run\\n' if p.exists() else 'run\\n'); "
                        "raise SystemExit(3 if Path('.factory/fail').exists() else 0)"],
                     "viewports": {"desktop": [64, 32], "phone": [48, 32]}, "wait_minutes": 0, "timeout_seconds": 10}
        self.state = {"version": 1, "key": "show-test", "project": str(self.project), "mode": "fast", "kind": "change",
                      "ui": True, "show_first": True, "light": True, "closed": False, "paused": None,
                      "created": "2020-01-01T00:00:00+00:00", "request": "Show fixture", "tickets": [],
                      "done": {k: {} for k in ("tickets", "plan", "design", "build")},
                      "show": {"plan": show.plan(self.plan)}}
        self.all_screens = [
            {"id": f"{theme}-{device}", "surface": "home", "theme": theme, "device": device,
             "viewport": self.plan["viewports"][device], "state": "ready", "reference_state": "ready",
             "reference": f".factory/{device}.png", "capture": f".factory/{device}.png",
             "description": "Summary now shows the count.", "inspected": True}
            for theme in ("light", "dark") for device in ("desktop", "phone")]
        self.data = {"version": 1, "screens": copy.deepcopy(self.all_screens[:1])}
        self.prepare()

    def prepare(self):
        self.data["candidate"] = evidence.candidate(self.project)
        report = show.prepare(self.project, self.state, self.data)
        path = self.project / ".factory/fast/show.md"
        path.write_text(show.markdown(self.project, report), encoding="utf-8")
        self.state["show"]["report"] = {**report, "path": ".factory/fast/show.md", "sha256": evidence.file_hash(path)}

    def share(self):
        self.state["show"]["shared"] = {"channel": "chat", "source": "Controlled fixture", "at": "2020-01-01T00:00:00+00:00"}


class ShowTests(ShowFixture):
    def test_planning_baseline_is_retained_through_show(self):
        self.state["show"]["plan"]["before"] = show.baseline(self.project, self.state["show"]["plan"],
                                                            [self.all_screens[0]])
        self.prepare()
        png(self.project / ".factory/desktop.png", 64, color=20)
        with self.assertRaisesRegex(ValueError, "retain the Before"):
            self.prepare()

    def test_planning_baseline_requires_complete_unique_coverage(self):
        for rows in ([], [self.all_screens[0], self.all_screens[0]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                show.baseline(self.project, self.state["show"]["plan"], rows)

    def test_observed_owner_wait_records_reply_without_quote_or_timeout_approval(self):
        from safe_engine import run_metrics
        import fast_metrics

        self.state["pr_instance"] = "b" * 32
        self.plan["wait_minutes"] = 1
        self.state["show"]["plan"] = show.plan(self.plan)
        self.prepare()
        gate = Mock()
        gate.open_run.return_value = (self.project, self.state)
        gate.now.side_effect = lambda: datetime.now(timezone.utc).isoformat()
        gate.fail.side_effect = AssertionError
        for action, data in (("shared", {"channel": "chat", "source": "Fixture", "sent": True,
                                     "images_accessible": True}),
                             ("reply", {"action": "proceed", "source": "Fixture",
                                        "quote": "SECRET_REPLY", "leave": []})):
            path = self.project / f".factory/{action}.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            args = SimpleNamespace(command="show", project=str(self.project), candidate=False,
                                   plan=None, prepare=None, shared=str(path) if action == "shared" else None,
                                   reply=str(path) if action == "reply" else None)
            show_command.run(args, gate)
            if action == "shared":
                time.sleep(.01)
        key = fast_metrics.identity(self.state)
        report = run_metrics.finalize(self.project, key)
        self.assertGreater(report["waits"]["approval"], 0)
        self.assertNotIn("SECRET_REPLY", (run_metrics.run_dir(self.project, key) / "events.jsonl").read_text())
        timeout = copy.deepcopy(self.state)
        timeout["key"], timeout["pr_instance"] = "timeout", "c" * 32
        timeout["show"]["plan"]["wait_minutes"] = 0
        timeout["show"].pop("reply")
        timeout["show"]["shared"] = {**timeout["show"]["shared"], "at": gate.now()}
        fast_metrics.on_show(self.project, timeout, "start")
        self.assertIn("not approval", show.ready_for_prove(self.project, timeout))
        events = run_metrics.read_events(self.project, fast_metrics.identity(timeout))
        self.assertEqual(next(row["status"] for row in events if row["type"] == "wait.finish"),
                         "deadline_elapsed")

    def test_complete_pairs_and_inspection_are_required(self):
        changes = (lambda d: d["screens"].pop(),
                   lambda d: d["screens"][0].update(viewport=[1, 1]),
                   lambda d: d["screens"][0].update(inspected=False),
                   lambda d: d["screens"][0].update(reference_state="loading"),
                   lambda d: d["screens"][0].update(theme="unknown"),
                   lambda d: d["screens"][0].update(device=[]),
                   lambda d: d["screens"].append(copy.deepcopy(self.all_screens[1])),
                   lambda d: d["screens"].append({**d["screens"][0], "id": "duplicate-case"}))
        for change in changes:
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                change(data)
                with self.assertRaises(ValueError):
                    show.prepare(self.project, self.state, data)
        report = (self.project / ".factory/fast/show.md").read_text(encoding="utf-8")
        self.assertEqual(report.count("| Before | After |"), 1)
        self.assertEqual(self.state["show"]["plan"]["variants"], [{"theme": "light", "device": "desktop"}])
        self.assertEqual(self.state["show"]["report"]["comparison"], "before")

    def test_mobile_and_explicit_four_pairs(self):
        for screens in (self.all_screens[1:2], self.all_screens):
            with self.subTest(screens=len(screens)):
                variants = [{key: row[key] for key in ("theme", "device")} for row in screens]
                devices = {row["device"] for row in screens}
                self.state["show"]["plan"] = show.plan({**self.plan, "variants": variants,
                    "viewports": {key: self.plan["viewports"][key] for key in devices}})
                self.data["screens"] = copy.deepcopy(screens)
                self.prepare()
                report = self.state["show"]["report"]
                self.assertEqual(len(report["screens"]), len(screens))
                self.assertEqual(show.markdown(self.project, report).count("| Before | After |"), len(screens))
                self.data["screens"].pop()
                with self.assertRaises(ValueError):
                    show.prepare(self.project, self.state, self.data)

    def test_legacy_four_cases_and_design_labels(self):
        self.state["show"]["plan"].pop("variants")
        self.state["show"]["plan"].pop("comparison")
        with self.assertRaises(ValueError):
            show.prepare(self.project, self.state, self.data)
        self.data["screens"] = copy.deepcopy(self.all_screens)
        self.prepare()
        report = self.state["show"]["report"]
        self.assertEqual(report["comparison"], "design")
        self.assertEqual(show.markdown(self.project, report).count("| Design | Current |"), 4)
        report.pop("comparison")
        self.assertEqual(show.markdown(self.project, report).count("| Design | Current |"), 4)

    def test_design_port_requires_design_and_preserves_original_reference(self):
        self.state["design_port"] = True
        with self.assertRaisesRegex(ValueError, "design comparison"):
            show.prepare(self.project, self.state, self.data)
        self.state["show"]["plan"] = show.plan({**self.plan, "comparison": "design"})
        design = {"version": 1, "builder": "fixture", "screens": [{
            "id": "light-desktop", "reference": ".factory/desktop.png", "viewport": [64, 32],
            "theme": "light", "state": "ready"}], "elements": [{"id": "count", "screen": "light-desktop",
            "name": "Count", "status": "done"}]}
        path = self.project / ".factory/design.json"
        path.write_text(json.dumps(design))
        self.state["design"] = {"path": ".factory/design.json", "inventory": evidence.inventory(self.project, design)}
        self.prepare()
        self.assertIn("| Design | Current |", show.markdown(self.project, self.state["show"]["report"]))
        self.data["screens"][0]["id"] = "replacement"
        with self.assertRaisesRegex(ValueError, "frozen design reference"):
            show.prepare(self.project, self.state, self.data)
        self.data["screens"][0]["id"] = "light-desktop"
        png(self.project / ".factory/desktop.png", 64, color=20)
        with self.assertRaisesRegex(ValueError, "preserve the original scope"):
            show.prepare(self.project, self.state, self.data)

    def test_generation_and_local_paths_never_establish_delivery(self):
        self.assertIn("actual delivery", " ".join(show.problems(self.state, self.project, final=True)))
        for source in (".factory/fast/show.md", "C:/report.md", "/report.md"):
            with self.assertRaisesRegex(ValueError, "local path"):
                show.publication({"channel": "chat", "source": source, "sent": True, "images_accessible": True})

    def test_default_deadline_and_explicit_owner_stop(self):
        self.plan.pop("wait_minutes")
        self.state["show"]["plan"] = show.plan(self.plan)
        self.share()
        with self.assertRaisesRegex(ValueError, "Waiting"):
            show.ready_for_prove(self.project, self.state, "2020-01-01T00:29:59+00:00")
        self.assertIn("No owner reply", show.ready_for_prove(self.project, self.state, "2020-01-01T00:30:00+00:00"))
        for action in ("stop", "change"):
            self.state["show"]["reply"] = {"action": action}
            with self.assertRaisesRegex(ValueError, "stop/change"):
                show.ready_for_prove(self.project, self.state, "2020-01-02T00:00:00+00:00")
        self.state["show"]["reply"] = {"action": "proceed"}
        self.assertIn("Owner reply", show.ready_for_prove(self.project, self.state, "2020-01-01T00:00:01+00:00"))

    def test_leave_requires_followup_and_exact_reply_evidence(self):
        data = {"action": "proceed", "source": "Fixture message", "quote": "Leave spacing for later",
                "leave": [{"surface": "home", "description": "Spacing", "followup": ""}]}
        with self.assertRaises(ValueError):
            show.reply(data, self.state)
        data["leave"][0]["followup"] = "https://example.test/issues/1"
        self.assertEqual(show.reply(data, self.state)["leave"], data["leave"])

    def test_source_image_and_report_tampering_require_fresh_show(self):
        self.share()
        for path, payload in (("source.txt", b"candidate B"), (".factory/desktop.png", b"broken"),
                              (".factory/fast/show.md", b"edited")):
            with self.subTest(path=path):
                file = self.project / path
                original = file.read_bytes()
                file.write_bytes(payload)
                self.assertTrue(show.problems(self.state, self.project, final=True))
                file.write_bytes(original)
        self.assertEqual(show.problems(self.state, self.project, final=True), [])

    def test_suite_hook_only_matches_declared_command_and_preserves_old_runs(self):
        self.state["show"]["plan"]["full_suite"] = ["python", "tests/run.py"]
        self.assertIn("actual delivery", show.suite_guard("python tests/run.py", self.state, self.project))
        self.assertIsNone(show.suite_guard("python quick.py", self.state, self.project))
        self.share()
        self.assertIsNone(show.suite_guard("python tests/run.py", self.state, self.project))
        for field in ("ui", "show_first"):
            old = {**self.state, field: False, "show": {"proof": {"passed": False}}}
            self.assertEqual(show.completion_problems(old, self.project), [])
            self.assertIsNone(show.suite_guard("python tests/run.py", old, self.project))

    def test_stale_pass_blocks_done_run_and_handoff_after_fresh_show(self):
        self.share()
        self.state["show"]["proof"] = {"passed": True, "candidate": self.data["candidate"]}
        (self.project / "source.txt").write_text("candidate B")
        self.prepare()
        for check in (fast_record.check_done_run, fast_record.check_handoff):
            with self.subTest(check=check.__name__):
                self.assertIn("proof is stale", " ".join(check(self.state, "", project=self.project)))
        self.state["show"]["proof"]["candidate"] = self.data["candidate"]
        self.assertEqual(show.completion_problems(self.state, self.project), [])


class ShowCommandTests(ShowFixture):
    def setUp(self):
        super().setUp()
        self.gate_home = self.home / "gate-home"
        self.entry = ledger.registry_path(self.gate_home / "active", self.project)
        ledger.save(self.entry, ledger.new_registration(self.project, self.state["key"]))
        self.installed = fast_install.copy_entries(self.home / "installed/.agents/skills") / "safe-engine/scripts/fast_gate.py"
        self.state["bundle"] = {"root": str(ROOT), "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
        ledger.save(ledger.state_path(self.entry), self.state)
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.gate_home), PYTHONIOENCODING="utf-8")
        self.env.pop("PYTHONPATH", None)
        (self.project / ".factory/fast/work-record.md").write_text("## Show\nControlled fixture\n## Done-run\nPASS fixture\n**Logs:** fixture\n")

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(self.installed), *args, "--project", str(self.project)],
                                cwd=self.home, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=45)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def json_action(self, action, data):
        path = self.project / f".factory/{action}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return self.cli("show", "--" + action, str(path))

    def shown(self):
        self.data["candidate"] = evidence.candidate(self.project)
        self.json_action("prepare", self.data)
        self.json_action("shared", {"channel": "chat", "source": "Controlled command fixture", "sent": True,
                                    "images_accessible": True})
        self.cli("done", "show")

    def test_plan_command_freezes_default_coverage(self):
        self.state.pop("show")
        self.state["done"].pop("plan")
        ledger.save(ledger.state_path(self.entry), self.state)
        self.json_action("plan", {**self.plan, "before": [self.all_screens[0]]})
        planned = ledger.load(ledger.state_path(self.entry))["show"]["plan"]
        self.assertEqual(planned["variants"], [{"theme": "light", "device": "desktop"}])
        self.assertEqual(planned["comparison"], "before")

    def test_installed_suite_stale_rejection_recovery_and_picture_only_reuse(self):
        self.cli("prove", "--suite", ok=False)
        self.assertFalse((self.project / ".factory/invocations").exists())
        self.shown()
        self.cli("prove", "--suite")
        original = ledger.load(ledger.state_path(self.entry))["show"]["proof"]
        png(self.project / ".factory/desktop.png", 64, color=20)
        self.shown()
        state = ledger.load(ledger.state_path(self.entry))
        self.assertEqual(state["show"]["proof"], original)
        self.assertEqual(show.completion_problems(state, self.project), [])
        self.assertEqual((self.project / ".factory/invocations").read_text(), "run\n")
        (self.project / "source.txt").write_text("candidate B")
        self.shown()
        state = ledger.load(ledger.state_path(self.entry))
        self.assertIn("proof is stale", " ".join(show.completion_problems(state, self.project)))
        self.assertIn("proof is stale", self.cli("done", "done-run", ok=False))
        # Close must revalidate even if an earlier handoff exists.
        state["done"]["handoff"] = {}
        ledger.save(ledger.state_path(self.entry), state)
        self.assertIn("proof is stale", self.cli("close", ok=False))
        self.cli("prove", "--suite")
        self.assertEqual(show.completion_problems(ledger.load(ledger.state_path(self.entry)), self.project), [])
        events = [json.loads(line) for line in (self.gate_home / "logs/gate.log").read_text().splitlines()]
        self.assertIn(original, [event["proof"] for event in events if event["event"] == "show.proof_replaced"])

    def test_failure_persists_across_show_then_success_recovers(self):
        self.shown()
        failure = self.project / ".factory/fail"
        failure.touch()
        self.cli("prove", "--suite", ok=False)
        self.shown()
        state = ledger.load(ledger.state_path(self.entry))
        self.assertIn("failed or was interrupted", " ".join(show.completion_problems(state, self.project)))
        failure.unlink()
        self.cli("prove", "--suite")
        self.assertEqual(show.completion_problems(ledger.load(ledger.state_path(self.entry)), self.project), [])

    def test_stop_survives_new_show_until_proceed(self):
        self.shown()
        self.json_action("reply", {"action": "stop", "source": "Controlled fixture", "quote": "Stop"})
        self.shown_without_completion()
        self.assertIn("stop/change", self.cli("prove", "--suite", ok=False))
        self.json_action("reply", {"action": "proceed", "source": "Controlled fixture", "quote": "Proceed"})
        self.cli("done", "show")
        self.cli("prove", "--suite")

    def test_concurrent_observation_pause_and_owner_stop_keep_current_state(self):
        self.shown()
        state = ledger.load(ledger.state_path(self.entry))
        state['show']['plan']['full_suite'] = [sys.executable, '-c',
            'from pathlib import Path\nimport time\n'
            'Path(".factory/suite-start").touch()\n'
            'end = time.monotonic() + 60\n'
            'while not Path(".factory/suite-release").exists() and time.monotonic() < end: time.sleep(.02)\n'
            'raise SystemExit(0 if Path(".factory/suite-release").exists() else 2)']
        state['show']['plan']['timeout_seconds'] = 90
        state['checks'] = {'prepared': {'checks': {'A1': {'manual': 'Observe the result'}}}}
        state['check_selection'] = True
        ledger.save(ledger.state_path(self.entry), state)

        def start():
            started = self.project / '.factory/suite-start'
            release = self.project / '.factory/suite-release'
            started.unlink(missing_ok=True)
            release.unlink(missing_ok=True)
            process = subprocess.Popen([sys.executable, str(self.installed), 'prove', '--suite', '--fresh',
                                        '--project', str(self.project)], cwd=self.home, env=self.env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                proof = ledger.load(ledger.state_path(self.entry))['show'].get('proof', {})
                if proof.get('status') == 'running' and started.exists():
                    return process
                if process.poll() is not None:
                    break
                time.sleep(.02)
            release.touch()
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5)
            self.fail('Suite did not start')

        def finish(process):
            (self.project / '.factory/suite-release').touch()
            try:
                return process.communicate(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

        process = start()
        try:
            observation = self.project / '.factory/observation.json'
            observation.write_text(json.dumps({'criterion': 'A1', 'candidate': evidence.candidate(self.project),
                                               'source': 'controlled fixture', 'observation': 'PASS during suite',
                                               'verdict': 'PASS'}))
            self.cli('checks', '--observe', str(observation))
            self.cli('pause', '--reason', 'owner checkpoint')
        finally:
            output, error = finish(process)
        self.assertEqual(process.returncode, 0, output + error)
        current = ledger.load(ledger.state_path(self.entry))
        self.assertTrue(current['show']['proof']['passed'])
        self.assertEqual(current['checks']['observations']['A1']['verdict'], 'PASS')
        self.assertEqual(current['paused']['reason'], 'owner checkpoint')

        self.cli('resume')
        process = start()
        try:
            self.json_action('reply', {'action': 'stop', 'source': 'controlled fixture', 'quote': 'Stop'})
        finally:
            output, error = finish(process)
        self.assertNotEqual(process.returncode, 0, output + error)
        current = ledger.load(ledger.state_path(self.entry))
        self.assertEqual(current['show']['reply']['action'], 'stop')
        self.assertFalse(current['show']['proof']['passed'])

    def test_a_b_a_reuses_original_log_and_tamper_reruns(self):
        subprocess.run(['git', 'add', '.gitignore', 'source.txt'], cwd=self.project, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid',
                        'commit', '-qm', 'fixture'], cwd=self.project, check=True)
        command = [sys.executable, '-c', 'import os; print(os.environ["PROOF_MODE"])']
        state = {'key': 'cache-fixture', 'ui': False, 'done': {'build': {}}, 'suite_policy': True,
                 'suite': {'plan': {'full_suite': command, 'timeout_seconds': 10,
                                    'suite_inputs': {'files': [], 'environment': ['PROOF_MODE']}}},
                 'bundle': self.state['bundle']}
        class Gate:
            def __init__(self):
                self.state = copy.deepcopy(state)
            def put(self, project, value):
                self.state = copy.deepcopy(value)
            def mutate(self, project, base, update):
                current = copy.deepcopy(self.state)
                update(current)
                self.state = current
            def log(self, *args, **kwargs):
                pass
        gate = Gate()
        queue = self.home / 'isolated-queue'
        queue.mkdir()
        receipts = []
        with patch.object(suite_queue, 'machine_directory', return_value=queue):
            for mode in ('A', 'B', 'A'):
                with patch.dict(os.environ, PROOF_MODE=mode):
                    show_command.prove(self.project, copy.deepcopy(gate.state), gate)
                receipts.append(copy.deepcopy(gate.state['suite']['proof']))
            first, second, third = receipts
            self.assertEqual([row['reused'] for row in receipts], [False, False, True])
            self.assertNotEqual(first['log'], second['log'])
            self.assertEqual(first['log'], third['log'])
            self.assertEqual(Path(first['log']).read_text().strip(), 'A')
            self.assertEqual(Path(second['log']).read_text().strip(), 'B')
            Path(first['log']).write_text('tampered')
            with patch.dict(os.environ, PROOF_MODE='A'):
                show_command.prove(self.project, copy.deepcopy(gate.state), gate)
            self.assertFalse(gate.state['suite']['proof']['reused'])

    def shown_without_completion(self):
        self.json_action("prepare", self.data)
        self.json_action("shared", {"channel": "chat", "source": "Controlled fixture", "sent": True,
                                    "images_accessible": True})

    def test_checkout_without_selection_uses_validated_checkout_runner(self):
        self.installed = SCRIPTS / "fast_gate.py"
        self.state["bundle"] = None
        ledger.save(ledger.state_path(self.entry), self.state)
        self.shown()
        self.cli("prove", "--suite")
        self.assertTrue(ledger.load(ledger.state_path(self.entry))["show"]["proof"]["passed"])

    def test_installed_entry_refuses_missing_or_mismatched_bundle(self):
        self.shown()
        state = ledger.load(ledger.state_path(self.entry))
        state["bundle"]["revision"] = "0" * 40
        ledger.save(ledger.state_path(self.entry), state)
        self.assertIn("requested commit", self.cli("prove", "--suite", ok=False))
        state["bundle"] = None
        ledger.save(ledger.state_path(self.entry), state)
        self.cli("prove", "--suite", ok=False)
        self.assertFalse((self.project / ".factory/invocations").exists())


if __name__ == "__main__":
    unittest.main()
