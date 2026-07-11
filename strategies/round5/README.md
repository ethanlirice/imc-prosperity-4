# Round 5 Strategy History

The active Round 5 model is the repository-root `trader.py`. This folder keeps
the iteration history that led to it.

## Current Final Result

Official placement: global `#320`, United States `#101`.

Documented in `TRADING.md`:

| Run | Total | Day Split |
|---|---:|---|
| v14 baseline | `+1,370,720` | `+447,335 / +397,392 / +525,994` |
| promoted `trader.py` | `+1,479,360` | `+447,335 / +397,392 / +634,633` |
| delta | `+108,640` | `0 / 0 / +108,639` |

Diagnostics:

| Mode | Result |
|---|---:|
| `--match-trades none` | `+958,900` |
| `--match-trades worse` | `+965,011` |

## Strategy Stack

The final model combines:

- residual and basket-style relationships inside product groups,
- re-anchored hidden-path fair values,
- product-local mean reversion,
- passive market making with product-specific side gates,
- NN/tree-assisted candidate generation converted into deterministic rules,
- a `ROBOT_DISHES` shock-takeover sleeve for the Round 5 D4 regime.

## Folder Guide

- `session/`: most relevant late-stage Round 5 candidates and promoted variants.
- `prev/`: earlier lower-PnL Round 5 strategy iterations.
- `alt-strategies/`: alternate strategies preserved for comparison.
- `competitor-alpha/`: background hypothesis notes; not part of the final model.

For validated findings, read root `DATA.md` and `TRADING.md`.
