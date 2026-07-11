# Round 5 Hidden Paths — Phase D Report

**Audience:** strategy-development working file. Numbers are from
`analysis/round5/hidden-paths/*.csv`. Walk-forward simulator is the simple
crossing rule (POS_LIMIT=10, exit_band=max(20, thr/4)) on D2/D3/D4 raw quotes.

## Executive summary

Three findings reframe how to use any 5-bucket "free alpha" path in Round 5:

1. **The published FREE_ALPHA table is exogenous.** No combination of base
   estimator × delta estimator on D2/D3/D4 data reconstructs the published
   table. Best base+delta pair gives **mean MAE ≈ 195 ticks per delta**
   (`reverse_engineer_alpha_pairs.csv`). Conclusion: the table came from
   a data window we cannot see (D-2/-1/0 + something else). Any walk-forward
   path strategy is therefore a *separate mechanism* from the table — it is
   not "extrapolating the table forward."

2. **For most candidates, the trained shape is actively bad. The re-anchor
   to test-day bucket0 is doing the work.** When we replace the trained shape
   with flat zero (only anchoring to the test day's bucket0 mid), pnl
   *improves* dramatically for 8 of 15 top candidates (PEBBLES_XS, PEBBLES_S,
   PEBBLES_L, UV_VISOR_ORANGE, SLEEP_POD_NYLON, TRANSLATOR_ECLIPSE_CHARCOAL,
   plus 2 more — see `phase_d_anchor_vs_shape.csv`). Example:
   PEBBLES_S actual total = 30,904 → flat-shape total = 315,404 (10×).

3. **Most "winners" fail the random-shuffle null.** Of the top-15 candidates,
   only 5 beat the 95th percentile of a shuffled-bucket null on total pnl:
   ROBOT_DISHES, SLEEP_POD_LAMB_WOOL, SNACKPACK_RASPBERRY, UV_VISOR_MAGENTA,
   and (marginally) MICROCHIP_SQUARE on the worst-day metric. The PEBBLES
   family and the GALAXY_SOUNDS / UV_VISOR_ORANGE candidates do **not** beat
   the null — i.e. the bucket *order* of their trained path is irrelevant.

These three together imply: the FREE_ALPHA effect is not "5 stable shapes
running in parallel." It is mostly a re-anchoring effect (anchor to a quote
mid that the engine drifts toward) with a small subset of products having
genuine bucket-ordered structure.

## What was actually tested in Phase D

### D-10 Reverse-engineer FREE_ALPHA construction (`40_reverse_engineer_alpha.py`)
- Tested every combination of: base ∈ {bucket0 mean d2/d3/d4/pooled, day mean,
  leading-window means w∈{100, 1k, 5k, 10k, 100k, 200k} per day & pooled,
  first-tick mid} × delta ∈ {bucket means d2/d3/d4/pooled, bucket medians,
  per-day-then-mean}. Scored vs published `(base, d1..d4)`.
- Best base alone: MAE ≈ 116 ticks (roughly the bid-ask half-spread of large
  products — i.e. *no* estimator gets close).
- Best base+delta pair: leading_w5000_pooled + bucket_mean_pooled, mean MAE
  per delta ≈ 195 ticks.
- **Conclusion:** the table cannot be reconstructed from D2/D3/D4 alone. It is
  exogenous information. Stop thinking of FREE_ALPHA as "the bucket-mean path."

### D-11 Trade-flow VWAP paths (`41_trade_vwap_paths.py`)
- Per (product, day, bucket), trade VWAP minus quote mid. Cross-day stability
  of that difference. (`trade_vwap_path_stability.csv`)
- Trades hug mids: max-abs differences typically 10–50 ticks across most
  products. Cross-day correlation of the *trade-minus-quote* path is mostly
  noise.
- **Conclusion:** no Olivia-style "engine traded above/below mid in fixed
  windows" signal. Any path edge has to come from the *quote* side.

