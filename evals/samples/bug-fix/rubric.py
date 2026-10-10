"""Rubric for the bug-fix sample: one check per reported bug, plus the existing tests (a KEEP item)."""
from evals.rubric_tools import run_python


def discount(work):
    """R1: the discount is applied once."""
    from invoice import total
    assert total([{"qty": 2, "price": 500}], discount_percent=10) == 900, "10% off 1000 must be 900"
    assert total([{"qty": 1, "price": 1000}], tax_percent=20) == 1200, "tax without discount changed"


def empty(work):
    """R2: an empty invoice totals 0."""
    from invoice import subtotal, total
    assert subtotal([]) == 0 and total([]) == 0, "empty invoice must total 0"


def rounding(work):
    """R3: half a cent rounds up."""
    from invoice import total
    assert total([{"qty": 1, "price": 3}], tax_percent=50) == 5, "4.5 cents must round to 5"
    assert total([{"qty": 1, "price": 1}], tax_percent=40) == 1, "1.4 cents must round to 1"


def existing_tests(work):
    """R4: the existing tests still pass."""
    code, _, err = run_python(work, "-m", "unittest", "-q")
    assert code == 0, f"existing tests fail: {err.strip().splitlines()[-1:]}"


CHECKS = {"R1": discount, "R2": empty, "R3": rounding, "R4": existing_tests}
KEEP = {"R4"}  # preserved behavior: passes on the untouched fixture too
