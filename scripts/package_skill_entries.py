"""Publish/check standalone resolver copies from their one canonical source."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = (root / "safe_engine/distribution.py").read_bytes()
    for name in ("safe-engine", "improve-factory"):
        target = root / "skills" / name / "scripts/resolve_bundle.py"
        if args.check:
            if not target.is_file() or target.read_bytes() != source:
                parser.exit(1, f"Stale packaged resolver: {target}\n")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source)
    print("Both standalone skill resolvers match safe_engine/distribution.py")


if __name__ == "__main__":
    main()
