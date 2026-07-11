# Round 5 Residual Trade Simulation

Leave-one-day-out test: fit each 1-vs-4 OLS residual on two sample days, trade the held-out day only, cross the target leg at top of book, use quantity 10, and allow only one open trade per product at a time. This tests whether residual shock markouts survive position occupancy and spread cost.

## Robust Candidates

| group         | target                     |   threshold |   horizon | exit_rule     |   total_pnl |   min_day_pnl |   total_trades |   win_pct |   avg_pnl_per_trade |   avg_hold |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------:|--------------:|---------------:|----------:|--------------------:|-----------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | zero_cross    |       48350 |          9570 |             48 |    0.7708 |            1007.29  |   460.854  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | fixed_horizon |       38580 |          6220 |             47 |    0.7447 |             820.851 |   485.745  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | fixed_horizon |       36400 |          4690 |             26 |    0.7692 |            1400     |   486.077  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | zero_cross    |       35370 |          4690 |             26 |    0.7692 |            1360.38  |   484.577  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | zero_cross    |       35000 |          4340 |             32 |    0.6875 |            1093.75  |   490.969  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | fixed_horizon |       35000 |          6970 |             37 |    0.7297 |             945.946 |   483.27   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | fixed_horizon |       34870 |          4340 |             32 |    0.6875 |            1089.69  |   491.938  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       500 | zero_cross    |       34590 |          6970 |             37 |    0.7297 |             934.865 |   482.838  |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | zero_cross    |       34250 |         11090 |             33 |    0.6061 |            1037.88  |   410.97   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       200 | zero_cross    |       34120 |          1780 |            102 |    0.5882 |             334.51  |   198.539  |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | fixed_horizon |       33740 |         10020 |             33 |    0.6061 |            1022.42  |   471.364  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | zero_cross    |       33650 |          3320 |             41 |    0.5854 |             820.732 |   489.732  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       200 | fixed_horizon |       33380 |          1780 |            102 |    0.5882 |             327.255 |   199.118  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | fixed_horizon |       33240 |          3320 |             41 |    0.5854 |             810.732 |   493.634  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | fixed_horizon |       32810 |          3480 |             69 |    0.5942 |             475.507 |   200      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       200 | zero_cross    |       32810 |          3480 |             69 |    0.5942 |             475.507 |   200      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | fixed_horizon |       30200 |          7160 |             81 |    0.5926 |             372.839 |   200      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       200 | zero_cross    |       30200 |          7160 |             81 |    0.5926 |             372.839 |   200      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       500 | fixed_horizon |       26950 |          3810 |             23 |    0.6522 |            1171.74  |   500      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       500 | zero_cross    |       26950 |          3810 |             23 |    0.6522 |            1171.74  |   500      |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       200 | fixed_horizon |       26230 |          3160 |             52 |    0.5769 |             504.423 |   198.75   |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       200 | zero_cross    |       26230 |          3160 |             52 |    0.5769 |             504.423 |   198.75   |
| ROBOT         | ROBOT_IRONING              |         1.5 |       500 | zero_cross    |       25920 |          1800 |             46 |    0.587  |             563.478 |   491.913  |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       100 | fixed_horizon |       25470 |          1660 |            194 |    0.5619 |             131.289 |    99.9485 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       100 | zero_cross    |       25470 |          1660 |            194 |    0.5619 |             131.289 |    99.9485 |
| ROBOT         | ROBOT_IRONING              |         1.5 |       500 | fixed_horizon |       25420 |          1800 |             46 |    0.587  |             552.609 |   499.565  |
| ROBOT         | ROBOT_IRONING              |         1.5 |       200 | fixed_horizon |       24120 |           230 |            110 |    0.5818 |             219.273 |   199.546  |
| ROBOT         | ROBOT_IRONING              |         1.5 |       200 | zero_cross    |       24120 |           230 |            110 |    0.5818 |             219.273 |   199.155  |
| ROBOT         | ROBOT_IRONING              |         2   |       200 | fixed_horizon |       22580 |           230 |             92 |    0.587  |             245.435 |   199.457  |
| ROBOT         | ROBOT_IRONING              |         2   |       200 | zero_cross    |       22580 |           230 |             92 |    0.587  |             245.435 |   199.457  |

## Fast Robust Candidates

