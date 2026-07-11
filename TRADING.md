# TRADING.md
Validated strategy decisions.
Update only when a change is confirmed by backtest or a strategy rule is
directly supported by findings in `DATA.md`.

---

## ROBOT_DISHES shock takeover — PROMOTED (this session)

**Promoted file:** `strategies/round5/session/14g-v14-dishes-shock-takeover-hold30.py`,
copied to root `trader.py`.

**What it does:** v14 with a `ROBOT_DISHES` shock module that takes over from
re-anchor + reduce-only MM on any tick where the per-tick mid log return exceeds
0.5%. The module fades the move (size 10 to bid on up-jumps, size 10 to ask on
down-jumps), holds with a passive limit at the entry anchor, flips to the
opposite side on each subsequent shock, and flattens at touch only after a
30-tick gap with no further shock. While the module holds inventory, re-anchor
and reduce-only MM are suppressed for `ROBOT_DISHES`. While dormant, the v14
logic owns `ROBOT_DISHES` bit-identically to baseline.

**Why it's safe:** D2 and D3 saw zero qualifying shocks (per-tick |log_ret|>0.005
fires 0/0/740 times across D2/D3/D4 — see DATA.md). On those days the shock
module is provably inert and v14 logic runs untouched, so D2/D3 PnL is bit
identical to v14 baseline in default and in `--match-trades none / worse`.

**Backtest results, Round 5 D2-D4:**

| Run | Total | D2 / D3 / D4 |
|-----|-------|--------------|
| v14 baseline (`v14nn-strat-dev.py`) | **+1,370,720** | +447,335 / +397,392 / +525,994 |
| 14g promoted (`trader.py`)          | **+1,479,360** | +447,335 / +397,392 / +634,633 |
| Delta                                | **+108,640**  | 0 / 0 / +108,639 |

`--match-trades none`: **+958,900** (D2 +241,699 / D3 +247,979 / D4 +469,222),
delta vs v14 baseline `+860,639`: **+98,261**, again entirely on D4.

`--match-trades worse`: **+965,011** (D2 +241,699 / D3 +247,979 / D4 +475,333),
delta **+104,372**.

ROBOT_DISHES-only PnL by day: v14 baseline +3,856 / +15,438 / +50,593 (total
+69,887). Promoted candidate +3,856 / +15,438 / +159,232 (total +178,526). The
+108,640 portfolio delta equals the ROBOT_DISHES D4 delta dollar-for-dollar,
confirming the alpha is isolated to that product on that day.

**HOLD parameter sweep on the same candidate (D2/D3 unchanged across all):**

| HOLD | Total | D4 |
|------|-------|----|
| 20 (signal1 default) | +1,462,912 | +618,185 |
| 30 (promoted)        | **+1,479,360** | **+634,633** |
| 40                   | +1,474,344 | +629,618 |
| 50                   | +1,474,602 | +629,875 |
| 60                   | +1,475,712 | +630,986 |
| 75                   | +1,478,954 | +634,227 |
| 100                  | +1,478,156 | +633,430 |
| 150 / 200 / 500      | +1,473,414 | +628,687 (saturates) |

HOLD>=150 saturates to the same number because shock keeps re-firing
within typical D4 cluster gaps and never flattens. That ceiling matches the
"shock-only" candidate (`14d`, +1,473,628) within rounding, confirming
saturation = no v14 dishes contribution. HOLD=30 beats both extremes by ~+5k
because it lets v14 logic capture residual edge in the post-cluster tail.

**Rejected variants (kept under `strategies/round5/session/14[a-f]*`):**

