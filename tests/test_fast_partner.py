"""Technical partner: owner profile, partner config, brief mail link and the handoff decision (partner.md)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
sys.path.insert(0, str(SCRIPTS))
import fast_partner as partner  # noqa: E402
import fast_record  # noqa: E402
from safe_engine.workflow import PARTNER  # noqa: E402

CONFIG = {"name": "Acme Partners", "email": "help@acme.example", "site": "https://acme.example", "book": "",
          "packages": ["Launch review"]}


class PartnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home, self.bundled = Path(self.tmp.name) / "home", Path(self.tmp.name) / "bundle-partner.json"
        self.bundled.write_text(json.dumps(CONFIG), encoding="utf-8")

    def gate(self, *args):
        env = {**os.environ, "SAFE_ENGINE_HOME": str(self.home)}
        return subprocess.run([sys.executable, str(SCRIPTS / "fast_gate.py"), *args], capture_output=True, text=True,
                              encoding="utf-8", env=env, cwd=self.tmp.name)

    def test_owner_values_are_checked_where_they_enter(self):
        self.assertEqual(partner.owner(self.home), {})
        self.assertEqual(partner.set_owner(self.home, ["tech=non-technical", "role=founder"]),
                         {"tech": "non-technical", "role": "founder"})
        for bad in ("tech=wizard", "mood=happy", "tech", "offers=maybe"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "Allowed"):
                partner.set_owner(self.home, [bad])
        (self.home / "owner.json").write_text('{"tech": "developer", "role": "x", "evil": 1}', encoding="utf-8")
        self.assertEqual(partner.owner(self.home), {"tech": "developer"})  # unknown keys and values never load
        partner.forget_owner(self.home)
        partner.forget_owner(self.home)  # forgetting twice is fine
        self.assertEqual(partner.owner(self.home), {})

    def test_broken_files_are_errors_not_empty_defaults(self):
        self.home.mkdir()
        (self.home / "owner.json").write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            partner.owner(self.home)
        (self.home / "owner.json").write_text("[1]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON object"):
            partner.owner(self.home)

    def test_partner_comes_from_the_bundle_or_the_home_override_only(self):
        self.assertEqual(partner.partner(self.home, self.bundled)["email"], "help@acme.example")
        self.assertIsNone(partner.partner(self.home, Path(self.tmp.name) / "missing.json"))
        self.bundled.write_text('{"email": "  "}', encoding="utf-8")
        self.assertIsNone(partner.partner(self.home, self.bundled))  # an empty email turns offers off
        self.home.mkdir()
        (self.home / "partner.json").write_text('{"name": "Other", "email": "a@b.example"}', encoding="utf-8")
        self.assertEqual(partner.partner(self.home, self.bundled),
                         {"name": "Other", "email": "a@b.example", "site": "", "book": "", "packages": []})
        (self.home / "partner.json").write_text('{"email": "nope"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not an address"):
            partner.partner(self.home, self.bundled)

    def test_a_project_never_names_the_recipient(self):
        (Path(self.tmp.name) / "partner.json").write_text('{"email": "thief@evil.example"}', encoding="utf-8")
        self.home.mkdir()
        (self.home / "partner.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        result = self.gate("partner")  # run from the folder holding the planted file
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("help@acme.example", result.stdout)
        self.assertNotIn("evil", result.stdout)

    def test_offers_follow_profile_and_config(self):
        for profile, config, expected in (({}, CONFIG, True), ({"tech": "some"}, CONFIG, True),
                                          ({"tech": "non-technical"}, CONFIG, True),
                                          ({"tech": "developer"}, CONFIG, False), ({"tech": "team"}, CONFIG, False),
                                          ({"offers": "off"}, CONFIG, False), ({}, None, False)):
            with self.subTest(profile=profile, config=bool(config)):
                self.assertEqual(partner.offers_on(profile, config), expected)

    def test_mail_link_uses_crlf_and_refuses_overlong_text(self):
        link = partner.mailto(CONFIG, "[Factory] go-live · MVP", "line one\nline two & more")
        self.assertTrue(link.startswith("mailto:help@acme.example?subject="))
        self.assertIn("line one\r\nline two & more", unquote(link))
        self.assertNotIn("&more", link)  # body text cannot add mail-link fields
        self.assertIsNone(partner.mailto(CONFIG, "s", "x" * partner.MAILTO_MAX))

    def test_brief_needs_a_subject_line_and_a_body(self):
        path = Path(self.tmp.name) / "brief.md"
        for text in ("no subject\nbody", "Subject: \nbody", "Subject: only"):
            path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "Subject"):
                partner.brief(path)
        path.write_text("Subject: [Factory] go-live\n\nHello\n", encoding="utf-8")
        self.assertEqual(partner.brief(path), ("[Factory] go-live", "Hello"))

    def test_commands_show_save_and_refuse(self):
        self.assertIn("👤 owner: unknown", self.gate("owner").stdout)
        refused = self.gate("owner", "--set", "tech=wizard")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("Allowed", refused.stderr)
        self.assertIn("non-technical founder", self.gate("owner", "--set", "tech=non-technical", "role=founder").stdout)
        self.assertIn("owner.set", (self.home / "logs/gate.log").read_text(encoding="utf-8"))
        self.assertNotIn("non-technical", (self.home / "logs/gate.log").read_text(encoding="utf-8"))  # keys only
        (self.home / "partner.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        brief = Path(self.tmp.name) / "brief.md"
        brief.write_text("no subject", encoding="utf-8")
        bad = self.gate("partner", "--draft", str(brief))
        self.assertEqual((bad.returncode, bad.stdout), (1, ""))  # a bad brief fails before printing anything
        brief.write_text("Subject: Launch review\n\nPlease help.", encoding="utf-8")
        self.assertIn("mailto:help@acme.example?subject=Launch%20review", self.gate("partner", "--draft", str(brief)).stdout)

    def test_decision_pattern_matches_its_controller_twin(self):
        self.assertEqual(partner.DECISION.pattern, PARTNER.pattern)
        for good in ("offered (go-live, upkeep)", "sent (salon-mvp-go-live)", "declined (not now)",
                     "none (owner is a developer)", "NONE (no evidence)"):
            self.assertTrue(partner.DECISION.fullmatch(good), good)
        for bad in ("maybe later", "none", "none ()", "none (  )", "offered (a (b))", "sent (x) and more"):
            self.assertFalse(partner.DECISION.fullmatch(bad), bad)

    def test_controller_cli_passes_the_decision(self):
        result = subprocess.run([sys.executable, "-m", "safe_engine", "handoff", "--help"], capture_output=True, text=True,
                                encoding="utf-8", cwd=Path(__file__).resolve().parents[1])
        self.assertIn("--partner", result.stdout, result.stderr)

    def test_handoff_needs_the_partner_line_only_on_current_methods(self):
        body = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n"
        self.assertEqual(fast_record.check_handoff({"partner": False}, body), [])
        self.assertIn("needs a '**Partner:**' line", fast_record.check_handoff({"partner": True}, body))
        self.assertIn("Partner line must", fast_record.check_handoff({"partner": True}, body + "**Partner:** later\n")[0])
        self.assertEqual(fast_record.check_handoff({"partner": True}, body + "**Partner:** none (no evidence)\n"), [])


if __name__ == "__main__":
    unittest.main()
