"""Rubric for the bug-fix sample: one check per reported bug, plus the original tests (a KEEP item).

Each check runs fixed regression cases and fresh random cases. Random cases are answered by the reference
solution (REFERENCE, in this process) and must match type-strictly; candidate code runs in a harness process.
Random cases for one bug avoid the other bugs (no discount, no half cents, no empty invoice) so items stay apart.
"""
import ast
from fractions import Fraction

from evals.rubric_tools import RANDOM, agree, call, expect, op, tests

LINE = {"qty": 1, "price": 1000}
TRAPS = 300  # half-cent cases per scoring: a float half-up fix passes all with odds near 5 in 10 million


def lines(count, cents=1):
    """`count` random invoice lines; prices are multiples of `cents`."""
    return [{"qty": RANDOM.randint(1, 9), "price": RANDOM.randint(1, 500) * cents} for _ in range(count)]


def reference():
    return REFERENCE["invoice.py"]  # noqa: F821 - provided by the check program


def discount(work):
    """R1: the discount is applied once."""
    off, taxed, both = call(work, "invoice", [op("total", [{"qty": 2, "price": 500}], discount_percent=10),
                                              op("total", [LINE], tax_percent=20),
                                              op("total", [{"qty": 1, "price": 10000}], discount_percent=10,
                                                 tax_percent=20)])
    expect(off, 900, "10% off 1000")
    expect(taxed, 1200, "20% tax on 1000, no discount")
    expect(both, 10800, "10% off 10000, then 20% tax on the discounted 9000")
    cases = [op("total", lines(RANDOM.randint(1, 4), cents=100), discount_percent=RANDOM.randint(1, 90))
             for _ in range(4)]  # whole-cent results: rounding never matters here
    cases += [op("total", lines(RANDOM.randint(1, 3), cents=10000), discount_percent=RANDOM.randint(1, 90),
                 tax_percent=RANDOM.randint(1, 60)) for _ in range(4)]  # discount and tax together, whole cents
    agree(work, "invoice", reference(), cases, "random discount")


def empty(work):
    """R2: an empty invoice totals 0."""
    for result, what in zip(call(work, "invoice", [op("subtotal", []), op("total", [])]), ("subtotal", "total")):
        expect(result, 0, f"{what} of an empty invoice")
    cases = [op("total", [], discount_percent=RANDOM.randint(0, 90), tax_percent=RANDOM.randint(0, 30))
             for _ in range(3)]
    agree(work, "invoice", reference(), [op("subtotal", []), *cases], "random empty invoice")


def rounding(work):
    """R3: half a cent rounds up."""
    half, under = call(work, "invoice", [op("total", [{"qty": 1, "price": 3}], tax_percent=50),
                                         op("total", [{"qty": 1, "price": 1}], tax_percent=40)])
    expect(half, 5, "4.5 cents")
    expect(under, 1, "1.4 cents")
    traps = [half_even_trap() for _ in range(TRAPS)]  # one harness call; float rounding misses about 1 in 21
    agree(work, "invoice", reference(), traps, "random half cent")


def half_even_trap():
    """A random line and tax whose exact total is an even number of cents plus one half: half-up and half-even
    (Python's round) disagree on every such case."""
    while True:
        qty, price, tax = RANDOM.randint(1, 9), RANDOM.randint(1, 5000), RANDOM.randint(1, 60)
        exact = Fraction(qty * price * (100 + tax), 100)
        if exact.denominator == 2 and exact.numerator // 2 % 2 == 0:
            return op("total", [{"qty": qty, "price": price}], tax_percent=tax)


def existing_tests(work):
    """R4: the fixture's original tests (from the snapshot, never the workspace) pass inside the harness, their
    cases hold type-strictly, and random subtotals and taxed totals still match."""
    source = FIXTURE["test_invoice.py"]  # noqa: F821 - provided by the check program
    count = sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test")
                for node in ast.walk(ast.parse(source)))
    ran, subtotal, taxed = call(work, "invoice", [tests(source),
                                                  op("subtotal", [{"qty": 2, "price": 150}, {"qty": 1, "price": 99}]),
                                                  op("total", [LINE], tax_percent=20)])
    expect(ran, {"run": count, "failures": 0, "errors": 0}, "the original tests")
    expect(subtotal, 399, "the original subtotal case")
    expect(taxed, 1200, "the original tax case")
    cases = [op("subtotal", lines(RANDOM.randint(1, 5))) for _ in range(2)]
    cases += [op("total", lines(RANDOM.randint(1, 3), cents=100), tax_percent=RANDOM.randint(1, 30))]
    agree(work, "invoice", reference(), cases, "random existing behavior")


CHECKS = {"R1": discount, "R2": empty, "R3": rounding, "R4": existing_tests}
KEEP = {"R4"}  # preserved behavior: passes on the untouched fixture too