| File | Total | Why rejected |
|------|-------|--------------|
| `14a-v14-dishes-shock-flat-gated.py` | +1,345,520 | Flat-only entry gate competed with re-anchor; D2/D3 OK but D4 -25k |
| `14b-v14-dishes-shock-priority.py` | +1,351,678 | Crossed at touch on revert (no passive exit); D2/D3 OK but D4 -19k |
| `14c-v14-dishes-shock-passive-exit.py` | +1,350,924 | Passive exit but missed flips when re-anchor entered first |
| `14d-v14-dishes-shock-only.py` | +1,473,628 | Shock owns DISHES every tick; loses D2 +3,856 and D3 +15,438 v14 baseline; D4 +172,794 |
| `14e-v14-dishes-shock-takeover.py` | +1,462,912 | Same takeover design as 14g, HOLD=20; sub-optimal hold (see sweep) |
| `14f-v14-dishes-shock-takeover-hold50.py` | +1,474,602 | HOLD=50; on plateau but ~5k below HOLD=30 |

**Pre-session DISHES experiments (kept for context):**

| File | Total | Why rejected |
|------|-------|--------------|
| `14-v14-robot-dishes-shock-endcap.py` | +971,736 | Endcap's `pos!=0 and not shock` flatten branch fired every tick re-anchor held inventory, destroying D2/D3 |
| `14-v14-robot-dishes-reanchor-edge-65.py` | +1,367,880 | Tighter edge regressed vs baseline |
| `14-v14-robot-dishes-reanchor-edge-100.py` | +1,343,188 | Wider edge regressed vs baseline |
| `strategies/round5/alt-strategies/signal1.py` | +595,827 | Full alt; non-DISHES sleeves much worse than v14's stack |

---

## Current promoted runtime

**File:** `trader.py` (matches
`strategies/round5/session/14g-v14-dishes-shock-takeover-hold30.py`).
**Status:** current active runtime.

Backtests:
- default `prosperity4btx trader.py 5 --merge-pnl`: **+1,479,360**
  day split **+447,335 / +397,392 / +634,633**
- `--match-trades none`: **+958,900** (D2 +241,699 / D3 +247,979 / D4 +469,222)
- `--match-trades worse`: **+965,011** (D2 +241,699 / D3 +247,979 / D4 +475,333)

Naming convention:
- Strategy filenames start with the iteration number
  (e.g. `14g-v14-dishes-shock-takeover-hold30.py`).

## Rejected Round 5 NN cross-pressure candidate

**File:** `strategies/round5/session/nn-cross-microchip-oval-v12-candidate.py`  
**Status:** rejected for primary promotion; keep as research-only.

Built from v11 and added one active sleeve from the same-group cross-pressure
scan:
`MICROCHIP_SQUARE` 100-tick move <= `-259.5` -> short `MICROCHIP_OVAL`, hold
1000 ticks.

Backtests:
- default `prosperity4btx ... 5 --merge-pnl`: **+1,349,478**, day split
  **+440,342 / +401,360 / +507,776**. This ties v11 exactly, so it does not
  improve the primary metric.
- `--match-trades none`: **+868,618**, day split
  **+251,049 / +241,647 / +375,922**.
- `--match-trades worse`: **+868,618**, same split.

Decision: do not promote to root `trader.py`. The diagnostic improvement is
interesting, but primary default score did not improve. Revisit as passive
`MICROCHIP_OVAL` skew or diagnostic-mode tuning, not as an active crossing
replacement.

## Promotion Method That Worked

Use this process before changing `trader.py`:

1. Start from the current best strategy, not from a clean skeleton.
2. Convert an alpha idea into a measurable offline proxy with day-by-day output.
3. Keep only candidates with stable per-day behavior and plausible execution
   after spread/position costs.
4. Integrate candidates in a configurable copy, one product or sleeve at a
   time, so product ownership conflicts are visible.
5. Compare against the current best using
   `prosperity4btx <candidate> 5 --merge-pnl`.
6. Promote only a compact non-configurable file after default mode improves and
   diagnostics (`--match-trades none`, `--match-trades worse`) are acceptable.

The v10 breakthrough followed this exactly:
- `free-alpha` / hidden-path tables suggested bucket fair-value paths.
- Offline walk-forward found candidates, but several failed after integration.
- The winning adjustment was **re-anchoring**: use historical bucket deltas but
  anchor to the current day's bucket-0 running mid.
