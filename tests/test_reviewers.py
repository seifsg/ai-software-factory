"""Safe review on any installed agent: preset choice, read-only argv, report capture and a controller run."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import speed_fixtures as speed
from safe_engine import reviewers
from safe_engine.project import EngineError


def agents(*names):
    """shutil.which that sees only these reviewer agents; other lookups stay real."""
    binaries = {binary: name for name, found in reviewers.BINARIES.items() for binary in found}
    return patch("shutil.which", side_effect=lambda binary, *a, **k: sys.executable if binaries.get(binary) in names
                 else None if binary in binaries else speed.REAL_WHICH(binary, *a, **k))


class PresetTests(unittest.TestCase):
    def test_auto_prefers_an_agent_that_did_not_build(self):
        with agents("codex", "claude"):
            self.assertEqual(reviewers.choose("auto", "codex")[0], "claude")
            self.assertEqual(reviewers.choose("auto", "claude")[0], "codex")
        with agents("claude"):
            self.assertEqual(reviewers.choose("auto", "claude")[0], "claude")  # alone: still reviews
            with self.assertRaisesRegex(EngineError, "not found"):
                reviewers.choose("cursor")
        with agents(), self.assertRaisesRegex(EngineError, "review-packet"):
            reviewers.choose("auto")
        with agents("codex", "claude"), patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(EngineError, "--builder"):
                reviewers.choose("auto")  # never guess when the builder is unknown
        self.assertEqual(reviewers.builder_from_env({"CLAUDECODE": "1"}), "claude")
        self.assertEqual(reviewers.builder_from_env({"CODEX_THREAD_ID": "t"}), "codex")
        self.assertEqual(reviewers.builder_from_env({"CURSOR_AGENT": "1"}), "cursor")

    def test_commands_are_read_only(self):
        schema = Path(reviewers.__file__).with_name("review-schema-v2.json")
        claude = reviewers.argv("claude", "claude", "/p", "/bundle", schema, "/out.json")
        self.assertEqual(claude[claude.index("--tools") + 1], "Read,Grep,Glob")
        self.assertIn("--json-schema", claude)
        self.assertIn("--strict-mcp-config", claude)  # no MCP tools inside a read-only review
        codex = reviewers.argv("codex", "codex", "/p", "/bundle", schema, "/out.json")
        self.assertEqual(codex[1:4], ["exec", "--sandbox", "read-only"])
        cursor = reviewers.argv("cursor", "agent", "/p", "/b", schema, "/o")
        self.assertEqual(cursor[1:4], ["-p", "--mode", "ask"])
        self.assertIn("--trust", cursor)
        self.assertNotIn("--force", cursor)

    def test_reports_are_lifted_out_of_host_envelopes(self):
        with tempfile.TemporaryDirectory() as temp:
            log, output = Path(temp) / "review.log", Path(temp) / "report.json"
            log.write_text("stderr note\n" + json.dumps({"result": 'Done:\n```json\n{"verdict": "PASS"}\n```'}), encoding="utf-8")
            reviewers.capture("claude", log, output)
            self.assertEqual(json.loads(output.read_text())["verdict"], "PASS")
            output.unlink()
            log.write_text(json.dumps({"structured_output": {"verdict": "FAIL"}}), encoding="utf-8")
            reviewers.capture("cursor", log, output)
            self.assertEqual(json.loads(output.read_text())["verdict"], "FAIL")
        prose = 'Checked {a} and {b}. {"verdict": "PASS", "x": {"y": 1}}'
        self.assertEqual(reviewers.first_report(prose)["x"], {"y": 1})  # braces before the report are skipped


class ControllerReviewTests(speed.Base):
    def test_claude_reviewer_runs_and_its_report_is_recorded(self):
        f = self.to_review()
        seen = {}

        def double(argv, cwd, timeout, log, stdin):
            seen["argv"] = argv
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("warning\n" + json.dumps({"type": "result", "structured_output": speed.report()}), encoding="utf-8")
            return {"passed": True}

        with agents("codex", "claude"), patch("safe_engine.workflow.run_command", side_effect=double):
            status = f.flow.review(10, None, None, "auto", "codex")
        self.assertEqual(status["phase"], "ready")
        self.assertIn("--json-schema", seen["argv"])
        self.assertEqual(f.flow.load()["review"]["execution"]["agent"], "claude")


if __name__ == "__main__":
    unittest.main()
