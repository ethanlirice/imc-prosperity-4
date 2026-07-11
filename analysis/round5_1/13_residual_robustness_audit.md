# Round 5 Residual Robustness Audit

Scope: days 2/3/4 only. This audit reruns 1-vs-4 residual trades with three variants: `ols_loo` fits coefficients and residual sigma only on the two non-test days; `demean_group_mean_loo` uses a simpler target-minus-peer-mean formula with train-day means only; `ols_all_days_leaky` intentionally fits all days as a leakage comparator. PnL uses quantity 10, one open trade per product, and a depth-aware 3-level VWAP for entry and exit.

Implementation checks:
- The prior `12_residual_trade_sim.py` avoids held-out coefficient and sigma leakage; this audit keeps that convention.
- The prior `11_residual_shock_execution.py` pooled tables use all days, and its leave-one-day-out rows still scale thresholds with all-day residual sigma. Treat those rows as discovery only.
- `fixed_horizon` is directly implementable by storing entry timestamp in `traderData`; `zero_cross` is also implementable if `traderData` stores the entry residual sign and recomputes the same residual each tick.
- Top-of-book quantity-10 fills are not always available. The accepted/rejected tables below use depth-aware VWAP; `top_short_trade_pct` reports how often entry/exit needed more than level 1.

## Strongest Findings

- **Accept SLEEP_POD_POLYESTER OLS residual, threshold 1.5, horizon 500.** Depth-aware held-out PnL is **+48,277** with zero-cross exit and **+38,540** with fixed-horizon exit. Day PnL for zero-cross is day 2 **+14,648**, day 3 **+9,528**, day 4 **+24,101** over **48** trades from **17,801** raw threshold signals. Thresholds **1.5/2/2.5/3** all stay positive on all three days, and the simpler demeaned peer-mean formula remains positive with **+22,318** total and **+1,976** minimum day PnL.
- **Accept UV_VISOR_MAGENTA only as a secondary, lower-capacity signal.** Threshold 1.5 / horizon 500 / fixed-horizon gives depth-aware day PnL **+4,802 / +11,080 / +5,320**, **+21,202** total, **36** trades, and the simple formula is also positive on all days (**+26,826**, min day **+3,940**). Parameter stability is weaker than SLEEP_POD_POLYESTER because only two threshold settings pass all days for the fixed-horizon rule.
- **Accept GALAXY_SOUNDS_SOLAR_WINDS only as marginal.** Threshold 1.5 / horizon 500 gives **+9,850** fixed-horizon PnL and **+9,870** zero-cross PnL, but day 2 contributes only **+210**. The simple formula is stronger (**+12,338**, min day **+3,890**), so this is real enough to keep on the list but not a primary allocation.
- **Do not accept GALAXY_SOUNDS_SOLAR_FLAMES despite high OLS PnL.** Held-out OLS threshold 2 / horizon 500 produces **+36,400** fixed-horizon PnL, but the same simple formula rule has minimum day **-529** and only **1** positive day. This is a plausible OLS-specific fit, not a robust formula-level signal.
- **Reject MICROCHIP_RECTANGLE as an implementation/overfit false positive.** Held-out OLS threshold 1.5 / horizon 500 shows **+34,009** zero-cross PnL and all three days positive, but it is stable at only threshold **1.5**, the simple same-rule PnL has min day **-8,507**, and **92.4%** of entry/exit events need more than level 1 for quantity 10.
- **Do not promote ROBOT_IRONING or TRANSLATOR_VOID_BLUE.** Both have positive held-out OLS grids, but the simple formula has zero-PnL days and ROBOT_IRONING requires deeper-than-top liquidity on roughly **86%+** of entry/exit events.

## Accepted OLS Candidates

