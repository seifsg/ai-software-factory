"""Rubric for the bug-fix sample: one check per reported bug, plus the original tests (a KEEP item).

Candidate code runs in a harness process; results come back as plain data and compare type-strictly.
"""
from evals.rubric_tools import call, expect, op, run_python, scratch

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
    """R4: the fixture's original tests (from the snapshot, not the workspace) pass against the candidate."""
    tmp = scratch()
    (tmp / "test_invoice.py").write_text(FIXTURE["test_invoice.py"], encoding="utf-8")  # noqa: F821
    code, _, err = run_python(tmp, "-m", "unittest", "-q", env={"PYTHONPATH": str(work)})
    ran = code == 0 and err.rstrip().endswith("OK") and "Ran " in err  # an early exit 0 prints no summary
    assert ran, f"original tests fail (exit {code}): {err.strip().splitlines()[-1:]}"
    lines, taxed = call(work, "invoice", [op("subtotal", [{"qty": 2, "price": 150}, {"qty": 1, "price": 99}]),
                                          op("total", [LINE], tax_percent=20)])
    expect(lines, 399, "the original subtotal case")  # type-strict: an always-equal object passes no test here
    expect(taxed, 1200, "the original tax case")


CHECKS = {"R1": discount, "R2": empty, "R3": rounding, "R4": existing_tests}
KEEP = {"R4"}  # preserved behavior: passes on the untouched fixture too
