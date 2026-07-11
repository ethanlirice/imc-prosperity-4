# Round 5 Residual Portfolio Conflict Simulation

Portfolio-level simulation for the residual-shock candidates from `12_residual_trade_sim`. Entries cross the target leg at top of book with quantity 10. Each residual fit is leave-one-day-out: coefficients and residual sigma are trained on the two non-test days, then applied to the held-out day.

At each timestamp, all selected candidate signals are scored by training-day isolated robustness: positive training days, minimum training-day PnL, total training PnL, average PnL per trade, then current absolute z-score. The resolver accepts signals in that order while enforcing at most one active position per product; lower-priority signals for active products are skipped.

Candidate-set names beginning with `lodo_` are selected separately for each test day from the two non-test days only. `static12_` sets are diagnostic baselines selected from the full prior `12_*` robust table, while still using leave-one-day-out coefficients and day-specific training priority during execution.

## Portfolio Summary

| candidate_set                |   total_pnl |   min_day_pnl |   positive_days |   total_trades |   win_pct |   avg_pnl_per_trade |   avg_candidates |   signals_accepted |   signals_blocked_active |   conflict_rate |
|:-----------------------------|------------:|--------------:|----------------:|---------------:|----------:|--------------------:|-----------------:|-------------------:|-------------------------:|----------------:|
| static12_long_horizon_500    |      257180 |         69320 |               3 |            501 |    0.5888 |            513.333  |           63     |                501 |                   748755 |          0.9993 |
| static12_top_per_group       |      211980 |         64090 |               3 |            455 |    0.578  |            465.89   |            9     |                455 |                   113126 |          0.996  |
| static12_fast_horizon_le_100 |       92650 |         23160 |               3 |           1117 |    0.5219 |             82.9454 |           28     |               1117 |                   310373 |          0.9964 |
| static12_top3_overall        |       79710 |         19430 |               3 |             81 |    0.7037 |            984.074  |            3     |                 81 |                    35029 |          0.9977 |
| lodo_top_per_group           |       51270 |          8590 |               3 |            518 |    0.5097 |             98.9768 |           10     |                518 |                   123398 |          0.9958 |
| lodo_top3_overall            |       20660 |         -4150 |               2 |             50 |    0.62   |            413.2    |            3     |                 50 |                    13048 |          0.9962 |
| lodo_long_horizon_500        |      -67400 |       -112370 |               1 |           1035 |    0.4908 |            -65.1208 |          121.667 |               1035 |                  1836935 |          0.9994 |
| lodo_fast_horizon_le_100     |     -273590 |       -251530 |               0 |           3153 |    0.4577 |            -86.7713 |           90     |               3153 |                  1484077 |          0.9979 |

## Day By Day

