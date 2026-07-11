# Round 2

## Final Model

`trader_v11_final.py`

Round 2 continued OSMIUM/PEPPER trading and added the manual-auction product
logic around `MAF_BID`.

## Strategy

The final model built on the v8-v10 core:

- OSMIUM fair value used a wall-mid anchor pulled toward `10000`.
- OSMIUM persisted wall values across shallow or one-sided book states.
- PEPPER used a rush-to-limit accumulator with a capped active take and passive
  fallback.
- The later v11 refinement added shallow-book inventory recycling: when large
  OSMIUM inventory was trapped in a thin book, the strategy could trade at fair
  against visible liquidity to free capacity.

## Results

Documented v8 baseline:

| Mode | Result |
|---|---:|
| `--match-trades none` | `252,967` |
| `--match-trades worse` | `301,531` |

Exact final v11 total is still to confirm from competition/backtest records.

## Files To Inspect

- `trader_v11_final.py`: final model.
- `trader_v8_final.py`: documented baseline with backtest commands.
- `trader_v9_final.py` and `trader_v10_final.py`: intermediate refinements.