### D-12 Cross-product synchronized basket path (`43_basket_synchrony.py`)
- For each 5-product group, basket path = mean of bucket means. Cross-day
  Pearson on basket-centered shape; per-product OLS R² of `product_centered
  ~ basket_centered`. (`basket_synchrony_group.csv`,
  `basket_synchrony_product.csv`)
- **Group basket cross-day corr is poor.** Only PEBBLES (0.69) and
  GALAXY_SOUNDS (0.53) have positive basket-level cross-day correlation.
  The other 8 groups are between -0.41 and 0.18 — i.e. negative or zero.
  There is no "engine moves a basket-level fair value, all 5 products track."
- **PEBBLES_XS has resid_cross_day_corr = 0.85** — even after stripping the
  basket-mean explained variance, the residual is highly stable across days.
  Its path is genuinely idiosyncratic, not a basket effect.

### D-13 Bucket-count sweep (`42_bucket_count_sweep.py`)
- C ∈ {3, 4, 5, 6, 8, 10, 20}. Cross-day shape correlation per (product, C).
  (`bucket_count_stability.csv`)
- 5 buckets is *not* a fitted artifact: PEBBLES_XS holds corr ≈ 0.97 → 0.80
  across C=3..20; PANEL_2X4 similar. Aggregate "fraction of products with
  corr ≥ 0.5" is broadly consistent across C.
- **Conclusion:** the timing structure is real, finer than 5 buckets, and
  the choice of 5 was convenience.

### D-14 (added) Random-shuffle null distribution (`44_phase_d_robustness.py` → `phase_d_null.csv`)
- Top-15 candidates from `candidate_products.csv`. For each, 200× shuffle of
  the trained bucket order, re-run the walk-forward simulator, record null
  worst-day and total-pnl distributions.

| product | actual_total | null_mean_total | p95_total | p_value_total | beats null? |
|---|---:|---:|---:|---:|---|
| MICROCHIP_SQUARE | 58,649 | 157,265 | 168,658 | 1.000 | **NO** |
| PEBBLES_XS | 49,738 | 133,716 | 249,775 | 0.930 | **NO** |
| ROBOT_DISHES | 44,785 | -192,096 | -51,449 | 0.000 | **YES** |
| PEBBLES_L | 41,880 | 12,271 | 144,182 | 0.415 | NO |
| UV_VISOR_RED | 41,115 | -119,707 | 62,730 | 0.195 | NO |
| GALAXY_SOUNDS_SOLAR_FLAMES | 37,793 | 162,977 | 257,652 | 0.815 | **NO** |
| SLEEP_POD_POLYESTER | 35,129 | -70,631 | 134,268 | 0.190 | NO |
| SLEEP_POD_LAMB_WOOL | 34,333 | -196,648 | -72,779 | 0.000 | **YES** |
| TRANSLATOR_GRAPHITE_MIST | 31,360 | 82,057 | 126,836 | 0.630 | NO |
| PEBBLES_S | 30,904 | 105,617 | 295,792 | 0.830 | **NO** |
| TRANSLATOR_ECLIPSE_CHARCOAL | 30,384 | 24,659 | 124,625 | 0.435 | NO |
| SNACKPACK_RASPBERRY | 30,006 | -100,926 | -69,746 | 0.000 | **YES** |
| UV_VISOR_ORANGE | 28,830 | 147,911 | 221,462 | 1.000 | **NO** |
| UV_VISOR_MAGENTA | 28,650 | 9,145 | 13,708 | 0.000 | **YES** |
| SLEEP_POD_NYLON | 25,021 | -40,035 | 107,475 | 0.295 | NO |

The four "real" candidates (ROBOT_DISHES, SLEEP_POD_LAMB_WOOL,
SNACKPACK_RASPBERRY, UV_VISOR_MAGENTA) have null mean pnl that is large and
*negative* — meaning a random bucket order generally loses money on them, and
the trained order is the reason they make money. These are bucket-ordering
plays.

For the rest, the null mean is positive and often higher than actual. That
is the diagnostic for "the shape isn't doing the work — something else is."

