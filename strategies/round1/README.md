# Round 1

## Final Model

`trader_v14_final.py`

Round 1 traded `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`. The final model
kept the earlier PEPPER logic and focused the last improvement on OSMIUM
execution.

## Strategy

The key OSMIUM diagnostic was that an earlier version skipped roughly 8% of
ticks when only one side of the order book was visible. The final model stores
the last observed wall mid, bid wall, and ask wall in `traderData`, then uses
those values to keep quoting and taking on one-sided books.

That made the strategy capture opportunities that were previously skipped while
leaving normal two-sided-book behavior unchanged.

## Results

Exact final Round 1 total is still to confirm from competition/backtest records.
The code comment documents the improvement source: extra PnL came only from
previously skipped one-sided ticks.

## Files To Inspect

- `trader_v14_final.py`: final submitted model.
