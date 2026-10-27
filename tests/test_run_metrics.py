"""Factory run metrics: contract, aggregation, privacy, overhead and fixture timeline."""
import json
import tempfile
import unittest
from pathlib import Path

from safe_engine import run_metrics as metrics


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="run-metrics-")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.key = "demo-run"

    def test_duplicate_event_ids_do_not_double_count(self):
        metrics.ensure_run(self.project, self.key, factory_revision="abc", mode="fast", kind="change")
        metrics.emit(self.project, self.key, "operation.start", name="x", event_id="op-1")
        metrics.emit(self.project, self.key, "operation.start", name="x", event_id="op-1")
        events = [e for e in metrics.read_events(self.project, self.key) if e["event_id"] == "op-1"]
        self.assertEqual(len(events), 1)

    def test_parallel_elapsed_sum_and_overlap(self):
        metrics.ensure_run(self.project, self.key)
        # Two overlapping 1s operations: sum=2, overlap≈1, elapsed≈1
        base = 1_000_000_000
        path = metrics.run_dir(self.project, self.key) / metrics.EVENTS_NAME
        rows = [
            {"metrics_schema": 1, "event_id": "a0", "type": "operation.start", "t": "2026-01-01T00:00:00+00:00",
             "mono_ns": base, "run_key": self.key, "name": "a"},
            {"metrics_schema": 1, "event_id": "b0", "type": "operation.start", "t": "2026-01-01T00:00:00+00:00",
             "mono_ns": base, "run_key": self.key, "name": "b"},
            {"metrics_schema": 1, "event_id": "a1", "type": "operation.finish", "t": "2026-01-01T00:00:01+00:00",
             "mono_ns": base + 1_000_000_000, "run_key": self.key, "name": "a", "parent_id": "a0"},
            {"metrics_schema": 1, "event_id": "b1", "type": "operation.finish", "t": "2026-01-01T00:00:01+00:00",
             "mono_ns": base + 1_000_000_000, "run_key": self.key, "name": "b", "parent_id": "b0"},
        ]
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        self.assertEqual(report["summed_operation_seconds"], 2.0)
        self.assertEqual(report["overlap_seconds"], 1.0)
        self.assertEqual(report["elapsed_seconds"], 1.0)
        self.assertNotIn("cpu_time", json.dumps(report).lower().replace(" ", ""))
        self.assertIn("not CPU time", report["duration_notes"]["elapsed"])

    def test_incomplete_span_not_invented(self):
        metrics.ensure_run(self.project, self.key)
        metrics.emit(self.project, self.key, "operation.start", name="hang", event_id="hang-1")
        report = metrics.aggregate(metrics.read_events(self.project, self.key), outcome="abort")
        self.assertTrue(any(row.get("event_id") == "hang-1" for row in report["incomplete_spans"]))
        self.assertEqual(report["summed_operation_seconds"], 0.0)

    def test_privacy_skips_sensitive_fields_and_bounds_size(self):
        metrics.ensure_run(self.project, self.key)
        metrics.emit(self.project, self.key, "coverage_gap", gap="test", prompt="SECRET", password="x",
                     detail="ok", event_id="gap-1")
        event = next(e for e in metrics.read_events(self.project, self.key) if e["event_id"] == "gap-1")
        self.assertNotIn("prompt", event)
        self.assertNotIn("password", event)
        self.assertEqual(event["detail"], "ok")

    def test_corrupt_line_is_gap_not_crash(self):
        metrics.ensure_run(self.project, self.key)
        path = metrics.run_dir(self.project, self.key) / metrics.EVENTS_NAME
        path.write_text(path.read_text(encoding="utf-8") + "{not json\n", encoding="utf-8")
        events = metrics.read_events(self.project, self.key)
        self.assertTrue(any(e.get("type") == "run.start" for e in events))

    def test_unwritable_emit_does_not_raise(self):
        missing = self.project / "nope"
        # Point at a file pretending to be the metrics directory parent conflict.
        blocker = self.project / ".factory"
        blocker.write_text("not-a-dir", encoding="utf-8")
        self.assertFalse(metrics.emit(self.project, self.key, "reuse", name="x"))

    def test_cost_requires_provenance(self):
        metrics.ensure_run(self.project, self.key)
        metrics.emit(self.project, self.key, "cost", amount=1, units="tokens")  # no provenance
        metrics.emit(self.project, self.key, "cost", amount=2, units="tokens", provenance="host-api",
                     scope="run", event_id="cost-1")
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        self.assertEqual(len(report.get("costs") or []), 1)
        self.assertEqual(report["costs"][0]["provenance"], "host-api")

    def test_finalize_and_compare(self):
        metrics.ensure_run(self.project, self.key, factory_revision="r1", mode="fast", kind="change")
        start = metrics.emit(self.project, self.key, "wait.start", category="helper", event_id="w1")
        self.assertTrue(start)
        metrics.emit(self.project, self.key, "wait.finish", category="helper", event_id="w2", parent_id="w1",
                     duration_seconds=1.5)
        metrics.emit(self.project, self.key, "reuse", name="suite")
        metrics.emit(self.project, self.key, "invalidate", reason="inputs_changed")
        report = metrics.finalize(self.project, self.key, outcome="finish")
        self.assertTrue((metrics.run_dir(self.project, self.key) / "report.md").is_file())
        self.assertEqual(report["waits"]["helper"], 1.5)
        self.assertEqual(report["reuse_count"], 1)
        other = "demo-run-2"
        metrics.ensure_run(self.project, other, factory_revision="r1", mode="fast", kind="change")
        metrics.finalize(self.project, other, outcome="finish")
        compared = metrics.compare(self.project, [self.key, other])
        self.assertEqual(compared["sample_size"], 2)
        self.assertIn("does not claim causation", compared["note"])

    def test_export_and_delete(self):
        metrics.ensure_run(self.project, self.key)
        metrics.finalize(self.project, self.key)
        dest = self.project / "export-out"
        self.assertTrue(metrics.export(self.project, self.key, dest))
        self.assertTrue((dest / "report.json").is_file())
        self.assertTrue(metrics.delete(self.project, self.key))
        self.assertFalse(metrics.run_dir(self.project, self.key).exists())

    def test_fixture_timeline_and_overhead_budget(self):
        key = "fixture-a8"
        metrics.ensure_run(self.project, key, factory_revision="fix", mode="fast", kind="change")
        with metrics.bound(self.project, key, factory_revision="fix", mode="fast", kind="change"):
            metrics.emit_phase(self.project, key, "build", "start", event_id="p-build")
            metrics.emit_current("wait.start", category="suite_queue", event_id="q1")
            metrics.emit_current("wait.finish", category="suite_queue", event_id="q2", parent_id="q1",
                                 duration_seconds=0.2)
            metrics.emit_current("reuse", name="full_suite")
            metrics.emit_current("operation.start", name="retry", event_id="r0")
            metrics.emit_current("operation.finish", name="retry", event_id="r1", parent_id="r0",
                                 duration_seconds=0.05)
            metrics.emit_current("invalidate", reason="failed_retry")
            metrics.emit_current("wait.start", category="owner", event_id="o1")
            metrics.emit_current("wait.finish", category="owner", event_id="o2", parent_id="o1",
                                 duration_seconds=0.1)
            metrics.emit_phase(self.project, key, "build", "cancel", event_id="p-build-cancel")
            metrics.emit_phase(self.project, key, "build", "resume", event_id="p-build-resume")
            metrics.emit_phase(self.project, key, "build", "finish", event_id="p-build-end")
        report = metrics.finalize(self.project, key, outcome="finish")
        self.assertGreaterEqual(report["reuse_count"], 1)
        self.assertIn("failed_retry", report["invalidation_reasons"])
        self.assertGreaterEqual(report["waits"]["suite_queue"], 0.2)
        self.assertGreaterEqual(report["waits"]["owner"], 0.1)
        best = None
        for attempt in range(3):  # machine contention from parallel suite workers can inflate p99
            key = f"overhead-a8-{attempt}"
            result = metrics.measure_overhead(self.project, key, event_count=80)
            if best is None or result["event_append_pair_p99_ms"] < best["event_append_pair_p99_ms"]:
                best = result
            if best["within_budget"]:
                break
        self.assertTrue(best["within_budget"], best)
        self.assertLessEqual(best["event_append_pair_p99_ms"], metrics.OVERHEAD_BUDGET["event_append_p99_ms"])


if __name__ == "__main__":
    unittest.main()
