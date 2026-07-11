# Round 5 Residual Online Calibration Check

Tests whether leave-one-day-out residual signals survive day-level intercept uncertainty. `raw` uses the held-out residual directly; `open100` and `open500` subtract only that day's first 100/500 residual observations; rolling modes subtract a past-only rolling mean.

## Non-Raw Robust Candidates

| group        | target               | center_mode   |   threshold |   horizon |   total_pnl |   min_day_pnl |   total_trades |   win_pct |   avg_pnl_per_trade |
|:-------------|:---------------------|:--------------|------------:|----------:|------------:|--------------:|---------------:|----------:|--------------------:|
| MICROCHIP    | MICROCHIP_RECTANGLE  | open500       |         1.5 |       500 |       43360 |          8030 |             34 |    0.6176 |            1275.29  |
| PEBBLES      | PEBBLES_S            | open100       |         1.5 |       200 |       36160 |          3780 |            128 |    0.5703 |             282.5   |
| PEBBLES      | PEBBLES_S            | open100       |         2   |       200 |       36160 |          3780 |            128 |    0.5703 |             282.5   |
| PEBBLES      | PEBBLES_S            | open100       |         2.5 |       200 |       36160 |          3780 |            128 |    0.5703 |             282.5   |
| PEBBLES      | PEBBLES_S            | open100       |         3   |       200 |       36160 |          3780 |            128 |    0.5703 |             282.5   |
| PEBBLES      | PEBBLES_S            | open500       |         1.5 |       200 |       28490 |           680 |            123 |    0.5691 |             231.626 |
| PEBBLES      | PEBBLES_S            | open500       |         2   |       200 |       28490 |           680 |            123 |    0.5691 |             231.626 |
| PEBBLES      | PEBBLES_S            | open500       |         2.5 |       200 |       28490 |           680 |            123 |    0.5691 |             231.626 |
| PEBBLES      | PEBBLES_S            | open500       |         3   |       200 |       28490 |           680 |            123 |    0.5691 |             231.626 |
| ROBOT        | ROBOT_IRONING        | open500       |         1.5 |       200 |       28370 |          1380 |             73 |    0.6027 |             388.63  |
| ROBOT        | ROBOT_IRONING        | open500       |         1.5 |       500 |       26270 |          2490 |             36 |    0.7222 |             729.722 |
| ROBOT        | ROBOT_IRONING        | open100       |         1.5 |       500 |       24510 |          2130 |             36 |    0.6389 |             680.833 |
| ROBOT        | ROBOT_IRONING        | open100       |         2   |       500 |       24460 |           860 |             29 |    0.6897 |             843.448 |
| PANEL        | PANEL_2X2            | open100       |         1.5 |       500 |       22570 |          6260 |             51 |    0.5882 |             442.549 |
| PANEL        | PANEL_2X2            | open500       |         2.5 |       500 |       21440 |          3020 |             41 |    0.6341 |             522.927 |
| ROBOT        | ROBOT_IRONING        | open100       |         2.5 |       500 |       20960 |           940 |             21 |    0.7619 |             998.095 |
| PANEL        | PANEL_2X2            | open500       |         1.5 |       500 |       20760 |          4260 |             51 |    0.5294 |             407.059 |
| ROBOT        | ROBOT_IRONING        | open100       |         1.5 |       200 |       20210 |           480 |             80 |    0.625  |             252.625 |
| ROBOT        | ROBOT_IRONING        | open100       |         2.5 |       200 |       20190 |           140 |             46 |    0.6304 |             438.913 |
| PANEL        | PANEL_2X2            | open100       |         3   |       500 |       19560 |          1680 |             32 |    0.5625 |             611.25  |
| UV_VISOR     | UV_VISOR_MAGENTA     | open100       |         2.5 |       500 |       19410 |          3380 |             29 |    0.5862 |             669.31  |
| TRANSLATOR   | TRANSLATOR_VOID_BLUE | open500       |         1.5 |       500 |       18950 |           290 |             34 |    0.5882 |             557.353 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_MINT    | open500       |         1.5 |       500 |       18180 |          4640 |             34 |    0.5882 |             534.706 |
| UV_VISOR     | UV_VISOR_MAGENTA     | open500       |         1.5 |       500 |       17590 |          3370 |             43 |    0.5116 |             409.07  |
| PANEL        | PANEL_2X2            | open100       |         2.5 |       500 |       17370 |          2440 |             39 |    0.5641 |             445.385 |
| UV_VISOR     | UV_VISOR_MAGENTA     | open100       |         2   |       500 |       16900 |          1690 |             39 |    0.5897 |             433.333 |
| ROBOT        | ROBOT_IRONING        | open500       |         2   |       500 |       16350 |           310 |             22 |    0.7273 |             743.182 |
| UV_VISOR     | UV_VISOR_MAGENTA     | open100       |         2.5 |       200 |       16330 |           650 |             60 |    0.55   |             272.167 |
| PANEL        | PANEL_2X2            | open100       |         2.5 |       200 |       15590 |          1180 |             89 |    0.5281 |             175.168 |
| PANEL        | PANEL_2X2            | open500       |         2.5 |       200 |       14370 |          1000 |             92 |    0.5109 |             156.196 |

