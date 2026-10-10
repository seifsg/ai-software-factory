"""Eval guards with fake agents: a planted site hook or a passing canary stops the eval; scoring leaves no files."""
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
from unittest.mock import patch

from eval_fixtures import FAKE, EvalCase, fake
from evals import agent, catalog, interpreter, isolation, runner

ROOT = Path(__file__).resolve().parents[1]
ALWAYS_PASS = "def run(payload):\n    print(payload['token'])\n    return 0\n"


class EvalGuardTests(EvalCase):
    def test_a_planted_site_hook_stops_the_eval(self):
        venv = self.tmp / "py"  # a throwaway interpreter: the real one is never touched
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True, timeout=120)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        template = (f"{agent.quote(python)} {agent.quote(FAKE)} {{arm}} {{sample}} {{workdir}} {{factory}} "
                    "none plant")
        out = self.tmp / "out"
        done = subprocess.run([str(python), "-m", "evals", "run", "--agent", template, "--sample", "bug-fix",
                               "--out", str(out)], cwd=ROOT, capture_output=True, text=True, timeout=300,
                              env={**os.environ, "TEMP": str(self.scratch), "TMP": str(self.scratch),
                                   "TMPDIR": str(self.scratch)})
        self.assertEqual(done.returncode, 3, done.stdout[-1500:] + done.stderr[-1500:])
        saved = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertIn("interpreter changed", saved["tainted"])
        self.assertEqual([(r["arm"], r["delivered"]) for r in saved["runs"]], [("factory", 0)])  # plain never ran
        self.assertIn("interpreter changed", saved["runs"][0]["void"])
        planted = list(venv.rglob("evals-plant.pth"))
        self.assertEqual(len(planted), 1)
        self.assertFalse(Path(sysconfig.get_paths()["purelib"], "evals-plant.pth").exists())

    def test_a_canary_passing_before_any_agent_refuses_the_eval(self):
        sources = {**catalog.kit(), "check": ALWAYS_PASS}  # a check environment that answers everything
        with patch.object(catalog, "kit", return_value=sources), self.assertRaisesRegex(RuntimeError, "canary"):
            runner.run_all(fake("none"), self.tmp / "out", names=["bug-fix"], jobs=1)
        self.assertFalse((self.tmp / "out/logs").exists())  # no agent started

    def test_a_canary_passing_after_an_agent_stops_the_eval(self):
        recorded = catalog.loaded_modules(catalog.load(["bug-fix"]), catalog.kit())  # a clean start
        sources = {**catalog.kit(), "check": ALWAYS_PASS}  # then a check environment that answers everything
        with patch.object(catalog, "kit", return_value=sources), \
                patch.object(catalog, "loaded_modules", return_value=recorded):
            result = runner.run_all(fake("none"), self.tmp / "out", names=["bug-fix"], jobs=1)
        self.assertIn("canary", result["tainted"])
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["runs"][0]["delivered"], 0)
        self.assertIn("canary", result["runs"][0]["void"])

    def test_the_guard_covers_what_real_checks_load(self):
        files, folders = catalog.loaded_modules(catalog.load(["bug-fix"]), catalog.kit())
        names = {Path(name).name for name in files}
        self.assertIn("decimal.py", names)  # loaded by the reference solution inside the check, not a fixed list
        self.assertFalse(any("eval-check-" in name for name in files))  # throwaway folders left out
        stand_in = self.tmp / "module.py"
        stand_in.write_text("x = 1\n", encoding="utf-8")
        before = interpreter.state({str(stand_in)}, folders)
        stand_in.write_text("x = 2\n", encoding="utf-8")
        self.assertNotEqual(interpreter.state({str(stand_in)}, folders), before)

    def test_scoring_writes_nothing_into_the_run_folder(self):
        result = runner.run_all(fake("factory"), self.tmp / "out", names=["bug-fix"], jobs=1, keep=True)
        for run in result["runs"]:
            folder = Path(run["workdir"]).parent
            self.assertFalse((folder / "checks").exists())
            self.assertEqual(sorted(p.suffix for p in folder.rglob("*.out")), [])
        self.assertEqual(result["runs"][0]["delivered"], 4)

    def test_bundle_is_read_once_and_the_run_env_names_no_runner_folder(self):
        with patch.object(isolation, "read_bundle", wraps=isolation.read_bundle) as reads:
            runner.run_all(fake("factory"), self.tmp / "out", jobs=6)
        self.assertEqual(reads.call_count, 1)
        folder = self.tmp / "env"
        folder.mkdir()
        with patch.dict(os.environ, {"PWD": "/runner", "OLDPWD": "/before"}):
            env = isolation.run_env(folder)
        self.assertNotIn("PWD", env)
        self.assertNotIn("OLDPWD", env)