| group         | target                    |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_trades |   depth_win_pct |   signal_count | stable_thresholds   |   simple_total_pnl_same_rule |   simple_min_day_pnl_same_rule |   top_short_trade_pct |
|:--------------|:--------------------------|------------:|----------:|:--------------|------------------:|--------------------:|---------------:|----------------:|---------------:|:--------------------|-----------------------------:|-------------------------------:|----------------------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER       |         1.5 |       500 | zero_cross    |             48277 |                9528 |             48 |          0.7708 |          17801 | 1.5,2,2.5,3         |                        22318 |                           1976 |                0.25   |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |         1.5 |       500 | fixed_horizon |             38540 |                6208 |             47 |          0.7447 |          17801 | 1.5,2,2.5,3         |                        20858 |                           1976 |                0.234  |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |         1.5 |       200 | zero_cross    |             33968 |                1731 |            102 |          0.5882 |          17801 | 1.5,2,2.5,3         |                        20487 |                            308 |                0.2892 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |         1.5 |       200 | fixed_horizon |             33230 |                1731 |            102 |          0.5882 |          17801 | 1.5,2,2.5,3         |                        20487 |                            308 |                0.2843 |
| UV_VISOR      | UV_VISOR_MAGENTA          |         1.5 |       500 | fixed_horizon |             21202 |                4802 |             36 |          0.5833 |          13476 | 1.5,2.5             |                        26826 |                           3940 |                0.0139 |
| UV_VISOR      | UV_VISOR_MAGENTA          |         1.5 |       500 | zero_cross    |             13772 |                 330 |             36 |          0.5833 |          13476 | 1.5,2,2.5           |                        26826 |                           3940 |                0.0139 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |         1.5 |       500 | zero_cross    |              9870 |                 210 |             40 |          0.5    |          16174 | 1.5,2.5,3           |                        12338 |                           3890 |                0      |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |         1.5 |       500 | fixed_horizon |              9850 |                 210 |             40 |          0.5    |          16174 | 1.5,2.5,3           |                        12338 |                           3890 |                0      |

## Tentative Candidates

| group         | target                     |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_trades |   signal_count | stable_thresholds   |   simple_total_pnl_same_rule |   simple_min_day_pnl_same_rule |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------------:|--------------------:|---------------:|---------------:|:--------------------|-----------------------------:|-------------------------------:|
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | fixed_horizon |             36400 |                4690 |             26 |           7870 | 1.5,2,2.5           |                         7571 |                           -529 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | zero_cross    |             35370 |                4690 |             26 |           7870 | 1.5,2,2.5           |                         7571 |                           -529 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | fixed_horizon |             34921 |                6950 |             37 |          14152 | 1.5,2,2.5,3         |                        14021 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | zero_cross    |             34902 |                4333 |             32 |          10295 | 1.5,2,2.5,3         |                        13598 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | fixed_horizon |             34772 |                4333 |             32 |          10295 | 1.5,2,2.5,3         |                        13598 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | zero_cross    |             34511 |                6950 |             37 |          14152 | 1.5,2,2.5,3         |                        14021 |                              0 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | zero_cross    |             33580 |                3292 |             41 |          15299 | 1.5,2,2.5           |                         8300 |                          -3810 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | fixed_horizon |             33170 |                3292 |             41 |          15299 | 1.5,2,2.5           |                         8300 |                          -3810 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | fixed_horizon |             32694 |                3467 |             69 |          10295 | 1.5,2,2.5,3         |                         7544 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | zero_cross    |             32694 |                3467 |             69 |          10295 | 1.5,2,2.5,3         |                         7544 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | fixed_horizon |             30013 |                7135 |             81 |          14152 | 1.5,2,2.5,3         |                         9880 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | zero_cross    |             30013 |                7135 |             81 |          14152 | 1.5,2,2.5,3         |                         9880 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       500 | fixed_horizon |             26925 |                3810 |             23 |           8402 | 1.5,2,2.5,3         |                        16186 |                              0 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       500 | zero_cross    |             26925 |                3810 |             23 |           8402 | 1.5,2,2.5,3         |                        16186 |                              0 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       200 | fixed_horizon |             26230 |                3160 |             52 |           7870 | 1.5,2,2.5           |                         3541 |                          -2589 |

