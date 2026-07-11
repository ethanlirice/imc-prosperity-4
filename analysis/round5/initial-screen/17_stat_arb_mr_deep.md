# Round 5 Stat-Arb Mean-Reversion Deep Scan

Validation is leave-one-day-out: fit on two of days 2, 3, 4 and test the held-out day, then require all three held-out days to be stable. Execution proxy trades only the target leg, crosses top of book on entry/exit, uses quantity 10, and allows one open position per candidate.

Broad screen covered 2350 candidate residual definitions. Parameter sweep covered 120 best-per-group/product/lens definitions across centers, z thresholds, horizons, exits, velocity gates, and volatility regimes.

Current v3 isolated-spec proxy total PnL is 136710 across 222 trades. Sum of isolated min-day PnL is 7390; this is not a portfolio conflict simulation, but it matches the same target-only crossing-cost proxy used below.

## Top Robust Candidates By Worst Day

| lens          | group     | target           | center_mode   |   threshold |   horizon | exit_rule   | slope_mode   | vol_mode   |   total_pnl |   min_day_pnl |   total_trades |   win_pct |   avg_pnl_per_trade |
|:--------------|:----------|:-----------------|:--------------|------------:|----------:|:------------|:-------------|:-----------|------------:|--------------:|---------------:|----------:|--------------------:|
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         1.5 |       500 | fixed       | any          | any        |       58540 |         18040 |             41 |    0.6829 |             1427.8  |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | reverting    | any        |       60940 |         17330 |             29 |    0.7241 |             2101.38 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | reverting    | low_vol    |       60940 |         17330 |             29 |    0.7241 |             2101.38 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       200 | fixed       | reverting    | any        |       51270 |         16960 |             51 |    0.6667 |             1005.29 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       200 | fixed       | reverting    | low_vol    |       51270 |         16960 |             51 |    0.6667 |             1005.29 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       200 | zero_cross  | reverting    | any        |       51270 |         16960 |             51 |    0.6667 |             1005.29 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       200 | zero_cross  | reverting    | low_vol    |       51270 |         16960 |             51 |    0.6667 |             1005.29 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | fixed       | any          | any        |       57050 |         16240 |             53 |    0.6981 |             1076.42 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | zero_cross  | any          | any        |       57050 |         16240 |             53 |    0.6981 |             1076.42 |
| integer_combo | PEBBLES   | PEBBLES_XL       | rolling500    |         2   |       500 | fixed       | reverting    | any        |       50200 |         16000 |             18 |    0.6111 |             2788.89 |
| integer_combo | PEBBLES   | PEBBLES_XL       | rolling500    |         2   |       500 | fixed       | reverting    | low_vol    |       50200 |         16000 |             18 |    0.6111 |             2788.89 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         1.5 |       500 | fixed       | reverting    | high_vol   |       55400 |         15870 |             32 |    0.6562 |             1731.25 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         1.5 |       500 | fixed       | any          | high_vol   |       62140 |         15810 |             34 |    0.6765 |             1827.65 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         1.5 |       500 | zero_cross  | any          | high_vol   |       58150 |         15810 |             34 |    0.6765 |             1710.29 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | zero_cross  | reverting    | any        |       54890 |         15710 |             29 |    0.7241 |             1892.76 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | zero_cross  | reverting    | low_vol    |       54890 |         15710 |             29 |    0.7241 |             1892.76 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         2   |       500 | fixed       | reverting    | high_vol   |       54830 |         15690 |             26 |    0.6923 |             2108.85 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         2   |       500 | zero_cross  | reverting    | high_vol   |       54830 |         15690 |             26 |    0.6923 |             2108.85 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | fixed       | reverting    | any        |       58920 |         15310 |             51 |    0.7059 |             1155.29 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | zero_cross  | reverting    | any        |       58920 |         15310 |             51 |    0.7059 |             1155.29 |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         2   |       500 | fixed       | any          | high_vol   |       54340 |         15280 |             26 |    0.6923 |             2090    |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         2   |       500 | zero_cross  | any          | high_vol   |       54340 |         15280 |             26 |    0.6923 |             2090    |
| integer_combo | PEBBLES   | PEBBLES_XL       | rolling500    |         2   |       500 | fixed       | any          | any        |       53160 |         14930 |             22 |    0.5909 |             2416.36 |
| integer_combo | PEBBLES   | PEBBLES_XL       | rolling500    |         2   |       500 | fixed       | any          | low_vol    |       53160 |         14930 |             22 |    0.5909 |             2416.36 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | any          | any        |       59120 |         14830 |             30 |    0.6667 |             1970.67 |

## Top Robust Candidates By Total PnL

