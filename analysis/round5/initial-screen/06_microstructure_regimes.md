# Round 5 Lens 2 - Microstructure Regimes

Scope: all 50 Round 5 products on days 2, 3, and 4.
Execution proxies use visible top-of-book only. `active_edge` crosses the current bid/ask; `passive_edge` assumes a fill at current bid/ask and is therefore an upper bound, paired with a next-5-tick touch-fill proxy.

## Actionable Findings

- **Best day-stable active residual signal:** PEBBLES_S at `|z| >= 1.0` has 853 signal ticks, h1 active edge 0.341, positive on all 3 days, and worst daily h1 active edge 0.116. Next-5-tick passive touch-fill proxy is 5.510%.
- **Largest active residual average:** PEBBLES_XL at `|z| >= 1.0` has h1 active edge 0.407 and h5 active edge 2.972, but only 2/3 h1-positive days.
- **Top-level imbalance alone is weak:** best product average is SLEEP_POD_COTTON with h1 active edge 0.777 over about 334 extreme ticks/day, but passive touch-fill proxy is only 3.897%.
- **Most fillable regime:** ROBOT day 3 time bin 8 has next-5-tick passive touch-fill 13.520%, trade-tick rate 3.200%, and median spread 7.0.

## Group Execution Surface

| group         |   spread_median |   top_depth_median |   top3_depth_median |   trade_ticks_pct |   passive_buy_fill_next5_pct |   passive_sell_fill_next5_pct |   fwd_abs_move_h5_to_halfspread |   imbalance_extreme_active_edge_h1 |
|:--------------|----------------:|-------------------:|--------------------:|------------------:|-----------------------------:|------------------------------:|--------------------------------:|-----------------------------------:|
| MICROCHIP     |         9       |            13.1333 |             32      |           0.01897 |                      0.0402  |                       0.03927 |                         5.62873 |                           -2.40585 |
| PEBBLES       |        12.9333  |            24.2667 |             76      |           0.02147 |                      0.0435  |                       0.0436  |                         5.13916 |                           -0.4807  |
| ROBOT         |         7.16667 |            14.3333 |             32      |           0.02443 |                      0.05337 |                       0.05203 |                         4.97056 |                           -2.74167 |
| SLEEP_POD     |         9.93333 |            22.1333 |             60      |           0.02443 |                      0.04879 |                       0.04727 |                         4.14683 |                           -0.43492 |
| TRANSLATOR    |         8.93333 |            22.4    |             60      |           0.02443 |                      0.04794 |                       0.04841 |                         4.08707 |                           -1.96663 |
| PANEL         |         9.66667 |            25.2    |             67.8667 |           0.02443 |                      0.04796 |                       0.04617 |                         3.83934 |                           -1.58052 |
| UV_VISOR      |        13.3333  |            36      |             99.3333 |           0.02443 |                      0.04592 |                       0.04165 |                         2.85021 |                            0.10247 |
| OXYGEN_SHAKE  |        13.0667  |            36      |             99.3333 |           0.02443 |                      0.04463 |                       0.04548 |                         2.84947 |                            0.06022 |
| GALAXY_SOUNDS |        13.8     |            36      |             99.3333 |           0.02443 |                      0.0436  |                       0.04341 |                         2.84006 |                           -0.00518 |
| SNACKPACK     |        16.9333  |            58.6667 |            160      |           0.02443 |                      0.03701 |                       0.03515 |                         1.46836 |                           -0.03896 |

## Residual-Z Executable Thresholds

Best active crossing candidates among product/group basket residual signals with at least 100 signal ticks:

