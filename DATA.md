# DATA.md
Verified empirical findings from Round 4 and Round 5 data.
Explorers write here. Strategy work reads this before making any decision.
Only confirmed findings. No hypotheses. No speculation.

---

## Round 5 ROBOT_DISHES shock regime (Apr 30 session)

Source: `raw-data/ROUND5/prices_round_5_day_{2,3,4}.csv` mid_price column,
direct tick-by-tick log return scan on `ROBOT_DISHES`.

Per-tick |log mid return| > threshold counts:

| Threshold | D2 | D3 | D4 |
|-----------|----|----|----|
| 0.003 | 24 | 29 | 746 |
| 0.004 | 0  | 0  | 743 |
| 0.005 (signal1's) | 0 | 0 | 740 |
| 0.006 | 0  | 0  | 740 |
| 0.007 | 0  | 0  | 740 |
| 0.008 | 0  | 0  | 740 |
| 0.010 | 0  | 0  | 6   |

ROBOT_DISHES on D4 is bimodal: the mid oscillates between $10,200 and $10,300
with frequent ~$100 jumps (log return ~+/-0.00976). Largest jump is +/-0.01005.
D2/D3 mids are smooth — zero per-tick jumps above 0.4% on either day. The
0.005 threshold therefore acts as a perfect day-2/day-3 self-gate: it is dormant
on D2/D3 and fires 740 times on D4. signal1's "+170k DISHES" shock alpha is
100% on D4 (D2: 0, D3: 0, D4: +172,794) and is a property of D4's regime, not a
generally portable per-product edge. See TRADING.md for the integrated
takeover-style port that captures this on D4 without disturbing D2/D3.

---

## Round 5 NN-assisted broad alpha scan

Scripts/output: `analysis/round5/neural-signals/41_hidden_mechanic_scan.py`,
`42_broad_feature_event_scan.py`, `43_cross_pressure_leadlag_scan.py`,
`44_tree_gru_research.py`, and top-ranked CSVs in
`analysis/round5/neural-signals/`. Data: `raw-data/ROUND5` days 2, 3, 4.

All scanner edges are execution-aware:
long edge = future bid1 - current ask1; short edge = current bid1 - future ask1.
Rows require positive mean edge on each of days 2/3/4.

Confirmed scanner results:
- `UV_VISOR_RED` visible suffix `420` did **not** survive the strict all-day
  count/stability gate; `41_uv_red_420_detail.csv` is empty.
- Visible suffix scan top rows are mostly h1000 effects for
  `GALAXY_SOUNDS_BLACK_HOLES`, `PEBBLES_XS`, `MICROCHIP_OVAL`, and
  `OXYGEN_SHAKE_EVENING_BREATH`. Treat as candidate generation only because
  many align with hidden-path/time drift.
- Broad feature scan found high raw product-time/path effects, especially
  `PEBBLES_XL`, `PEBBLES_XS`, `GALAXY_SOUNDS_SOLAR_WINDS`, and
  `MICROCHIP_SQUARE`; high overfit risk unless converted to re-anchored or
  product-local rules.
- Strongest non-time deterministic feature rows:
  `UV_VISOR_YELLOW` high group residual -> short h1000
  (worst-day mean **+348.02**, count **1325**),
  `PANEL_1X4` low group residual z -> long h1000
  (worst-day mean **+279.60**, count **1500**), and
  `MICROCHIP_SQUARE` low vol regimes -> long h1000.
- Same-group cross-pressure scan top rows:
  `OXYGEN_SHAKE_CHOCOLATE` ret100 low -> `OXYGEN_SHAKE_GARLIC` long h1000
  (worst-day mean **+158.07**, count **1466**);
  `GALAXY_SOUNDS_DARK_MATTER` ret100 high ->
  `GALAXY_SOUNDS_BLACK_HOLES` long h1000 (worst-day **+168.49**, count
  **1328**);
  `MICROCHIP_SQUARE` ret100 low -> `MICROCHIP_OVAL` short h1000
  (worst-day **+146.83**, count **2526**);
  `MICROCHIP_TRIANGLE` high microprice/imbalance ->
  `MICROCHIP_OVAL` short h1000 (worst-day about **+160.55**).
- ExtraTrees sampled-target stable rows across d2->d3, d3->d4, d23->d4:
  `UV_VISOR_MAGENTA` long h1000 (min top5 edge **+192.49**),
  `OXYGEN_SHAKE_CHOCOLATE` long h1000 (**+80.66**),
  `GALAXY_SOUNDS_PLANETARY_RINGS` short h1000 (**+97.32**),
  `SLEEP_POD_SUEDE` long h1000 (**+53.92**).
- Compact GRU d23->d4 top rows:
  `MICROCHIP_SQUARE` short h1000 (top5 edge **+663.98**, corr **0.176**),
  `UV_VISOR_MAGENTA` long h1000 (**+299.54**, corr **0.312**),
  `OXYGEN_SHAKE_CHOCOLATE` long h1000 (**+274.63**, corr **0.291**),
  `SLEEP_POD_NYLON` long h500 (**+222.50**, corr **0.272**).

Interpretation: NN/tree tooling found broad hidden structure, but top rows are
mostly h500/h1000 and often collide with existing free-alpha/re-anchor/MM
ownership. Promote only after copy-based integrated backtests.

## Round 5 NN/stochastic lab v2

Script/output: `analysis/round5/neural-signals/45_rnn_stochastic_lab.py`,
`45_rnn_stable_targets.csv`,
`45_rnn_saliency.csv`, `45_stochastic_ou_summary.csv`,
`45_synthetic_injection_recovery.csv`.

Reference audit: historical NN reference notes were incomplete and did not compile; useful replicated ideas were rich product/book/group features, product/group embeddings, high-edge sample weighting, synthetic mechanics, and explicit leaky/diagnostic separation.

The v2 RNN is a real product-sequence GRU: 32-tick product-local sequence,
product/group embeddings, cross-product group/market context, and 12
execution-aware targets (`long/short` x horizons 10/50/100/200/500/1000).
Validation splits: d2->d3, d3->d4, d2+d3->d4.

Top stable GRU targets across all 3 splits:
- `MICROCHIP_SQUARE` short h1000: min top5 edge **+492.15**, min win
  **0.7561**, mean corr **0.3849**.
- `GALAXY_SOUNDS_SOLAR_WINDS` short h1000: min edge **+355.51**, min win
  **0.9756**, mean corr **0.5255**.
- `PANEL_2X4` long h1000: min edge **+370.63**, min win **0.8780**,
  mean corr **0.5003**.
- `MICROCHIP_OVAL` short h1000: min edge **+308.29**, min win **0.8293**,
  mean corr **0.3783**; h500 also stable with min edge **+252.71**.
- `SNACKPACK_CHOCOLATE` short h1000: min edge **+264.46**, min win
  **0.9268**, mean corr **0.4502**.
- `OXYGEN_SHAKE_GARLIC` long h1000: min edge **+201.85**, min win
  **0.9024**, mean corr **0.3426**.
- `UV_VISOR_RED` long h1000: min edge **+218.24**, min win **0.9268**,
  mean corr **0.4618**.

GRU saliency on validation batches ranked cross-product context highest:
`group_imbalance_mean`, `group_micro_mean`, `group_ret50_mean`,
`group_ret10_mean`, then market context. Product-local features followed:
`mid_centered`, group rank/residual, imbalance, ret1/ret100, vol50, spread,
and OU z. This supports searching group-context rules rather than only
single-product suffix mechanics.

Stochastic diagnostics: products with best median h50 hit proxy vs half-spread
are `PEBBLES_XL`, `MICROCHIP_SQUARE`, `MICROCHIP_TRIANGLE`, `PEBBLES_XS`,
`ROBOT_IRONING`, and `MICROCHIP_OVAL`; their median spread/sigma ratios are
about **0.56-0.62** for the top five. OU half-lives are generally long
(hundreds to thousands of ticks), so OU results are better for opportunity
ranking than direct fast mean-reversion unless paired with event triggers.

Synthetic injection check now recovers planted mechanics:
suffix neighborhood around residue **42** (residue 42 edge **+38.77**, win
**0.8239**), time-bucket short clusters, and lead-lag
`leader_ret50_gt_8` -> long lagger h100 with edge **+22.87**, win **0.8059**.
This validates scanner mechanics, but also shows suffix effects appear as
clusters rather than a single exact residue.

## Round 5 NN integration results (execution-aware)

Outputs: `analysis/round5/neural-signals/46_nn_cross_integration_summary.csv` and
`47_nn_mm_side_gate_summary.csv`.

Confirmed integrated findings:
- Most single NN cross-pressure active sleeves that look strong offline are
  **default-inert** in integrated portfolio runs (often exact ties to base).
- `MICROCHIP_SQUARE ret50 low -> MICROCHIP_OVAL short` is a small additive
  sleeve (about **+614** vs the compared baseline) and survives when combined
  into v13.
- Broad direction-only MM side gates mostly regress despite favorable NN labels
  (e.g., short-only/long-only toggles on several products).
- Two generated side-gate variants were positive in default mode:
  - `add_pebbles_m_long_only`: **+1,361,384**
  - `add_translator_space_gray_short_only`: **+1,370,720**
  These are candidate-generation results and require full promotion gating
  (default + diagnostics + code hardening) before becoming canonical.

## Round 5 Phase 1 — group tradeability screen

Script/output: `notebooks/round5/01_group_tradeability.py`,
`01_group_tradeability_ranking.csv`, `01_group_tradeability_by_day.csv`,
`01_group_tradeability.md`. Data: `data/ROUND5` days 2, 3, 4.

Composite score =
`intra_group_corr * spread_to_vol * depth * lively_ticks_pct`, where
`spread_to_vol` is return-volatility divided by median spread. Stable score is
minimum daily score divided by worst daily rank.

Ranked groups by stable tradeability:
1. **SNACKPACK** — stable score **23.217253**, ranks **1 / 1 / 1** on days
   2/3/4; avg return corr **0.374163**, vol/spread **0.406472**, depth **160**,
   lively **0.960536**.
2. **PEBBLES** — stable score **10.686380**, ranks **2 / 2 / 2**; avg return
   corr **0.207132**, vol/spread **1.392946**, depth **76**, lively
   **0.984125**.
3. **UV_VISOR** — stable score **0.108117**, ranks **3 / 3 / 6**; weak return
   corr **0.009902** despite decent depth/liveliness. Exploratory only.
4. **TRANSLATOR** — stable score **0.076697**, ranks **5 / 4 / 7**; weak return
   corr **0.009334**. Exploratory only.

Rejected for Phase 2 priority:
- **SLEEP_POD:** worst rank **9**, below-median return co-movement.
- **MICROCHIP:** worst rank **9**, low minimum daily score despite high
  vol/spread.
- **PANEL:** worst rank **10**, low minimum daily score, below-median
  co-movement, and thin movement versus spread.
- **GALAXY_SOUNDS:** worst rank **9**, low minimum daily score, below-median
  co-movement, and thin movement versus spread.
- **OXYGEN_SHAKE:** worst rank **10**, low minimum daily score, below-median
  co-movement, thin movement versus spread.
- **ROBOT:** worst rank **10**, low minimum daily score and below-median
  co-movement.

## Round 5 Phase 2/3 — relationship and lead-lag screens

Scripts/output: `notebooks/round5/02_within_group_pairs.py`,
`02_within_group_pairs.csv`, `02_within_group_pairs.md`,
`03_basket_synthetic.py`, `03_basket_synthetic.csv`,
`03_basket_synthetic.md`, `04_lead_lag_scan.py`,
`04_lead_lag_tensor.csv`, `04_lead_lag_survivors.csv`,
`04_lead_lag_scan.md`. Data: `data/ROUND5` days 2, 3, 4.

**Pair spreads:** no pair in the top-4 Phase 1 groups passed the full gate
(combined residual ADF t < −2.8, at least 2 daily ADF passes, and max daily
half-life ≤300 ticks). Best raw examples, such as
SNACKPACK_CHOCOLATE vs SNACKPACK_VANILLA, had strong co-movement
(`all_corr_mid=-0.925873`, `all_adf_t=-3.135021`) but half-life was too slow
or unstable (`half_life_mean_day=265.24`, `half_life_max_day=435.96`), so do
not promote raw pair trading yet.

**Basket synthetic:** PEBBLES has the only confirmed fast relationship. All
five 1-against-4 PEBBLES regressions pass on all 3 days:
- PEBBLES_XL: `R2=0.999998`, residual σ **2.798402**, ADF t **−170.962669**,
  half-life **0.159551**, max daily half-life **0.180043**.
- PEBBLES_XS: `R2=0.999996`, residual σ **2.798402**, ADF t **−170.961100**,
  half-life **0.159577**, max daily half-life **0.180168**.
- PEBBLES_L/M/S similarly pass with `R2≥0.999980`, residual σ ≈ **2.7983**,
  ADF t ≈ **−170.96**, and half-life ≈ **0.1596**.

SNACKPACK baskets are structurally correlated but slower than the strict gate:
CHOCOLATE (`R2=0.948367`, ADF t **−5.234722**, half-life **374.85**) and
VANILLA (`R2=0.929416`, ADF t **−5.076796**, half-life **388.23**) are
research candidates only, not first implementation.

**Lead-lag:** all ordered 50×50 product pairs at lags
{1,2,5,10,20,50,100,200} were scanned. No pair passed the persistence gate
(`|corr|≥0.10`, beats lag-0, same sign, passes ≥2 of 3 days). Do not allocate
strategy effort to lead-lag until a looser event-conditioned scan finds
something executable.

## Round 5 deeper alpha screens — residual shocks, flow, execution

Scripts/output: `notebooks/round5/05_algebraic_structure.py`,
`06_microstructure_regimes.py`, `07_event_lead_lag.py`, `08_trade_flow.py`,
`09_pebbles_executable_basket.py`, `10_pebbles_leg_fair_proxy.py`,
`11_residual_shock_execution.py`, `12_residual_trade_sim.py`,
`15_residual_online_calibration.py`. Data: `data/ROUND5` days 2, 3, 4.

**PEBBLES algebra:** equal-weight identity
`XS + S + M + L + XL ≈ 50000` is confirmed with residual σ **2.798327**,
p95 abs residual **1.059250**, ADF t **−170.971776**, half-life **0.159400**
ticks, and identical PCA null vector across days. Full-basket crossing is not
the main play: estimated round-trip crossing cost is **64.0** points
(**22.87** residual σ). Best crossed full-basket proxy only made **+1280**
total over D2/D3/D4 (`buy_sum=49997`, `exit_sum=49998`, qty 10), so PEBBLES
should be traded as fair-value/skew or target-leg residual, not brute-force
five-leg market orders.

**Flow/participant screen:** Round 5 has **0 non-blank buyer/seller names** in
**35,385 / 35,385** trade rows, so there is no Mark/Olivia-style direct copy
signal. Every trade row is part of a complete same-side 5-product group basket:
**3,485** all-buy events, **3,592** all-sell events, **0** mixed-side events.
Blindly crossing after public prints is negative after spread at t+200:
`buy_at_ask` **−5.533**, `sell_at_bid` **−5.666**.

**Microstructure/execution:** PEBBLES has the best execution surface among the
first-ranked groups despite lower depth than SNACKPACK: group h5
move/half-spread **5.13916**, trade tick rate **2.147%**, top3 depth **76**.
SNACKPACK has depth **160** but h5 move/half-spread only **1.46836**. Best
day-stable active residual signal in the microstructure screen was
`PEBBLES_S` (`|z|≥1.0`, **853** signal ticks, h1 active edge **+0.34056**,
positive **3/3** days, worst day **+0.11632**). Passive fills are low-single
digit touch proxies, so passive edges are quote-skew candidates only.

**Event-conditioned lead-lag:** large-move and sign-only lead-lag averages
exist but are too weak or too slow as standalone crossing rules. Example:
`SNACKPACK_VANILLA -> PEBBLES_XL`, lag 200, mean markout **23.5069**, good_pct
**0.524**, only **1.383×** follower median spread. Use as context only.

**OLS residual shocks:** 1-vs-4 residual shocks across groups produced the
largest executable research candidates. Active entry + active exit with pooled
fits showed many large markouts, so a stricter leave-one-day-out trade sim was
run: fit coefficients on two days, trade the held-out day only, cross one
target leg at qty **10**, and allow one open trade per product.

Best raw leave-one-day-out candidates (`12_residual_trade_sim.py`):
- `SLEEP_POD_POLYESTER`, z **1.5**, hold **500**, zero-cross exit:
  total **+48,350**, day PnL **+14,670 / +9,570 / +24,110**, **48** trades.
- `GALAXY_SOUNDS_SOLAR_FLAMES`, z **2.0**, hold **500**, fixed exit:
  total **+36,400**, day PnL **+11,140 / +4,040 / +1,330**, **26** trades.
- `MICROCHIP_RECTANGLE`, z **1.5**, hold **500**, zero-cross exit:
  total **+34,250**, day PnL **+11,570 / +11,090 / +11,590**, **33** trades.

Because raw residuals can exploit unknown day-level intercepts, an online
calibration check was run. Non-raw robust candidates subtract only first
100/500 same-day residual observations or a past rolling mean before trading.
Best non-raw candidates (`15_residual_online_calibration.py`):
- `MICROCHIP_RECTANGLE`, **open500**, z **1.5**, hold **500**:
  total **+43,360**, day PnL **+19,480 / +8,030 / +15,850**, **34** trades.
- `PEBBLES_S`, **open100**, z **1.5–3.0**, hold **200**:
  total **+36,160**, day PnL **+8,250 / +24,130 / +3,780**, **128** trades.
- `ROBOT_IRONING`, **open500**, z **1.5**, hold **200**:
  total **+28,370**, day PnL **+1,380 / +19,460 / +7,530**, **73** trades.
- `PANEL_2X2`, **open100**, z **1.5**, hold **500**:
  total **+22,570**, day PnL **+6,260 / +7,830 / +8,480**, **51** trades.
- `UV_VISOR_MAGENTA`, **open100**, z **2.5**, hold **500**:
  total **+19,410**, day PnL **+3,380 / +3,380 / +12,650**, **29** trades.
- `OXYGEN_SHAKE_MINT`, **open500**, z **1.5**, hold **500**:
  total **+18,180**, day PnL **+6,550 / +4,640 / +6,990**, **34** trades.

Interpretation: promote candidates in this order for strategy testing:
`MICROCHIP_RECTANGLE` open500 residual, `PEBBLES_S` open100 residual,
then `ROBOT_IRONING` / `PANEL_2X2` / `UV_VISOR_MAGENTA` / `OXYGEN_SHAKE_MINT`
only after conflict-resolved portfolio simulation. Treat raw-only
`SLEEP_POD_POLYESTER` and `GALAXY_SOUNDS_SOLAR_FLAMES` as high-risk until
they survive online calibration or live-style backtest gates.

**Depth-aware robustness audit:** `13_residual_robustness_audit.py` reran
1-vs-4 residual trades with quantity **10**, one open target position, and
3-level VWAP for entry/exit. It confirms the prior `12_*` script avoided
held-out coefficient/sigma leakage; `11_*` pooled tables remain discovery only.
Accepted OLS set:
- `SLEEP_POD_POLYESTER`, z **1.5**, hold **500**, zero-cross exit:
  depth-aware total **+48,277**, min day **+9,528**, **48** trades,
  win_pct **0.7708**. Top-of-book was short on **25.0%** of entry/exit
  fills, but VWAP still preserved the edge.
- Same target, z **1.5**, hold **200**, zero-cross exit:
  depth-aware total **+33,968**, min day **+1,731**, **102** trades.

Tentative/rejected audit notes:
- `GALAXY_SOUNDS_SOLAR_FLAMES` keeps strong OLS PnL
  (**+36,400**, min day **+4,690**) but the simpler target-minus-peer-mean
  formula has negative min day (**−529** or worse), so it is not first promote.
- `MICROCHIP_RECTANGLE` keeps depth-aware OLS PnL
  (**+34,009**, min day **+10,988**) but is rejected from the top OLS set in
  this audit because the simpler formula is poor (**+1,632** total,
  min day **−8,507**) and top-of-book is short on **92.4%** of fills. It can
  still be tested as an OLS-only sleeve, but not treated as the cleanest alpha.

**Portfolio conflict simulation:** `14_residual_portfolio_conflicts.py` enforces
one active position per product and resolves simultaneous signals by isolated
training-day robustness. Full-sample `static12_*` sets are diagnostic only, but
they show capacity if parameters are fixed from research:
- `static12_long_horizon_500`: total **+257,180**, day PnL
  **+89,000 / +98,860 / +69,320**, **501** trades, win_pct **0.5888**.
- `static12_top_per_group`: total **+211,980**, day PnL
  **+68,020 / +79,870 / +64,090**, **455** trades, win_pct **0.5780**.
- `static12_fast_horizon_le_100`: total **+92,650**, day PnL
  **+35,590 / +33,900 / +23,160**, **1,117** trades.

True leave-one-day-out selection by only the two non-test days is stricter:
- `lodo_top_per_group`: total **+51,270**, day PnL
  **+29,390 / +13,290 / +8,590**, **518** trades. This is the best robust
  live-style policy from the portfolio screen.
- `lodo_fast_horizon_le_100` and `lodo_long_horizon_500` over-select and fail
  out of sample (**−273,590** and **−67,400** respectively). Do not run broad
  residual templates.

Current strategy implication: build one factor at a time. The cleanest first
implementation candidate is `SLEEP_POD_POLYESTER` OLS residual z **1.5** with
500-tick/zero-cross exit, despite earlier online-centering caution, because it
survived held-out coefficients, depth-aware fills, simple-formula sanity, and
portfolio top-per-group selection. Next candidates are top-per-group residuals
from the portfolio report, not a broad all-groups scanner.

## Round 5 deeper alpha screens — passive/MM capture and hybrid overlays

Scripts/output: `notebooks/round5/16_wall_mid_mm.py`,
`17_stat_arb_mr_deep.py`, `18_passive_fill_hidden_taker.py` and their
corresponding `16_*`, `17_*`, `18_*` reports. Data: `data/ROUND5` days 2, 3, 4.

**Wall / popular-level fair values:** the best aggregate `wall_mid` horizon is
`500`, with **45,380** active observations, signed mid markout **3.944**,
hit rate **0.5069**, crossing edge **3.637**, and passive edge **6.828**.
`popular_mid` is not useful for short horizons, with negative crossing edge
through `h100`; at `h500` it becomes viable with **1,383,823** active
observations, signed markout **9.816**, and crossing edge **4.459**. Best
popular-level candidate is `MICROCHIP_TRIANGLE` `h500`
(`signed markout 105.471`, `min day 87.091`, crossing edge `102.433`,
passive edge `109.795`). Best wall-mid candidate is `PEBBLES_XL` `h500`
(`signed markout 30.238`, `min day 19.455`, crossing edge `103.008`,
passive edge `34.435`).

**Passive fill / hidden taker:** the broad passive fill screen found the best
conservative row at `SNACKPACK_PISTACHIO` sell `best_touch` `h1`
(`fill rate 0.006434`, `193` fills, mean edge `+4.222798`, EV/quote
`+0.027169`, positive `3/3` days), but forced liquidation is negative
(`-3.818653`, or `-38.186528` for a full 10-lot inventory). The best average
forced-liquidation row was `OXYGEN_SHAKE_GARLIC` buy `residual_fair` `h500`
(`fill rate 0.792175`, mean edge `+22.476281`, cross-liq edge `+14.946937`),
but only `2/3` days are positive. Hidden-taker behavior is broad rather than
product-specific; the top repeated trade size was `2` with share `0.263302`,
and public trades matched the best touch at an average rate of `1.000000`.

**Deep stat-arb / MR:** the deeper sweep screened **2,350** residual
definitions and narrowed to **117** robust candidates. Best worst-day row was
`MICROCHIP_SQUARE` PCA residual, raw `z=1.5`, `h500`, fixed exit:
`58,540` total PnL, `18,040` min-day PnL, `41` trades. Best online-centered
row was `PEBBLES_S` PCA residual, expanding center, `z=1.5`, `h500`,
fixed exit: `60,940` total PnL, `17,330` min-day PnL, `29` trades. Strongest
plateau was `integer_combo PEBBLES_XS` with `188` robust parameter rows; best
row there was `57,050` total PnL, `16,240` min-day PnL, `53` trades.

**Hybrid execution overlay:** a one-tick-inside MM probe on all products made
`+401,415` on `--match-trades worse` and `0` on `none`. The current
`base-strategy.py` baseline reaches `+534,757` on the primary default
`prosperity4btx ... 5 --merge-pnl` command. Recent 3-layer merge variants did
not improve it: `base-strategy-3layer-v2.py` regressed to `+466,166`, while
`base-strategy-3layer-v3.py` tied `+534,757` with no incremental edge. This
confirms the passive/MM layer is a major source of the current Round 5 edge,
but broad pair stacking is not the next path forward.

## Round 5 simple MM/MR framework

Historical prototype summarized here; detailed generated outputs were pruned from the public workspace.

The reverse-engineering/stable-line hypothesis was tested directly. Broad
all-product fair-value skew plus active mean reversion was strongly negative:
`simple_mm_mr_all50_v1.py` made **−1,239,202**. Pure passive controls were
positive and stable: all-50 one-tick-inside MM made **+401,415**, while all-50
touch MM made **+476,800**. The useful edge is therefore passive touch spread
capture, not generic active MR.

Applying that to the current baseline improved results:
- `base-strategy-touch-mm-v1.py`: touch quotes on the selected MM sleeve,
  **+581,939**.
- `base-strategy-touch-mm-target-select-v2.py`: passive MM owns `PANEL_2X2`,
  `PEBBLES_S`, `ROBOT_IRONING`, and `SNACKPACK_STRAWBERRY`, **+623,546**.
- `base-strategy-touch-mm-target-select-v3.py`: removes
  `TRANSLATOR_SPACE_GRAY`, **+627,758** with day split
  **+196,332 / +181,566 / +249,860**.

## Round 5 free-alpha path table

Historical free-alpha probe summarized here; the promoted hidden-path evidence now lives under `analysis/round5/hidden-paths/`.

The supplied five-number table is best interpreted as a five-bucket fair path:
`[base, base+d1, base+d2, base+d3, base+d4]`. Against actual mids, the anchor
has cross-product correlation **0.976461** with product mean price, and the
five-bucket path has mean absolute fit error about **184** ticks.

As a broad active rule it is real but unsafe: default entry **20** made
**+478,380**, while the best broad sweep entry **200** made **+742,005** but
day 4 was only **+23,686**. The safe use is selective product ownership.

Best selective overlay:
- `base-strategy-free-alpha-selected-v1.py`: **+822,226**.
- `base-strategy-free-alpha-selected-v2.py`: **+823,611**.
- `base-strategy-free-alpha-selected-v3.py`: **+841,042**.
- `base-strategy-free-alpha-selected-v5.py`: standalone best,
  **+868,478** with day split **+306,588 / +225,446 / +336,444**.

## Round 5 in-flight ablation study (session handoff)

Prepared but not finished this session:
- Configurable v5 candidate:
  `strategies/round5/base-strategy-free-alpha-configurable.py`.
- Ablation runner: historical owner-side sweep summarized below; detailed generated outputs were pruned.

Designed ablation families:
- MM ownership ablations per product: `mm_bid_off`, `mm_ask_off`, `mm_drop`.
- Free-alpha sleeve ablations per product: `free_drop`.
- Selective free-alpha adds with per-product edge overrides: `free_add`.

Run status:
- Completed in the v6 promotion session; final accepted deltas are recorded
  below.

## Round 5 owner/side ablation completion and v6 bundle

Historical owner/side ablation outputs are summarized here; detailed generated files were pruned from the public workspace.

The owner/side/free-alpha ablation sweep completed with **101 / 101** cases OK.
Positive single-factor deltas over v5 included:
- `mm_ask_off__PEBBLES_XL`: **+36,331**, total **904,809**,
  day split **348,766 / 195,621 / 360,422**.
- `mm_bid_off__MICROCHIP_OVAL`: **+31,682**, total **900,160**,
  day split **307,266 / 238,922 / 353,972**.
- `mm_ask_off__OXYGEN_SHAKE_GARLIC`: **+28,781**, total **897,259**,
  day split **328,012 / 219,959 / 349,288**.
- `mm_ask_off__MICROCHIP_SQUARE`: **+26,605**, total **895,083**,
  day split **329,073 / 258,938 / 307,072**.
- `mm_ask_off__GALAXY_SOUNDS_BLACK_HOLES`: **+22,139**, total
  **890,617**, day split **328,962 / 225,130 / 336,525**.
- `free_add__TRANSLATOR_ECLIPSE_CHARCOAL`: **+15,002**, total
  **883,480**, day split **292,220 / 248,914 / 342,346**.

Combined testing confirmed that single-case deltas were not purely additive but
the owner-map stack was stable. Final accepted v6 bundle:
- MM bid-off: `MICROCHIP_OVAL`, `MICROCHIP_TRIANGLE`, `ROBOT_IRONING`,
  `TRANSLATOR_ASTRO_BLACK`, `UV_VISOR_AMBER`.
- MM ask-off: `GALAXY_SOUNDS_BLACK_HOLES`, `MICROCHIP_SQUARE`,
  `OXYGEN_SHAKE_GARLIC`, `PANEL_2X4`, `PEBBLES_XL`, `SLEEP_POD_SUEDE`,
  `UV_VISOR_RED`.
- Free-alpha adds at entry edge **200**: `ROBOT_MOPPING`,
  `ROBOT_VACUUMING`, `SLEEP_POD_POLYESTER`,
  `TRANSLATOR_ECLIPSE_CHARCOAL`.

This bundle backtested at **+1,086,126** on
`prosperity4btx trader.py 5 --merge-pnl`, with day split
**+401,596 / +316,338 / +368,192**. Leave-one-out checks around the final
bundle confirmed every accepted toggle improves the combined result. Adding
conflicting free-alpha overlays for `GALAXY_SOUNDS_BLACK_HOLES` or
`PEBBLES_XL` worsened the bundle and was rejected.

## Round 5 direct and group-index mean reversion scan

Scripts/output:
`analysis/round5/mean-reversion/23_mean_reversion_scan.py`,
`analysis/round5/mean-reversion/24_mr_executable_probe.py`,
`mr_product_scan.csv`, `mr_product_day.csv`, `mr_group_scan.csv`,
`mr_group_day.csv`, `mr_executable_summary.csv`, `mr_executable_day.csv`.

Overlap audit:
- Existing work already covered residual/stat-arb MR heavily in
  `17_stat_arb_mr_deep.*`, wall/popular/depth fair microstructure in
  `16_wall_mid_mm.*`, and broad MM/MR strategy controls in
  the historical MM/MR framework prototype.
- Missing coverage was a uniform direct product rolling-anchor MR scan and a
  comparable group-index MR scan across all 50 products.

Initial diagnostics:
- Product rolling MR generated **7,500** aggregate rows and group-index MR
  generated **22,500** aggregate rows.
- Many diagnostic rows were day-stable after current-spread active-entry cost,
  but this is still a signal proxy until integrated with v6 ownership.
- Top stable product-level active-edge rows included `PEBBLES_XS`
  window **1000**, z **3.0**, horizon **500**; `PEBBLES_XL` window **500**,
  z **3.0**, horizon **200**; and `MICROCHIP_TRIANGLE` window **1000**,
  z **1.5–2.5**, horizon **500**.
- Top group-index rows overlapped strongly with direct product MR:
  `PEBBLES_XL` and `PEBBLES_XS` against equal/vol group anchors, plus
  `MICROCHIP_TRIANGLE` against the microchip group.

Execution-aware isolated probe:
- Active entry + active exit, position cap **10**, zero-cross or max-hold exit.
- Best stable isolated rows:
  - `PEBBLES_XL` product rolling window **200**, z **2.5**, hold **500**:
    **+126,780**, day split **+19,620 / +38,640 / +68,520**, **133** trades.
  - `PEBBLES_XS` product rolling window **1000**, z **3.0**, hold **500**:
    **+31,420**, day split **+9,650 / +9,490 / +12,280**, **21** trades.
  - `MICROCHIP_TRIANGLE` product rolling window **1000**, z **2.5**,
    hold **500**: **+30,810**, day split
    **+6,325 / +10,233 / +14,252**, **31** trades.
  - `ROBOT_LAUNDRY` product rolling window **1000**, z **2.5**, hold **500**:
    **+14,644**, day split **+6,149 / +4,800 / +3,695**, **32** trades.

Interpretation:
- Direct product/group-index MR is feasible enough to justify a v6-integrated
  configurable sleeve, especially for `PEBBLES_XL`, `PEBBLES_XS`, and
  `MICROCHIP_TRIANGLE`.
- At the isolated-probe stage this was not promotion-ready because
  `PEBBLES_XL` had MM ask disabled, `MICROCHIP_TRIANGLE` had MM bid disabled,
  and several candidates overlapped free-alpha/residual ownership. This led to
  the v6-integrated portfolio test below.

## Round 5 MR integration and v7 promotion

Scripts/output:
`strategies/round5/base-strategy-free-alpha-side-gated-mr-configurable.py`,
`strategies/round5/base-strategy-free-alpha-side-gated-mr-v7.py`,
`analysis/round5/mean-reversion/mr_configurable_backtest_summary.csv`,
`analysis/round5/mean-reversion/mr_configurable_loo_diagnostics.csv`.

Configurable integration around v6 tested direct rolling-anchor MR with product
ownership conflicts resolved by running free-alpha/residual first, then MR, then
MM. MR products are removed from MM ownership while enabled.

Primary integration results versus v6 **+1,086,126**:
- `PEBBLES_XL`: **+1,149,800**, delta **+63,674**,
  day split **+379,075 / +369,852 / +400,874**.
- `PEBBLES_XS`: **+1,117,546**, delta **+31,420**,
  day split **+411,246 / +325,828 / +380,472**.
- `MICROCHIP_TRIANGLE`: **+1,094,126**, delta **+8,000**,
  day split **+413,486 / +311,534 / +369,106**.
- `ROBOT_LAUNDRY`: **+1,093,108**, delta **+6,982**,
  day split **+409,432 / +318,592 / +365,084**.
- `PEBBLES_XL + PEBBLES_XS`: **+1,181,220**, delta **+95,094**.
- `PEBBLES_XL + PEBBLES_XS + MICROCHIP_TRIANGLE`: **+1,189,220**,
  delta **+103,094**.
- All four MR products: **+1,196,202**, delta **+110,076**,
  day split **+408,451 / +376,792 / +410,959**.

Leave-one-out around all four:
- Drop `PEBBLES_XL`: **−63,674** versus all-four bundle.
- Drop `PEBBLES_XS`: **−31,420**.
- Drop `MICROCHIP_TRIANGLE`: **−8,000**.
- Drop `ROBOT_LAUNDRY`: **−6,982**.

Root `trader.py` promoted to v7 after standalone verification. Root line count
is **495**, preserving the under-500 target. Diagnostic match modes both made
**+670,289**, day split **+203,731 / +193,086 / +273,472**, improving v6
diagnostics by **+203,764**.

## Round 5 MM refinement, event schedule, and re-anchored hidden paths

Scripts/output:
Historical v7 MM-refinement outputs are summarized here; retained re-anchor artifacts live in
`analysis/round5/hidden-paths/36_reanchor_integration_sweep.py`,
`analysis/round5/hidden-paths/37_reanchor_winner_bundles.py`,
`analysis/round5/hidden-paths/reanchor_integration_summary.csv`.

MM refinement around v7 found the default full-size touch layer was already
good, but a small set of quote-size changes was additive:
- Best single cases included `GALAXY_SOUNDS_PLANETARY_RINGS` size 1
  (**+9,973**), `UV_VISOR_ORANGE` size 1 (**+9,061**), and adding touch-MM
  coexistence on `ROBOT_LAUNDRY` (**+7,567**).
- Best bundle was top-8 size overrides plus `ROBOT_LAUNDRY`, producing
  **+1,234,316**, day split **+414,292 / +386,527 / +433,497**.

The shared hardcoded `EVENT_TARGETS` schedule was tested as a high-priority
timestamp-position overlay and rejected. Integrated score was only **+877,992**,
with large losses on several overridden legs. It may be a regime-specific
schedule, not portable alpha.

Re-anchored hidden-path testing was the strongest new result. The sleeve uses
the existing bucket-delta paths, but replaces fixed base levels with the
current day's bucket-0 running average. Product integration versus v8:
- `ROBOT_DISHES`: **+1,287,135**, delta **+52,819**.
- `OXYGEN_SHAKE_MINT`: **+1,257,734**, delta **+23,418**.
- `SNACKPACK_STRAWBERRY`: **+1,244,575**, delta **+10,259**.
- `SNACKPACK_CHOCOLATE`: **+1,237,322**, delta **+3,006**.
- Winner bundle (`ROBOT_DISHES`, `OXYGEN_SHAKE_MINT`,
  `SNACKPACK_STRAWBERRY`, `SNACKPACK_CHOCOLATE`): **+1,323,819**, day split
  **+444,338 / +384,488 / +494,994**.

Rejected re-anchor candidates after live integration despite good offline
proxy scores: `PEBBLES_S`, `UV_VISOR_ORANGE`, `SLEEP_POD_NYLON`,
`PANEL_4X4`, `OXYGEN_SHAKE_EVENING_BREATH`, `PANEL_1X2`, and broad all-10
bundles. Offline path proxy is useful for candidate generation, but promotion
requires conflict-aware `prosperity4btx` testing against the current trader.

## Round 5 rolling TLS / pair-fair alpha test

Scripts/output:
`analysis/round5/tls-pair-spreads/38_rolling_tls_target_scan.py`,
`analysis/round5/tls-pair-spreads/39_tls_integration_sweep.py`,
`analysis/round5/tls-pair-spreads/40_tls_passive_sweep.py`,
`analysis/round5/tls-pair-spreads/rolling_tls_target_summary.csv`,
`analysis/round5/tls-pair-spreads/tls_integration_summary.csv`,
`analysis/round5/tls-pair-spreads/tls_passive_summary.csv`.

Hypothesis from `strategies/reverse-engineering/alpha_inspo.md`: TLS or
rolling-beta same-family relationships, especially Snackpack/Microchip/Robot,
may reveal more stat-arb/mean-reversion edge than static OLS spreads.

Signal proxy:
- A rolling target-leg scanner found several all-3-day-positive candidates,
  but the gross standalone edge was modest. Best rows were about **+20k**:
  `MICROCHIP_OVAL` vs `MICROCHIP_TRIANGLE`, `MICROCHIP_TRIANGLE` vs
  `MICROCHIP_SQUARE`, `ROBOT_LAUNDRY` vs `ROBOT_IRONING`, and
  `SNACKPACK_STRAWBERRY` vs `SNACKPACK_CHOCOLATE`.
- In the scan, OLS often beat TLS. This does not disprove TLS statistically,
  but it means TLS was not the obvious executable edge under our rule.

Portfolio integration against v10 **+1,323,819**:
- Active rolling target sleeves mostly regressed:
  `MICROCHIP_OVAL/TRIANGLE` **−23,951**,
  `MICROCHIP_TRIANGLE/SQUARE` **−11,122**,
  `ROBOT_LAUNDRY/IRONING` **−7,365**,
  `SNACKPACK_STRAWBERRY/CHOCOLATE` **−9,790**,
  `ROBOT_DISHES/LAUNDRY` **−59,266**.
- Only active positive was `ROBOT_VACUUMING/MOPPING` TLS at **+1,408**, but
  it lost materially on day 3 and is too unstable to promote.
- Passive TLS-skew was closer to viable but still weak. Best tested case:
  `MICROCHIP_CIRCLE/SQUARE` TLS passive size 5/10, **+2,146**. This is below
  the promotion bar.

Conclusion: the findings are useful as research direction, but current v10
already captures enough product-local edge that rolling TLS pair logic does not
improve PnL materially. If revisited, test it as passive quote skew with
stricter day-stability and only on products not already owned by strong
re-anchor/free-alpha/MR sleeves.

## Round 5 hidden-path Phase D follow-up

Re-read both the original hidden-path report and the Phase D robustness report.
The useful distinction held up: offline path candidates need to be separated
into add-only unowned overlays, owned-product replacements, and anchor-only
effects. The original proxy was directionally useful for finding candidates,
but Phase D's anchor-vs-shape split was better for deciding what to test as a
replacement.

Integrated finding:
- The broad Tier 2 anchor-only bundle failed in the real portfolio
  (**+1,207,514**), but `PEBBLES_L` alone was a clean exception.
- `PEBBLES_L` flat bucket-0 re-anchor with edge 80 improved current v10 by
  **+25,659**, promoting root to **+1,349,478**.

Interpretation: Phase D's flat-anchor result is not broadly portable after
product ownership conflicts, but it correctly identified that `PEBBLES_L`'s
trained/fixed path was worse than a simple current-day bucket-0 anchor.

## Round 5 ROBOT_DISHES — signal1 vs v14 (confirmed integration)

Alternate file `strategies/round5/alt-strategies/signal1.py` (docstring “Strategy 1” vs v14
“Strategy 2”) routes `ROBOT_DISHES` through **mid shock** logic (`|log mid
return|>0.005`) with short hold and no normal MM on that product, instead of
v14’s **re-anchored hidden-path** plus **reduce-only touch MM**.

Confirmed `prosperity4btx` Round 5 D2–D4 defaults:
- v14 baseline **+1,370,720**; full `signal1.py` **+595,827** (portfolio-level
  `signal1` is not dominant vs v14 under the same harness).
- Porting shock as an **end-of-run override** on v14
  (`strategies/round5/session/14-v14-robot-dishes-shock-endcap.py`) produced **+971,736**
  with **+254,393 / +174,334** on D2/D3 (single-sleeve conflict with re-anchor/MM).
- Re-anchor entry edge only for `ROBOT_DISHES` at **65** or **100** vs **80**
  (`14-v14-robot-dishes-reanchor-edge-65.py`, `14-v14-robot-dishes-reanchor-edge-100.py`)
  both **lowered** default totals vs v14.

Interpretation: the dishes PnL gap vs `signal1` is **not** a clean isolated fair
value tweak; it bundles **ownership** (no MM on shock path), **momentum shock**
entries, and a different global signal stack. None of the minimal ported sleeves
beat v14 on the primary default while preserving day stability.

## Round 5 v11 market-making attribution and refinements

Scripts/output:
`analysis/round5/market-making-v11/45a_v11_mm_core_attribution.py`,
`47b_v11_mm_side_on_tests.py`, `47c_v11_mm_size_tests.py`,
`47d_v11_mm_owned_coexistence.py`, `47e_v11_mm_bundle_tests.py`,
`47f_v11_mm_imbalance_tests.py`,
`v11_mm_contribution_by_product.csv`,
`v11_mm_rejected_changes.csv`,
`v11_mm_final_candidate_summary.csv`.

Current v11 pure MM contribution is large. Dropping all current MM products
from the v11 configurable copy regressed from **+1,349,478** to **+843,517**,
so current touch-MM contribution is **+505,961**.

Product drop attribution ranked the largest current MM contributors as:
- `PEBBLES_S`: **+48,509**.
- `MICROCHIP_OVAL`: **+43,346**.
- `OXYGEN_SHAKE_GARLIC`: **+41,605**.
- `GALAXY_SOUNDS_BLACK_HOLES`: **+38,589**.
- `MICROCHIP_SQUARE`: **+36,297**.
- `PANEL_1X4`: **+31,196**.
- `GALAXY_SOUNDS_PLANETARY_RINGS`: **+29,645**.

Side-gating and size results around v11:
- Re-enabling disabled MM sides was rejected. Best side-on test was still
  negative: `ROBOT_IRONING` bid-on **−1,836**. Larger regressions included
  `OXYGEN_SHAKE_GARLIC` ask-on **−35,564**, `MICROCHIP_OVAL` bid-on
  **−31,681**, and `MICROCHIP_SQUARE` ask-on **−26,604**.
- Relaxing current size caps was rejected. Closest case was `ROBOT_IRONING`
  size 2 at **−50**. Other tested size relaxations for
  `OXYGEN_SHAKE_GARLIC`, `GALAXY_SOUNDS_PLANETARY_RINGS`,
  `MICROCHIP_CIRCLE`, and `PANEL_2X4` all regressed.

Owned-product MM coexistence found a small positive edge:
- `SNACKPACK_CHOCOLATE` size-1 touch MM while re-anchor owns product:
  **+1,610**.
- `PEBBLES_L` reduce-only touch MM while re-anchor owns product: **+1,510**.
- `ROBOT_DISHES` reduce-only touch MM while re-anchor owns product: **+188**.
- Bundle of all three: **+3,308**, day split
  **+441,976 / +403,608 / +507,202**.

Book-imbalance no-quote filter was mostly not useful, but one product passed:
`MICROCHIP_CIRCLE` top-of-book imbalance threshold **0.4** improved v11 by
**+2,216**. The rule skips bid quotes when imbalance ≤ −0.4 and skips ask
quotes when imbalance ≥ 0.4. Tested imbalance filters on `PEBBLES_S` and
`OXYGEN_SHAKE_GARLIC` regressed; `MICROCHIP_SQUARE` produced no trades/delta.

Best integrated MM candidate:
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v12-mm-owned-imbalance.py`
made **+1,355,002**, day split **+442,320 / +404,218 / +508,464**,
delta **+5,524** versus v11. Diagnostics were unchanged:
`--match-trades none` **+832,689** and `--match-trades worse` **+832,689**.
