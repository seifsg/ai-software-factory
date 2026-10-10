"""PR proof at the Fast handoff: the PR body's Before & after per outcome (fast_proof.py, fast_record.pr_proof)."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
sys.path.insert(0, str(SCRIPTS))
import fast_proof  # noqa: E402

IMG = "https://github.com/acme/site/blob/0a1b2c3/{}.png?raw=true"
F = "```"
HEAD = "## 🎬 Before & after\n\n"
PAIR = f"### 🧾 Invoice totals include tax\n**Before:** tax missing\n![b]({IMG.format('b')})\n**After:** tax\n![a]({IMG.format('a')})\n"
DIFF = f"### 🔌 GET /api/orders/42: shows the refund\n**Before → After:** same request\n{F}diff\n- paid\n+ refunded\n{F}\n"
HANDOFF = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n**PR:** {}\n"


def record():
    spec = importlib.util.spec_from_file_location("fast_record", SCRIPTS / "fast_record.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class ProofTests(unittest.TestCase):
    def test_each_outcome_shows_openable_before_and_after_proof(self):
        passing = {
            "screenshot pair": HEAD + PAIR,
            "diff": HEAD + DIFF,
            "added lines": HEAD + DIFF.replace("- paid\n+ refunded", "  4. claim vs diff\n+    proof rule"),
            "image table": HEAD + f"### Theme survives reload\n**Before → After:**\n| Before | After |\n|---|---|\n"
                                  f"| ![b]({IMG.format('b')}) | ![a]({IMG.format('a')}) |\n",
            "new": HEAD + f"### Export button\n**Before:** did not exist\n**After:** exports\n![a]({IMG.format('a')})\n",
            "fenced output": HEAD + f"### Rule text\n**Before:** x\r\n{F}\r\nold\r\n{F}\r\n**After:** y\r\n{F}\r\nnew\r\n{F}\r\n",
            "nested level": "### 🎬 Before & after\n\n" + PAIR.replace("### ", "#### ") + "### 🔧 What & why\nreason\n",
        }
        for name, body in passing.items():
            self.assertEqual(fast_proof.problems(body), [], name)
        refused = {
            "no section": ("## 🔧 What & why\n| Before | After |\n|---|---|\n| x | y |\n", "needs a '## 🎬 Before & after'"),
            "no outcome": (HEAD + "**Before:** x\n**After:** y\n", "one heading per outcome"),
            "prose only": (HEAD + "### Login fix\n**Before:** broke\n**After:** works\n", "Before needs proof"),
            "after missing": (HEAD + f"### Login fix\n**Before:** broke\n![b]({IMG.format('b')})\n", "'**Before:**' then"),
            "file name": (HEAD + PAIR.replace("🧾 Invoice totals include tax", "`src/invoice.ts`"), "names a file"),
            "localhost": (HEAD + PAIR.replace(IMG.format('a'), "http://localhost:3000/a.png"), "cannot be opened"),
            "local path": (HEAD + PAIR.replace(IMG.format('a'), ".factory/fast/shots/a.png"), "cannot be opened"),
            "not a diff": (HEAD + DIFF.replace("- paid\n+ refunded", "refunded"), "diff block (- or + lines"),
            "label in code": (HEAD + f"### Docs\n**Before:** x\n{F}md\n## no heading\n**After:** fake\n{F}\n", "then '**After:**'"),
        }
        for name, (body, expected) in refused.items():
            self.assertIn(expected, " ".join(fast_proof.problems(body)), name)

    def test_ui_runs_need_a_screenshot(self):
        self.assertIn("needs >=1 screenshot", fast_proof.problems(HEAD + DIFF, ui=True)[0])
        video = DIFF + f"[journey](https://github.com/acme/site/blob/0a1b2c3/booking.mp4?raw=true)\n"
        self.assertIn("needs >=1 screenshot", fast_proof.problems(HEAD + video, ui=True)[0])
        self.assertEqual(fast_proof.problems(HEAD + PAIR + DIFF, ui=True), [])

    def test_handoff_reads_the_pr_named_on_its_line(self):
        rec, run = record(), {"kind": "change", "pr_proof": True}
        url = "https://github.com/acme/site/pull/7"
        check = lambda text, **kw: rec.check_handoff(run, text, all_sections={}, **{"offline": None, **kw})
        self.assertIn("needs a '**PR:**' line", check(HANDOFF.replace("**PR:** {}\n", ""))[0])
        self.assertEqual(rec.check_handoff({"kind": "change"}, HANDOFF.replace("**PR:** {}\n", ""), offline=None,
                                           all_sections={}), [])  # runs on older methods keep the old check
        with patch.object(rec, "gh", return_value=HEAD + PAIR) as gh:
            self.assertEqual(check(HANDOFF.format(url)), [])
        self.assertEqual(gh.call_args.args[:3], ("pr", "view", url))
        with patch.object(rec, "gh", return_value="## 🔧 What & why\n"):
            self.assertIn("PR body: needs a '## 🎬 Before & after'", check(HANDOFF.format(url))[0])
        with patch.object(rec, "gh", side_effect=RuntimeError("no network")):
            self.assertIn("pass --offline", check(HANDOFF.format(url))[0])
        self.assertIn("GitHub PR URL", check(HANDOFF.format("https://gitlab.com/a/b/-/merge_requests/1"))[0])
        with tempfile.TemporaryDirectory(prefix="proof ") as project:
            Path(project, "pr body.md").write_text(HEAD + PAIR, encoding="utf-8")
            offline = dict(offline="no network", project=project)
            self.assertEqual(check(HANDOFF.format(f"{url} (body: pr body.md)"), **offline), [])
            self.assertIn("name the PR body file", check(HANDOFF.format(url), **offline)[0])
            self.assertIn("name the PR body file", check(HANDOFF.format(f"{url} (body: gone.md)"), **offline)[0])
            Path(project, "pr body.md").write_text(HEAD + DIFF, encoding="utf-8")
            self.assertEqual(check(HANDOFF.format(f"{url} (body: pr body.md)"), **offline), [])  # not a UI run
            run["ui"] = True
            self.assertIn("needs >=1 screenshot", check(HANDOFF.format(f"{url} (body: pr body.md)"), **offline)[0])


if __name__ == "__main__":
    unittest.main()
