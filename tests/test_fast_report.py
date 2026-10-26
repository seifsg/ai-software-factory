"""Report boundaries and picture evidence across owner-facing consumers."""
from pathlib import Path
import sys
import tempfile
import unittest

from png_fixtures import png

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
sys.path.insert(0, str(SCRIPTS))
import fast_image
import fast_report

TICKETS = ("https://example.test/issues/11", "https://example.test/issues/12")


def unavailable(reason="No attributed measurement yet"):
    return {"status": "unavailable", "value": None, "source": "Work record", "reason": reason}


def item(ticket=TICKETS[0], visual=False):
    return {"ticket": ticket, "feature": "Visible progress", "changed": "The page shows the latest result.",
            "next": "Inspect the result", "waiting": "Nobody", "time_left": "About one hour",
            "worth": {"unavailable": "Benefits have not been estimated"},
            "spend": {key: unavailable() for key in fast_report.METRICS}, "visual": visual}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / ".factory").mkdir()
        self.picture = self.project / ".factory/current.png"
        png(self.picture)

    def prepare(self, *items, **extra):
        return fast_report.prepare({"version": 1, "items": list(items), **extra}, self.project, set(TICKETS))

    def test_body_codes_are_rejected_at_token_boundaries_with_narrow_literal_exception(self):
        for body in ("Fixed T7.", "See A12", "Issue #156", "Branch codex/progress", "lane A2", "deadbee", "fix/report"):
            with self.subTest(body=body), self.assertRaisesRegex(ValueError, "code, lane, branch or hash"):
                fast_report.lint(body)
        fast_report.lint("The T7 connector now loads.\nCheck the latest picture.", ("T7",))
        with self.assertRaisesRegex(ValueError, "code, lane, branch or hash"):
            fast_report.lint("The T7 connector now loads; T8 still fails.", ("T7",))
        report = item()
        report["changed"] = "The T7 connector now loads."
        accepted = self.prepare(report, literal_exceptions=[{"text": "T7", "reason": "Exact product label"}])
        self.assertIn("T7 connector", fast_report.markdown(accepted))
        for exception in ({"text": "T7", "reason": ""}, {"text": "progress", "reason": "label"}):
            with self.subTest(exception=exception), self.assertRaises(ValueError):
                self.prepare(report, literal_exceptions=[exception])

    def test_metric_attribution_and_unknowns_cannot_be_misreported(self):
        first, second = item(), item(TICKETS[1])
        first["spend"]["tokens"] = {"status": "measured", "value": 120, "source": "Per ticket counter",
                                    "scope": TICKETS[0], "measurement": "count-one"}
        report = self.prepare(first, second)
        self.assertEqual(report["items"][0]["spend"]["tokens"]["text"], "120 tokens (measured)")
        self.assertIn("Unavailable: No attributed measurement yet", fast_report.markdown(report))
        second["spend"]["tokens"] = {**first["spend"]["tokens"], "scope": TICKETS[1]}
        with self.assertRaisesRegex(ValueError, "same measurement"):
            self.prepare(first, second)
        second["spend"]["tokens"]["measurement"] = "count-two"
        second["spend"]["tokens"]["scope"] = "all tickets"
        with self.assertRaisesRegex(ValueError, "never a shared total"):
            self.prepare(first, second)
        first["spend"]["planned_minutes"] = {"status": "measured", "value": 20, "source": "Plan",
                                             "scope": TICKETS[0], "measurement": "plan-one"}
        with self.assertRaisesRegex(ValueError, "estimated"):
            self.prepare(first)

    def test_valid_picture_is_bound_to_current_bytes_and_markdown_falls_back(self):
        row = item(visual=True)
        row["picture"] = {"path": ".factory/current.png", "caption": "Current progress"}
        report = self.prepare(row)
        self.assertIn("![Current progress]", fast_report.markdown(report, self.project))
        original = self.picture.read_bytes()
        png(self.picture, color=21)
        with self.assertRaisesRegex(ValueError, "Picture changed"):
            fast_report.checked_picture(report["items"][0]["picture"], self.project)
        self.assertIn("Picture changed or unavailable", fast_report.markdown(report, self.project))
        self.picture.write_bytes(original)
        self.assertIn("![Current progress]", fast_report.markdown(report, self.project))

    def test_flat_transparent_corrupt_and_oversized_pngs_fail_while_sparse_content_passes(self):
        self.assertEqual(fast_image.check(self.picture), (64, 32))
        png(self.picture, blank=True)
        with self.assertRaisesRegex(ValueError, "blank or near-blank"):
            fast_image.check(self.picture)
        png(self.picture, transparent=True)
        with self.assertRaisesRegex(ValueError, "blank or near-blank"):
            fast_image.check(self.picture)
        png(self.picture)
        broken = bytearray(self.picture.read_bytes())
        broken[-16] ^= 1
        self.picture.write_bytes(broken)
        with self.assertRaisesRegex(ValueError, "checksum"):
            fast_image.check(self.picture)
        self.picture.write_bytes(b"x" * (fast_image.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "16 MiB"):
            fast_image.check(self.picture)

    def test_card_puts_lifecycle_status_ahead_of_last_accepted_report(self):
        import fast_card
        report = self.prepare(item())
        base = {"owner_report": report, "project": str(self.project)}
        waiting = fast_card.card({**base, "paused": {"reason": "Owner feedback"}}, [], {}, "")
        self.assertLess(waiting.index("WAITING ON YOU"), waiting.index("Last published report"))
        self.assertNotIn("Waiting on: Nobody", waiting)
        closed = fast_card.card({**base, "closed": True}, [], {}, "")
        self.assertLess(closed.index("closed"), closed.index("Last published report"))
        self.assertIn("References\n- [Ticket 1]", closed)


if __name__ == "__main__":
    unittest.main()
