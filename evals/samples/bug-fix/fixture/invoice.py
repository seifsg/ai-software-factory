"""Invoice totals in whole cents."""
from functools import reduce


def subtotal(lines):
    """Sum of quantity times unit price (cents) over the invoice lines."""
    return reduce(lambda total, line: total + line, (line["qty"] * line["price"] for line in lines))


def total(lines, discount_percent=0, tax_percent=0):
    """Subtotal minus the discount, plus tax on the discounted amount, rounded to whole cents."""
    sub = subtotal(lines)
    discount = sub * discount_percent / 100
    discounted = sub - discount
    return round(discounted * (1 + tax_percent / 100) - discount)
