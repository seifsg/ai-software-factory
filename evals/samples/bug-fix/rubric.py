"""Rubric for the bug-fix sample: one check per reported bug, plus the original tests (a KEEP item).

Each check runs fixed regression cases and fresh random cases. Random cases are answered by the reference
solution (REFERENCE, in this process) and must match type-strictly; candidate code runs in a harness process.
Random cases for one bug avoid the other bugs (no discount, no half cents, no empty invoice) so items stay apart.
"""
import ast

from evals.rubric_tools import RANDOM, agree, call, expect, op, tests

LINE = {"qty": 1, "price": 1000}


def lines(count, cents=1):
    """`count` random invoice lines; prices are multiples of `cents`."""
    return [{"qty": RANDOM.randint(1, 9), "price": RANDOM.randint(1, 500) * cents} for _ in range(count)]


def reference():
    return REFERENCE["invoice.py"]  # noqa: F821 - provided by the check program


def discount(work):
    """R1: the discount is applied once."""
    off, taxed = call(work, "invoice", [op("total", [{"qty": 2, "price": 500}], discount_percent=10),
                                        op("total", [LINE], tax_percent=20)])
    expect(off, 900, "10% off 1000")
    expect(taxed, 1200, "20% tax on 1000, no discount")
    cases = [op("total", lines(RANDOM.randint(1, 4), cents=100), discount_percent=RANDOM.randint(1, 90))
             for _ in range(4)]  # whole-cent results: rounding never matters here
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
    halves = [op("total", [{"qty": 1, "price": RANDOM.randrange(1, 9999, 2)}], tax_percent=50) for _ in range(3)]
    others = [op("total", lines(RANDOM.randint(1, 3)), tax_percent=RANDOM.randint(1, 30)) for _ in range(3)]
    agree(work, "invoice", reference(), halves + others, "random rounding")


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
