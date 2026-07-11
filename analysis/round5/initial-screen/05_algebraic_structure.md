# Round 5 Lens 1 - Algebraic Structure

Scope: all 10 Round 5 product groups, days 2/3/4. Prices use mid-price.
Residual metrics for integer and signed-index identities are day-demeaned, so coefficients must stay fixed while each day may have its own intercept.
ADF is the same lightweight ADF(0) t-statistic used by earlier round 5 notebooks.

## Top Findings

- **PEBBLES has a near-exact equal-weight sum identity.** The best integer relation is `+1` on all five PEBBLES products with residual sigma 2.798327, p95 abs residual 1.059250, ADF t -170.971776, half-life 0.159400 ticks. This is the algebraic source of the prior PEBBLES 1-vs-4 basket result: every coefficient is effectively `-1` against the other four.
- **Crossing the whole PEBBLES basket is not attractive by spread math.** For the all-five sum, the estimated round-trip crossing cost is 64.000000, or 22.87 residual sigmas. Use it as a fair-value/skew anchor, not a market-order basket.
- **SNACKPACK has strong sign-flipped pairs but no fast algebraic identity.** The most negative pair is SNACKPACK_CHOCOLATE vs SNACKPACK_VANILLA with day-demeaned mid corr -0.966834 and return corr -0.915924; the best multi-term integer residual is still much wider and slower than PEBBLES.
- **No other group shows a PEBBLES-grade null dimension.** The next best non-pair integer relation by residual sigma per unit coefficient is SNACKPACK with resid_sd_per_l1 16.389118, versus PEBBLES 0.559665.

## PCA / Null Structure By Group

| group         |   pc1_var_share |   smallest_var_share |   condition_pc1_to_smallest |   min_day_smallest_vec_abs_cosine | smallest_int_relation                                                                                                                                    |
|:--------------|----------------:|---------------------:|----------------------------:|----------------------------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------|
| PEBBLES       |        0.73893  |             1e-06    |                 1.24725e+06 |                          1        | 1*PEBBLES_XS +1*PEBBLES_S +1*PEBBLES_M +1*PEBBLES_L +1*PEBBLES_XL                                                                                        |
| SNACKPACK     |        0.48577  |             0.005171 |                93.9499      |                          0.980195 | 56*SNACKPACK_CHOCOLATE +56*SNACKPACK_VANILLA -8*SNACKPACK_PISTACHIO -7*SNACKPACK_STRAWBERRY -14*SNACKPACK_RASPBERRY                                      |
| ROBOT         |        0.660933 |             0.035553 |                18.5903      |                          0.452621 | 28*ROBOT_VACUUMING -16*ROBOT_MOPPING -7*ROBOT_DISHES -56*ROBOT_LAUNDRY -21*ROBOT_IRONING                                                                 |
| UV_VISOR      |        0.538199 |             0.035945 |                14.9727      |                          0.751233 | 8*UV_VISOR_YELLOW +40*UV_VISOR_AMBER +5*UV_VISOR_ORANGE +35*UV_VISOR_RED +30*UV_VISOR_MAGENTA                                                            |
| MICROCHIP     |        0.557398 |             0.042381 |                13.152       |                          0.254843 | 14*MICROCHIP_CIRCLE -24*MICROCHIP_OVAL +7*MICROCHIP_SQUARE +24*MICROCHIP_RECTANGLE +56*MICROCHIP_TRIANGLE                                                |
| OXYGEN_SHAKE  |        0.447461 |             0.046212 |                 9.68283     |                          0.081697 | 42*OXYGEN_SHAKE_MORNING_BREATH +168*OXYGEN_SHAKE_EVENING_BREATH +96*OXYGEN_SHAKE_MINT -105*OXYGEN_SHAKE_CHOCOLATE +112*OXYGEN_SHAKE_GARLIC               |
| TRANSLATOR    |        0.510354 |             0.051642 |                 9.8826      |                          0.657104 | 280*TRANSLATOR_SPACE_GRAY +105*TRANSLATOR_ASTRO_BLACK +180*TRANSLATOR_ECLIPSE_CHARCOAL -420*TRANSLATOR_GRAPHITE_MIST -336*TRANSLATOR_VOID_BLUE           |
| PANEL         |        0.399225 |             0.055039 |                 7.25352     |                          0.338594 | 5*PANEL_1X2 +8*PANEL_2X2 +2*PANEL_1X4 +2*PANEL_2X4 +7*PANEL_4X4                                                                                          |
| SLEEP_POD     |        0.5299   |             0.073283 |                 7.23091     |                          0.065429 | 112*SLEEP_POD_SUEDE -35*SLEEP_POD_LAMB_WOOL -280*SLEEP_POD_POLYESTER -56*SLEEP_POD_NYLON +160*SLEEP_POD_COTTON                                           |
| GALAXY_SOUNDS |        0.36519  |             0.09234  |                 3.95485     |                          0.664123 | 56*GALAXY_SOUNDS_DARK_MATTER -14*GALAXY_SOUNDS_BLACK_HOLES -21*GALAXY_SOUNDS_PLANETARY_RINGS -16*GALAXY_SOUNDS_SOLAR_WINDS -7*GALAXY_SOUNDS_SOLAR_FLAMES |