| group         | target                     |   threshold |   horizon | exit_rule     |   total_pnl |   min_day_pnl |   total_trades |   win_pct |   avg_pnl_per_trade |   avg_hold |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------:|--------------:|---------------:|----------:|--------------------:|-----------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       100 | fixed_horizon |       25470 |          1660 |            194 |    0.5619 |            131.289  |    99.9485 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       100 | zero_cross    |       25470 |          1660 |            194 |    0.5619 |            131.289  |    99.9485 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       100 | fixed_horizon |       21200 |          2280 |            157 |    0.5987 |            135.032  |   100      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2   |       100 | zero_cross    |       21200 |          2280 |            157 |    0.5987 |            135.032  |   100      |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       100 | fixed_horizon |       16510 |          1330 |             97 |    0.5258 |            170.206  |    99.268  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       100 | zero_cross    |       16510 |          1330 |             97 |    0.5258 |            170.206  |    99.268  |
| ROBOT         | ROBOT_IRONING              |         2.5 |       100 | fixed_horizon |       16440 |           350 |            152 |    0.5921 |            108.158  |    99.8158 |
| ROBOT         | ROBOT_IRONING              |         2.5 |       100 | zero_cross    |       16440 |           350 |            152 |    0.5921 |            108.158  |    99.8158 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2.5 |       100 | fixed_horizon |       13610 |           900 |             53 |    0.6415 |            256.793  |    99.8113 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2.5 |       100 | zero_cross    |       13610 |           900 |             53 |    0.6415 |            256.793  |    99.8113 |
| ROBOT         | ROBOT_IRONING              |         3   |       100 | fixed_horizon |       13210 |          1600 |            108 |    0.5463 |            122.315  |    99.2407 |
| ROBOT         | ROBOT_IRONING              |         3   |       100 | zero_cross    |       13210 |          1600 |            108 |    0.5463 |            122.315  |    99.2407 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       100 | fixed_horizon |       12000 |          1890 |             91 |    0.5495 |            131.868  |   100      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         3   |       100 | zero_cross    |       12000 |          1890 |             91 |    0.5495 |            131.868  |   100      |
| PANEL         | PANEL_2X2                  |         2.5 |       100 | fixed_horizon |       11110 |          1070 |            191 |    0.534  |             58.1675 |    99.6597 |
| PANEL         | PANEL_2X2                  |         2.5 |       100 | zero_cross    |       11110 |          1070 |            191 |    0.534  |             58.1675 |    99.6597 |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |        50 | fixed_horizon |       10620 |           500 |            227 |    0.533  |             46.7841 |    50      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |        50 | zero_cross    |       10620 |           500 |            227 |    0.533  |             46.7841 |    50      |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         2.5 |       100 | fixed_horizon |        9460 |          1660 |            117 |    0.5641 |             80.8547 |   100      |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         2.5 |       100 | zero_cross    |        9460 |          1660 |            117 |    0.5641 |             80.8547 |   100      |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       100 | fixed_horizon |        9190 |           130 |            105 |    0.5333 |             87.5238 |    99.4095 |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       100 | zero_cross    |        9190 |           130 |            105 |    0.5333 |             87.5238 |    99.4095 |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         1.5 |       100 | fixed_horizon |        7990 |          1830 |            160 |    0.5188 |             49.9375 |    99.9312 |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         1.5 |       100 | zero_cross    |        7990 |          1830 |            160 |    0.5188 |             49.9375 |    99.9312 |
| ROBOT         | ROBOT_DISHES               |         2.5 |       100 | fixed_horizon |        7110 |           110 |             77 |    0.4545 |             92.3377 |    98.8182 |
| ROBOT         | ROBOT_DISHES               |         2.5 |       100 | zero_cross    |        7110 |           110 |             77 |    0.4545 |             92.3377 |    98.8182 |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          |         2.5 |       100 | fixed_horizon |        2370 |            10 |            130 |    0.5231 |             18.2308 |   100      |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          |         2.5 |       100 | zero_cross    |        2370 |            10 |            130 |    0.5231 |             18.2308 |   100      |

## Best By Group

