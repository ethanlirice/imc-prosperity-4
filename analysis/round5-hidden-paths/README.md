# Round 5 hidden time-bucket fair-value paths — research log

Goal: search Round 5 raw data for product-level and group-level five-bucket
fair-value paths similar to the user-supplied free-alpha table that produced
roughly +240k of edge in v5. The next agent decides what to integrate.

Bucket convention matches v7 trader:
`bucket = int(timestamp * 5 // 1_000_000)`, clamped to `[0, 4]`. Each day is
split into five 200_000-tick windows.

**Nothing here has been promoted; nothing here has been integrated. All pnl
numbers are from offline simulations described below, not from
`prosperity4btx`.**

---

## Outputs (all in this directory)

| file | contents |
|---|---|
| `_common.py` | shared loader, group map, free-alpha table, v7 ownership flags |
| `30_bucket_paths.py` → `product_bucket_paths.csv` | per `(product, day, bucket)` mean / median / open / close / vwap / micro mid plus deltas vs bucket0, day mean, prev bucket, group bucket mean |
| `31_path_stability.py` → `product_path_stability.csv` | per `(product, normalisation)` cross-day shape correlation, sign consistency, magnitude vs spread / realized vol, single-day overfit ratio |
| `32_free_alpha_compare.py` → `free_alpha_shape_comparison.csv` | per product, comparison of v7 `FREE_ALPHA` path to actual bucket means, pooled and per-day |
| `33_group_paths.py` → `group_path_summary.csv`, `group_product_residual_paths.csv` | group-mean bucket path; per-product `(alpha, beta)` fits and residual stability |
| `34_walkforward_proxy.py` → `path_proxy_backtest_summary.csv`, `path_proxy_backtest_day.csv` | walk-forward 2-train / 1-test simulation of an active crossing rule using four candidate paths and seven thresholds |
| `35_rank_candidates.py` → `candidate_products.csv` | best per-product config from the proxy joined with stability + ownership labels |

### Reproduce

```bash
cd "$REPO_ROOT"
python3 analysis/round5-hidden-paths/30_bucket_paths.py
python3 analysis/round5-hidden-paths/31_path_stability.py
python3 analysis/round5-hidden-paths/32_free_alpha_compare.py
python3 analysis/round5-hidden-paths/33_group_paths.py
python3 analysis/round5-hidden-paths/34_walkforward_proxy.py
python3 analysis/round5-hidden-paths/35_rank_candidates.py
```

Data path used: `raw-data/ROUND5/prices_round_5_day_{2,3,4}.csv` (50 products × 10000 ticks per day).

---

## Walk-forward proxy rules

For each `(product, path_type, threshold)` and each fold `(train days, test day)`
in `[(3,4)→2, (2,4)→3, (2,3)→4]`:

- Build a 5-vector fair path on the train days.
- On the test day, for each tick:
  - if `best_ask < fair[bucket] - threshold` and `pos < +10`: buy 1 at the ask.
  - if `best_bid > fair[bucket] + threshold` and `pos > -10`: sell 1 at the bid.
  - if `|mid - fair[bucket]| <= max(20, threshold/4)`: close to flat at touch.
- Mark to market the residual position at the last mid.

Path types tested: `bucket_mean` (avg of train-day bucket means), `bucket_delta_b0`
(test-day bucket0 + avg train shape), `group_offset` (group bucket mean +
avg per-product offset), `group_scaled` (`alpha*group + beta` fit per train day,
averaged). Thresholds: 20, 40, 80, 120, 160, 200, 300.

This is a strict offline test that punishes single-day shape leakage.

---

## Top 10 product candidates (by walk-forward worst-day PnL with all 3 folds positive)

Source: `candidate_products.csv` filtered to `folds_positive == 3`.

| # | product | path | thr | total | worst | best | trades | v7 owner |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | `MICROCHIP_SQUARE` | group_scaled | 300 | 58,649 | 14,121 | 24,506 | 256 | mm_ask_off |
| 2 | `PEBBLES_XS` | bucket_delta_b0 | 200 | 49,738 | 13,937 | 20,438 | 874 | mr |
| 3 | `UV_VISOR_RED` | bucket_delta_b0 | 120 | 41,115 | 13,271 | 13,956 | 718 | mm_ask_off |
| 4 | `ROBOT_DISHES` | bucket_delta_b0 | 80 | 44,785 | 11,121 | 18,652 | 928 | **unowned** |
| 5 | `PEBBLES_L` | bucket_delta_b0 | 80 | 41,880 | 10,826 | 19,943 | 1,500 | free_alpha |
| 6 | `GALAXY_SOUNDS_SOLAR_FLAMES` | bucket_mean | 300 | 37,793 | 10,059 | 15,768 | 238 | free_alpha |
| 7 | `UV_VISOR_ORANGE` | group_scaled | 200 | 28,830 | 8,828 | 11,156 | 288 | **unowned** |
| 8 | `SLEEP_POD_LAMB_WOOL` | group_scaled | 20 | 34,333 | 8,812 | 13,474 | 3,024 | free_alpha |
| 9 | `SLEEP_POD_POLYESTER` | bucket_mean | 40 | 35,129 | 8,778 | 17,454 | 940 | free_alpha,residual |
| 10 | `TRANSLATOR_GRAPHITE_MIST` | group_scaled | 120 | 31,360 | 7,896 | 11,496 | – | free_alpha |