## Best Bounded Small-Integer Relation Per Group

| group         | relation                                                                                                                                             |   resid_sd |   resid_sd_per_l1 |   resid_p95_abs |      adf_t |   adf_days_lt_-2_8 |   half_life |   daily_half_life_max |   round_trip_cross_cost |   round_trip_cost_z |
|:--------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|-----------:|------------------:|----------------:|-----------:|-------------------:|------------:|----------------------:|------------------------:|--------------------:|
| PEBBLES       | 1*PEBBLES_XS +1*PEBBLES_S +1*PEBBLES_M +1*PEBBLES_L +1*PEBBLES_XL                                                                                    |    2.79833 |          0.559665 |         1.05925 | -170.972   |                  3 |      0.1594 |              0.181275 |                      64 |           22.8708   |
| SNACKPACK     | 2*SNACKPACK_CHOCOLATE +2*SNACKPACK_VANILLA -1*SNACKPACK_PISTACHIO -1*SNACKPACK_STRAWBERRY -2*SNACKPACK_RASPBERRY                                     |  131.113   |         16.3891   |       255.436   |   -4.80023 |                  1 |    446.633  |            746.322    |                     136 |            1.03727  |
| ROBOT         | 1*ROBOT_VACUUMING -1*ROBOT_MOPPING -1*ROBOT_DISHES -2*ROBOT_LAUNDRY -1*ROBOT_IRONING                                                                 |  503.348   |         83.8914   |       948.728   |   -5.47213 |                  2 |    319.336  |            617.297    |                      42 |            0.083441 |
| TRANSLATOR    | 1*TRANSLATOR_SPACE_GRAY +1*TRANSLATOR_ASTRO_BLACK +1*TRANSLATOR_ECLIPSE_CHARCOAL -2*TRANSLATOR_GRAPHITE_MIST -2*TRANSLATOR_VOID_BLUE                 |  615.508   |         87.9298   |      1253.96    |   -5.62301 |                  3 |    334.992  |            772.816    |                      64 |            0.103979 |
| UV_VISOR      | 1*UV_VISOR_YELLOW +2*UV_VISOR_AMBER +1*UV_VISOR_ORANGE +2*UV_VISOR_RED +1*UV_VISOR_MAGENTA                                                           |  675.662   |         96.5231   |      1366.66    |   -4.10881 |                  2 |    540.711  |            880.051    |                      89 |            0.131723 |
| PANEL         | 2*PANEL_1X2 +2*PANEL_2X2 +1*PANEL_1X4 +1*PANEL_2X4 +2*PANEL_4X4                                                                                      |  865.563   |        108.195    |      1647.95    |   -3.7518  |                  1 |    706.246  |           1036.27     |                      78 |            0.090115 |
| OXYGEN_SHAKE  | 1*OXYGEN_SHAKE_MORNING_BREATH +2*OXYGEN_SHAKE_EVENING_BREATH +1*OXYGEN_SHAKE_MINT -1*OXYGEN_SHAKE_CHOCOLATE +1*OXYGEN_SHAKE_GARLIC                   |  658.318   |        109.72     |      1257.74    |   -3.96072 |                  1 |    616.03   |            948.408    |                      77 |            0.116965 |
| SLEEP_POD     | 1*SLEEP_POD_SUEDE +1*SLEEP_POD_LAMB_WOOL -2*SLEEP_POD_POLYESTER -2*SLEEP_POD_NYLON +1*SLEEP_POD_COTTON                                               |  845.115   |        120.731    |      1563.79    |   -3.96904 |                  0 |    695.923  |            864.745    |                      70 |            0.082829 |
| MICROCHIP     | 1*MICROCHIP_CIRCLE -1*MICROCHIP_OVAL +1*MICROCHIP_SQUARE +2*MICROCHIP_RECTANGLE +2*MICROCHIP_TRIANGLE                                                |  889.573   |        127.082    |      1786.47    |   -4.69126 |                  0 |    473.37   |            635.354    |                      62 |            0.069696 |
| GALAXY_SOUNDS | 2*GALAXY_SOUNDS_DARK_MATTER -1*GALAXY_SOUNDS_BLACK_HOLES -2*GALAXY_SOUNDS_PLANETARY_RINGS -2*GALAXY_SOUNDS_SOLAR_WINDS -1*GALAXY_SOUNDS_SOLAR_FLAMES | 1073.78    |        134.222    |      1904.74    |   -3.35318 |                  1 |    767.307  |           1475.36     |                     110 |            0.102442 |