| candidate_set                |   test_day |   n_candidates |   n_products |     pnl |   trades |   win_pct |   signals_seen |   signals_accepted |   signals_blocked_active |   max_concurrent_positions |
|:-----------------------------|-----------:|---------------:|-------------:|--------:|---------:|----------:|---------------:|-------------------:|-------------------------:|---------------------------:|
| lodo_fast_horizon_le_100     |          2 |             80 |           13 |  -16430 |      831 |    0.4789 |         525632 |                831 |                   524801 |                         11 |
| lodo_fast_horizon_le_100     |          3 |             54 |           12 |   -5630 |      495 |    0.5111 |         122104 |                495 |                   121609 |                          9 |
| lodo_fast_horizon_le_100     |          4 |            136 |           25 | -251530 |     1827 |    0.4335 |         839494 |               1827 |                   837667 |                         22 |
| lodo_long_horizon_500        |          2 |            115 |           24 |  -11770 |      373 |    0.5147 |         625133 |                373 |                   624760 |                         22 |
| lodo_long_horizon_500        |          3 |             91 |           17 |   56740 |      188 |    0.5319 |         244562 |                188 |                   244374 |                         14 |
| lodo_long_horizon_500        |          4 |            159 |           32 | -112370 |      474 |    0.4557 |         968275 |                474 |                   967801 |                         27 |
| lodo_top3_overall            |          2 |              3 |            1 |   -4150 |       19 |    0.4737 |            858 |                 19 |                      839 |                          1 |
| lodo_top3_overall            |          3 |              3 |            1 |    9170 |       12 |    0.75   |           5007 |                 12 |                     4995 |                          1 |
| lodo_top3_overall            |          4 |              3 |            2 |   15640 |       19 |    0.6842 |           7233 |                 19 |                     7214 |                          2 |
| lodo_top_per_group           |          2 |             10 |           10 |   29390 |      122 |    0.5246 |          43059 |                122 |                    42937 |                          8 |
| lodo_top_per_group           |          3 |             10 |           10 |   13290 |      209 |    0.488  |          33508 |                209 |                    33299 |                          8 |
| lodo_top_per_group           |          4 |             10 |           10 |    8590 |      187 |    0.5241 |          47349 |                187 |                    47162 |                          9 |
| static12_fast_horizon_le_100 |          2 |             28 |            8 |   35590 |      380 |    0.5105 |         143626 |                380 |                   143246 |                          6 |
| static12_fast_horizon_le_100 |          3 |             28 |            8 |   33900 |      298 |    0.5537 |          60966 |                298 |                    60668 |                          6 |
| static12_fast_horizon_le_100 |          4 |             28 |            8 |   23160 |      439 |    0.5103 |         106898 |                439 |                   106459 |                          7 |
| static12_long_horizon_500    |          2 |             63 |           14 |   89000 |      194 |    0.5928 |         292385 |                194 |                   292191 |                         12 |
| static12_long_horizon_500    |          3 |             63 |           14 |   98860 |      141 |    0.6099 |         159452 |                141 |                   159311 |                         11 |
| static12_long_horizon_500    |          4 |             63 |           14 |   69320 |      166 |    0.5663 |         297419 |                166 |                   297253 |                         12 |
| static12_top3_overall        |          2 |              3 |            2 |   25280 |       25 |    0.72   |          12013 |                 25 |                    11988 |                          2 |
| static12_top3_overall        |          3 |              3 |            2 |   19430 |       26 |    0.6538 |           9269 |                 26 |                     9243 |                          2 |
| static12_top3_overall        |          4 |              3 |            2 |   35000 |       30 |    0.7333 |          13828 |                 30 |                    13798 |                          2 |
| static12_top_per_group       |          2 |              9 |            9 |   68020 |      155 |    0.5548 |          44175 |                155 |                    44020 |                          7 |
| static12_top_per_group       |          3 |              9 |            9 |   79870 |      126 |    0.6429 |          26256 |                126 |                    26130 |                          7 |
| static12_top_per_group       |          4 |              9 |            9 |   64090 |      174 |    0.5517 |          43150 |                174 |                    42976 |                          8 |

## Best Robust Candidate Set

Best by positive held-out days, then minimum day PnL, then total PnL: `static12_long_horizon_500` with total PnL 257180, minimum day PnL 69320, and 3/3 positive days.

### Best Set Membership

