# Round 3

## Final Model

`traderfinal.py`

Round 3 centered on `VELVETFRUIT_EXTRACT`, `HYDROGEL_PACK`, and VEV option
contracts.

## Strategy

The final strategy combined:

- online fair-value anchors from wall-mid behavior,
- Black-Scholes-style option pricing,
- implied-volatility and strike-specific option logic,
- underlying/HGP market making and mean reversion,
- inventory-aware execution.

One important design decision was to avoid relying entirely on fixed fair values.
The final model uses rolling wall-mid medians for VFE/HGP anchors and reuses the
online VFE anchor for deep-ITM option fair values.

## Results

Official placement after finalist reset: global `#617`, United States `#183`.

Documented variant evidence:

| Test | Result |
|---|---:|
| Static 5250 VFE anchor + cap 15 | `+98,963` |
| Rolling median W=2000 + cap 15 | `+89,846` |
| Key no-hardcoded-FV variant total | `194,999` |

The rolling-anchor choice sacrificed some in-sample PnL for portability. Exact
final Round 3 PnL total is not documented in this cleaned workspace.

## Files To Inspect

- `traderfinal.py`: final model.
- `trader_v32.py`, `trader_v33.py`: late-stage online-anchor variants.
- `variations/`: smaller experiments showing how the Round 3 model evolved.
- `analysis/round3/`: notebooks for data foundation, reverse engineering,
  option surface behavior, and hidden-pattern mapping.