## Best Non-Pair Small-Integer Relation Per Group

| group         | relation                                                                                                                                             |   nonzero_terms |   resid_sd |   resid_sd_per_l1 |   resid_p95_abs |      adf_t |   half_life |   round_trip_cost_z |
|:--------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|----------------:|-----------:|------------------:|----------------:|-----------:|------------:|--------------------:|
| PEBBLES       | 1*PEBBLES_XS +1*PEBBLES_S +1*PEBBLES_M +1*PEBBLES_L +1*PEBBLES_XL                                                                                    |               5 |    2.79833 |          0.559665 |         1.05925 | -170.972   |      0.1594 |           22.8708   |
| SNACKPACK     | 2*SNACKPACK_CHOCOLATE +2*SNACKPACK_VANILLA -1*SNACKPACK_PISTACHIO -1*SNACKPACK_STRAWBERRY -2*SNACKPACK_RASPBERRY                                     |               5 |  131.113   |         16.3891   |       255.436   |   -4.80023 |    446.633  |            1.03727  |
| ROBOT         | 1*ROBOT_VACUUMING -1*ROBOT_MOPPING -1*ROBOT_DISHES -2*ROBOT_LAUNDRY -1*ROBOT_IRONING                                                                 |               5 |  503.348   |         83.8914   |       948.728   |   -5.47213 |    319.336  |            0.083441 |
| TRANSLATOR    | 1*TRANSLATOR_SPACE_GRAY +1*TRANSLATOR_ASTRO_BLACK +1*TRANSLATOR_ECLIPSE_CHARCOAL -2*TRANSLATOR_GRAPHITE_MIST -2*TRANSLATOR_VOID_BLUE                 |               5 |  615.508   |         87.9298   |      1253.96    |   -5.62301 |    334.992  |            0.103979 |
| UV_VISOR      | 1*UV_VISOR_YELLOW +2*UV_VISOR_AMBER +1*UV_VISOR_ORANGE +2*UV_VISOR_RED +1*UV_VISOR_MAGENTA                                                           |               5 |  675.662   |         96.5231   |      1366.66    |   -4.10881 |    540.711  |            0.131723 |
| PANEL         | 2*PANEL_1X2 +2*PANEL_2X2 +1*PANEL_1X4 +1*PANEL_2X4 +2*PANEL_4X4                                                                                      |               5 |  865.563   |        108.195    |      1647.95    |   -3.7518  |    706.246  |            0.090115 |
| OXYGEN_SHAKE  | 1*OXYGEN_SHAKE_MORNING_BREATH +2*OXYGEN_SHAKE_EVENING_BREATH +1*OXYGEN_SHAKE_MINT -1*OXYGEN_SHAKE_CHOCOLATE +1*OXYGEN_SHAKE_GARLIC                   |               5 |  658.318   |        109.72     |      1257.74    |   -3.96072 |    616.03   |            0.116965 |
| SLEEP_POD     | 1*SLEEP_POD_SUEDE +1*SLEEP_POD_LAMB_WOOL -2*SLEEP_POD_POLYESTER -2*SLEEP_POD_NYLON +1*SLEEP_POD_COTTON                                               |               5 |  845.115   |        120.731    |      1563.79    |   -3.96904 |    695.923  |            0.082829 |
| MICROCHIP     | 1*MICROCHIP_CIRCLE -1*MICROCHIP_OVAL +1*MICROCHIP_SQUARE +2*MICROCHIP_RECTANGLE +2*MICROCHIP_TRIANGLE                                                |               5 |  889.573   |        127.082    |      1786.47    |   -4.69126 |    473.37   |            0.069696 |
| GALAXY_SOUNDS | 2*GALAXY_SOUNDS_DARK_MATTER -1*GALAXY_SOUNDS_BLACK_HOLES -2*GALAXY_SOUNDS_PLANETARY_RINGS -2*GALAXY_SOUNDS_SOLAR_WINDS -1*GALAXY_SOUNDS_SOLAR_FLAMES |               5 | 1073.78    |        134.222    |      1904.74    |   -3.35318 |    767.307  |            0.102442 |