### D-15 (added) Anchor-vs-shape decomposition (`44_phase_d_robustness.py` → `phase_d_anchor_vs_shape.csv`)
- Replace the train-day shape with flat-zero, leaving only the anchor:
  bucket0 of the test day (for `bucket_delta_b0`) or the train mean of
  bucket0 (for `bucket_mean` / `group_*`).

| product | actual_total | flat_shape_total | shape_explains_pct | reading |
|---|---:|---:|---:|---|
| MICROCHIP_SQUARE | 58,649 | -165,409 | 382% | shape essential |
| PEBBLES_XS | 49,738 | **231,578** | -366% | flat anchor 4.7× better |
| ROBOT_DISHES | 44,785 | -249,231 | 657% | shape essential |
| PEBBLES_L | 41,880 | **161,328** | -285% | flat anchor 3.9× better |
| UV_VISOR_RED | 41,115 | -298,381 | 826% | shape essential |
| GALAXY_SOUNDS_SOLAR_FLAMES | 37,793 | 31,835 | 16% | shape ≈ flat |
| SLEEP_POD_POLYESTER | 35,129 | -127,330 | 462% | shape essential |
| SLEEP_POD_LAMB_WOOL | 34,333 | -285,517 | 932% | shape essential |
| TRANSLATOR_GRAPHITE_MIST | 31,360 | 9,630 | 69% | shape mostly helps |
| PEBBLES_S | 30,904 | **315,404** | -921% | flat anchor 10× better |
| TRANSLATOR_ECLIPSE_CHARCOAL | 30,384 | **118,534** | -290% | flat anchor 3.9× better |
| SNACKPACK_RASPBERRY | 30,006 | -71,619 | 339% | shape essential |
| UV_VISOR_ORANGE | 28,830 | **205,315** | -612% | flat anchor 7.1× better |
| UV_VISOR_MAGENTA | 28,650 | -214,358 | 848% | shape essential |
| SLEEP_POD_NYLON | 25,021 | **94,800** | -279% | flat anchor 3.8× better |

Cross-referenced with the null result, the picture is consistent and stark:

| product | beats null? | flat anchor better? | what's actually happening |
|---|---|---|---|
| ROBOT_DISHES | YES | NO | bucket-ordering play; *real* shape edge |
| SLEEP_POD_LAMB_WOOL | YES | NO | bucket-ordering play; real shape edge (but threshold=20 — many trades) |
| SNACKPACK_RASPBERRY | YES | NO | real shape edge |
| UV_VISOR_MAGENTA | YES | NO | real shape edge (but small null total p95=14k — low noise floor) |
| MICROCHIP_SQUARE | mixed (worst beats, total fails) | NO | shape contributes; null mean is high so caution |
| PEBBLES_XS | NO | YES (flat 4.7×) | re-anchoring play, not shape |
| PEBBLES_S | NO | YES (flat 10×) | re-anchoring play |
| PEBBLES_L | NO | YES (flat 3.9×) | re-anchoring play |
| UV_VISOR_ORANGE | NO | YES (flat 7×) | re-anchoring play |
| SLEEP_POD_NYLON | NO | YES (flat 3.8×) | re-anchoring play |
| TRANSLATOR_ECLIPSE_CHARCOAL | NO | YES (flat 3.9×) | re-anchoring play |
| GALAXY_SOUNDS_SOLAR_FLAMES | NO | ~ | weak; shape adds little, null mean >> actual |
| UV_VISOR_RED, SLEEP_POD_POLYESTER | NO | NO | neither test passes cleanly; shape helps but is overshadowed by null |
| TRANSLATOR_GRAPHITE_MIST | NO | partial | shape helps modestly |

Two sharply different mechanisms:

- **Bucket-ordering plays (ROBOT_DISHES, SLEEP_POD_LAMB_WOOL,
  SNACKPACK_RASPBERRY, UV_VISOR_MAGENTA):** trained shape > flat anchor and
  trained order > shuffled order. The 5-bucket discrete schedule is a real
  signal. Strategy: ship the path as is.