## Rejected From Top OLS Set

| group         | target                     |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_trades |   signal_count | stable_thresholds   |   simple_total_pnl_same_rule |   simple_min_day_pnl_same_rule |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------------:|--------------------:|---------------:|---------------:|:--------------------|-----------------------------:|-------------------------------:|
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | zero_cross    |             34009 |               10988 |             33 |           8656 | 1.5                 |                         1632 |                          -8507 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | fixed_horizon |             33489 |                9921 |             33 |           8656 | 1.5                 |                         1632 |                          -8507 |
| SLEEP_POD     | SLEEP_POD_SUEDE            |         2.5 |       500 | fixed_horizon |             22204 |                2055 |             34 |          12472 | 2.5                 |                         5443 |                              0 |
| SLEEP_POD     | SLEEP_POD_SUEDE            |         2.5 |       500 | zero_cross    |             22204 |                2055 |             34 |          12472 | 2.5                 |                         5443 |                              0 |
| ROBOT         | ROBOT_IRONING              |         3   |       500 | fixed_horizon |             20581 |                1726 |             25 |           9111 | 1.5,2,2.5,3         |                            0 |                              0 |
| ROBOT         | ROBOT_IRONING              |         3   |       500 | zero_cross    |             20581 |                1726 |             25 |           9111 | 1.5,2,2.5,3         |                            0 |                              0 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL        |         1.5 |       500 | fixed_horizon |             20373 |                1169 |             22 |           6914 | 1.5                 |                          579 |                          -4325 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       200 | zero_cross    |             19380 |                5713 |             62 |           8656 | 1.5                 |                         1525 |                          -9037 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2.5 |       200 | fixed_horizon |             19190 |                3400 |             28 |           4505 | 1.5,2,2.5           |                        -2590 |                          -2590 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2.5 |       200 | zero_cross    |             19190 |                3400 |             28 |           4505 | 1.5,2,2.5           |                        -2590 |                          -2590 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL        |         1.5 |       200 | zero_cross    |             18615 |                3808 |             47 |           6914 | 1.5                 |                        -1115 |                          -5266 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL        |         1.5 |       200 | fixed_horizon |             18615 |                3808 |             47 |           6914 | 1.5                 |                        -1115 |                          -5266 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL        |         1.5 |       500 | zero_cross    |             18463 |                1169 |             22 |           6914 | 1.5                 |                          579 |                          -4325 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       200 | fixed_horizon |             18145 |                4478 |             62 |           8656 | 1.5                 |                         1525 |                          -9037 |
| ROBOT         | ROBOT_IRONING              |         3   |       200 | fixed_horizon |             16753 |                 979 |             58 |           9111 | 2.5,3               |                            0 |                              0 |

## Best Held-Out OLS Depth Rows