## Day-Stable 1-vs-4 Basket Fits

| group         | target                    |       r2 |   min_day_r2 |   resid_sd |      adf_t |   half_life |   max_day_half_life |   max_beta_abs_dev |   beta_stability_ratio |
|:--------------|:--------------------------|---------:|-------------:|-----------:|-----------:|------------:|--------------------:|-------------------:|-----------------------:|
| PEBBLES       | PEBBLES_XL                | 0.999998 |     0.999981 |     2.7984 | -170.963   |    0.159551 |            0.180043 |           0.00021  |               0.00021  |
| SNACKPACK     | SNACKPACK_CHOCOLATE       | 0.948367 |     0.955567 |    45.6118 |   -5.23472 |  374.847    |          217.174    |           0.140417 |               0.493483 |
| MICROCHIP     | MICROCHIP_OVAL            | 0.918629 |     0.405748 |   442.684  |   -4.33115 |  553.82     |          469.139    |           0.714418 |               4.17855  |
| UV_VISOR      | UV_VISOR_AMBER            | 0.896354 |     0.298534 |   320.944  |   -4.12557 |  565.893    |          557.179    |           0.324893 |               1.45035  |
| SLEEP_POD     | SLEEP_POD_POLYESTER       | 0.887887 |     0.411289 |   327.307  |   -4.05489 |  654.418    |          752.054    |           0.41358  |               2.27519  |
| ROBOT         | ROBOT_MOPPING             | 0.791477 |     0.113378 |   350.313  |   -4.22546 |  584.894    |          758.525    |           0.529172 |               1.79183  |
| PANEL         | PANEL_2X2                 | 0.700084 |     0.300469 |   369.542  |   -3.04917 | 1140.54     |          438.528    |           0.57303  |               2.76747  |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_GARLIC       | 0.694596 |     0.453867 |   526.844  |   -3.65736 |  955.994    |          315.385    |           1.0599   |               4.15194  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE      | 0.677091 |     0.310751 |   329.156  |   -3.7204  |  778.898    |          412.456    |           0.494604 |               1.36694  |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS | 0.301419 |     0.474068 |   452.259  |   -2.05335 | 2116.61     |          453.754    |           0.930767 |               6.02999  |

