# IMC Prosperity 4

This repository is my cleaned workspace for IMC Prosperity 4. It keeps the code,
analysis, strategy variants, and final models that show how I approached each
round of the trading competition.

## Competition Results

| Round | Global Rank | United States Rank | Main Strategy |
|---|---:|---:|---|
| 1 | `#2009` | `#590` | OSMIUM wall-mid execution and one-sided book handling. |
| 2 | `#1699` | `#422` | OSMIUM anchored wall-mid model with inventory recycling. |
| 3 (finalist reset) | `#617` | `#183` | Online anchors and option-surface execution. |
| 4 | `#270` | `#82` | Options/underlying stack with IV regimes and informed-flow signals. |
| 5 | `#320` | `#101` | Group relationships, hidden-path re-anchoring, MR/MM, and NN-assisted candidate generation. |

## Repository Map

| Path | Purpose |
|---|---|
| `trader.py` | Final Round 5 strategy currently at the repository root. |
| `strategies/round1` | Round 1 final strategy and summary. |
| `strategies/round2` | Round 2 final strategy plus major prior versions. |
| `strategies/round3` | Round 3 options/underlying strategy variants and final model. |
| `strategies/round4` | Round 4 final model, major variants, and strategy experiments. |
| `strategies` | Strategy history organized by round, including final models and selected variants. |
| `analysis` | Research notebooks/scripts used to diagnose signals and validate ideas. |
| `manual-challenge` | Manual challenge analysis and recommendations, organized by round. |
| `docs/strategy-summary.md` | Short round-by-round strategy writeup. |
| `DATA.md` / `TRADING.md` | Condensed empirical findings and validated Round 5 strategy decisions. |

## Round Results Snapshot

| Round | Final / Main Model | Current documented result |
|---|---|---|
| 1 | `strategies/round1/trader_v14_final.py` | Global `#2009`; US `#590`. |
| 2 | `strategies/round2/trader_v11_final.py` | Global `#1699`; US `#422`; v8 baseline `252,967` none / `301,531` worse. |
| 3 | `strategies/round3/traderfinal.py` | Global `#617`; US `#183`; key variant evidence `194,999`. |
| 4 | `strategies/round4/final.py` | Global `#270`; US `#82`; R4 backtest total `970,314`. |
| 5 | `trader.py` | Global `#320`; US `#101`; default `+1,479,360`. |

For a concise explanation of each round's strategy, see `docs/strategy-summary.md`.

## Strategy Themes

- Structural fair values from book behavior, wall mids, online anchors, and
  product relationships.
- Position-aware execution and inventory recycling, especially when limits block
  future edge.
- Options modeling with Black-Scholes-style fair values, volatility regimes, and
  strike-specific execution.
- Round 5 group-level research, hidden-path re-anchoring, mean-reversion,
  passive market making, and NN-assisted candidate generation.