| group         | target                     |   threshold |   horizon | exit_rule     |   total_pnl |   min_day_pnl |   positive_days |   total_trades |   avg_pnl_per_trade |
|:--------------|:---------------------------|------------:|----------:|:--------------|------------:|--------------:|----------------:|---------------:|--------------------:|
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | zero_cross    |       48350 |          9570 |               3 |             48 |           1007.29   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         1.5 |       500 | fixed_horizon |       38580 |          6220 |               3 |             47 |            820.851  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | fixed_horizon |       36400 |          4690 |               3 |             26 |           1400      |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         2   |       500 | zero_cross    |       35370 |          4690 |               3 |             26 |           1360.38   |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |         2.5 |       500 | zero_cross    |       35000 |          4340 |               3 |             32 |           1093.75   |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | zero_cross    |       34250 |         11090 |               3 |             33 |           1037.88   |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       500 | fixed_horizon |       33740 |         10020 |               3 |             33 |           1022.42   |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |         1.5 |       500 | zero_cross    |       33650 |          3320 |               3 |             41 |            820.732  |
| ROBOT         | ROBOT_IRONING              |         1.5 |       500 | zero_cross    |       25920 |          1800 |               3 |             46 |            563.478  |
| ROBOT         | ROBOT_IRONING              |         1.5 |       500 | fixed_horizon |       25420 |          1800 |               3 |             46 |            552.609  |
| ROBOT         | ROBOT_IRONING              |         1.5 |       200 | fixed_horizon |       24120 |           230 |               3 |            110 |            219.273  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         2.5 |       500 | fixed_horizon |       22300 |          5290 |               3 |             27 |            825.926  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         2.5 |       500 | zero_cross    |       22300 |          5290 |               3 |             27 |            825.926  |
| UV_VISOR      | UV_VISOR_MAGENTA           |         1.5 |       500 | fixed_horizon |       21230 |          4830 |               3 |             36 |            589.722  |
| MICROCHIP     | MICROCHIP_RECTANGLE        |         1.5 |       200 | zero_cross    |       19830 |          5860 |               3 |             62 |            319.839  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE       |         2   |       500 | fixed_horizon |       16050 |          3410 |               3 |             29 |            553.448  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          |         2   |       500 | zero_cross    |       15990 |          1410 |               3 |             36 |            444.167  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          |         2   |       500 | fixed_horizon |       15990 |          1410 |               3 |             36 |            444.167  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MINT          |         3   |       500 | fixed_horizon |       14540 |          4160 |               3 |             23 |            632.174  |
| UV_VISOR      | UV_VISOR_MAGENTA           |         1.5 |       500 | zero_cross    |       13800 |           330 |               3 |             36 |            383.333  |
| UV_VISOR      | UV_VISOR_MAGENTA           |         2.5 |       500 | fixed_horizon |       11600 |           710 |               3 |             21 |            552.381  |
| PANEL         | PANEL_2X2                  |         2.5 |       100 | zero_cross    |       11110 |          1070 |               3 |            191 |             58.1675 |
| PANEL         | PANEL_2X2                  |         2.5 |       100 | fixed_horizon |       11110 |          1070 |               3 |            191 |             58.1675 |
| SNACKPACK     | SNACKPACK_STRAWBERRY       |         2   |       500 | zero_cross    |        3640 |           450 |               3 |             36 |            101.111  |
| SNACKPACK     | SNACKPACK_STRAWBERRY       |         2   |       500 | fixed_horizon |        3470 |           280 |               3 |             36 |             96.3889 |
| SNACKPACK     | SNACKPACK_PISTACHIO        |         2   |       500 | fixed_horizon |         610 |            10 |               3 |             27 |             22.5926 |

## Top Day Rows

