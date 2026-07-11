# Round 4

## Final Model

`final.py`

Round 4 extended the options and underlying framework with stronger volatility
regime detection, strike-specific logic, and informed-flow signals.

## Strategy

The final stack combined:

- OU mean-reversion models for `VELVETFRUIT_EXTRACT` and `HYDROGEL_PACK`.
- Black-Scholes-style option fair values.
- Conditional implied-volatility regime detection from `VEV_5300`.
- Specialized deep-ITM handling for `VEV_4000` and `VEV_4500`.
- HGP opening-regime classification.
- Mark-specific informed-flow signals for HGP and selected options.
- Online OU kappa estimation for VFE and HGP.

## Results

Documented final backtest results from `final.py`:

| Segment | Result |
|---|---:|
| R3 D0 hold-out | `272,934` |
| R4 D1 | `358,296` |
| R4 D2 | `212,936` |
| R4 D3 | `399,082` |
| R4 total | `970,314` |
| All documented days | `1,243,248` |

Major documented improvements:

| Layer | Increment |
|---|---:|
| V1 baseline | `746K` R4 |
| Conditional IV regime detection | `+120K` R4 |
| Deep ITM module | `+37K` R4 |
| HGP micro-buy edge | `+28K` R4 |
| Mark 22 vulnerable strikes alpha | `+18K` R4 |
| Online OU kappa estimation | `+13K` over V63 |

## Files To Inspect

- `final.py`: final Round 4 model.
- `v314159.py`, `merged.py`, `big_swing.py`, `alternative.py`: major tested
  variants.
- `analysis/round4/`: mark analysis, informed-trader analysis, validation
  outputs, and candidate ranking.
