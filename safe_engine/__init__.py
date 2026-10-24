"""Safe Engine: a local, agent-operated delivery pilot."""
from pathlib import Path

# The factory's one canonical version (docs/releasing.md); every bundle carries this file.
__version__ = (Path(__file__).resolve().parents[1] / "skills/safe-engine/VERSION").read_text(encoding="utf-8").strip()
