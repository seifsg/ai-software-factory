"""Plausible wrong fixes, one per case gap: each must fail its item in every scoring (several scorings each).

Most are the reference solution with one line changed, so the named item is the only thing they get wrong.
"""
import codecs
import locale
import unittest

from eval_fixtures import EvalCase
from evals import catalog

SCORINGS = 3
UTF8_LOCALE = codecs.lookup(locale.getpreferredencoding(False)).name == "utf-8"
TAX_FULL_SUBTOTAL = (  # taxes the full subtotal, then takes the discount off: right only without one of them
    "from decimal import Decimal, ROUND_HALF_UP\n\n\n"
    "def subtotal(lines):\n"
    "    return sum(line['qty'] * line['price'] for line in lines)\n\n\n"
    "def total(lines, discount_percent=0, tax_percent=0):\n"
    "    sub = Decimal(subtotal(lines))\n"
    "    value = sub * (100 + Decimal(tax_percent)) / 100 - sub * Decimal(discount_percent) / 100\n"
    "    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))\n")
FLOAT_HALF_UP = (  # rounds half up on a float, which sometimes lands just under the half cent
    "def subtotal(lines):\n"
    "    return sum(line['qty'] * line['price'] for line in lines)\n\n\n"
    "def total(lines, discount_percent=0, tax_percent=0):\n"
    "    return int(subtotal(lines) * (1 - discount_percent / 100) * (1 + tax_percent / 100) + 0.5)\n")


def changed(sample, name, old, new):
    """The reference file `name` of `sample` with `old` replaced by `new` (which must occur once)."""
    source = catalog.load([sample])[0].solution[name].decode("utf-8")
    assert source.count(old) == 1, old
    return source.replace(old, new)


class EvalWrongFixTests(EvalCase):
    def assert_fails(self, sample, files, item):
        for scoring in range(SCORINGS):
            with self.subTest(scoring=scoring):
                self.assertIn(item, self.scores(sample, files))

    def test_tax_on_the_full_subtotal_fails_r1(self):
        self.assert_fails("bug-fix", {"invoice.py": TAX_FULL_SUBTOTAL}, "R1")

    def test_float_half_up_fails_r3(self):
        self.assert_fails("bug-fix", {"invoice.py": FLOAT_HALF_UP}, "R3")

    def test_a_query_matched_against_lowercased_notes_only_fails_r3(self):
        app = changed("web-feature", "app.py", '.get("q", [""])[0].lower()', '.get("q", [""])[0]')
        self.assert_fails("web-feature", {"app.py": app}, "R3")

    def test_json_that_is_not_an_object_fails_r2(self):
        app = changed("web-feature", "app.py", 'body.get("text") if isinstance(body, dict) else None',
                      'body.get("text") if body else None')
        self.assert_fails("web-feature", {"app.py": app}, "R2")

    def test_counting_newlines_as_lines_fails_r1(self):
        program = changed("cli-tool", "wordcount.py", "len(text.splitlines())", 'text.count("\\n")')
        self.assert_fails("cli-tool", {"wordcount.py": program}, "R1")

    def test_counting_bytes_as_characters_fails_r1(self):
        program = changed("cli-tool", "wordcount.py", "len(words), len(text))",
                          'len(words), len(text.encode("utf-8")))')
        self.assert_fails("cli-tool", {"wordcount.py": program}, "R1")

    @unittest.skipIf(UTF8_LOCALE, "this host reads files as UTF-8 by default, so a missing encoding cannot show")
    def test_reading_without_an_encoding_fails_r1_on_this_host(self):
        program = changed("cli-tool", "wordcount.py", 'open(args.file, encoding="utf-8")', "open(args.file)")
        self.assert_fails("cli-tool", {"wordcount.py": program}, "R1")
