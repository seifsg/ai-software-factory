"""Publish/check standalone resolver copies from their one canonical source."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    copies = [("safe_engine/distribution.py", f"skills/{name}/scripts/resolve_bundle.py")
              for name in ("safe-engine", "improve-factory")]
    copies.append(("safe_engine/worth.py", "skills/safe-engine/scripts/fast_worth.py"))
    for source_name, target_name in copies:
        source, target = (root / source_name).read_bytes(), root / target_name
        if args.check:
            if not target.is_file() or target.read_bytes() != source:
                parser.exit(1, f"Stale packaged helper: {target}\n")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source)
    print("Both standalone skill resolvers and the worth helper match their canonical sources")


if __name__ == "__main__":
    main()