### Top 10 NOT yet owned by any v7 sleeve (cleanest replacements/additions)

These are the best add-only candidates because no existing sleeve fights them:

| # | product | path | thr | total | worst | best | stab b0 corr | free_alpha pooled δ-corr |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `ROBOT_DISHES` | bucket_delta_b0 | 80 | 44,785 | 11,121 | 18,652 | -0.111 | 0.840 |
| 2 | `UV_VISOR_ORANGE` | group_scaled | 200 | 28,830 | 8,828 | 11,156 | -0.038 | 0.636 |
| 3 | `SLEEP_POD_NYLON` | group_offset | 40 | 25,021 | 7,524 | 9,110 | -0.365 | 0.889 |
| 4 | `PEBBLES_S` | bucket_delta_b0 | 80 | 30,904 | 7,368 | 14,817 | 0.370 | 0.976 |
| 5 | `OXYGEN_SHAKE_MINT` | group_offset | 300 | 20,615 | 6,457 | 7,647 | -0.321 | 0.191 |
| 6 | `SNACKPACK_STRAWBERRY` | bucket_delta_b0 | 200 | 20,220 | 5,958 | 8,118 | 0.167 | 0.579 |
| 7 | `PANEL_4X4` | group_scaled | 300 | 20,578 | 4,318 | 9,984 | 0.068 | 0.204 |
| 8 | `SNACKPACK_CHOCOLATE` | group_scaled | 160 | 12,732 | 3,313 | 4,798 | 0.200 | -0.008 |
| 9 | `OXYGEN_SHAKE_EVENING_BREATH` | group_offset | 300 | 31,990 | 3,260 | 19,950 | 0.063 | 0.525 |
| 10 | `PANEL_1X2` | group_scaled | 300 | 23,023 | 3,151 | 15,795 | -0.230 | -0.176 |

`ROBOT_DISHES` is the standout: balanced day-by-day pnl
(d2 +11,121 / d3 +15,012 / d4 +18,652) and the heaviest trade volume of any
unowned candidate, but the path-shape signal averaged across days is weak
(stab b0 corr -0.11). The walk-forward score is positive because the product's
*level* (anchored on test-day bucket0) plus a small train-day shape gives
predictable mean reversion versus its group, not because the shape itself is a
strong scheduled path. Treat it as a group-residual candidate, not a
free-alpha-style fixed-path overlay.

`PEBBLES_S` is the cleanest "free-alpha-shaped" unowned candidate: stab b0
corr 0.37, free-alpha pooled δ-corr 0.98, three-fold positive at thresholds
40/80/120/200.

---

## Top 5 group-level path candidates

Source: `group_product_residual_paths.csv` sorted by `scale_cross_day_corr_mean`.

| # | group | best product | α | R² | residual max abs | scale corr | sign consistency |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | PANEL | `PANEL_2X4` | 1.18 | 0.29 | 442 | 0.938 | 0.933 |
| 2 | PEBBLES | `PEBBLES_XS` | 48074* | 0.25 | 608 | 0.853 | 1.000 |
| 3 | GALAXY_SOUNDS | `GALAXY_SOUNDS_DARK_MATTER` | 0.02 | 0.81 | 116 | 0.485 | 0.933 |
| 4 | SNACKPACK | `SNACKPACK_PISTACHIO` | 2.40 | 0.30 | 94 | 0.451 | 0.733 |
| 5 | ROBOT | `ROBOT_DISHES` | 0.85 | 0.36 | 232 | 0.418 | 0.800 |

*The PEBBLES alpha is an artefact of the equal-weight basket sum 50_000
identity — alphas are unreliable for that group, but the residual path is still
real and stable; PEBBLES_XS scale residual sign is consistent across all 5
buckets across 3 days.

The cleanest group structure outside what v7 already exploits is
`SNACKPACK_PISTACHIO` (already free_alpha), `ROBOT_DISHES` (unowned), and
`GALAXY_SOUNDS_DARK_MATTER` (free_alpha). PANEL_2X4 has the strongest
group-residual shape but is already mm_ask_off. PEBBLES_XS is already MR.

---

## Products where path structure is strong AND v7 likely already captures it