## Executable Threshold Lens

Rows below use each group's best bounded small-integer relation. `mean_reversion_points` is signed residual improvement after 20 ticks when `|residual| >= 2.5 sigma`.

| group         | relation                                                                                                                                             |   z |   threshold_points |   horizon |   trigger_n |   trigger_pct |   mean_reversion_points |   good_pct |
|:--------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|----:|-------------------:|----------:|------------:|--------------:|------------------------:|-----------:|
| OXYGEN_SHAKE  | 1*OXYGEN_SHAKE_MORNING_BREATH +2*OXYGEN_SHAKE_EVENING_BREATH +1*OXYGEN_SHAKE_MINT -1*OXYGEN_SHAKE_CHOCOLATE +1*OXYGEN_SHAKE_GARLIC                   | 2.5 |         1645.8     |        20 |         112 |      0.003733 |               129.344   |   0.901786 |
| MICROCHIP     | 1*MICROCHIP_CIRCLE -1*MICROCHIP_OVAL +1*MICROCHIP_SQUARE +2*MICROCHIP_RECTANGLE +2*MICROCHIP_TRIANGLE                                                | 2.5 |         2223.93    |        20 |         365 |      0.012167 |               112.832   |   0.753425 |
| TRANSLATOR    | 1*TRANSLATOR_SPACE_GRAY +1*TRANSLATOR_ASTRO_BLACK +1*TRANSLATOR_ECLIPSE_CHARCOAL -2*TRANSLATOR_GRAPHITE_MIST -2*TRANSLATOR_VOID_BLUE                 | 2.5 |         1538.77    |        20 |         482 |      0.016067 |                84.2614  |   0.761411 |
| ROBOT         | 1*ROBOT_VACUUMING -1*ROBOT_MOPPING -1*ROBOT_DISHES -2*ROBOT_LAUNDRY -1*ROBOT_IRONING                                                                 | 2.5 |         1258.37    |        20 |         151 |      0.005033 |                72.2219  |   0.668874 |
| SLEEP_POD     | 1*SLEEP_POD_SUEDE +1*SLEEP_POD_LAMB_WOOL -2*SLEEP_POD_POLYESTER -2*SLEEP_POD_NYLON +1*SLEEP_POD_COTTON                                               | 2.5 |         2112.79    |        20 |         219 |      0.0073   |                63.5388  |   0.625571 |
| UV_VISOR      | 1*UV_VISOR_YELLOW +2*UV_VISOR_AMBER +1*UV_VISOR_ORANGE +2*UV_VISOR_RED +1*UV_VISOR_MAGENTA                                                           | 2.5 |         1689.15    |        20 |         572 |      0.019067 |                31.868   |   0.587413 |
| PANEL         | 2*PANEL_1X2 +2*PANEL_2X2 +1*PANEL_1X4 +1*PANEL_2X4 +2*PANEL_4X4                                                                                      | 2.5 |         2163.91    |        20 |         370 |      0.012333 |                28.777   |   0.583784 |
| PEBBLES       | 1*PEBBLES_XS +1*PEBBLES_S +1*PEBBLES_M +1*PEBBLES_L +1*PEBBLES_XL                                                                                    | 2.5 |            6.99582 |        20 |         853 |      0.028433 |                16.578   |   0.996483 |
| GALAXY_SOUNDS | 2*GALAXY_SOUNDS_DARK_MATTER -1*GALAXY_SOUNDS_BLACK_HOLES -2*GALAXY_SOUNDS_PLANETARY_RINGS -2*GALAXY_SOUNDS_SOLAR_WINDS -1*GALAXY_SOUNDS_SOLAR_FLAMES | 2.5 |         2684.44    |        20 |         341 |      0.011367 |                 3.90909 |   0.513196 |
| SNACKPACK     | 2*SNACKPACK_CHOCOLATE +2*SNACKPACK_VANILLA -1*SNACKPACK_PISTACHIO -1*SNACKPACK_STRAWBERRY -2*SNACKPACK_RASPBERRY                                     | 2.5 |          327.782   |        20 |         191 |      0.006367 |                -2.40576 |   0.554974 |