| group         | target                     |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_positive_days |   depth_trades |   signal_count |   buy_signals |   sell_signals |   top_short_trade_pct |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------------:|--------------------:|----------------------:|---------------:|---------------:|--------------:|---------------:|----------------------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | zero_cross    |             48277 |                9528 |                     3 |             48 |          17801 |          9873 |           7928 |                0.25   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | fixed_horizon |             38540 |                6208 |                     3 |             47 |          17801 |          9873 |           7928 |                0.234  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | fixed_horizon |             36400 |                4690 |                     3 |             26 |           7870 |          4753 |           3117 |                0      |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | zero_cross    |             35370 |                4690 |                     3 |             26 |           7870 |          4753 |           3117 |                0      |
| PEBBLES       | PEBBLES_M                  |         1.5 |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |            853 |           447 |            406 |                0.5    |
| PEBBLES       | PEBBLES_M                  |         2.5 |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |            853 |           447 |            406 |                0.5    |
| PEBBLES       | PEBBLES_M                  |         3   |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |            853 |           447 |            406 |                0.5    |
| PEBBLES       | PEBBLES_M                  |         2   |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |            853 |           447 |            406 |                0.5    |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | fixed_horizon |             34921 |                6950 |                     3 |             37 |          14152 |          9128 |           5024 |                0.4054 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | zero_cross    |             34902 |                4333 |                     3 |             32 |          10295 |          8405 |           1890 |                0.3438 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | fixed_horizon |             34772 |                4333 |                     3 |             32 |          10295 |          8405 |           1890 |                0.3438 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | zero_cross    |             34511 |                6950 |                     3 |             37 |          14152 |          9128 |           5024 |                0.4054 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | zero_cross    |             34009 |               10988 |                     3 |             33 |           8656 |          3010 |           5646 |                0.9242 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       200 | zero_cross    |             33968 |                1731 |                     3 |            102 |          17801 |          9873 |           7928 |                0.2892 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | zero_cross    |             33580 |                3292 |                     3 |             41 |          15299 |          9138 |           6161 |                0.0244 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | fixed_horizon |             33489 |                9921 |                     3 |             33 |           8656 |          3010 |           5646 |                0.9091 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       200 | fixed_horizon |             33230 |                1731 |                     3 |            102 |          17801 |          9873 |           7928 |                0.2843 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | fixed_horizon |             33170 |                3292 |                     3 |             41 |          15299 |          9138 |           6161 |                0.0244 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | fixed_horizon |             32694 |                3467 |                     3 |             69 |          10295 |          8405 |           1890 |                0.2464 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | zero_cross    |             32694 |                3467 |                     3 |             69 |          10295 |          8405 |           1890 |                0.2464 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | zero_cross    |             30013 |                7135 |                     3 |             81 |          14152 |          9128 |           5024 |                0.2963 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | fixed_horizon |             30013 |                7135 |                     3 |             81 |          14152 |          9128 |           5024 |                0.2963 |
| PEBBLES       | PEBBLES_S                  |         1.5 |       200 | fixed_horizon |             29859 |               -4266 |                     2 |            130 |            853 |           447 |            406 |                0.5038 |
| PEBBLES       | PEBBLES_S                  |         2.5 |       200 | fixed_horizon |             29859 |               -4266 |                     2 |            130 |            853 |           447 |            406 |                0.5038 |
| PEBBLES       | PEBBLES_S                  |         2   |       200 | fixed_horizon |             29859 |               -4266 |                     2 |            130 |            853 |           447 |            406 |                0.5038 |

## Best Simple Formula Rows