Path is strong (3 folds positive in proxy) but a v7 sleeve already owns the
product. The proxy pnl is therefore an alternative, not an additive, signal.
Listed by proxy worst-day PnL:

- `MICROCHIP_SQUARE` — 14,121 worst, mm_ask_off in v7. Proxy uses group_scaled
  thr 300; could be tested as a *replacement* for the mm_ask_off mark when
  retuning v7.
- `PEBBLES_XS` — 13,937 worst, MR in v7. The bucket_delta_b0 path proxy hits a
  comparable trade frequency to the rolling-anchor MR sleeve.
- `UV_VISOR_RED` — 13,271 worst, mm_ask_off in v7.
- `PEBBLES_L` — 10,826 worst, free_alpha in v7. Proxy threshold 80 is much
  more aggressive than v7's edge 200; if v7 is missing trades on this product
  the answer might be a lower edge or `bucket_delta_b0` style anchoring.
- `GALAXY_SOUNDS_SOLAR_FLAMES` — 10,059 worst, free_alpha in v7 (already at
  edge 200).
- `SLEEP_POD_LAMB_WOOL` — 8,812 worst, free_alpha in v7.
- `SLEEP_POD_POLYESTER` — 8,778 worst, free_alpha + residual in v7.
- `TRANSLATOR_GRAPHITE_MIST` — 7,896 worst, free_alpha in v7.
- `SNACKPACK_RASPBERRY`, `UV_VISOR_MAGENTA`, `TRANSLATOR_ECLIPSE_CHARCOAL`,
  `GALAXY_SOUNDS_DARK_MATTER`, `ROBOT_LAUNDRY`, `SNACKPACK_VANILLA`,
  `SNACKPACK_PISTACHIO` — all owned by free_alpha or mr in v7.

## Products where path structure is strong AND v7 may not capture it

Filter: `folds_positive == 3` AND `v7_owner_label == "unowned"`. Listed in the
"Top 10 not yet owned" table above. Concretely:

- `ROBOT_DISHES`, `UV_VISOR_ORANGE`, `SLEEP_POD_NYLON`, `PEBBLES_S`,
  `OXYGEN_SHAKE_MINT`, `SNACKPACK_STRAWBERRY`, `PANEL_4X4`,
  `SNACKPACK_CHOCOLATE`, `OXYGEN_SHAKE_EVENING_BREATH`, `PANEL_1X2`,
  `MICROCHIP_RECTANGLE`, `PEBBLES_M`, `GALAXY_SOUNDS_PLANETARY_RINGS`,
  `MICROCHIP_CIRCLE`, `PANEL_1X4`.

`PEBBLES_S` and `ROBOT_DISHES` have the strongest combination of walk-forward
worst-day PnL and shape stability; both are reasonable first targets for
integrated testing.

---

## Warnings — unstable / one-day overfit / single-day patterns

Products with NO `(path_type, threshold)` configuration showing all 3 folds
positive, sorted by best worst-day PnL:

| product | best path | best thr | folds positive | best total | best worst-day | v7 owner |
|---|---|---:|---:|---:|---:|---|
| `TRANSLATOR_VOID_BLUE` | bucket_delta_b0 | 120 | 2 | 3,978 | -30 | unowned |
| `OXYGEN_SHAKE_MORNING_BREATH` | bucket_mean | 300 | 2 | 9,597 | -179 | unowned |
| `MICROCHIP_TRIANGLE` | bucket_delta_b0 | 160 | 2 | 17,932 | -798 | mr, mm_bid_off |
| `UV_VISOR_AMBER` | bucket_delta_b0 | 160 | 2 | 16,885 | -1,999 | mm_bid_off |
| `UV_VISOR_YELLOW` | group_offset | 300 | 2 | 4,020 | -2,354 | free_alpha |
| `SLEEP_POD_SUEDE` | bucket_delta_b0 | 120 | 2 | 16,920 | -2,723 | mm_ask_off |
| `TRANSLATOR_SPACE_GRAY` | bucket_mean | 160 | 1 | 998 | -4,421 | unowned |
| `GALAXY_SOUNDS_BLACK_HOLES` | bucket_delta_b0 | 300 | 2 | 6,472 | -6,765 | mm_ask_off |

Single-day overfits to watch:

- `GALAXY_SOUNDS_SOLAR_FLAMES`: very high pooled day2 free-alpha shape corr
  (0.985) but day3 corr -0.625, day4 0.856 — pooled δ-corr 0.934 is misleading.
  The path-direction flips on day 3, so v7's edge 200 free-alpha gating is
  actually more conservative than the broad walk-forward result and likely
  correct. Don't lower the threshold.
- `ROBOT_VACUUMING`: free-alpha pooled δ-corr 0.844 but day-by-day pattern
  swings from -0.62 to +0.91 to +0.62. Sign-stable signal is the long bias,
  not the shape.
