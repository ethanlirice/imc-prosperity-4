# Round 5 MM/MR Framework

Purpose: test the "simple stable-line" hypothesis directly. The framework
separates passive spread capture from fair-value skew and active mean reversion.

Current results under the primary command,
`prosperity4btx <strategy> 5 --merge-pnl`:

| variant | D2 | D3 | D4 | total | decision |
|---|---:|---:|---:|---:|---|
| base-strategy.py | 147320 | 185325 | 202112 | 534757 | old baseline |
| simple_mm_mr_all50_v1.py | -425605 | -514520 | -299077 | -1239202 | rejected |
| simple_mm_all50_inside_v2.py | 118766 | 105130 | 177518 | 401415 | diagnostic |
| simple_mm_all50_touch_v3.py | 141311 | 134250 | 201238 | 476800 | diagnostic |
| base-strategy-touch-mm-v1.py | 161420 | 203525 | 216994 | 581939 | improved |
| base-strategy-touch-mm-target-select-v2.py | 206398 | 181641 | 235507 | 623546 | improved |
| base-strategy-touch-mm-target-select-v3.py | 196332 | 181566 | 249860 | 627758 | best current |

Interpretation:
- Broad fair-value skew / active MR is toxic across all 50 products.
- The stable-line edge is mostly passive touch market making, not prediction.
- Touch quoting beats one-tick-inside quoting by about 75k on the all-product
  passive control.
- Letting passive MM own `PANEL_2X2`, `PEBBLES_S`, `ROBOT_IRONING`, and
  `SNACKPACK_STRAWBERRY` beats their active residual sleeves.
- Removing `TRANSLATOR_SPACE_GRAY` adds a small net improvement.

To rerun the framework:

```bash
python3 analysis/round5/mm-mr-framework/19_mm_mr_framework.py
```

Outputs:
- `variant_summary.csv`
- `variant_product_day_pnl.csv`
- `product_variant_totals.csv`
