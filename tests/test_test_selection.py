"""Named dependency selection does not select unrelated siblings or miss unknown graphs."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import run as selector


class SelectionTests(unittest.TestCase):
    def test_real_dependency_graph_and_unknown_fallback(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            for name, text in {"leaf": "value=1", "consumer": "from . import leaf", "sibling": "pass"}.items():
                (root / "src" / (name + ".py")).write_text(text)
                (root / "tests" / ("test_" + name + ".py")).write_text("import " + name)
            def select(path):
                returns = [SimpleNamespace(stdout=path+"\0"), SimpleNamespace(stdout=""), SimpleNamespace(stdout="")]
                with patch.object(selector, "ROOT", root), patch.object(selector, "TESTS", root / "tests"), \
                     patch.object(selector.subprocess, "run", side_effect=returns):
                    return selector.selected("fixture-base")
            self.assertEqual(select("src/leaf.py"), {"test_leaf", "test_consumer"})
            (root / "tests/helper.py").write_text("import leaf")
            (root / "tests/test_via_helper.py").write_text("import helper")
            self.assertEqual(select("src/leaf.py"), {"test_leaf", "test_consumer", "test_via_helper"})
            self.assertIsNone(select("unknown.file"))
            (root / "src/consumer.py").write_text("def broken(")
            self.assertIsNone(select("src/leaf.py"))