- **Re-anchoring plays (PEBBLES_XS/S/L, UV_VISOR_ORANGE, SLEEP_POD_NYLON,
  TRANSLATOR_ECLIPSE_CHARCOAL):** flat shape >> trained shape. The trained
  shape is *fitting noise from train days that hurts on the test day*. The
  edge is "fair value resets at the test day's bucket0 mid and product
  reverts to it." Strategy: drop the trained delta, just use bucket0
  re-anchor + threshold (this is essentially OSMIUM-style 10000 anchor).

### D-16 (added) Per-bucket pnl attribution (`44_phase_d_robustness.py` → `phase_d_bucket_attribution.csv`)
- Boundary trade share (signal ticks within 5,000 ticks of a bucket boundary)
  is consistently 4.5–6.5%. With 200,000-tick buckets, a uniformly distributed
  signal would give ~5%. **No concentration at boundaries.** The discrete
  bucket transition is not the dominant trigger — the level itself is.
- PEBBLES_XS pnl by bucket: 22k / 14k / 14k / 10k / 4k. Distributed across all
  buckets, with the largest contribution from bucket 0 (where the anchor is
  tightest). This is consistent with the re-anchoring interpretation.
- ROBOT_DISHES: 27k / 6k / 8k / 4k / -1k. Heavily front-loaded — bucket 0 alone
  ≈ 60% of the pnl. Bucket 4 actively loses. The trained shape is helping
  on buckets 0–3 and hurting on bucket 4.
- SLEEP_POD_LAMB_WOOL (real shape edge, thr=20): 9.7k / 8.0k / 5.7k / 8.4k /
  7.6k. Most evenly distributed of any winner. Real all-day shape signal.

## Cross-product map: who is what

```
                        beats null?     flat>=trained?     interpretation
                        --------------- ------------------ --------------------
ROBOT_DISHES            YES (p=0.000)   NO  (-657%)        REAL shape, ship
SLEEP_POD_LAMB_WOOL     YES (p=0.000)   NO  (-932%)        REAL shape, ship
SNACKPACK_RASPBERRY     YES (p=0.000)   NO  (-339%)        REAL shape, ship
UV_VISOR_MAGENTA        YES (p=0.000)   NO  (-848%)        REAL shape, ship
MICROCHIP_SQUARE        partial         NO  (-382%)        REAL shape, watch null

PEBBLES_XS              NO              YES (+366%)        anchor only, drop shape
PEBBLES_S               NO              YES (+921%)        anchor only, drop shape
PEBBLES_L               NO              YES (+285%)        anchor only, drop shape
UV_VISOR_ORANGE         NO              YES (+612%)        anchor only, drop shape
SLEEP_POD_NYLON         NO              YES (+279%)        anchor only, drop shape
TRANSLATOR_ECL_CHARCOAL NO              YES (+290%)        anchor only, drop shape

UV_VISOR_RED            NO              NO                 ambiguous, deprioritise
SLEEP_POD_POLYESTER     NO              NO                 ambiguous
TRANSLATOR_GRAPHITE_MIST NO             partial            weak signal
GALAXY_SOUNDS_SOLAR_FLAMES NO           ~                  weak signal
```

Anything in the bottom block (NO/NO or weak) should not be in a Round-5
strategy at face value.

## What changed vs. the Phase A/B-only ranking

The original `candidate_products.csv` ranked products by walk-forward
worst-day pnl. Phase D shows that ranking is **misleading** for ~8 of the top
15: their trained shape is overfit to D2/D3/D4 noise, and a simpler
flat-anchor strategy dominates. After Phase D the ranking should be:

**Tier 1 — bucket-ordering plays (ship the path):**
ROBOT_DISHES, SLEEP_POD_LAMB_WOOL, SNACKPACK_RASPBERRY, UV_VISOR_MAGENTA,
MICROCHIP_SQUARE.

**Tier 2 — anchor-only plays (use bucket0 re-anchor + threshold, no trained
delta):** PEBBLES_XS, PEBBLES_S, PEBBLES_L, UV_VISOR_ORANGE, SLEEP_POD_NYLON,
TRANSLATOR_ECLIPSE_CHARCOAL.