| group   | product    |   threshold_abs_z |   signal_n |   signal_pct |   mid_edge_h1 |   active_edge_h1 |   active_edge_h1_positive_days |   active_edge_h1_min_day |   passive_edge_h1 |   passive_fill_next5_pct |
|:--------|:-----------|------------------:|-----------:|-------------:|--------------:|-----------------:|-------------------------------:|-------------------------:|------------------:|-------------------------:|
| PEBBLES | PEBBLES_XL |               1   |        853 |      0.02843 |       4.61547 |          0.40739 |                              2 |                 -0.48958 |           8.82356 |                  0.04103 |
| PEBBLES | PEBBLES_XL |               1.5 |        853 |      0.02843 |       4.61547 |          0.40739 |                              2 |                 -0.48958 |           8.82356 |                  0.04103 |
| PEBBLES | PEBBLES_XL |               2   |        853 |      0.02843 |       4.61547 |          0.40739 |                              2 |                 -0.48958 |           8.82356 |                  0.04103 |
| PEBBLES | PEBBLES_XL |               2.5 |        853 |      0.02843 |       4.61547 |          0.40739 |                              2 |                 -0.48958 |           8.82356 |                  0.04103 |
| PEBBLES | PEBBLES_XL |               3   |        853 |      0.02843 |       4.61547 |          0.40739 |                              2 |                 -0.48958 |           8.82356 |                  0.04103 |
| PEBBLES | PEBBLES_S  |               1   |        853 |      0.02843 |       3.25557 |          0.34056 |                              3 |                  0.11632 |           6.17057 |                  0.0551  |
| PEBBLES | PEBBLES_S  |               1.5 |        853 |      0.02843 |       3.25557 |          0.34056 |                              3 |                  0.11632 |           6.17057 |                  0.0551  |
| PEBBLES | PEBBLES_S  |               2   |        853 |      0.02843 |       3.25557 |          0.34056 |                              3 |                  0.11632 |           6.17057 |                  0.0551  |
| PEBBLES | PEBBLES_S  |               2.5 |        853 |      0.02843 |       3.25557 |          0.34056 |                              3 |                  0.11632 |           6.17057 |                  0.0551  |
| PEBBLES | PEBBLES_S  |               3   |        853 |      0.02843 |       3.25557 |          0.34056 |                              3 |                  0.11632 |           6.17057 |                  0.0551  |
| PEBBLES | PEBBLES_XS |               1   |        853 |      0.02843 |       2.63189 |          0.17761 |                              1 |                 -0.77098 |           5.08617 |                  0.0422  |
| PEBBLES | PEBBLES_XS |               1.5 |        853 |      0.02843 |       2.63189 |          0.17761 |                              1 |                 -0.77098 |           5.08617 |                  0.0422  |
| PEBBLES | PEBBLES_XS |               2   |        853 |      0.02843 |       2.63189 |          0.17761 |                              1 |                 -0.77098 |           5.08617 |                  0.0422  |
| PEBBLES | PEBBLES_XS |               2.5 |        853 |      0.02843 |       2.63189 |          0.17761 |                              1 |                 -0.77098 |           5.08617 |                  0.0422  |
| PEBBLES | PEBBLES_XS |               3   |        853 |      0.02843 |       2.63189 |          0.17761 |                              1 |                 -0.77098 |           5.08617 |                  0.0422  |
| PEBBLES | PEBBLES_XS |               0.5 |        957 |      0.0319  |       2.60188 |         -0.15674 |                              1 |                 -0.98485 |           5.3605  |                  0.03866 |
| PEBBLES | PEBBLES_L  |               1   |        853 |      0.02843 |       2.86049 |         -0.42907 |                              1 |                 -0.90909 |           6.15006 |                  0.04455 |
| PEBBLES | PEBBLES_L  |               1.5 |        853 |      0.02843 |       2.86049 |         -0.42907 |                              1 |                 -0.90909 |           6.15006 |                  0.04455 |
| PEBBLES | PEBBLES_L  |               2   |        853 |      0.02843 |       2.86049 |         -0.42907 |                              1 |                 -0.90909 |           6.15006 |                  0.04455 |
| PEBBLES | PEBBLES_L  |               2.5 |        853 |      0.02843 |       2.86049 |         -0.42907 |                              1 |                 -0.90909 |           6.15006 |                  0.04455 |

Best passive upper-bound candidates among the same residual signals:

| group        | product                     |   threshold_abs_z |   signal_n |   signal_pct |   passive_edge_h1 |   passive_fill_next5_pct |   active_edge_h1 |   active_edge_h1_positive_days |
|:-------------|:----------------------------|------------------:|-----------:|-------------:|------------------:|-------------------------:|-----------------:|-------------------------------:|
| TRANSLATOR   | TRANSLATOR_VOID_BLUE        |               2.5 |        106 |      0.00353 |           6.6934  |                  0.08491 |         -3.42925 |                              0 |
| UV_VISOR     | UV_VISOR_ORANGE             |               2.5 |        682 |      0.02273 |           5.53377 |                  0.07625 |         -6.76138 |                              0 |
| UV_VISOR     | UV_VISOR_ORANGE             |               3   |        380 |      0.01267 |           5.48945 |                  0.07368 |         -6.65303 |                              0 |
| UV_VISOR     | UV_VISOR_ORANGE             |               2   |       1093 |      0.03643 |           5.6859  |                  0.06496 |         -6.75641 |                              0 |
| ROBOT        | ROBOT_LAUNDRY               |               2   |       1007 |      0.03357 |           4.19513 |                  0.06356 |         -3.20209 |                              0 |
| TRANSLATOR   | TRANSLATOR_ASTRO_BLACK      |               2   |        960 |      0.032   |           4.66006 |                  0.06354 |         -3.74348 |                              0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_EVENING_BREATH |               2   |       1076 |      0.03587 |           6.17007 |                  0.06227 |         -5.59758 |                              0 |
| ROBOT        | ROBOT_LAUNDRY               |               1.5 |       3735 |      0.1245  |           4.11379 |                  0.05971 |         -3.06693 |                              0 |
| ROBOT        | ROBOT_LAUNDRY               |               2.5 |        279 |      0.0093  |           4.71505 |                  0.05735 |         -2.79391 |                              0 |
| ROBOT        | ROBOT_IRONING               |               0.5 |      21034 |      0.70113 |           3.38944 |                  0.05619 |         -3.01574 |                              0 |
| UV_VISOR     | UV_VISOR_AMBER              |               2   |       1286 |      0.04287 |           4.96656 |                  0.05599 |         -4.79393 |                              0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_MORNING_BREATH |               2.5 |        524 |      0.01747 |           6.58492 |                  0.05534 |         -5.17653 |                              0 |
| PEBBLES      | PEBBLES_S                   |               1   |        853 |      0.02843 |           6.17057 |                  0.0551  |          0.34056 |                              3 |
| PEBBLES      | PEBBLES_S                   |               1.5 |        853 |      0.02843 |           6.17057 |                  0.0551  |          0.34056 |                              3 |
| PEBBLES      | PEBBLES_S                   |               2   |        853 |      0.02843 |           6.17057 |                  0.0551  |          0.34056 |                              3 |
| PEBBLES      | PEBBLES_S                   |               2.5 |        853 |      0.02843 |           6.17057 |                  0.0551  |          0.34056 |                              3 |
| PEBBLES      | PEBBLES_S                   |               3   |        853 |      0.02843 |           6.17057 |                  0.0551  |          0.34056 |                              3 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_EVENING_BREATH |               1   |      10293 |      0.3431  |           6.2182  |                  0.05499 |         -5.59882 |                              0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_CHOCOLATE      |               2.5 |        332 |      0.01107 |           7.26807 |                  0.05422 |         -5.4488  |                              0 |
| ROBOT        | ROBOT_LAUNDRY               |               1   |      10865 |      0.36217 |           3.7917  |                  0.05403 |         -3.31618 |                              0 |

## Top-Level Imbalance

Extreme imbalance is each product/day's top 20% by absolute top-level imbalance. Active edge crosses in the imbalance direction at h=1.

