"""Queue admission serializes callers and cancels only the waiting owner."""
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from safe_engine.project import EngineError
from safe_engine.suite_queue import admission


class SuiteQueueTests(unittest.TestCase):
    def test_owned_lease_cleanup_preserves_foreign_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            foreign = root / 'foreign.txt'
            foreign.write_text('keep')
            with patch('safe_engine.suite_queue.machine_directory', return_value=root):
                with admission(timeout=5) as slot:
                    lease = slot.lease()
                    self.assertTrue(lease.is_dir())
                    self.assertEqual(len(list(root.glob('*.request.json'))), 1)
            self.assertFalse(lease.exists())
            self.assertFalse(list(root.glob('*.request.json')))
            self.assertEqual(foreign.read_text(), 'keep')

    def test_fifo_and_cancelled_waiter_never_enter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first_entered, release, cancel = (threading.Event() for _ in range(3))
            entered, errors = [], []
            def worker(name, stop=None):
                try:
                    with admission(stop=stop, timeout=5) as slot:
                        entered.append(name)
                        self.assertTrue(slot.generation)
                        if name == 'first':
                            first_entered.set()
                            if not release.wait(5):
                                errors.append((name, 'release timeout'))
                except EngineError as error:
                    errors.append((name, str(error)))
            with patch('safe_engine.suite_queue.machine_directory', return_value=root):
                first = threading.Thread(target=worker, args=('first',))
                waiting = threading.Thread(target=worker, args=('cancelled', cancel))
                last = threading.Thread(target=worker, args=('last',))
                first.start()
                self.assertTrue(first_entered.wait(5))
                waiting.start()
                deadline = time.monotonic() + 5
                while len(list(root.glob('*.request.json'))) < 2 and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertEqual(len(list(root.glob('*.request.json'))), 2)
                last.start()
                while len(list(root.glob('*.request.json'))) < 3 and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertEqual(len(list(root.glob('*.request.json'))), 3)
                cancel.set()
                waiting.join(5)
                self.assertFalse(waiting.is_alive())
                self.assertEqual(entered, ['first'])
                release.set()
                first.join(5)
                last.join(5)
                self.assertFalse(first.is_alive() or last.is_alive())
            self.assertEqual(entered, ['first', 'last'])
            self.assertEqual(errors, [('cancelled', 'Queued suite cancelled before execution')])
            self.assertFalse(list(root.glob('*.request.json')))
