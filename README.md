# IMC Prosperity 4

This repository is my cleaned workspace for IMC Prosperity 4. It keeps the code,
data, analysis, strategy variants, and final models that show how I approached
each round of the trading competition.

## Repository Map

| Path | Purpose |
|---|---|
| `trader.py` | Final Round 5 strategy currently at the repository root. |
| `archive/round1` | Round 1 final strategy and summary. |
| `archive/round2` | Round 2 final strategy plus major prior versions. |
| `archive/round3` | Round 3 options/underlying strategy variants and final model. |
| `archive/round4` | Round 4 final model, major variants, and strategy experiments. |
| `strategies` | Round 5 strategy iteration history and promoted candidates. |
| `analysis` | Research notebooks/scripts used to diagnose signals and validate ideas. |
| `raw-data` | Competition price/trade data used for local analysis and backtests. |
| `manual-challenge` | Round 5 manual challenge optimizer and recommendation. |
| `DATA.md` / `TRADING.md` | Condensed empirical findings and validated Round 5 strategy decisions. |

## Round Results Snapshot

| Round | Final / Main Model | Current documented result |
|---|---|---|
| 1 | `archive/round1/trader_v14_final.py` | Exact final result to confirm. |
| 2 | `archive/round2/trader_v11_final.py` | v8 baseline documented: `252,967` none / `301,531` worse. Final v11 result to confirm. |
| 3 | `archive/round3/traderfinal.py` | Variant evidence documented: `194,999` for a key no-hardcoded-FV variant; final total to confirm. |
| 4 | `archive/round4/final.py` | R4 total `970,314`; all documented days total `1,243,248`. |
| 5 | `trader.py` | Round 5 default `+1,479,360`; diagnostics `+958,900` none / `+965,011` worse. |

## Strategy Themes

- Structural fair values from book behavior, wall mids, online anchors, and
  product relationships.
- Position-aware execution and inventory recycling, especially when limits block
  future edge.
- Options modeling with Black-Scholes-style fair values, volatility regimes, and
  strike-specific execution.
- Round 5 group-level research, hidden-path re-anchoring, mean-reversion,
  passive market making, and NN-assisted candidate generation.