| group         | product                       |   spread_median |   imbalance_abs_mean |   imbalance_corr_h1 |   imbalance_extreme_mid_edge_h1 |   imbalance_extreme_active_edge_h1 |   imbalance_extreme_passive_edge_h1 |   imbalance_extreme_passive_fill_next5 |
|:--------------|:------------------------------|----------------:|---------------------:|--------------------:|--------------------------------:|-----------------------------------:|------------------------------------:|---------------------------------------:|
| SLEEP_POD     | SLEEP_POD_COTTON              |         10.3333 |              0.01535 |             0.04851 |                         3.34743 |                            0.77705 |                             5.9178  |                                0.03897 |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_GARLIC           |         15.3333 |              0.02116 |             0.06524 |                         4.27898 |                            0.43879 |                             8.11917 |                                0.04818 |
| PEBBLES       | PEBBLES_XL                    |         16.3333 |              0.01146 |             0.0244  |                         4.62252 |                            0.41469 |                             8.83035 |                                0.04095 |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_CHOCOLATE        |         12.3333 |              0.02116 |             0.05811 |                         3.43988 |                            0.34992 |                             6.52984 |                                0.04512 |
| PEBBLES       | PEBBLES_S                     |         12      |              0.01146 |             0.03579 |                         3.25788 |                            0.34132 |                             6.17444 |                                0.05513 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS     |         13.3333 |              0.02116 |             0.06356 |                         3.695   |                            0.31455 |                             7.07545 |                                0.04572 |
| MICROCHIP     | MICROCHIP_SQUARE              |         12      |              0.00751 |             0.02589 |                         3.29318 |                            0.2702  |                             6.31617 |                                0.05162 |
| PANEL         | PANEL_2X4                     |         10.3333 |              0.01526 |             0.03969 |                         2.74872 |                            0.2579  |                             5.23954 |                                0.0531  |
| UV_VISOR      | UV_VISOR_YELLOW               |         14      |              0.02116 |             0.06111 |                         3.7875  |                            0.24875 |                             7.32625 |                                0.0477  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_EVENING_BREATH   |         12      |              0.02116 |             0.05506 |                         3.24282 |                            0.2321  |                             6.25354 |                                0.05032 |
| UV_VISOR      | UV_VISOR_MAGENTA              |         14.3333 |              0.02116 |             0.05921 |                         3.78024 |                            0.2016  |                             7.35888 |                                0.04155 |
| SNACKPACK     | SNACKPACK_RASPBERRY           |         17      |              0.02525 |             0.10171 |                         4.47813 |                            0.19689 |                             8.75938 |                                0.03877 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_PLANETARY_RINGS |         14      |              0.02116 |             0.05894 |                         3.6294  |                            0.1508  |                             7.108   |                                0.04798 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_BLACK_HOLES     |         14.6667 |              0.02116 |             0.05912 |                         3.79861 |                            0.10829 |                             7.48892 |                                0.04596 |
| SNACKPACK     | SNACKPACK_CHOCOLATE           |         16.6667 |              0.02525 |             0.11759 |                         4.2751  |                            0.07815 |                             8.47206 |                                0.03703 |
| UV_VISOR      | UV_VISOR_ORANGE               |         13.6667 |              0.02116 |             0.05806 |                         3.44687 |                            0.06962 |                             6.82412 |                                0.04282 |
| SLEEP_POD     | SLEEP_POD_POLYESTER           |         10.6667 |              0.01568 |             0.0381  |                         2.75131 |                            0.06826 |                             5.43435 |                                0.04675 |
| UV_VISOR      | UV_VISOR_RED                  |         14.3333 |              0.02116 |             0.05929 |                         3.60232 |                            0.02271 |                             7.18192 |                                0.05024 |
| UV_VISOR      | UV_VISOR_AMBER                |         10.3333 |              0.02156 |             0.05982 |                         2.64571 |                           -0.03033 |                             5.32174 |                                0.0538  |
| PANEL         | PANEL_1X2                     |         11.6667 |              0.02116 |             0.05714 |                         2.83079 |                           -0.10313 |                             5.7647  |                                0.03965 |

## Trade Occurrence And Fill Quality

