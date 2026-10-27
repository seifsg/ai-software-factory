"""Keep subprocess suite tests off the real machine queue."""
from unittest.mock import patch
from pathlib import Path
import tempfile


def isolate_suite_queue(test):
    """Bind a test's queue to its disposable project for nested full-suite runs."""
    temp = tempfile.TemporaryDirectory(prefix='factory-suite-test-')
    test.addCleanup(temp.cleanup)
    directory = Path(temp.name)
    binding = patch('safe_engine.suite_queue.machine_directory', return_value=directory)
    binding.start()
    test.addCleanup(binding.stop)
    return directory