| group     | target              |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_positive_days |   depth_trades |   signal_count |
|:----------|:--------------------|------------:|----------:|:--------------|------------------:|--------------------:|----------------------:|---------------:|---------------:|
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       200 | zero_cross    |             48645 |                   0 |                     2 |             73 |          13494 |
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       200 | fixed_horizon |             48645 |                   0 |                     2 |             73 |          13494 |
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       500 | fixed_horizon |             48171 |                   0 |                     2 |             32 |          13494 |
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       500 | zero_cross    |             48171 |                   0 |                     2 |             32 |          13494 |
| PEBBLES   | PEBBLES_XL          |         3   |       500 | fixed_horizon |             45190 |                   0 |                     2 |             10 |           2324 |
| PEBBLES   | PEBBLES_XL          |         3   |       500 | zero_cross    |             45190 |                   0 |                     2 |             10 |           2324 |
| PEBBLES   | PEBBLES_XL          |         3   |       200 | fixed_horizon |             38554 |                   0 |                     2 |             20 |           2324 |
| PEBBLES   | PEBBLES_XL          |         3   |       200 | zero_cross    |             38554 |                   0 |                     2 |             20 |           2324 |
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       100 | zero_cross    |             34672 |                   0 |                     2 |            138 |          13494 |
| MICROCHIP | MICROCHIP_SQUARE    |         1.5 |       100 | fixed_horizon |             34672 |                   0 |                     2 |            138 |          13494 |
| SNACKPACK | SNACKPACK_RASPBERRY |         1.5 |       500 | fixed_horizon |             31794 |               10010 |                     3 |             23 |           3810 |
| PEBBLES   | PEBBLES_XL          |         3   |       100 | zero_cross    |             28584 |                   0 |                     2 |             34 |           2324 |
| PEBBLES   | PEBBLES_XL          |         3   |       100 | fixed_horizon |             28584 |                   0 |                     2 |             34 |           2324 |
| MICROCHIP | MICROCHIP_SQUARE    |         2   |       500 | fixed_horizon |             27467 |                   0 |                     2 |             21 |          10045 |
| MICROCHIP | MICROCHIP_SQUARE    |         2   |       500 | zero_cross    |             27467 |                   0 |                     2 |             21 |          10045 |
| SNACKPACK | SNACKPACK_RASPBERRY |         1.5 |       500 | zero_cross    |             27170 |                8570 |                     3 |             23 |           3810 |
| UV_VISOR  | UV_VISOR_MAGENTA    |         1.5 |       500 | zero_cross    |             26826 |                3940 |                     3 |             31 |          12254 |
| UV_VISOR  | UV_VISOR_MAGENTA    |         1.5 |       500 | fixed_horizon |             26826 |                3940 |                     3 |             31 |          12254 |
| PEBBLES   | PEBBLES_XL          |         1.5 |       500 | zero_cross    |             25790 |               -4590 |                     1 |             24 |          10580 |
| PEBBLES   | PEBBLES_XL          |         1.5 |       500 | fixed_horizon |             25790 |               -4590 |                     1 |             24 |          10580 |

## Leakage Comparator

| group         | target                     |   threshold |   horizon | exit_rule     |   depth_total_pnl |   depth_min_day_pnl |   depth_positive_days |   depth_trades |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------------:|--------------------:|----------------------:|---------------:|
| MICROCHIP     | MICROCHIP_TRIANGLE         |         1.5 |       500 | fixed_horizon |             41906 |                5872 |                     3 |             22 |
| MICROCHIP     | MICROCHIP_SQUARE           |         1.5 |       500 | fixed_horizon |             41292 |                6948 |                     3 |             20 |
| MICROCHIP     | MICROCHIP_SQUARE           |         1.5 |       500 | zero_cross    |             41120 |                6729 |                     3 |             20 |
| MICROCHIP     | MICROCHIP_TRIANGLE         |         1.5 |       500 | zero_cross    |             41057 |                6534 |                     3 |             23 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | fixed_horizon |             40244 |                2804 |                     3 |             25 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | zero_cross    |             39245 |                3904 |                     3 |             25 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | zero_cross    |             36440 |                8310 |                     3 |             16 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | fixed_horizon |             35240 |                7980 |                     3 |             16 |
| PEBBLES       | PEBBLES_M                  |         2   |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |
| PEBBLES       | PEBBLES_M                  |         2.5 |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |
| PEBBLES       | PEBBLES_M                  |         3   |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |
| PEBBLES       | PEBBLES_M                  |         1.5 |       500 | fixed_horizon |             35147 |               -4733 |                     2 |             58 |
| PANEL         | PANEL_2X4                  |         1.5 |       500 | zero_cross    |             34323 |                4295 |                     3 |             20 |
| PANEL         | PANEL_2X4                  |         1.5 |       500 | fixed_horizon |             34185 |                4295 |                     3 |             20 |
| MICROCHIP     | MICROCHIP_SQUARE           |         1.5 |       200 | fixed_horizon |             33834 |                -718 |                     2 |             38 |

## Day-By-Day Accepted Rows

