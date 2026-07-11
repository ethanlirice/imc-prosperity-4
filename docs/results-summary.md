# Results Summary

This file tracks the public-facing round results. Numbers marked "confirm" need
to be filled from official or saved backtest records before publishing final
claims.

| Round | Main File | Strategy Focus | Documented Result |
|---|---|---|---|
| 1 | `strategies/round1/trader_v14_final.py` | OSMIUM wall-mid execution, one-sided book handling, PEPPER carryover logic | Final total: confirm |
| 2 | `strategies/round2/trader_v11_final.py` | OSMIUM anchored wall-mid model, shallow-book inventory recycling, PEPPER accumulator | v8 baseline: `252,967` none / `301,531` worse; v11 final: confirm |
| 3 | `strategies/round3/traderfinal.py` | Online anchors, VFE/HGP trading, option pricing and strike-specific execution | Key variant total: `194,999`; final total: confirm |
| 4 | `strategies/round4/final.py` | OU + options stack, IV regime detection, informed-flow signals, online kappa | R4 total `970,314`; all documented days `1,243,248` |
| 5 | `trader.py` | Group relationships, re-anchored hidden paths, MR/MM stack, NN candidate generation, DISHES shock sleeve | Default `+1,479,360`; none `+958,900`; worse `+965,011` |

## Missing Confirmation Items

- Round 1 final backtest/competition result.
- Round 2 final v11 backtest/competition result.
- Round 3 final `traderfinal.py` backtest/competition result.

The rest of the repo preserves the code and analysis needed to inspect how each
number was developed.