## Raw Robust Candidates

| group         | target                     | center_mode   |   threshold |   horizon |   total_pnl |   min_day_pnl |   total_trades |   win_pct |   avg_pnl_per_trade |
|:--------------|:---------------------------|:--------------|------------:|----------:|------------:|--------------:|---------------:|----------:|--------------------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         1.5 |       500 |       38580 |          6220 |             47 |    0.7447 |             820.851 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2   |       500 |       36400 |          4690 |             26 |    0.7692 |            1400     |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2   |       500 |       35000 |          6970 |             37 |    0.7297 |             945.946 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2.5 |       500 |       34870 |          4340 |             32 |    0.6875 |            1089.69  |
| MICROCHIP     | MICROCHIP_RECTANGLE        | raw           |         1.5 |       500 |       33740 |         10020 |             33 |    0.6061 |            1022.42  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         1.5 |       200 |       33380 |          1780 |            102 |    0.5882 |             327.255 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         1.5 |       500 |       33240 |          3320 |             41 |    0.5854 |             810.732 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2.5 |       200 |       32810 |          3480 |             69 |    0.5942 |             475.507 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2   |       200 |       30200 |          7160 |             81 |    0.5926 |             372.839 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         3   |       500 |       26950 |          3810 |             23 |    0.6522 |            1171.74  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2   |       200 |       26230 |          3160 |             52 |    0.5769 |             504.423 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         1.5 |       100 |       25470 |          1660 |            194 |    0.5619 |             131.289 |
| ROBOT         | ROBOT_IRONING              | raw           |         1.5 |       500 |       25420 |          1800 |             46 |    0.587  |             552.609 |
| ROBOT         | ROBOT_IRONING              | raw           |         1.5 |       200 |       24120 |           230 |            110 |    0.5818 |             219.273 |
| ROBOT         | ROBOT_IRONING              | raw           |         2   |       200 |       22580 |           230 |             92 |    0.587  |             245.435 |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       | raw           |         2.5 |       500 |       22300 |          5290 |             27 |    0.6296 |             825.926 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2.5 |       500 |       22230 |          1410 |             14 |    0.7143 |            1587.86  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         1.5 |       200 |       22040 |           820 |             94 |    0.5532 |             234.468 |
| UV_VISOR      | UV_VISOR_MAGENTA           | raw           |         1.5 |       500 |       21230 |          4830 |             36 |    0.5833 |             589.722 |
| ROBOT         | ROBOT_IRONING              | raw           |         2.5 |       500 |       21210 |          2720 |             33 |    0.6364 |             642.727 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2   |       100 |       21200 |          2280 |            157 |    0.5987 |             135.032 |
| ROBOT         | ROBOT_IRONING              | raw           |         3   |       500 |       20790 |          1760 |             25 |    0.56   |             831.6   |
| ROBOT         | ROBOT_IRONING              | raw           |         2   |       500 |       20530 |          1800 |             41 |    0.5366 |             500.732 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2.5 |       200 |       19190 |          3400 |             28 |    0.6071 |             685.357 |
| ROBOT         | ROBOT_IRONING              | raw           |         2.5 |       200 |       19180 |           550 |             80 |    0.4875 |             239.75  |
| MICROCHIP     | MICROCHIP_RECTANGLE        | raw           |         1.5 |       200 |       18590 |          4620 |             62 |    0.5645 |             299.839 |
| ROBOT         | ROBOT_IRONING              | raw           |         3   |       200 |       17250 |          1060 |             58 |    0.5517 |             297.414 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2   |       100 |       16510 |          1330 |             97 |    0.5258 |             170.206 |
| ROBOT         | ROBOT_IRONING              | raw           |         2.5 |       100 |       16440 |           350 |            152 |    0.5921 |             108.158 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         3   |       200 |       16120 |          3880 |             48 |    0.5417 |             335.833 |