| group         | target                     |   test_day |   threshold |   horizon | exit_rule     |   pnl |   trades |   wins |   avg_hold |
|:--------------|:---------------------------|-----------:|------------:|----------:|:--------------|------:|---------:|-------:|-----------:|
| PEBBLES       | PEBBLES_XL                 |          3 |         2   |       100 | fixed_horizon | 48370 |       73 |     41 |    99.0959 |
| PEBBLES       | PEBBLES_XL                 |          3 |         3   |       100 | fixed_horizon | 48370 |       73 |     41 |    99.0959 |
| PEBBLES       | PEBBLES_XL                 |          3 |         1.5 |       100 | fixed_horizon | 48370 |       73 |     41 |    99.0959 |
| PEBBLES       | PEBBLES_XL                 |          3 |         2.5 |       100 | fixed_horizon | 48370 |       73 |     41 |    99.0959 |
| PEBBLES       | PEBBLES_L                  |          2 |         2.5 |       500 | fixed_horizon | 40330 |       19 |     13 |   481.526  |
| PEBBLES       | PEBBLES_L                  |          2 |         2   |       500 | fixed_horizon | 40330 |       19 |     13 |   481.526  |
| PEBBLES       | PEBBLES_L                  |          2 |         3   |       500 | fixed_horizon | 40330 |       19 |     13 |   481.526  |
| PEBBLES       | PEBBLES_L                  |          2 |         1.5 |       500 | fixed_horizon | 40330 |       19 |     13 |   481.526  |
| PEBBLES       | PEBBLES_XL                 |          3 |         1.5 |        50 | fixed_horizon | 37550 |      112 |     64 |    49.8571 |
| PEBBLES       | PEBBLES_XL                 |          3 |         3   |        50 | fixed_horizon | 37550 |      112 |     64 |    49.8571 |
| PEBBLES       | PEBBLES_XL                 |          3 |         2.5 |        50 | fixed_horizon | 37550 |      112 |     64 |    49.8571 |
| PEBBLES       | PEBBLES_XL                 |          3 |         2   |        50 | fixed_horizon | 37550 |      112 |     64 |    49.8571 |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       500 | zero_cross    | 32410 |       16 |     11 |   488.5    |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       500 | fixed_horizon | 32410 |       16 |     11 |   488.5    |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       500 | fixed_horizon | 31500 |       19 |     12 |   492.789  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       500 | zero_cross    | 31500 |       19 |     12 |   492.789  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       100 | zero_cross    | 30800 |       70 |     43 |   100      |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       100 | fixed_horizon | 30800 |       70 |     43 |   100      |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         1.5 |       200 | fixed_horizon | 29400 |       47 |     28 |   199.596  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         1.5 |       200 | zero_cross    | 29400 |       47 |     28 |   199.596  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       200 | zero_cross    | 29330 |       36 |     23 |   200      |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2.5 |       200 | fixed_horizon | 29330 |       36 |     23 |   200      |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         3   |       500 | fixed_horizon | 28940 |       14 |      9 |   476.214  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         3   |       500 | zero_cross    | 28940 |       14 |      9 |   476.214  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       200 | zero_cross    | 28690 |       42 |     25 |   196.667  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       200 | fixed_horizon | 28690 |       42 |     25 |   196.667  |
| PEBBLES       | PEBBLES_M                  |          4 |         1.5 |       500 | fixed_horizon | 27040 |       20 |     15 |   478.8    |
| PEBBLES       | PEBBLES_M                  |          4 |         2.5 |       500 | fixed_horizon | 27040 |       20 |     15 |   478.8    |
| PEBBLES       | PEBBLES_M                  |          4 |         2   |       500 | fixed_horizon | 27040 |       20 |     15 |   478.8    |
| PEBBLES       | PEBBLES_M                  |          4 |         3   |       500 | fixed_horizon | 27040 |       20 |     15 |   478.8    |
| PEBBLES       | PEBBLES_S                  |          3 |         1.5 |       200 | fixed_horizon | 26810 |       44 |     30 |   196.227  |
| PEBBLES       | PEBBLES_S                  |          3 |         2   |       200 | fixed_horizon | 26810 |       44 |     30 |   196.227  |
| PEBBLES       | PEBBLES_S                  |          3 |         2.5 |       200 | fixed_horizon | 26810 |       44 |     30 |   196.227  |
| PEBBLES       | PEBBLES_S                  |          3 |         3   |       200 | fixed_horizon | 26810 |       44 |     30 |   196.227  |
| MICROCHIP     | MICROCHIP_TRIANGLE         |          3 |         2.5 |       500 | zero_cross    | 25570 |       15 |      8 |   473.667  |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       100 | fixed_horizon | 25530 |       81 |     47 |    99.4568 |
| MICROCHIP     | MICROCHIP_SQUARE           |          2 |         2   |       100 | zero_cross    | 25530 |       81 |     47 |    99.4568 |
| MICROCHIP     | MICROCHIP_TRIANGLE         |          3 |         2.5 |       500 | fixed_horizon | 25020 |       15 |      8 |   500      |
| SLEEP_POD     | SLEEP_POD_POLYESTER        |          4 |         1.5 |       500 | zero_cross    | 24110 |       17 |     14 |   431.294  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_FLAMES |          2 |         1.5 |       500 | zero_cross    | 24080 |       15 |     12 |   489.333  |