"""Wait receipts through the real gate command and Stop hook."""
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stdout
from io import StringIO
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_fast_gate import GateHarness, GATE, module

wait, entry, hosts, gate = (module(name) for name in ("fast_wait", "fast_entry", "fast_hosts", "fast_gate"))

class WaitTests(GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.start(kind="change")
        self.stop_event = {"hook_event_name": "Stop"}

    def payload(self, job="worker", name="Finite worker", **changes):
        now = datetime.now(timezone.utc)
        return {"version": 1, "coordinator": "s1", "job": job, "name": name, "kind": "helper",
                "host": "codex", "wakeup": "native-subagent-result", "source": "spawn acknowledgement",
                "observed_at": now.isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(), **changes}

    def command(self, action, data, ok=True, project=None):
        path = self.root / f"{action}-{len(list(self.root.glob(action + '-*.json')))}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        output = self.gate("wait", f"--{action}", str(path), ok=ok, project=project)
        return json.JSONDecoder().raw_decode(output)[0] if action == "add" and ok else output

    def stop(self, tasks=None, **changes):
        event = {**self.stop_event, **changes}
        if tasks is not None:
            event["background_tasks"] = tasks
        return self.hook(event) or {}

    def test_receipt_lifecycle_replay_conflict_and_terminal_dominance(self):
        self.assertEqual(self.stop()["decision"], "block")
        state = next((self.root / "home" / "runs").rglob("*.json"))
        before = state.read_bytes()
        identity = self.command("add", self.payload())
        self.assertEqual(before, state.read_bytes())
        self.assertIn("Finite worker", self.stop()["systemMessage"])
        self.assertIn("already registered", self.command("add", self.payload(), ok=False).lower())
        done = {"version": 1, **identity, "status": "completed", "source": "native result"}
        self.command("finish", done)
        self.command("finish", done)  # idempotent callback, even in a later process
        self.assertIn("Conflicting completion", self.command("finish", {**done, "status": "failed"}, ok=False))
        self.assertEqual(before, state.read_bytes())
        stale = [{"id": "worker", "type": "subagent", "status": "running"}]
        self.assertEqual(self.stop(stale)["decision"], "block")
        self.assertIn("completed", self.gate("wait", "--status"))
        second = self.command("add", self.payload())
        self.assertNotEqual(identity["generation"], second["generation"])
        self.assertNotIn("decision", self.stop())
        for altered in ({**done, "generation": "0" * 32}, {**done, "run": "0" * 32},
                        {**done, "coordinator": "other"}):
            self.command("finish", altered, ok=False)

    def test_concurrent_registration_and_completion(self):
        data = self.payload()
        source = self.root / "concurrent.json"
        source.write_text(json.dumps(data), encoding="utf-8")
        args = [sys.executable, str(GATE), "wait", "--add", str(source), "--project", str(self.project)]
        with subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as one, \
             subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as two:
            results = [p.communicate() for p in (one, two)]
            codes = [p.returncode for p in (one, two)]
        self.assertEqual(sorted(codes), [0, 1], results)
        identity = json.JSONDecoder().raw_decode(next(out for out, _ in results if out.startswith(b"{")).decode())[0]
        finish = self.root / "finish.json"
        finish.write_text(json.dumps({"version": 1, **identity, "status": "failed", "source": "native result"}), encoding="utf-8")
        args[3:5] = ["--finish", str(finish)]
        with subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as one, \
             subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as two:
            results = [p.communicate() for p in (one, two)]
            codes = [p.returncode for p in (one, two)]
        self.assertEqual(codes, [0, 0], results)
        self.assertEqual(self.stop()["decision"], "block")

    def test_contrary_host_evidence_disqualifies_pending(self):
        self.command("add", self.payload())
        self.assertNotIn("decision", self.stop())
        for task in ({"type": "subagent", "status": "completed"},
                     {"type": "subagent", "status": "running", "observer": True},
                     {"type": "subagent", "status": "running", "persistent": True},
                     {"type": "server", "status": "running"}):
            with self.subTest(task=task):
                self.assertEqual(self.stop([{"id": "worker", **task}])["decision"], "block")
        self.assertNotIn("decision", self.stop([{"id": "worker", "type": "subagent", "status": "running"}]))

    def test_two_helpers_finish_out_of_order_and_failed_result_rearms(self):
        first = self.command("add", self.payload(job="first", name="First"))
        second = self.command("add", self.payload(job="second", name="Second"))
        message = self.stop()["systemMessage"]
        self.assertIn("First", message)
        self.assertIn("Second", message)
        self.command("finish", {"version": 1, **second, "status": "failed", "source": "native result"})
        self.assertIn("First", self.stop()["systemMessage"])
        self.command("finish", {"version": 1, **first, "status": "completed", "source": "native result"})
        self.assertEqual(self.stop()["decision"], "block")

    def test_padding_roundtrip_and_invalid_waits(self):
        payload = self.payload(name=" " * 7900 + "Worker" + " " * 7900)
        identity = self.command("add", payload)
        self.assertIn("Worker", self.gate("wait", "--status"))
        self.assertLess(next((self.root / "home" / "waits").rglob("*.pending.json")).stat().st_size, 16384)
        self.assertEqual(identity["job"], "worker")
        self.command("finish", {"version": 1, **identity, "status": "cancelled", "source": "native result"})
        self.assertEqual(self.stop()["decision"], "block")
        for changed in ({"kind": "job"}, {"wakeup": "none"}, {"host": "cursor"}):
            with self.subTest(changed=changed):
                self.command("add", self.payload(job=str(changed), **changed))
                self.assertEqual(self.stop()["decision"], "block")

    def test_stale_unknown_corrupt_and_lost_state_fail_closed(self):
        now = datetime.now(timezone.utc)
        for changed in ({"observed_at": (now - timedelta(hours=1)).isoformat()},
                        {"expires_at": (now - timedelta(seconds=1)).isoformat()},
                        {"observed_at": (now + timedelta(minutes=1)).isoformat()}):
            self.command("add", self.payload(job=str(changed), **changed), ok=False)
        identity = self.command("add", self.payload())
        receipt = next((self.root / "home" / "waits").rglob("*.pending.json"))
        original = receipt.read_bytes()
        stored = json.loads(original)
        stored["expires_at"] = (now - timedelta(seconds=1)).isoformat()
        receipt.write_text(json.dumps(stored), encoding="utf-8")
        self.assertEqual(self.stop()["decision"], "block")
        receipt.write_bytes(original)
        with patch.object(wait, "clock", return_value=now.timestamp() - 60):
            run = json.loads(next((self.root / "home" / "runs").glob("*.json")).read_text(encoding="utf-8"))
            self.assertFalse(wait.state(self.root / "home", run)["pending"])
        receipt.write_text("{bad", encoding="utf-8")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertIn("unknown", self.gate("wait", "--status").lower())
        self.command("finish", {"version": 1, **identity, "status": "completed", "source": "native result"}, ok=False)
        receipt.unlink()
        self.assertEqual(self.stop()["decision"], "block")

    def test_legacy_pause_repeat_abort_and_other_owned_run(self):
        self.assertIsNone(self.stop(stop_hook_active=True).get("decision"))
        self.command("add", self.payload())
        other = self.root / "other"
        other.mkdir()
        self.gate("start", "--key", "other", "--kind", "change", "--request", "Other work", project=other)
        self.hook({"hook_event_name": "PreToolUse", "tool_name": "Write",
                   "tool_input": {"file_path": str(other / "file.txt")}, "cwd": str(other)})
        self.assertEqual(self.stop(cwd=str(self.root))["decision"], "block")
        self.gate("pause", "--reason", "owner input")
        self.assertEqual(self.stop(cwd=str(self.root))["decision"], "block")

    def test_mixed_bundle_requires_each_owned_run_and_legacy_observation(self):
        home = self.root / "home"
        run = json.loads(next((home / "runs").glob("*.json")).read_text(encoding="utf-8"))
        selected = self.root / "selected" / "skills/safe-engine/scripts"
        selected.mkdir(parents=True)
        (selected / "fast_gate.py").write_text("# selected gate identity\n", encoding="utf-8")
        other = {**run, "project": str(self.root / "other"), "pr_instance": "c" * 32,
                 "bundle": {"root": str(selected.parents[2])}}
        first = self.command("add", self.payload(job="first", name="First"))
        tasks = [(None, {}, run), (None, {}, other)]
        raw = {"hook_event_name": "Stop", "cwd": str(self.root), "session_id": "s1"}

        def mixed():
            with patch.object(gate, "HOME", home), patch.object(entry, "hook_runs", return_value=tasks), \
                 redirect_stdout(StringIO()) as output:
                entry.hook("codex", raw, hosts.read("codex", raw), tasks, gate)
            return json.loads(output.getvalue())

        self.assertEqual(mixed()["decision"], "block")
        second = wait.add(home, other, self.payload(job="second", name="Second"))
        message = mixed()["systemMessage"]
        self.assertIn("First", message)
        self.assertIn("Second", message)
        wait.finish(home, other, {"version": 1, **second, "status": "completed", "source": "native result"})
        self.assertEqual(mixed()["decision"], "block")
        wait.finish(home, run, {"version": 1, **first, "status": "completed", "source": "native result"})
        legacy = {**run, "pr_instance": "d" * 32, "wait_receipts": False}
        event = {"waiting": True}
        with patch.object(gate, "HOME", home):
            self.assertIsNone(wait.blocked(event, [(None, {}, legacy)], "s1", gate))
            self.assertEqual(wait.blocked({"waiting": True}, [(None, {}, {**legacy, "lost": True})], "s1", gate),
                             {**legacy, "lost": True})