## Best Modes By Candidate

| group         | target                     | center_mode   |   threshold |   horizon |   total_pnl |   min_day_pnl |   positive_days |   total_trades |   avg_pnl_per_trade |
|:--------------|:---------------------------|:--------------|------------:|----------:|------------:|--------------:|----------------:|---------------:|--------------------:|
| MICROCHIP     | MICROCHIP_RECTANGLE        | open500       |         1.5 |       500 |       43360 |          8030 |               3 |             34 |           1275.29   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         1.5 |       500 |       38580 |          6220 |               3 |             47 |            820.851  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         2   |       500 |       36400 |          4690 |               3 |             26 |           1400      |
| PEBBLES       | PEBBLES_S                  | open100       |         1.5 |       200 |       36160 |          3780 |               3 |            128 |            282.5    |
| PEBBLES       | PEBBLES_S                  | open100       |         2   |       200 |       36160 |          3780 |               3 |            128 |            282.5    |
| SLEEP_POD     | SLEEP_POD_POLYESTER        | raw           |         2   |       500 |       35000 |          6970 |               3 |             37 |            945.946  |
| MICROCHIP     | MICROCHIP_RECTANGLE        | raw           |         1.5 |       500 |       33740 |         10020 |               3 |             33 |           1022.42   |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES | raw           |         1.5 |       500 |       33240 |          3320 |               3 |             41 |            810.732  |
| ROBOT         | ROBOT_IRONING              | open500       |         1.5 |       200 |       28370 |          1380 |               3 |             73 |            388.63   |
| ROBOT         | ROBOT_IRONING              | open500       |         1.5 |       500 |       26270 |          2490 |               3 |             36 |            729.722  |
| PANEL         | PANEL_2X2                  | open100       |         1.5 |       500 |       22570 |          6260 |               3 |             51 |            442.549  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       | raw           |         2.5 |       500 |       22300 |          5290 |               3 |             27 |            825.926  |
| PANEL         | PANEL_2X2                  | open500       |         2.5 |       500 |       21440 |          3020 |               3 |             41 |            522.927  |
| UV_VISOR      | UV_VISOR_MAGENTA           | raw           |         1.5 |       500 |       21230 |          4830 |               3 |             36 |            589.722  |
| UV_VISOR      | UV_VISOR_MAGENTA           | open100       |         2.5 |       500 |       19410 |          3380 |               3 |             29 |            669.31   |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       | open500       |         1.5 |       500 |       18950 |           290 |               3 |             34 |            557.353  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          | open500       |         1.5 |       500 |       18180 |          4640 |               3 |             34 |            534.706  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          | raw           |         2   |       500 |       15990 |          1410 |               3 |             36 |            444.167  |
| SNACKPACK     | SNACKPACK_STRAWBERRY       | raw           |         2   |       500 |        3470 |           280 |               3 |             36 |             96.3889 |