| lens          | group     | target           | center_mode   |   threshold |   horizon | exit_rule   | slope_mode   | vol_mode   |   total_pnl |   min_day_pnl |   total_trades |   win_pct |
|:--------------|:----------|:-----------------|:--------------|------------:|----------:|:------------|:-------------|:-----------|------------:|--------------:|---------------:|----------:|
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       500 | fixed       | reverting    | any        |       73140 |           500 |             29 |    0.7241 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       500 | zero_cross  | reverting    | any        |       73140 |           500 |             29 |    0.7241 |
| pca1_residual | PEBBLES   | PEBBLES_XL       | rolling500    |         1.5 |       500 | zero_cross  | any          | any        |       68710 |          9950 |             43 |    0.7209 |
| pca1_residual | PEBBLES   | PEBBLES_XL       | rolling500    |         1.5 |       500 | zero_cross  | any          | low_vol    |       68710 |          9950 |             43 |    0.7209 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       200 | fixed       | reverting    | any        |       67800 |           500 |             65 |    0.6308 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       200 | zero_cross  | reverting    | any        |       67800 |           500 |             65 |    0.6308 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2   |       500 | fixed       | any          | any        |       65300 |           520 |             43 |    0.6279 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2   |       500 | zero_cross  | any          | any        |       65300 |           520 |             43 |    0.6279 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       100 | fixed       | reverting    | any        |       62380 |           500 |            123 |    0.561  |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2.5 |       100 | zero_cross  | reverting    | any        |       62380 |           500 |            123 |    0.561  |
| pca2_residual | MICROCHIP | MICROCHIP_SQUARE | raw           |         1.5 |       500 | fixed       | any          | high_vol   |       62140 |         15810 |             34 |    0.6765 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2   |       200 | fixed       | any          | any        |       61850 |          1750 |            103 |    0.5631 |
| integer_combo | PEBBLES   | PEBBLES_XL       | raw           |         2   |       200 | zero_cross  | any          | any        |       61850 |          1750 |            103 |    0.5631 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | fixed       | reverting    | high_vol   |       61200 |         11150 |             45 |    0.7111 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | zero_cross  | reverting    | high_vol   |       61200 |         11150 |             45 |    0.7111 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | reverting    | any        |       60940 |         17330 |             29 |    0.7241 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | reverting    | low_vol    |       60940 |         17330 |             29 |    0.7241 |
| pca1_residual | PEBBLES   | PEBBLES_XL       | rolling500    |         1.5 |       200 | fixed       | any          | any        |       60370 |         10790 |             59 |    0.5254 |
| pca1_residual | PEBBLES   | PEBBLES_XL       | rolling500    |         1.5 |       200 | fixed       | any          | low_vol    |       60370 |         10790 |             59 |    0.5254 |
| pair_ols      | MICROCHIP | MICROCHIP_SQUARE | open100       |         1.5 |       500 | fixed       | any          | any        |       60190 |          7290 |             24 |    0.75   |
| pair_ols      | MICROCHIP | MICROCHIP_SQUARE | open100       |         1.5 |       500 | fixed       | any          | low_vol    |       60190 |          7290 |             24 |    0.75   |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | fixed       | any          | high_vol   |       59530 |         11050 |             46 |    0.6957 |
| integer_combo | PEBBLES   | PEBBLES_XS       | raw           |         1.5 |       500 | zero_cross  | any          | high_vol   |       59530 |         11050 |             46 |    0.6957 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | any          | any        |       59120 |         14830 |             30 |    0.6667 |
| pca2_residual | PEBBLES   | PEBBLES_S        | expanding     |         1.5 |       500 | fixed       | any          | low_vol    |       59120 |         14830 |             30 |    0.6667 |

## Parameter Plateaus

