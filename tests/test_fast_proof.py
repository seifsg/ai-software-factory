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
    def test_demo_requires_scoped_screenshots_and_every_journey_video(self):
        flags = "**Visual:** yes\n**Journey:** yes\n"
        video = "**Video:** [Pay](https://example.com/pay.webm) 00:03-00:12\n"
        body = HEAD + PAIR.replace("**Before:**", flags + "**Before:**") + video
        self.assertEqual(fast_proof.problems(body, ui=True, demo=True), [])
        for name, changed in {
            "missing before": body.replace(f"![b]({IMG.format('b')})", "did not exist"),
            "same image": body.replace(IMG.format('a'), IMG.format('b')),
            "same image fragment": body.replace(IMG.format('a'), IMG.format('b') + "#after"),
            "missing video": body.replace(video, ""),
            "image as video": body.replace("pay.webm", "pay.png"),
            "video as image": body.replace("b.png", "b.mp4"),
            "commented video": body.replace(video, "<!--" + video + "-->"),
            "inline video": body.replace(video, "`" + video.rstrip() + "`\n"),
            "fenced declarations": body.replace(flags, F + "md\n" + flags + F + "\n"),
            "duplicate declaration": body + "**Visual:** no (backend)\n",
            "reasonless no": body.replace("**Journey:** yes", "**Journey:** no"),
            "invalid host": body.replace(IMG.format('a'), "https:///after.png"),
            "local host": body.replace(IMG.format('a'), "https://127.0.0.1/a.png"),
            "invalid port": body.replace(IMG.format('a'), "https://example.com:bad/a.png"),
            "credentials": body.replace(IMG.format('a'), "https://user:pass@example.com/a.png"),
            "second journey": body + PAIR.replace("**Before:**", flags + "**Before:**"),
        }.items():
            with self.subTest(name=name):
                self.assertTrue(fast_proof.problems(changed, ui=True, demo=True))

    def test_demo_accepts_explicit_embeds_tables_and_nonvisual_command_proof(self):
        flags = "**Visual:** yes\n**Journey:** yes\n"
        table = ("### Checkout completes\n" + flags + "| Before | After |\n|---|---|\n"
                 f"| ![b]({IMG.format('b')}) | ![a]({IMG.format('a')}) |\n")
        for video in ('<video src="https://github.com/user-attachments/assets/abc-123"></video>',
                      '<video controls><source src="https://example.com/movie"></video>',
                      '[pay](https://example.com/clip.mp4#t=3,12)'):
            self.assertEqual(fast_proof.problems(HEAD + table + "**Video:** " + video, ui=True, demo=True), [])
        cli = HEAD + DIFF.replace("**Before", "**Visual:** no (CLI only)\n**Journey:** no (internal parser)\n**Before")
        self.assertEqual(fast_proof.problems(cli, demo=True), [])
        self.assertIn("declare >=1 Visual", " ".join(fast_proof.problems(cli, ui=True, demo=True)))
        self.assertTrue(fast_proof.problems(HEAD + "<!--" + table + "-->", demo=True))

    def test_demo_waivers_are_local_explicit_and_media_specific(self):
        base = HEAD + "### Checkout completes\n**Visual:** yes\n**Journey:** yes\n**Before:** old\n**After:** new\n"
        waiver = "**Media waiver:** all | Skip checkout media | owner message in this chat\n"
        self.assertEqual(fast_proof.problems(base + waiver, ui=True, demo=True), [])
        self.assertTrue(fast_proof.problems(base.replace("**After:** new", "**After:**") + waiver, demo=True))
        for changed in (waiver.replace("all |", "screenshots |"), waiver.replace("all |", "video |"),
                        waiver.replace("all |", "none |"), waiver.replace("Skip checkout media", ""),
                        waiver.replace("owner message in this chat", ""), waiver.replace("Skip checkout media", "<owner exact request>"),
                        "<!--" + waiver + "-->", waiver + waiver):
            self.assertTrue(fast_proof.problems(base + changed, demo=True), changed)
        self.assertTrue(fast_proof.problems(base + waiver + base.replace(HEAD, ""), demo=True))

    def test_shared_demo_video_needs_each_outcomes_segment(self):
        flags = "**Visual:** yes\n**Journey:** yes\n"
        proof = PAIR.replace("**Before:**", flags + "**Before:**")
        video = "**Video:** [Pay](https://example.com/pay.webm)\n"
        body = HEAD + proof + video + proof.replace("Invoice totals include tax", "Refund includes tax") + video
        self.assertIn("start/end timestamps", " ".join(fast_proof.problems(body, demo=True)))
        self.assertEqual(fast_proof.problems(body.replace("[Pay]", "[Pay 00:01-00:05]"), demo=True), [])

    def test_demo_is_versioned_and_handoff_checks_online_and_offline_bodies(self):
        rec, run = record(), {"kind": "change", "pr_proof": True}
        handoff = HANDOFF.format("https://github.com/acme/site/pull/7 (body: proof.md)")
        with patch.object(rec, "gh", return_value=HEAD + PAIR):
            self.assertEqual(rec.pr_proof(run, handoff), [])
            self.assertTrue(rec.pr_proof({**run, "pr_demo": True}, handoff))
            self.assertEqual(rec.pr_proof({"pr_demo": True}, handoff), [])
        body = HEAD + DIFF.replace("**Before", "**Visual:** no (CLI)\n**Journey:** no (internal)\n**Before")
        with tempfile.TemporaryDirectory() as project:
            Path(project, "proof.md").write_text(body, encoding="utf-8")
            self.assertEqual(rec.pr_proof({**run, "pr_demo": True}, handoff, project=project, offline="fixture"), [])

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

    def test_credit_line_closes_the_body(self):
        self.assertEqual(fast_proof.credit(HEAD + PAIR + "\n---\n" + fast_proof.CREDIT + "\n\n"), [])
        for name, body in (("missing", HEAD + PAIR), ("not last", HEAD + PAIR + fast_proof.CREDIT + "\nthanks\n"),
                           ("agent trailer", HEAD + PAIR + "\n---\nGenerated with an agent\n"), ("empty", "")):
            self.assertIn("factory credit line", " ".join(fast_proof.credit(body)), name)
        credit_md = SCRIPTS.parents[2] / ".agents/skills/how-to-make-a-pr/references/credit.md"
        self.assertIn(f"\n{fast_proof.CREDIT}\n", credit_md.read_text(encoding="utf-8"))  # one line, two homes, held equal

    def test_handoff_reads_the_pr_named_on_its_line(self):
        rec, run = record(), {"kind": "change", "pr_proof": True}
        url = "https://github.com/acme/site/pull/7"
        check = lambda text, **kw: rec.check_handoff(run, text, all_sections={}, **{"offline": None, **kw})
        self.assertIn("needs a '**PR:** <value or evidence>' line", check(HANDOFF.replace("**PR:** {}\n", ""))[0])
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
        run = {"kind": "change", "pr_proof": True, "credit": True}  # runs on current methods also need the credit line
        with patch.object(rec, "gh", return_value=HEAD + PAIR):
            self.assertIn("factory credit line", check(HANDOFF.format(url))[0])
        with patch.object(rec, "gh", return_value=HEAD + PAIR + "\n---\n" + fast_proof.CREDIT):
            self.assertEqual(check(HANDOFF.format(url)), [])


if __name__ == "__main__":
    unittest.main()
