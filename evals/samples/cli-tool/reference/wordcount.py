"""Count lines, words and characters of a text file; optionally list the most frequent words."""
import argparse
from collections import Counter
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=0, help="Also print the N most frequent words")
    parser.add_argument("file")
    args = parser.parse_args()
    try:
        with open(args.file, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        print(f"wordcount: cannot read {args.file}: {error.strerror}", file=sys.stderr)
        return 2
    words = text.split()
    print(len(text.splitlines()), len(words), len(text))
    ranked = sorted(Counter(word.lower() for word in words).items(), key=lambda pair: (-pair[1], pair[0]))
    for word, count in ranked[:max(args.top, 0)]:
        print(word, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
