"""Rubric for the bug-fix sample: one check per reported bug, plus the original tests (a KEEP item).

Candidate code runs in a harness process; results come back as plain data and compare type-strictly.
"""
import ast

from evals.rubric_tools import call, expect, op, tests

LINE = {"qty": 1, "price": 1000}


def discount(work):
    """R1: the discount is applied once."""
    off, taxed = call(work, "invoice", [op("total", [{"qty": 2, "price": 500}], discount_percent=10),
                                        op("total", [LINE], tax_percent=20)])
    expect(off, 900, "10% off 1000")
    expect(taxed, 1200, "20% tax on 1000, no discount")


def empty(work):
    """R2: an empty invoice totals 0."""
    for result, what in zip(call(work, "invoice", [op("subtotal", []), op("total", [])]), ("subtotal", "total")):
        expect(result, 0, f"{what} of an empty invoice")


def rounding(work):
    """R3: half a cent rounds up."""
    half, under = call(work, "invoice", [op("total", [{"qty": 1, "price": 3}], tax_percent=50),
                                         op("total", [{"qty": 1, "price": 1}], tax_percent=40)])
    expect(half, 5, "4.5 cents")
    expect(under, 1, "1.4 cents")


def existing_tests(work):
    """R4: the fixture's original tests (from the snapshot, never the workspace) pass inside the harness, and
    their cases hold type-strictly."""
    source = FIXTURE["test_invoice.py"]  # noqa: F821 - provided by the check program
    count = sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test")
                for node in ast.walk(ast.parse(source)))
    ran, lines, taxed = call(work, "invoice", [tests(source),
                                               op("subtotal", [{"qty": 2, "price": 150}, {"qty": 1, "price": 99}]),
                                               op("total", [LINE], tax_percent=20)])
    expect(ran, {"run": count, "failures": 0, "errors": 0}, "the original tests")
    expect(lines, 399, "the original subtotal case")  # an always-equal object passes no test here
    expect(taxed, 1200, "the original tax case")


CHECKS = {"R1": discount, "R2": empty, "R3": rounding, "R4": existing_tests}
KEEP = {"R4"}  # preserved behavior: passes on the untouched fixture too