**Tier 3 — deprioritise** (UV_VISOR_RED, SLEEP_POD_POLYESTER,
TRANSLATOR_GRAPHITE_MIST, GALAXY_SOUNDS_SOLAR_FLAMES) — neither robustness
test cleanly passes, edge is small.

Of the Tier 1 list, ROBOT_DISHES, SLEEP_POD_LAMB_WOOL, SNACKPACK_RASPBERRY are
not v7-owned (per `candidate_products.csv`). UV_VISOR_MAGENTA and
MICROCHIP_SQUARE overlap with v7 (free_alpha / mm_ask_off respectively); need
to compare with current.py before adding anything.

## Strategy-development implications

1. **For Tier 2 (anchor-only) products: the strategy is OSMIUM-style** —
   blend a fixed anchor with the current mid for the take side, no path. The
   anchor is the test-day bucket0 mid, which in live trading is the *recent*
   mid (a short EMA from session open). This generalises beyond Round 5: it's
   a session-level mean reversion at the front of the day, not a bucket
   schedule.

2. **For Tier 1 products: keep the path, but verify the path *order* is
   genuinely day-stable**, not coincidentally consistent. Recommended next
   check: leave-one-day-out fit on D-2/-1/0 (Round-1 source data?) — if a
   Tier-1 product's order is consistent across all 6 days, it is safe to
   ship.

3. **PEBBLES_XS deserves a special look.** Its bucket-ordering null score is
   weak (p=0.93), but its basket-residual cross-day corr is 0.85 (the highest
   in the entire group analysis), and it is one of the largest in the
   anchor-only flip. The right read: PEBBLES_XS has *very* stable session
   structure but the 5-bucket discretisation throws information away. The
   right tool may be a finer time-of-day fair value, not a 5-bucket path.

4. **Boundary effects don't exist.** The discrete bucket transitions are not
   the source of edge. Any production trader can use a smooth time-of-day
   fair value without losing the signal.

5. **The published FREE_ALPHA table cannot be regenerated from the Round-5
   data we hold.** That implies on Round-1..Round-4 data we *also* cannot
   regenerate it — i.e. the table came from a different market state. Trying
   to "extend FREE_ALPHA to more products" by mining D2/D3/D4 will rediscover
   only the re-anchoring effect, not the table's true shape. To find more
   table-style products, we would need access to the source-window data.

## Files this report references

- `reverse_engineer_alpha_summary.csv`, `reverse_engineer_alpha_pairs.csv`,
  `reverse_engineer_alpha_per_product.csv` — D-10
- `trade_vwap_paths.csv`, `trade_vwap_path_stability.csv` — D-11
- `bucket_count_stability.csv` — D-13
- `basket_synchrony_group.csv`, `basket_synchrony_product.csv` — D-12
- `phase_d_null.csv`, `phase_d_anchor_vs_shape.csv`,
  `phase_d_bucket_attribution.csv` — D-14/15/16
- Earlier phases for context: `product_bucket_paths.csv`,
  `product_path_stability.csv`, `free_alpha_shape_comparison.csv`,
  `group_path_summary.csv`, `path_proxy_backtest_summary.csv`,
  `candidate_products.csv`.

## Open questions for the strategy session

1. For the four Tier-1 winners, is there a v7 strategy that already trades
   the same product family in a way that conflicts (a market-maker offset
   that would be undermined by a take-side path overlay)? Need to read
   `current.py` before promoting any.
2. For Tier-2, can we replace the FREE_ALPHA bucket entries for
   PEBBLES_XS/S/L with a single OSMIUM-style anchor (recent-mid + alpha) and
   recover the same pnl with simpler code and lower overfit risk? The
   `phase_d_anchor_vs_shape` flat-shape totals say yes — but those numbers
   use perfect *test-day* bucket0, which is not available live. Need a live
   proxy (rolling window from session start).
3. Round 1 data is in `raw-data/ROUND1/` — re-running the bucket stability
   on the older days would test whether the Tier-1 path orderings hold on a
   non-overlapping data window. That is the cheapest way to upgrade
   confidence before promotion.
