# Strategy Summary

This is a short, readable overview of the strategy progression across IMC
Prosperity 4. The repository keeps the implementation details in
`strategies/`, research artifacts in `analysis/`, and manual challenge work in
`manual-challenge/`.

## Final Cleanup Plan

1. Keep one clear navigation path: root `README.md` for overview,
   `docs/results-summary.md` for rankings/results, and this file for strategy
   explanations.
2. Keep strategies organized by round under `strategies/round1/` through
   `strategies/round5/`.
3. Keep analysis compact and evidence-focused: notebooks/scripts plus summary
   outputs, not every generated CSV.
4. Keep manual challenge work separate under `manual-challenge/`.
5. Before calling the repo finished, confirm there are no stale paths, no cache
   files, and no unintended local deletions staged.

## Round 1

Placement: global `#2009`, United States `#590`.

Round 1 focused on `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`. The final
strategy was built around robust OSMIUM fair-value execution. The main
improvement came from diagnosing that earlier versions skipped one-sided order
books; the final model persisted wall-mid, bid-wall, and ask-wall anchors in
`traderData` so it could keep trading when only one side of the book was visible.

Main file: `strategies/round1/trader_v14_final.py`.

## Round 2

Placement: global `#1699`, United States `#422`.

Round 2 extended the OSMIUM/PEPPER framework. The OSMIUM model used a wall-mid
anchor pulled toward a stable central value, while PEPPER kept a rush-to-limit
accumulator with passive fallback. The later refinement added shallow-book
inventory recycling so the strategy could free capacity instead of getting stuck
at position limits.

Main file: `strategies/round2/trader_v11_final.py`.

## Round 3

Placement after finalist reset: global `#617`, United States `#183`.

Round 3 introduced `VELVETFRUIT_EXTRACT`, `HYDROGEL_PACK`, and VEV options. The
strategy combined online fair-value anchors, Black-Scholes-style option pricing,
strike-specific execution, and inventory-aware market making. A key design shift
was reducing dependence on fixed fair values by using rolling wall-mid anchors
for the underlying products and option fair values.

Main file: `strategies/round3/traderfinal.py`.

## Round 4

Placement: global `#270`, United States `#82`.

Round 4 was the strongest ranking round. It expanded the options/underlying
stack with OU mean-reversion models, conditional implied-volatility regime
detection, deep-ITM option handling, and mark-specific informed-flow signals.
The documented final Round 4 backtest total is `970,314`, with major gains from
IV regime detection, deep-ITM handling, HGP microstructure, and online OU kappa
estimation.

Main file: `strategies/round4/final.py`.

## Round 5

Placement: global `#320`, United States `#101`.

Round 5 was the broadest research problem: 50 products grouped into 10 families.
The final strategy combined group-level relationship screens, re-anchored
hidden-path fair values, product-local mean reversion, side-gated passive market
making, and NN/tree-assisted candidate generation converted back into
deterministic rules. The final documented default backtest is `+1,479,360`,
with diagnostics of `+958,900` in `--match-trades none` and `+965,011` in
`--match-trades worse`.

Main file: `trader.py`; iteration history: `strategies/round5/`.