| group      | product                     |   trade_count |   at_bid_share |   at_ask_share |   inside_share |   outside_share |   touch_qty_to_depth_median |   trade_markout_1_mean |   trade_markout_5_mean |   trade_markout_20_mean |
|:-----------|:----------------------------|--------------:|---------------:|---------------:|---------------:|----------------:|----------------------------:|-----------------------:|-----------------------:|------------------------:|
| ROBOT      | ROBOT_DISHES                |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.33333 |               -3.64256 |               -2.29918 |                -0.7863  |
| ROBOT      | ROBOT_MOPPING               |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.375   |               -3.55321 |               -2.48361 |                -3.18767 |
| PEBBLES    | PEBBLES_M                   |           644 |        0.50155 |        0.49845 |              0 |               0 |                     0.28571 |               -5.33307 |               -2.60093 |                -3.48598 |
| MICROCHIP  | MICROCHIP_RECTANGLE         |           569 |        0.47276 |        0.52724 |              0 |               0 |                     0.28571 |               -3.92091 |               -2.70035 |                -1.13732 |
| ROBOT      | ROBOT_VACUUMING             |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.28571 |               -3.54297 |               -3.14959 |                -4.44863 |
| ROBOT      | ROBOT_IRONING               |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.33333 |               -3.36426 |               -3.15642 |                -2.53151 |
| TRANSLATOR | TRANSLATOR_VOID_BLUE        |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -4.84311 |               -3.59904 |                -5.79932 |
| MICROCHIP  | MICROCHIP_OVAL              |           569 |        0.47276 |        0.52724 |              0 |               0 |                     0.25    |               -4.39807 |               -3.70738 |                -4.0713  |
| TRANSLATOR | TRANSLATOR_GRAPHITE_MIST    |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -3.69031 |               -3.80601 |                -5.69795 |
| TRANSLATOR | TRANSLATOR_ECLIPSE_CHARCOAL |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -4.6146  |               -3.8709  |                -6.12603 |
| MICROCHIP  | MICROCHIP_CIRCLE            |           569 |        0.47276 |        0.52724 |              0 |               0 |                     0.28571 |               -4.12039 |               -4.21705 |                -2.70863 |
| SLEEP_POD  | SLEEP_POD_NYLON             |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.21429 |               -3.97271 |               -4.30533 |                -4.79315 |
| PANEL      | PANEL_1X2                   |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.13636 |               -5.54229 |               -4.36954 |                -4.98973 |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK      |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.21429 |               -3.9925  |               -4.42008 |                -6.68767 |
| TRANSLATOR | TRANSLATOR_SPACE_GRAY       |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.21429 |               -4.51023 |               -4.63934 |                -6.07877 |
| PANEL      | PANEL_1X4                   |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.21429 |               -4.22306 |               -4.68511 |                -2.89932 |
| PANEL      | PANEL_2X2                   |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.21429 |               -4.01705 |               -4.69945 |                -5.1589  |
| PANEL      | PANEL_2X4                   |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -4.95157 |               -4.73634 |                -4.50479 |
| SLEEP_POD  | SLEEP_POD_SUEDE             |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -5.12347 |               -4.76434 |                -8.68014 |
| ROBOT      | ROBOT_LAUNDRY               |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.33333 |               -3.98022 |               -4.79508 |                -5.50616 |
| PEBBLES    | PEBBLES_XS                  |           644 |        0.50155 |        0.49845 |              0 |               0 |                     0.27273 |               -5.32298 |               -4.95963 |                -1.72741 |
| MICROCHIP  | MICROCHIP_TRIANGLE          |           569 |        0.47276 |        0.52724 |              0 |               0 |                     0.33333 |               -4.73462 |               -5.06942 |                -8.46215 |
| UV_VISOR   | UV_VISOR_RED                |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.13636 |               -6.40518 |               -5.14003 |                -4.29521 |
| UV_VISOR   | UV_VISOR_YELLOW             |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.13636 |               -5.96112 |               -5.15301 |                -5.70685 |
| SLEEP_POD  | SLEEP_POD_LAMB_WOOL         |           733 |        0.5116  |        0.4884  |              0 |               0 |                     0.22222 |               -4.8322  |               -5.16257 |                -4.13562 |

## Day And Time Regimes

Most volatile group/day/time bins:

| group   |   day |   time_bin |   spread_median |   top_depth_median |   mid_ret_abs_mean |   trade_ticks_pct |   passive_fill_next5_pct |
|:--------|------:|-----------:|----------------:|-------------------:|-------------------:|------------------:|-------------------------:|
| PEBBLES |     2 |          9 |              12 |                 24 |            14.8506 |             0.021 |                   0.0856 |
| PEBBLES |     3 |          7 |              13 |                 26 |            14.7896 |             0.023 |                   0.0936 |
| PEBBLES |     3 |          9 |              14 |                 24 |            14.6384 |             0.03  |                   0.1174 |
| PEBBLES |     3 |          4 |              12 |                 26 |            14.606  |             0.019 |                   0.075  |
| PEBBLES |     2 |          6 |              12 |                 24 |            14.5995 |             0.016 |                   0.0684 |
| PEBBLES |     3 |          1 |              12 |                 24 |            14.5842 |             0.024 |                   0.1002 |
| PEBBLES |     4 |          7 |              13 |                 26 |            14.5726 |             0.026 |                   0.1034 |
| PEBBLES |     4 |          3 |              13 |                 26 |            14.5482 |             0.018 |                   0.0766 |
| PEBBLES |     4 |          8 |              12 |                 24 |            14.5481 |             0.014 |                   0.0592 |
| PEBBLES |     4 |          0 |              14 |                 24 |            14.5418 |             0.021 |                   0.0832 |
| PEBBLES |     2 |          7 |              12 |                 24 |            14.5381 |             0.029 |                   0.1082 |
| PEBBLES |     4 |          5 |              14 |                 26 |            14.5344 |             0.018 |                   0.0764 |
| PEBBLES |     3 |          8 |              14 |                 26 |            14.5292 |             0.022 |                   0.0882 |
| PEBBLES |     2 |          3 |              13 |                 26 |            14.526  |             0.025 |                   0.0994 |
| PEBBLES |     3 |          0 |              12 |                 24 |            14.5011 |             0.023 |                   0.1008 |
| PEBBLES |     3 |          5 |              13 |                 24 |            14.4642 |             0.019 |                   0.0818 |
| PEBBLES |     2 |          1 |              13 |                 24 |            14.4546 |             0.021 |                   0.0836 |
| PEBBLES |     4 |          2 |              14 |                 26 |            14.4534 |             0.02  |                   0.0792 |
| PEBBLES |     2 |          2 |              13 |                 24 |            14.4511 |             0.016 |                   0.0668 |
| PEBBLES |     3 |          3 |              13 |                 24 |            14.4026 |             0.022 |                   0.0906 |