| lens          | group         | target                      |   robust_param_count |   best_total_pnl |   best_min_day_pnl |   best_trades | best_center_mode   |   best_threshold |   best_horizon | thresholds_passing   | horizons_passing   |
|:--------------|:--------------|:----------------------------|---------------------:|-----------------:|-------------------:|--------------:|:-------------------|-----------------:|---------------:|:---------------------|:-------------------|
| integer_combo | PEBBLES       | PEBBLES_XS                  |                  188 |            57050 |              16240 |            53 | raw                |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |
| pca1_residual | PEBBLES       | PEBBLES_S                   |                  172 |            55680 |              12840 |            29 | expanding          |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca2_residual | PEBBLES       | PEBBLES_S                   |                  144 |            60940 |              17330 |            29 | expanding          |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca2_residual | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |                  142 |            27210 |               7350 |            32 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca2_residual | ROBOT         | ROBOT_IRONING               |                  142 |            24250 |               7100 |            29 | raw                |              2   |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |                  136 |            20630 |               6110 |            57 | raw                |              1.5 |            200 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | ROBOT         | ROBOT_DISHES                |                  130 |            16840 |               5000 |            27 | open100            |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |
| pair_ols      | SNACKPACK     | SNACKPACK_CHOCOLATE         |                  122 |            19520 |               3640 |            29 | open100            |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |
| integer_combo | MICROCHIP     | MICROCHIP_OVAL              |                  120 |            49150 |              12200 |            51 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca2_residual | SLEEP_POD     | SLEEP_POD_POLYESTER         |                  120 |            34380 |               9020 |            38 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| basket_1v4    | SLEEP_POD     | SLEEP_POD_POLYESTER         |                  116 |            38900 |              11800 |            40 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pair_ols      | SLEEP_POD     | SLEEP_POD_POLYESTER         |                  116 |            24940 |               7980 |            24 | raw                |              2   |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca2_residual | MICROCHIP     | MICROCHIP_SQUARE            |                  114 |            58540 |              18040 |            41 | raw                |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |
| integer_combo | PANEL         | PANEL_2X4                   |                  112 |            26070 |               7290 |            51 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | SLEEP_POD     | SLEEP_POD_POLYESTER         |                  108 |            46850 |              13160 |            38 | raw                |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | SNACKPACK     | SNACKPACK_CHOCOLATE         |                  106 |            10870 |               2410 |            31 | open100            |              1.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pair_ols      | SNACKPACK     | SNACKPACK_RASPBERRY         |                  104 |            31750 |               9040 |            29 | raw                |              1.5 |            500 | 1.5,2.0              | 100,200,500        |
| basket_1v4    | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |                  104 |            22300 |               5290 |            27 | raw                |              2.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| basket_1v4    | ROBOT         | ROBOT_IRONING               |                  104 |            20100 |               2900 |            27 | raw                |              2.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | SNACKPACK     | SNACKPACK_RASPBERRY         |                   98 |            30780 |               8030 |            25 | open100            |              1.5 |            500 | 1.5,2.0              | 100,200,500        |
| pca2_residual | PEBBLES       | PEBBLES_M                   |                   98 |            22460 |               6230 |            24 | raw                |              2.5 |            500 | 1.5,2.0,2.5,3.0      | 100,200,500        |
| pca1_residual | TRANSLATOR    | TRANSLATOR_ECLIPSE_CHARCOAL |                   96 |            17380 |               5510 |            24 | raw                |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |
| basket_1v4    | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |                   90 |            31890 |               6680 |            20 | raw                |              2   |            500 | 1.5,2.0,2.5          | 100,200,500        |
| pca2_residual | ROBOT         | ROBOT_DISHES                |                   90 |            19220 |               3900 |            20 | raw                |              2   |            500 | 1.5,2.0,2.5          | 100,200,500        |
| pair_ols      | GALAXY_SOUNDS | GALAXY_SOUNDS_DARK_MATTER   |                   90 |            16250 |               3020 |            20 | raw                |              1.5 |            500 | 1.5,2.0,2.5          | 100,200,500        |

## Robust Candidate Counts By Lens

| lens          |   robust_candidate_count |
|:--------------|-------------------------:|
| pair_ols      |                       39 |
| pca1_residual |                       28 |
| pca2_residual |                       21 |
| integer_combo |                       15 |
| basket_1v4    |                       14 |

## Rejected Ideas

| scope   | lens          |   candidates |   robust_candidates |   best_total_pnl |   best_min_day_pnl |   best_positive_days | verdict            |
|:--------|:--------------|-------------:|--------------------:|-----------------:|-------------------:|---------------------:|:-------------------|
| screen  | basket_1v4    |           50 |                   5 |            30200 |               7160 |                    3 | kept for sweep     |
| screen  | integer_combo |         2000 |                  62 |            41590 |              11660 |                    3 | kept for sweep     |
| screen  | pair_ols      |          200 |                  37 |            20080 |               6550 |                    3 | kept for sweep     |
| screen  | pca1_residual |           50 |                  10 |            31890 |               6740 |                    3 | kept for sweep     |
| screen  | pca2_residual |           50 |                   8 |            23670 |               5500 |                    3 | kept for sweep     |
| sweep   | basket_1v4    |           14 |                  14 |            38900 |              11800 |                    3 | candidate-specific |
| sweep   | integer_combo |           16 |                  15 |            57050 |              16240 |                    3 | candidate-specific |
| sweep   | pair_ols      |           41 |                  39 |            47010 |              12190 |                    3 | candidate-specific |
| sweep   | pca1_residual |           28 |                  28 |            46850 |              13160 |                    3 | candidate-specific |
| sweep   | pca2_residual |           21 |                  21 |            58540 |              18040 |                    3 | candidate-specific |

## Notes

- The strongest rows are still target-only proxies; no hedge-leg fills are assumed. A deployable change should check portfolio conflicts before replacing v3 specs.
- `open100`, rolling, and expanding centers are included to avoid relying on held-out day intercepts. Robust rows that only pass under `raw` should be treated as lower quality.
- Velocity gates distinguish entries while residuals are already reverting versus still extending. Volatility regimes split on train-only rolling residual volatility median.