- Add only products that improved the live integrated portfolio:
  `ROBOT_DISHES`, `OXYGEN_SHAKE_MINT`, `SNACKPACK_STRAWBERRY`,
  `SNACKPACK_CHOCOLATE`.

Current lesson: offline alpha is only a candidate generator. The real test is
whether it beats the existing owner/MM/MR/free-alpha stack after opportunity
cost and position-limit conflicts.

## Current Round 5 candidate: re-anchor v10

**File:** `trader.py` and
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v10.py`  
**Status:** promoted current best. Previous root saved as
`strategies/round5/trader_root_before_reanchor_v10.py`. `current.py` remains
the prior v7 baseline.

Primary backtest:
- `prosperity4btx trader.py 5 --merge-pnl`: **+1,323,819**
- Day split: **+444,338 / +384,488 / +494,994**
- Line count: **479**

Diagnostics:
- `--match-trades none`: **+807,030**
- `--match-trades worse`: **+807,030**

What changed versus v7:
- v8 MM refinement: per-product passive quote sizing plus
  `ROBOT_LAUNDRY` touch-MM coexistence. Standalone **+1,234,316**.
- v10 re-anchored hidden-path overlays for:
  `ROBOT_DISHES`, `OXYGEN_SHAKE_MINT`, `SNACKPACK_STRAWBERRY`,
  `SNACKPACK_CHOCOLATE`.

Rejected:
- `base-strategy-free-alpha-side-gated-mr-mm-event-v9.py`: hardcoded
  timestamp target schedule, **+877,992**.
- Broad re-anchor add-all and several single additions that lost after
  conflict-aware integration.

Next trading work should tune the four v10 re-anchor products before adding
new sleeves: threshold, exit edge, bucket-0 anchor calculation, and whether
each product should retain any passive MM side while the re-anchor sleeve is
active.

## Current Round 5 candidate: free-alpha side-gated MR v7

**File:** `strategies/round5/base-strategy-free-alpha-side-gated-mr-v7.py`  
**Status:** prior baseline. Root `trader.py` has since been promoted to v10.
Clean v7 is also saved as `strategies/round5/current.py`. Previous v7 root was
saved as `strategies/round5/trader_root_before_mr_v7.py`.

What it adds over v6:
- Direct rolling-anchor active MR for `PEBBLES_XL`, `PEBBLES_XS`,
  `MICROCHIP_TRIANGLE`, and `ROBOT_LAUNDRY`.
- MR products are removed from MM ownership; free-alpha/residual sleeves still
  run first, then MR, then MM.
- Root line count is **495**.

Primary backtest, Round 5 D2/D3/D4:
- `prosperity4btx trader.py 5 --merge-pnl` default match mode:
  **+1,196,202**
- Day split: **+408,451 / +376,792 / +410,959**
- Improvement over v6: **+110,076**

Diagnostics:
- `--match-trades none`: **+670,289**
- `--match-trades worse`: **+670,289**

Validated MR integration notes:
- Individual integrated deltas versus v6:
  - `PEBBLES_XL`: **+63,674**
  - `PEBBLES_XS`: **+31,420**
  - `MICROCHIP_TRIANGLE`: **+8,000**
  - `ROBOT_LAUNDRY`: **+6,982**
- Leave-one-out around all four confirmed every MR product contributes to the
  final bundle.

## Previous Round 5 candidate: free-alpha side-gated v6

**File:** `strategies/round5/base-strategy-free-alpha-side-gated-v6.py`  
**Status:** previous best Round 5 candidate. Previous root saved as
`strategies/round5/trader_root_before_free_alpha_side_gated_v6.py`.

What it does:
- Keeps the useful selected 1-vs-4 residual sleeves.
- Keeps the selected five-bucket free-alpha path overlay from v5.
- Adds four selected free-alpha products at entry edge **200**:
  `ROBOT_MOPPING`, `ROBOT_VACUUMING`, `SLEEP_POD_POLYESTER`,
  `TRANSLATOR_ECLIPSE_CHARCOAL`.
- Applies side-specific touch-MM gating:
  - bid-off: `MICROCHIP_OVAL`, `MICROCHIP_TRIANGLE`, `ROBOT_IRONING`,
    `TRANSLATOR_ASTRO_BLACK`, `UV_VISOR_AMBER`
  - ask-off: `GALAXY_SOUNDS_BLACK_HOLES`, `MICROCHIP_SQUARE`,
    `OXYGEN_SHAKE_GARLIC`, `PANEL_2X4`, `PEBBLES_XL`,
    `SLEEP_POD_SUEDE`, `UV_VISOR_RED`
- Primary backtest, Round 5 D2/D3/D4:
  - `prosperity4btx trader.py 5 --merge-pnl` default match mode:
    **+1,086,126**
  - Day split: **+401,596 / +316,338 / +368,192**
- Diagnostics:
  - `--match-trades none`: **+466,525**
  - `--match-trades worse`: **+466,525**

Validated ablation notes:
- Owner/side/free-alpha sweep completed **101 / 101** cases OK.
- Combined final bundle was leave-one-out checked; each accepted toggle
  improved combined PnL.
- Conflicting free-alpha adds for `GALAXY_SOUNDS_BLACK_HOLES` and `PEBBLES_XL`
  were rejected because they worsened the final bundle.

## Mean-reversion research status

**Status:** research-only; not promoted to `trader.py`.

New diagnostics in `analysis/round5/mean-reversion/` separate direct
product rolling-anchor MR from group-index MR and prior residual/stat-arb MR.
The first isolated active-entry/active-exit probe found stable candidates:
- `PEBBLES_XL` product rolling window **200**, z **2.5**, hold **500**:
  **+126,780**, day split **+19,620 / +38,640 / +68,520**.
- `PEBBLES_XS` product rolling window **1000**, z **3.0**, hold **500**:
  **+31,420**, day split **+9,650 / +9,490 / +12,280**.
- `MICROCHIP_TRIANGLE` product rolling window **1000**, z **2.5**,
  hold **500**: **+30,810**, day split **+6,325 / +10,233 / +14,252**.

Next MR step must be a v6-integrated configurable sleeve with product
ownership/conflict rules. It must beat **+1,086,126** on
`prosperity4btx trader.py 5 --merge-pnl` before promotion.

## Previous Round 5 candidate: free-alpha selected v5

**File:** `strategies/round5/base-strategy-free-alpha-selected-v5.py`  
**Status:** previous best Round 5 candidate. Previous root was saved as
`strategies/round5/trader_root_before_free_alpha_selected_v5.py`.

What it does:
- Keeps the useful selected 1-vs-4 residual sleeves.
- Keeps the selected touch passive/MM sleeve from the prior candidate.
- Adds a selective five-bucket free-alpha path overlay for products that were
  positive on all three sample days and beat their current product PnL.
- Primary backtest, Round 5 D2/D3/D4:
  - `prosperity4btx ... 5 --merge-pnl` default match mode: **+868,478**
  - Day split: **+306,588 / +225,446 / +336,444**

Free-alpha overlay products:
`GALAXY_SOUNDS_DARK_MATTER`, `GALAXY_SOUNDS_SOLAR_FLAMES`,
`GALAXY_SOUNDS_SOLAR_WINDS`, `PANEL_2X2`, `PEBBLES_L`,
`SLEEP_POD_COTTON`, `SLEEP_POD_LAMB_WOOL`, `SNACKPACK_PISTACHIO`,
`SNACKPACK_RASPBERRY`, `SNACKPACK_VANILLA`, `TRANSLATOR_GRAPHITE_MIST`,
`UV_VISOR_MAGENTA`, `UV_VISOR_YELLOW`.

Framework controls:
- `simple_mm_mr_all50_v1.py`: broad fair-skew/active MR lost **−1,239,202**.
- `simple_mm_all50_inside_v2.py`: pure all-50 inside MM made **+401,415**.
- `simple_mm_all50_touch_v3.py`: pure all-50 touch MM made **+476,800**.
- `base-strategy-touch-mm-v1.py`: touch quote level alone improved to
  **+581,939**.
- `base-strategy-touch-mm-target-select-v2.py`: target ownership switch
  improved to **+623,546**.
- `base-strategy-touch-mm-target-select-v3.py`: removes
  `TRANSLATOR_SPACE_GRAY`, **+627,758**.
- Broad `free_alpha_path_active_v1.py` best sweep made **+742,005** but was
  unstable; selective overlay v5 made **+868,478**.

Rejected recent variants:
- `base-strategy-3layer-v2.py`: added active pair sleeves and regressed to
  **+466,166**.
- `base-strategy-3layer-v3.py`: converted pairs to quote skew and tied
  **+534,757**, so it adds complexity without edge.

Next strategy effort should target v6-local refinements: side-specific touch
MM, free-alpha product/threshold ablations, and the new MR candidates only via
conflict-aware integration. Do not turn on broad all-product active crossing.

## Session Wrap-Up Update

New tooling prepared for fast promotion testing:
- `strategies/round5/base-strategy-free-alpha-configurable.py`
  - adds env toggles for product ownership and side gating:
    `ADD_FREE_ALPHA_PRODUCTS`, `DROP_FREE_ALPHA_PRODUCTS`,
    `DROP_MM_PRODUCTS`, `MM_BID_OFF_PRODUCTS`, `MM_ASK_OFF_PRODUCTS`,
    `MM_ONLY_PRODUCTS`, `FREE_ALPHA_EDGE_OVERRIDES`.
- Historical owner/side ablation runner
  - ran batched owner/side ablations; conclusions are summarized in `DATA.md` and detailed generated files were pruned.

Status: harness is ready; full sweep result is pending because the run was
interrupted before completion.

## Rejected Round 5 rolling TLS pair-fair tests

**Status:** research-only; not promoted.

Files:
- `strategies/round5/v10-tls-configurable.py`
- `analysis/round5/tls-pair-spreads/38_rolling_tls_target_scan.py`
- `analysis/round5/tls-pair-spreads/39_tls_integration_sweep.py`
- `analysis/round5/tls-pair-spreads/40_tls_passive_sweep.py`

Result versus v10 **+1,323,819**:
- Active rolling pair-fair replacements were negative for the main candidates.
- Best active case was only `ROBOT_VACUUMING/MOPPING` TLS at **+1,408**, with
  poor day stability.
- Best passive quote-skew case was `MICROCHIP_CIRCLE/SQUARE` TLS size 5/10 at
  **+2,146**, below promotion threshold.

Decision: do not add TLS/rolling-beta pair sleeves to `trader.py` yet. The
idea may still be useful later as a passive skew feature, but not as an active
crossing strategy or broad pair-trading layer.

## Round 5 v11 PEBBLES_L flat re-anchor replacement

Promoted one owned-product replacement from the hidden-path/Phase D findings.
`PEBBLES_L` now uses a flat bucket-0 re-anchor (`deltas=[0,0,0,0,0]`,
edge 80) instead of the fixed `FREE_ALPHA` path. This validates the Phase D
anchor-only read for `PEBBLES_L`, but not for the broader Tier 2 bundle.

Results:
- Previous v10: **+1,323,819**, day split **+444,338 / +384,488 / +494,994**.
- New root v11: **+1,349,478**, day split **+440,342 / +401,360 / +507,776**.
- Delta: **+25,659** total.
- `--match-trades none`: **+832,689**.
- `--match-trades worse`: **+832,689**.
- Line count: **480**.

Rejected/diagnosed in this pass:
- Full Phase D Tier 2 flat-anchor bundle
  (`PEBBLES_XS`, `PEBBLES_S`, `PEBBLES_L`, `UV_VISOR_ORANGE`,
  `SLEEP_POD_NYLON`, `TRANSLATOR_ECLIPSE_CHARCOAL`) regressed to
  **+1,207,514**. The offline anchor-only result does not survive portfolio
  ownership for most products.
- `PEBBLES_L` flat edge sweep with current v10 overlays:
  edge 20 **+1,322,346**, 40 **+1,336,340**, 80 **+1,349,478**,
  120 **+1,338,852**, 160 **+1,330,494**, 200 **+1,334,216**,
  300 **+1,309,732**. Edge 80 is retained.

Saved versions:
- Prior root before v11: `strategies/round5/trader_v8.py`.
- Promoted root copy: `strategies/round5/trader_v9.py` and
  `strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v11.py`.

## Round 5 v11 MM refinement candidate

**File:** `strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v12-mm-owned-imbalance.py`  
**Status:** best research candidate from independent MM pass; not copied to
`trader.py` in this session.

What changed versus v11:
- Add reduce-only touch MM coexistence for owned `PEBBLES_L`.
- Add reduce-only touch MM coexistence for owned `ROBOT_DISHES`.
- Add size-1 touch MM coexistence for owned `SNACKPACK_CHOCOLATE`.
- Add `MICROCHIP_CIRCLE` top-of-book imbalance filter at threshold **0.4**:
  skip bid if imbalance ≤ −0.4, skip ask if imbalance ≥ 0.4.

Results:
- v11 baseline: **+1,349,478**, day split
  **+440,342 / +401,360 / +507,776**.
- v12 MM candidate: **+1,355,002**, day split
  **+442,320 / +404,218 / +508,464**.
- Delta: **+5,524** total.
- `--match-trades none`: **+832,689**.
- `--match-trades worse`: **+832,689**.
- Line count: **496**.

Rejected MM changes:
- Re-enabling current one-sided MM gates all regressed; worst tested examples
  included `OXYGEN_SHAKE_GARLIC` ask-on **−35,564** and `MICROCHIP_OVAL`
  bid-on **−31,681**.
- Relaxing tested size caps all regressed; closest was `ROBOT_IRONING` size 2
  at **−50**.
- Imbalance filters on `PEBBLES_S` and `OXYGEN_SHAKE_GARLIC` regressed, while
  `MICROCHIP_SQUARE` had no effect.

Supporting outputs:
`analysis/round5/market-making-v11/v11_mm_contribution_by_product.csv`,
`v11_mm_rejected_changes.csv`, and `v11_mm_final_candidate_summary.csv`.

## Alternate trader compatibility cleanup

The alternate local trader file was preserved for research comparison; root
`trader.py` was restored to the original active runtime after the compatibility
experiment.

The removed half was a local CSV-backed planner using `prosperity4bt.datamodel`,
`os`, `pathlib`, `dataclasses`, `numpy`, `pandas`, environment variables, and
runtime `pd.read_csv`. That cannot run on the Prosperity site. The retained file
keeps only the self-contained V5 sleeve and uses local `datamodel` plus allowed
runtime imports.

Stripped uploadable copy:
- file: alternate V5 uploadable copy
- `prosperity4btx trader.py 5 --merge-pnl`: **+219,896**
  (**+114,859 / +28,666 / +76,371**)
- `--match-trades none`: **0**
- `--match-trades worse`: **+219,896**

Full local-only adapter:
- file: alternate full local backtest adapter
- preserves the CSV-backed planner, switches import to local `datamodel`, and
  points data lookup at `raw-data/ROUND5`
- `PYTHONPATH=. prosperity4btx <alternate_full_local_backtest.py> 5 --merge-pnl`:
  **+959,544** (**+397,930 / +296,758 / +264,856**)

Decision: the stripped uploadable copy loses most of the alternate strategy's
performance because the profitable planner is the non-uploadable CSV-reading
half. Treat the full local file as research only until its rules are distilled
into upload-safe logic.
