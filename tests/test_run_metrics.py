"""Factory run metrics: contract, aggregation, privacy, overhead and fixture timeline."""
import json
import subprocess
import sys
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
        self.assertEqual(report["unaccounted_seconds"], 0.0)
        self.assertEqual(report["ranked"][0]["kind"], "command")
        self.assertIn("Where this run went", metrics.markdown(report))
        self.assertNotIn("cpu_time", json.dumps(report).lower().replace(" ", ""))
        self.assertIn("not CPU time", report["duration_notes"]["elapsed"])

    def test_container_ops_excluded_from_sum_and_overlap(self):
        metrics.ensure_run(self.project, self.key)
        base = 2_000_000_000
        path = metrics.run_dir(self.project, self.key) / metrics.EVENTS_NAME
        rows = [
            {"metrics_schema": 1, "event_id": "s0", "type": "operation.start", "t": "2026-01-01T00:00:00+00:00",
             "mono_ns": base, "run_key": self.key, "name": "full_suite", "container": True},
            {"metrics_schema": 1, "event_id": "c0", "type": "operation.start", "t": "2026-01-01T00:00:00+00:00",
             "mono_ns": base, "run_key": self.key, "name": "python"},
            {"metrics_schema": 1, "event_id": "c1", "type": "operation.finish", "t": "2026-01-01T00:00:01+00:00",
             "mono_ns": base + 1_000_000_000, "run_key": self.key, "name": "python", "parent_id": "c0"},
            {"metrics_schema": 1, "event_id": "s1", "type": "operation.finish", "t": "2026-01-01T00:00:01+00:00",
             "mono_ns": base + 1_000_000_000, "run_key": self.key, "name": "full_suite",
             "parent_id": "s0", "container": True, "duration_seconds": 1.0},
        ]
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        self.assertEqual(report["summed_operation_seconds"], 1.0)
        self.assertEqual(report["overlap_seconds"], 0.0)

    def test_wait_uses_utc_not_cross_process_mono(self):
        metrics.ensure_run(self.project, self.key)
        path = metrics.run_dir(self.project, self.key) / metrics.EVENTS_NAME
        rows = [
            {"metrics_schema": 1, "event_id": "w0", "type": "wait.start", "t": "2026-01-01T00:00:00+00:00",
             "mono_ns": 10, "run_key": self.key, "category": "helper"},
            {"metrics_schema": 1, "event_id": "w1", "type": "wait.finish", "t": "2026-01-01T00:00:02+00:00",
             "mono_ns": 11, "run_key": self.key, "category": "helper", "parent_id": "w0"},
        ]
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        self.assertEqual(report["waits"]["helper"], 2.0)

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

    def test_host_usage_prices_only_solid_records(self):
        from safe_engine.host_usage import load, summarize
        transcript = "\n".join([
            '{"type":"user","message":"secret prompt"}',
            '{"type":"cost-state","modelUsage":{"old":{"inputTokens":1,"outputTokens":1,"costUSD":9}},"totalCostUSD":9,"hasUnknownModelCost":false}',
            '{"type":"cost-state","modelUsage":{"m":{"inputTokens":10,"outputTokens":5,"thinkingTokens":0,"cacheReadInputTokens":0,"cacheCreationInputTokens":0,"costUSD":0.2}},"totalCostUSD":0.2,"hasUnknownModelCost":false}',
        ])
        summary = summarize(load(transcript))
        self.assertEqual(summary["tokens"], 15)
        self.assertEqual(summary["cost_kind"], "host")
        self.assertEqual(summary["cost_usd"], 0.2)
        unknown = {"modelUsage": {"m": {"inputTokens": 10, "outputTokens": 5}}, "hasUnknownModelCost": True}
        bare = summarize(unknown)
        self.assertEqual(bare["tokens"], 15)
        self.assertEqual(bare["cost_kind"], "unavailable")
        rates = {"per_million": {"m": {"input": 1, "output": 2, "thinking": 2, "cache_read": 0.1, "cache_write": 1}}}
        priced = summarize(unknown, rates)
        self.assertEqual(priced["cost_kind"], "estimated")
        self.assertAlmostEqual(priced["cost_usd"], 10 / 1_000_000 + 10 / 1_000_000)
        partial = {"per_million": {"m": {"input": 1}}}
        self.assertEqual(summarize(unknown, partial)["cost_kind"], "unavailable")
        metrics.ensure_run(self.project, self.key)
        self.assertTrue(metrics.attach_usage(self.project, self.key, summary))
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        text = metrics.markdown(report)
        self.assertIn("host-reported", text)
        self.assertIn("tokens counted: 15", text)
        self.assertNotIn("secret prompt", text)

    def test_cumulative_sessions_and_codex_counts(self):
        from safe_engine.host_usage import load, summarize
        metrics.ensure_run(self.project, self.key)
        for session, count in (("helper-a", 100), ("helper-a", 150), ("helper-a", 150),
                               ("helper-b", 70), ("helper-a", 100)):
            summary = summarize({"sessionId": session, "modelUsage": {"same": {"inputTokens": count}},
                                 "hasUnknownModelCost": True})
            self.assertTrue(metrics.attach_usage(self.project, self.key, summary))
        transcript = "\n".join(json.dumps(row) for row in (
            {"type": "session_meta", "payload": {"id": "codex-helper"}},
            {"type": "turn_context", "payload": {"model": "gpt-test"}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": 100, "cached_input_tokens": 40,
                                      "output_tokens": 20, "reasoning_output_tokens": 5,
                                      "total_tokens": 120}}}},
        ))
        codex = summarize(load(transcript))
        self.assertEqual(codex["tokens"], 120)
        self.assertEqual(codex["provenance"], "codex-token-count")
        self.assertTrue(metrics.attach_usage(self.project, self.key, codex))
        costs = metrics.aggregate(metrics.read_events(self.project, self.key))["costs"]
        self.assertEqual(sorted(row["amount"] for row in costs), [70, 120, 150])
        self.assertEqual(len({row["session_id"] for row in costs}), 3)
        self.assertTrue(all(row["scope"] == "shared_session" for row in costs))
        self.assertIn("cache_read 40", next(row["detail"] for row in costs if row["amount"] == 120))
        self.assertIn("reasoning_output 5 (included in output)",
                      next(row["detail"] for row in costs if row["amount"] == 120))
        self.assertNotIn("thinking 0", next(row["detail"] for row in costs if row["amount"] == 120))
        with self.assertRaises(ValueError):
            summarize({"type": "codex-usage", "total_token_usage": {
                "input_tokens": 10, "cached_input_tokens": 11, "output_tokens": 1}})

    def test_incomplete_usage_snapshot_is_not_reported_as_a_total(self):
        summary = {"provenance": "host-cost-state", "session_id": "fixture",
                   "tokens": 30, "models": [{"model": "a", "tokens": 10, "counts": {"input": 10}},
                                            {"model": "b", "tokens": 20, "counts": {"input": 20}}],
                   "cost_kind": "unavailable", "cost_usd": None}
        old_cap = metrics.MAX_EVENTS_PER_RUN
        self.addCleanup(setattr, metrics, "MAX_EVENTS_PER_RUN", old_cap)
        metrics.MAX_EVENTS_PER_RUN = 1
        self.assertFalse(metrics.attach_usage(self.project, self.key, summary))
        report = metrics.aggregate(metrics.read_events(self.project, self.key))
        self.assertFalse(report.get("costs"))
        self.assertTrue(any(gap["gap"] == "usage_snapshot_incomplete" for gap in report["coverage_gaps"]))

    def test_event_index_survives_processes_and_rewrite(self):
        root = Path(__file__).resolve().parents[1]
        script = ("from safe_engine import run_metrics as m; import sys; "
                  "[m.emit(sys.argv[1], 'run', 'reuse', event_id=f'{sys.argv[2]}-{i}') "
                  "for i in range(30)]")
        workers = [subprocess.Popen([sys.executable, "-c", script, str(self.project), str(i)], cwd=root)
                   for i in range(3)]
        self.assertTrue(all(worker.wait() == 0 for worker in workers))
        self.assertEqual(len(metrics.read_events(self.project, "run")), 90)
        self.assertTrue(metrics.emit(self.project, "run", "reuse", event_id="0-0"))
        path = metrics.run_dir(self.project, "run") / metrics.EVENTS_NAME
        path.write_text('{"event_id":"reset","type":"reuse","t":"2026-01-01T00:00:00Z"}\n'
                        '{bad json\n', encoding="utf-8")
        self.assertTrue(metrics.emit(self.project, "run", "reuse", event_id="after-reset"))
        events = metrics.read_events(self.project, "run")
        self.assertEqual({row["event_id"] for row in events if row["type"] == "reuse"},
                         {"reset", "after-reset"})
        self.assertTrue(any(row.get("gap") == "analytics_corrupt" for row in events))

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

    def test_observed_tasks_helpers_resume_and_failed_commands(self):
        rows = [
            ("t0", "task.declare", 0, {"task_id": "T1"}),
            ("t1", "task.start", 0, {"task_id": "T1"}),
            ("p0", "phase.start", 0, {"phase": "build"}),
            ("c0", "operation.start", 1, {"name": "check"}),
            ("w0", "wait.start", 1, {"category": "helper", "helper_id": "opaque"}),
            ("w1", "wait.finish", 4, {"category": "helper", "helper_id": "opaque",
                                           "parent_id": "w0", "status": "completed"}),
            ("c1", "operation.finish", 5, {"name": "check", "parent_id": "c0", "passed": False}),
            ("p1", "phase.cancel", 5, {"phase": "build"}),
            ("t2", "task.cancel", 5, {"task_id": "T1"}),
            ("p2", "phase.resume", 6, {"phase": "build"}),
            ("t3", "task.resume", 6, {"task_id": "T1"}),
            ("p3", "phase.finish", 8, {"phase": "build"}),
            ("t4", "task.finish", 8, {"task_id": "T1"}),
        ]
        events = [{"event_id": name, "type": kind, "t": f"2026-01-01T00:00:{second:02d}+00:00",
                   "pid": 10, "mono_ns": second * 1_000_000_000, **fields}
                  for name, kind, second, fields in rows]
        report = metrics.aggregate(events, outcome="finish")
        self.assertEqual(report["phases"]["build"]["duration_seconds"], 7.0)
        self.assertEqual(report["tasks"]["T1"]["duration_seconds"], 7.0)
        self.assertEqual(report["helpers"][0]["helper_id"], "opaque")
        self.assertEqual(report["helpers"][0]["status"], "completed")
        self.assertEqual(report["failed_operation_count"], 1)
        self.assertEqual(report["failed_operations"][0]["status"], "failed")
        self.assertEqual(report["unaccounted_seconds"], 4.0)
        self.assertIn("Failed commands", metrics.markdown(report))

    def test_compare_excludes_incomplete_and_unmatched_scope(self):
        for key, scope, outcome in (("first", "same", "finish"), ("second", "same", "finish"),
                                     ("partial", "same", "partial"), ("other", "different", "finish")):
            metrics.ensure_run(self.project, key, factory_revision="r1", mode="fast", kind="change")
            metrics.set_scope(self.project, key, [scope])
            metrics.finalize(self.project, key, outcome=outcome)
        result = metrics.compare(self.project, ["first", "second", "partial", "other"])
        self.assertEqual(result["requested"], 4)
        self.assertEqual(result["eligible_completed"], 3)
        self.assertEqual(result["sample_size"], 2)
        self.assertEqual(result["groups"][0]["pair_count"], 1)
        self.assertIsNotNone(result["groups"][0]["deltas"][0]["elapsed_seconds_delta"])
        self.assertEqual({row["reason"] for row in result["excluded"]}, {"not_completed", "no_matching_run"})

    def test_interrupted_resume_keeps_unknown_prior_segment(self):
        events = [
            {"event_id": "start", "type": "task.start", "task_id": "T1",
             "t": "2026-01-01T00:00:00+00:00", "pid": 1, "mono_ns": 10},
            {"event_id": "resume", "type": "task.resume", "task_id": "T1",
             "t": "2026-01-01T00:00:05+00:00", "pid": 2, "mono_ns": 10},
            {"event_id": "finish", "type": "task.finish", "task_id": "T1",
             "t": "2026-01-01T00:00:07+00:00", "pid": 2, "mono_ns": 2_000_000_010},
        ]
        report = metrics.aggregate(events)
        self.assertIsNone(report["tasks"]["T1"]["duration_seconds"])
        self.assertEqual(report["tasks"]["T1"]["segments"][0]["duration_seconds"], 2.0)
        self.assertTrue(any(gap["gap"] == "task_interrupted_segment_unknown" for gap in report["coverage_gaps"]))

    def test_export_and_delete(self):
        metrics.ensure_run(self.project, self.key)
        metrics.finalize(self.project, self.key)
        dest = self.project / "export-out"
        self.assertTrue(metrics.export(self.project, self.key, dest))
        self.assertTrue((dest / "report.json").is_file())
        self.assertTrue(metrics.delete(self.project, self.key))
        self.assertFalse(metrics.run_dir(self.project, self.key).exists())

    def test_delete_rejects_root_aliases_and_preserves_sibling(self):
        metrics.ensure_run(self.project, "one")
        metrics.ensure_run(self.project, "two")
        for key in (".", "..", "C:", "C:/x", "/tmp/x", "a/b", "a\\b", "x ", "x.", "CON", "nul.txt"):
            with self.subTest(key=key):
                self.assertFalse(metrics.delete(self.project, key))
                self.assertTrue(metrics.run_dir(self.project, "one").is_dir())
                self.assertTrue(metrics.run_dir(self.project, "two").is_dir())
        self.assertTrue(metrics.delete(self.project, "one"))
        self.assertTrue(metrics.run_dir(self.project, "two").is_dir())

    def test_open_report_and_late_usage_do_not_change_delivery_wall(self):
        from safe_engine.host_usage import summarize
        metrics.ensure_run(self.project, self.key, factory_revision="r", mode="fast", kind="change")
        partial = metrics.finalize(self.project, self.key)
        self.assertEqual(partial["outcome"], "partial")
        self.assertFalse(any(row["type"] == "run.finish" for row in metrics.read_events(self.project, self.key)))
        finished = metrics.finalize(self.project, self.key, outcome="finish")
        usage = summarize({"sessionId": "later", "modelUsage": {"same": {"inputTokens": 12}}})
        self.assertTrue(metrics.attach_usage(self.project, self.key, usage))
        metrics.emit(self.project, self.key, "coverage_gap", gap="analytics_corrupt", detail="later")
        later = metrics.finalize(self.project, self.key)
        self.assertEqual(later["outcome"], "finish")
        self.assertEqual(later["elapsed_seconds"], finished["elapsed_seconds"])
        self.assertGreater(later["event_count"], finished["event_count"])

    def test_fast_instances_and_explicit_task_context(self):
        scripts = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
        sys.path.insert(0, str(scripts))
        import fast_metrics
        keys = []
        for instance in ("1" * 32, "2" * 32):
            run = {"key": "reused", "pr_instance": instance, "mode": "fast", "kind": "change",
                   "bundle": {"revision": "r"}}
            fast_metrics.on_start(self.project, run)
            fast_metrics.on_close(self.project, run, False)
            keys.append(fast_metrics.identity(run))
        self.assertNotEqual(*keys)
        self.assertTrue(all(metrics.run_dir(self.project, key).is_dir() for key in keys))
        with metrics.bound(self.project, "scoped", task_id="T1"):
            metrics.emit_current("operation.start", name="command", event_id="op")
            metrics.emit_current("operation.finish", name="command", parent_id="op")
        report = metrics.finalize(self.project, "scoped", outcome="finish")
        self.assertEqual(report["longest_operations"][0]["task_id"], "T1")

    def test_parallel_safe_checks_keep_bound_task_context(self):
        from safe_engine.checks import CheckMixin

        class Probe(CheckMixin):
            def prepare_outputs(self, check):
                return []

            def run_check(self, state, check, outputs, stop=None, slot=None):
                metrics.emit_current("operation.start", name=check["id"], event_id=check["id"])
                metrics.emit_current("operation.finish", name=check["id"], parent_id=check["id"])
                return {"passed": True}

        with metrics.bound(self.project, "parallel", task_id="ticket"):
            self.assertEqual(len(Probe().execute_checks({"profile": {"parallel_checks": True}},
                                                       [{"id": "a"}, {"id": "b"}])), 2)
        finished = [row for row in metrics.read_events(self.project, "parallel")
                    if row["type"] == "operation.finish"]
        self.assertEqual(len(finished), 2)
        self.assertEqual({row["task_id"] for row in finished}, {"ticket"})

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
        self.assertTrue(metrics.within_budget(5.0, 4.0, 1.0, 2.0))
        self.assertFalse(metrics.within_budget(31.0, 4.0, 1.0, 2.0))
        overhead = metrics.measure_overhead(self.project, "overhead-a8", event_count=40)
        self.assertTrue(overhead["workload"].get("single_shot"))
        self.assertEqual(
            overhead["within_budget"],
            metrics.within_budget(
                overhead["event_append_pair_p99_ms"],
                overhead["report_generate_ms"],
                overhead["collection_seconds"],
                overhead["whole_run_cap_seconds"],
            ),
        )


if __name__ == "__main__":
    unittest.main()
