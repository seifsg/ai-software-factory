Users report three bugs in `invoice.py`. Fix them without changing the function names or signatures, and keep the existing tests passing.

1. The discount is subtracted twice: `total([{"qty": 2, "price": 500}], discount_percent=10)` returns 800 instead of 900.
2. An empty invoice crashes: `total([])` and `subtotal([])` raise instead of returning 0.
3. Half a cent must round up: `total([{"qty": 1, "price": 3}], tax_percent=50)` is 4.5 cents and must return 5, not 4.
