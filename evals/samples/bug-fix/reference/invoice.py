"""Invoice totals in whole cents."""
from decimal import Decimal, ROUND_HALF_UP


def subtotal(lines):
    """Sum of quantity times unit price (cents) over the invoice lines."""
    return sum(line["qty"] * line["price"] for line in lines)


def total(lines, discount_percent=0, tax_percent=0):
    """Subtotal minus the discount, plus tax on the discounted amount, rounded half up to whole cents."""
    discounted = Decimal(subtotal(lines)) * (100 - Decimal(str(discount_percent))) / 100
    taxed = discounted * (100 + Decimal(str(tax_percent))) / 100
    return int(taxed.quantize(Decimal(1), rounding=ROUND_HALF_UP))