| candidate_set             |   test_day | group         | target                      |   threshold |   horizon | exit_rule     |   train_min_day_pnl |   train_total_pnl |   train_total_trades |
|:--------------------------|-----------:|:--------------|:----------------------------|------------:|----------:|:--------------|--------------------:|------------------:|---------------------:|
| static12_long_horizon_500 |          2 | MICROCHIP     | MICROCHIP_RECTANGLE         |         1.5 |       500 | zero_cross    |               11090 |             22680 |                   27 |
| static12_long_horizon_500 |          2 | MICROCHIP     | MICROCHIP_RECTANGLE         |         1.5 |       500 | fixed_horizon |               10020 |             22170 |                   27 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_LAMB_WOOL         |         1.5 |       500 | fixed_horizon |                9590 |             19210 |                    8 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         1.5 |       500 | zero_cross    |                9570 |             33680 |                   29 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_LAMB_WOOL         |         1.5 |       500 | zero_cross    |                7680 |             17300 |                    8 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2   |       500 | fixed_horizon |                6970 |             23090 |                   19 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2   |       500 | zero_cross    |                6970 |             22680 |                   19 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         3   |       500 | fixed_horizon |                6880 |             19030 |                   21 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         3   |       500 | zero_cross    |                6880 |             19030 |                   21 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         1.5 |       500 | fixed_horizon |                6220 |             23910 |                   28 |
| static12_long_horizon_500 |          2 | UV_VISOR      | UV_VISOR_MAGENTA            |         1.5 |       500 | fixed_horizon |                5320 |             16400 |                   28 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2.5 |       500 | fixed_horizon |                5290 |             14040 |                    8 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2.5 |       500 | zero_cross    |                5290 |             14040 |                    8 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         2.5 |       500 | fixed_horizon |                4790 |             18490 |                   27 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         2.5 |       500 | zero_cross    |                4790 |             18490 |                   27 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2   |       500 | fixed_horizon |                4690 |             15080 |                   15 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2   |       500 | zero_cross    |                4690 |             15080 |                   15 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2.5 |       500 | zero_cross    |                4340 |             19320 |                   14 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2.5 |       500 | fixed_horizon |                4340 |             19190 |                   14 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         3   |       500 | fixed_horizon |                4160 |             10110 |                   22 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         3   |       500 | zero_cross    |                4160 |             10110 |                   22 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         3   |       500 | fixed_horizon |                3810 |             13200 |                    6 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         3   |       500 | zero_cross    |                3810 |             13200 |                    6 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2.5 |       500 | fixed_horizon |                3720 |             10080 |                   29 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2.5 |       500 | zero_cross    |                3720 |             10080 |                   29 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_DISHES                |         2.5 |       500 | fixed_horizon |                3480 |              8670 |                   10 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_DISHES                |         2.5 |       500 | zero_cross    |                3480 |              8670 |                   10 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2   |       500 | fixed_horizon |                3410 |              7790 |                   10 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2   |       500 | zero_cross    |                3410 |              7790 |                   10 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         1.5 |       500 | zero_cross    |                3320 |              9570 |                   26 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         1.5 |       500 | fixed_horizon |                3320 |              9570 |                   26 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         1.5 |       500 | zero_cross    |                3140 |              9660 |                   29 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         1.5 |       500 | fixed_horizon |                3140 |              9640 |                   29 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         3   |       500 | fixed_horizon |                2140 |              4470 |                   20 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         3   |       500 | zero_cross    |                2140 |              4470 |                   20 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         3   |       500 | fixed_horizon |                2100 |              4860 |                    3 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         3   |       500 | zero_cross    |                2100 |              4860 |                    3 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_SUEDE             |         2.5 |       500 | fixed_horizon |                2060 |             10000 |                   14 |
| static12_long_horizon_500 |          2 | SLEEP_POD     | SLEEP_POD_SUEDE             |         2.5 |       500 | zero_cross    |                2060 |             10000 |                   14 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         1.5 |       500 | fixed_horizon |                2040 |              6680 |                   36 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         1.5 |       500 | zero_cross    |                2040 |              6680 |                   36 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         1.5 |       500 | zero_cross    |                1800 |             22320 |                   34 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         1.5 |       500 | fixed_horizon |                1800 |             21820 |                   34 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         2   |       500 | fixed_horizon |                1800 |             17590 |                   31 |
| static12_long_horizon_500 |          2 | ROBOT         | ROBOT_IRONING               |         2   |       500 | zero_cross    |                1800 |             17590 |                   31 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         2.5 |       500 | fixed_horizon |                1670 |              3860 |                   22 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   |         2.5 |       500 | zero_cross    |                1670 |              3860 |                   22 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         1.5 |       500 | fixed_horizon |                1640 |              6840 |                   16 |
| static12_long_horizon_500 |          2 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         1.5 |       500 | zero_cross    |                1640 |              6800 |                   16 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2.5 |       500 | zero_cross    |                1410 |              8410 |                    8 |
| static12_long_horizon_500 |          2 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2.5 |       500 | fixed_horizon |                1410 |              8410 |                    8 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2   |       500 | fixed_horizon |                1410 |              7400 |                   32 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2   |       500 | zero_cross    |                1410 |              7400 |                   32 |
| static12_long_horizon_500 |          2 | UV_VISOR      | UV_VISOR_MAGENTA            |         2.5 |       500 | fixed_horizon |                 710 |              7420 |                   17 |
| static12_long_horizon_500 |          2 | UV_VISOR      | UV_VISOR_MAGENTA            |         2.5 |       500 | zero_cross    |                 710 |              7420 |                   17 |
| static12_long_horizon_500 |          2 | UV_VISOR      | UV_VISOR_MAGENTA            |         2   |       500 | zero_cross    |                 560 |              3240 |                   20 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_EVENING_BREATH |         2.5 |       500 | fixed_horizon |                 520 |              1560 |                   18 |
| static12_long_horizon_500 |          2 | OXYGEN_SHAKE  | OXYGEN_SHAKE_EVENING_BREATH |         2.5 |       500 | zero_cross    |                 520 |              1560 |                   18 |
| static12_long_horizon_500 |          2 | SNACKPACK     | SNACKPACK_STRAWBERRY        |         2   |       500 | zero_cross    |                 450 |              2940 |                   16 |
| static12_long_horizon_500 |          2 | UV_VISOR      | UV_VISOR_MAGENTA            |         1.5 |       500 | zero_cross    |                 330 |              8970 |                   28 |
| static12_long_horizon_500 |          2 | SNACKPACK     | SNACKPACK_STRAWBERRY        |         2   |       500 | fixed_horizon |                 280 |              2770 |                   16 |
| static12_long_horizon_500 |          2 | SNACKPACK     | SNACKPACK_PISTACHIO         |         2   |       500 | fixed_horizon |                 220 |               600 |                   16 |
| static12_long_horizon_500 |          2 | SNACKPACK     | SNACKPACK_PISTACHIO         |         2   |       500 | zero_cross    |                  10 |               230 |                   16 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2.5 |       500 | zero_cross    |               14980 |             30660 |                   28 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2.5 |       500 | fixed_horizon |               14850 |             30530 |                   28 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         1.5 |       500 | zero_cross    |               14670 |             38780 |                   36 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         1.5 |       500 | fixed_horizon |               14670 |             32360 |                   35 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2   |       500 | fixed_horizon |               11910 |             28030 |                   30 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         2   |       500 | zero_cross    |               11910 |             27620 |                   30 |
| static12_long_horizon_500 |          3 | MICROCHIP     | MICROCHIP_RECTANGLE         |         1.5 |       500 | fixed_horizon |               11570 |             23720 |                   19 |
| static12_long_horizon_500 |          3 | MICROCHIP     | MICROCHIP_RECTANGLE         |         1.5 |       500 | zero_cross    |               11570 |             23160 |                   19 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         3   |       500 | fixed_horizon |                9390 |             23140 |                   21 |
| static12_long_horizon_500 |          3 | SLEEP_POD     | SLEEP_POD_POLYESTER         |         3   |       500 | zero_cross    |                9390 |             23140 |                   21 |
| static12_long_horizon_500 |          3 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2   |       500 | fixed_horizon |                5990 |             14580 |                   20 |
| static12_long_horizon_500 |          3 | OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT           |         2   |       500 | zero_cross    |                5990 |             14580 |                   20 |
| static12_long_horizon_500 |          3 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2.5 |       500 | fixed_horizon |                5290 |             13550 |                   24 |
| static12_long_horizon_500 |          3 | TRANSLATOR    | TRANSLATOR_VOID_BLUE        |         2.5 |       500 | zero_cross    |                5290 |             13550 |                   24 |
| static12_long_horizon_500 |          3 | UV_VISOR      | UV_VISOR_MAGENTA            |         1.5 |       500 | fixed_horizon |                4830 |             10150 |                   27 |
| static12_long_horizon_500 |          3 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2   |       500 | fixed_horizon |                4690 |             26010 |                   17 |
| static12_long_horizon_500 |          3 | GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES  |         2   |       500 | zero_cross    |                4690 |             24980 |                   17 |