Highest next-5-tick passive touch-fill bins:

| group         |   day |   time_bin |   spread_median |   top_depth_median |   mid_ret_abs_mean |   trade_ticks_pct |   passive_fill_next5_pct |
|:--------------|------:|-----------:|----------------:|-------------------:|-------------------:|------------------:|-------------------------:|
| ROBOT         |     3 |          8 |               7 |                 14 |            7.8988  |             0.032 |                   0.1352 |
| MICROCHIP     |     4 |          8 |               8 |                 14 |           10.5764  |             0.031 |                   0.1308 |
| TRANSLATOR    |     3 |          8 |               9 |                 22 |            7.818   |             0.032 |                   0.1268 |
| ROBOT         |     4 |          2 |               7 |                 14 |            8.1053  |             0.028 |                   0.125  |
| SLEEP_POD     |     3 |          8 |              10 |                 22 |            9.1189  |             0.032 |                   0.1246 |
| ROBOT         |     2 |          9 |               8 |                 16 |            8.0072  |             0.03  |                   0.1246 |
| PANEL         |     3 |          8 |               9 |                 24 |            7.7895  |             0.032 |                   0.124  |
| ROBOT         |     2 |          3 |               7 |                 14 |            7.9296  |             0.027 |                   0.1238 |
| ROBOT         |     4 |          0 |               7 |                 14 |            7.62182 |             0.03  |                   0.1232 |
| ROBOT         |     3 |          7 |               7 |                 14 |            7.9061  |             0.028 |                   0.1222 |
| SLEEP_POD     |     2 |          9 |              10 |                 22 |            8.4335  |             0.03  |                   0.1192 |
| ROBOT         |     3 |          0 |               8 |                 16 |            7.91151 |             0.027 |                   0.1182 |
| SLEEP_POD     |     4 |          0 |              11 |                 22 |            9.198   |             0.03  |                   0.118  |
| PEBBLES       |     3 |          9 |              14 |                 24 |           14.6384  |             0.03  |                   0.1174 |
| OXYGEN_SHAKE  |     3 |          8 |              12 |                 38 |            7.9637  |             0.032 |                   0.1166 |
| ROBOT         |     3 |          5 |               7 |                 14 |            7.8513  |             0.028 |                   0.1164 |
| ROBOT         |     4 |          1 |               7 |                 14 |            8.0458  |             0.027 |                   0.1162 |
| GALAXY_SOUNDS |     3 |          8 |              14 |                 38 |            9.071   |             0.032 |                   0.116  |
| ROBOT         |     4 |          8 |               7 |                 14 |            7.4101  |             0.026 |                   0.1152 |
| PANEL         |     4 |          0 |               9 |                 26 |            7.62052 |             0.03  |                   0.1148 |

## Interpretation

- Residual mean reversion is statistically visible, but active crossing must beat a median half-spread of roughly 5-8 ticks depending on group. The residual-z scan is the decisive executable filter.
- Passive residual signals show positive upper-bound markouts because they collect spread, but next-5-tick touch-fill probabilities are generally low enough that queue/fill uncertainty dominates. Treat passive results as quote-skew candidates, not guaranteed trades.
- Top-level imbalance has a few small positive active averages after spread, but the signal is thin and low-fill; use it only as a secondary skew/gating variable.
- Historical trade prints are mostly touch prints with small quantity relative to visible top depth; observed active print markouts are a fill-quality diagnostic, not a copy signal because trade files have no named counterparties.