- `GALAXY_SOUNDS_BLACK_HOLES`: pooled δ-corr 0.926 but conflicting free-alpha
  add was previously rejected in v6 because it worsened the bundle. Walk-
  forward worst day -6,765. Confirms it should not be reactivated.
- `UV_VISOR_AMBER`: stab cross-day corr 0.50, all 4 buckets same-sign across
  days, but worst-day in proxy is -1,999. The shape is real but the level
  drifts; integration would need anchor-correcting.

---

## Notes on shape-vs-level

`bucket_delta_b0` (test-day bucket0 + avg train delta) is the path type that
most often hit all 3 folds positive across products (82 / 1400 rows). It
matches the existing `FREE_ALPHA` interpretation almost exactly — the only
difference is that v7 uses a fixed `base` per product while this proxy
re-anchors per day, which removes day-to-day intercept drift. If a product
shows `bucket_delta_b0 ≫ bucket_mean` in walk-forward PnL but a similar shape,
the `base` in `FREE_ALPHA` is stale and the gating should re-anchor.

Examples where `bucket_delta_b0` clearly beats `bucket_mean` at the same
threshold (test on `path_proxy_backtest_summary.csv`):

- `ROBOT_DISHES`: bucket_delta_b0 thr 80 worst +11,121; bucket_mean thr 80
  fails 3-fold gate.
- `PEBBLES_S`: bucket_delta_b0 thr 80 worst +7,368, bucket_mean thr 80 worst
  much lower.
- `UV_VISOR_RED`: bucket_delta_b0 thr 120 worst +13,271; bucket_mean thr 120
  fails 3-fold gate.

This argues that for the next agent, when adding new free-alpha-style products,
the safer parameterisation is "shape from history, anchor from today" rather
than "fixed base + fixed deltas".

---

## Suggested next-agent test order

1. Add `PEBBLES_S` `bucket_delta_b0` thr 80 (or 120/200) as a free-alpha-style
   overlay; v7 ownership is clean.
2. Add `ROBOT_DISHES` `bucket_delta_b0` thr 80 as a group-residual overlay;
   v7 ownership is clean.
3. Try `UV_VISOR_ORANGE` `group_scaled` thr 200 — moderate trade volume, all
   3 folds positive, nothing else owns it.
4. Conflict-aware retests for already-owned products with strong proxy results
   (`MICROCHIP_SQUARE`, `UV_VISOR_RED`, `PEBBLES_L`, `SLEEP_POD_LAMB_WOOL`):
   compare current sleeve PnL against a `bucket_delta_b0` overlay at threshold
   80–160 with side-gating.
5. Group-residual investigation for `PANEL` family — `PANEL_2X4` already
   ask-off but the group-relative shape (R² 0.94 on scale residual stability)
   suggests a tighter MR sleeve might be more profitable than spread capture.

None of these is promotion-ready. They are the highest-priority candidates the
next agent should run through `prosperity4btx trader.py 5 --merge-pnl` after
configurable integration similar to v6/v7.

---

## Integration update

The suggested re-anchored hidden-path test was implemented in
`strategies/round5/v8-reanchor-configurable.py` and promoted in compact form as
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v10.py`.

Important correction from live integration: offline proxy rankings are only
candidate generators. Several high-ranked names lost once they displaced the
current MM/residual sleeves.

Validated additions versus v8 **+1,234,316**:

| case | total | delta vs v8 | day2 | day3 | day4 |
|---|---:|---:|---:|---:|---:|
| `ROBOT_DISHES` | 1,287,135 | +52,819 | 413,228 | 391,797 | 482,110 |
| `OXYGEN_SHAKE_MINT` | 1,257,734 | +23,418 | 441,541 | 384,658 | 431,535 |
| `SNACKPACK_STRAWBERRY` | 1,244,575 | +10,259 | 422,630 | 383,084 | 438,862 |
| `SNACKPACK_CHOCOLATE` | 1,237,322 | +3,006 | 421,872 | 386,638 | 428,812 |
| winner bundle | 1,323,819 | +89,503 | 444,338 | 384,488 | 494,994 |

Winner bundle:
`ROBOT_DISHES,OXYGEN_SHAKE_MINT,SNACKPACK_STRAWBERRY,SNACKPACK_CHOCOLATE`.

Rejected after integration:
`PEBBLES_S`, `UV_VISOR_ORANGE`, `SLEEP_POD_NYLON`, `PANEL_4X4`,
`OXYGEN_SHAKE_EVENING_BREATH`, `PANEL_1X2`, and the all-10 bundle.

Promoted root `trader.py` now scores **+1,323,819** and diagnostics
`--match-trades none` / `worse` both score **+807,030**.