## Strongest Sign-Flipped Pairs

| group        | a                           | b                    |   corr_mid_day_demeaned |   corr_ret |   min_abs_daily_mid_corr |
|:-------------|:----------------------------|:---------------------|------------------------:|-----------:|-------------------------:|
| SNACKPACK    | SNACKPACK_CHOCOLATE         | SNACKPACK_VANILLA    |               -0.966834 |  -0.915924 |                 0.961571 |
| SNACKPACK    | SNACKPACK_STRAWBERRY        | SNACKPACK_RASPBERRY  |               -0.7805   |  -0.923783 |                 0.75218  |
| PEBBLES      | PEBBLES_L                   | PEBBLES_XL           |               -0.753559 |  -0.500006 |                 0.658439 |
| PEBBLES      | PEBBLES_S                   | PEBBLES_XL           |               -0.741482 |  -0.495641 |                 0.181487 |
| SNACKPACK    | SNACKPACK_PISTACHIO         | SNACKPACK_RASPBERRY  |               -0.710159 |  -0.830937 |                 0.434007 |
| ROBOT        | ROBOT_MOPPING               | ROBOT_IRONING        |               -0.653332 |  -0.000241 |                 0.26864  |
| ROBOT        | ROBOT_VACUUMING             | ROBOT_MOPPING        |               -0.610651 |  -0.003857 |                 0.017496 |
| MICROCHIP    | MICROCHIP_SQUARE            | MICROCHIP_RECTANGLE  |               -0.606086 |   0.006117 |                 0.039924 |
| PEBBLES      | PEBBLES_XS                  | PEBBLES_XL           |               -0.605767 |  -0.497268 |                 0.015264 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_EVENING_BREATH | OXYGEN_SHAKE_GARLIC  |               -0.591215 |   0.006958 |                 0.069625 |
| TRANSLATOR   | TRANSLATOR_GRAPHITE_MIST    | TRANSLATOR_VOID_BLUE |               -0.589964 |   0.018096 |                 0.519234 |
| MICROCHIP    | MICROCHIP_CIRCLE            | MICROCHIP_TRIANGLE   |               -0.501268 |   0.003106 |                 0.228142 |
| UV_VISOR     | UV_VISOR_AMBER              | UV_VISOR_MAGENTA     |               -0.499419 |   0.006165 |                 0.164378 |
| ROBOT        | ROBOT_MOPPING               | ROBOT_LAUNDRY        |               -0.485764 |  -0.009395 |                 0.096711 |
| PANEL        | PANEL_2X2                   | PANEL_4X4            |               -0.436572 |   0.001425 |                 0.261039 |

## Interpretation

- Promote **PEBBLES algebraic fair value** first: equal-weight group sum and target-vs-other-four forms are equivalent enough for implementation.
- Treat **SNACKPACK** as slower sign-flipped structure only. It has useful correlation evidence, but threshold reversion and spread/cost math are weaker than PEBBLES.
- Do not allocate implementation effort to hidden integer baskets in the remaining eight groups from this lens; their residual scales, PCA null shares, and day-stability are not competitive.