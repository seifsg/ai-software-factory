"""Existing tests for invoice.py: `python -m unittest`."""
import unittest

from invoice import subtotal, total


class InvoiceTests(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([{"qty": 2, "price": 150}, {"qty": 1, "price": 99}]), 399)

    def test_total_with_tax(self):
        self.assertEqual(total([{"qty": 1, "price": 1000}], tax_percent=20), 1200)


if __name__ == "__main__":
    unittest.main()
