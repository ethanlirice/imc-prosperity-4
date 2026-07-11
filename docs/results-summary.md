# Results Summary

This file tracks the public-facing round results. Placement stats are official
competition rankings; PnL/backtest numbers are included only where they are
documented in this workspace.

| Round | Main File | Strategy Focus | Placement / Documented Result |
|---|---|---|---|
| 1 | `strategies/round1/trader_v14_final.py` | OSMIUM wall-mid execution, one-sided book handling, PEPPER carryover logic | Global `#2009`; US `#590` |
| 2 | `strategies/round2/trader_v11_final.py` | OSMIUM anchored wall-mid model, shallow-book inventory recycling, PEPPER accumulator | Global `#1699`; US `#422`; v8 baseline `252,967` none / `301,531` worse |
| 3 | `strategies/round3/traderfinal.py` | Online anchors, VFE/HGP trading, option pricing and strike-specific execution | Global `#617`; US `#183`; key variant total `194,999` |
| 4 | `strategies/round4/final.py` | OU + options stack, IV regime detection, informed-flow signals, online kappa | Global `#270`; US `#82`; R4 total `970,314`; all documented days `1,243,248` |
| 5 | `trader.py` | Group relationships, re-anchored hidden paths, MR/MM stack, NN candidate generation, DISHES shock sleeve | Global `#320`; US `#101`; default `+1,479,360`; none `+958,900`; worse `+965,011` |

## Notes

The rest of the repo preserves the code and analysis needed to inspect how each
result was developed. For a concise narrative, read `docs/strategy-summary.md`.