| group         | target                    |   test_day |   threshold |   horizon | exit_rule     |   depth_pnl |   depth_trades |   depth_wins |   depth_signal_count |   depth_buy_signals |   depth_sell_signals |   depth_avg_hold |
|:--------------|:--------------------------|-----------:|------------:|----------:|:--------------|------------:|---------------:|-------------:|---------------------:|--------------------:|---------------------:|-----------------:|
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          2 |         1.5 |       500 | fixed_horizon |         210 |             11 |            5 |                 3976 |                3976 |                    0 |          466     |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          3 |         1.5 |       500 | fixed_horizon |        6500 |              9 |            5 |                 2953 |                1073 |                 1880 |          500     |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          4 |         1.5 |       500 | fixed_horizon |        3140 |             20 |           10 |                 9245 |                   0 |                 9245 |          481.35  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          2 |         1.5 |       500 | zero_cross    |         210 |             11 |            5 |                 3976 |                3976 |                    0 |          466     |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          3 |         1.5 |       500 | zero_cross    |        6520 |              9 |            5 |                 2953 |                1073 |                 1880 |          480.444 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS |          4 |         1.5 |       500 | zero_cross    |        3140 |             20 |           10 |                 9245 |                   0 |                 9245 |          481.35  |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          2 |         1.5 |       200 | fixed_horizon |       11994 |             46 |           24 |                 9167 |                9167 |                    0 |          200     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          3 |         1.5 |       200 | fixed_horizon |        1731 |             22 |           13 |                 3319 |                 706 |                 2613 |          200     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          4 |         1.5 |       200 | fixed_horizon |       19505 |             34 |           23 |                 5315 |                   0 |                 5315 |          197.353 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          2 |         1.5 |       200 | zero_cross    |       11994 |             46 |           24 |                 9167 |                9167 |                    0 |          200     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          3 |         1.5 |       200 | zero_cross    |        1731 |             22 |           13 |                 3319 |                 706 |                 2613 |          200     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          4 |         1.5 |       200 | zero_cross    |       20243 |             34 |           23 |                 5315 |                   0 |                 5315 |          195.618 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          2 |         1.5 |       500 | fixed_horizon |       14648 |             19 |           14 |                 9167 |                9167 |                    0 |          500     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          3 |         1.5 |       500 | fixed_horizon |        6208 |             12 |            8 |                 3319 |                 706 |                 2613 |          475.667 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          4 |         1.5 |       500 | fixed_horizon |       17684 |             16 |           13 |                 5315 |                   0 |                 5315 |          476.375 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          2 |         1.5 |       500 | zero_cross    |       14648 |             19 |           14 |                 9167 |                9167 |                    0 |          500     |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          3 |         1.5 |       500 | zero_cross    |        9528 |             12 |            9 |                 3319 |                 706 |                 2613 |          440.75  |
| SLEEP_POD     | SLEEP_POD_POLYESTER       |          4 |         1.5 |       500 | zero_cross    |       24101 |             17 |           14 |                 5315 |                   0 |                 5315 |          431.294 |
| UV_VISOR      | UV_VISOR_MAGENTA          |          2 |         1.5 |       500 | fixed_horizon |        4802 |              8 |            6 |                 3319 |                3319 |                    0 |          500     |
| UV_VISOR      | UV_VISOR_MAGENTA          |          3 |         1.5 |       500 | fixed_horizon |       11080 |              9 |            5 |                 1793 |                1688 |                  105 |          500     |
| UV_VISOR      | UV_VISOR_MAGENTA          |          4 |         1.5 |       500 | fixed_horizon |        5320 |             19 |           10 |                 8364 |                 124 |                 8240 |          497.053 |
| UV_VISOR      | UV_VISOR_MAGENTA          |          2 |         1.5 |       500 | zero_cross    |        4802 |              8 |            6 |                 3319 |                3319 |                    0 |          500     |
| UV_VISOR      | UV_VISOR_MAGENTA          |          3 |         1.5 |       500 | zero_cross    |        8640 |              9 |            5 |                 1793 |                1688 |                  105 |          442     |
| UV_VISOR      | UV_VISOR_MAGENTA          |          4 |         1.5 |       500 | zero_cross    |         330 |             19 |           10 |                 8364 |                 124 |                 8240 |          485.316 |
