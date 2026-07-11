# Phase 1: walk-forward pair scan

Entry |z| >= 1.5, exit |z| <= 0.5, train mean/std per day, evaluate on next day.
Pass gate: min walk-forward Sharpe > 1.0 AND >=4 trades.

## Survivors (3)

| group        | a                      | b                   |   corr_mid_full |   spread_sd_full |   adf_t_full |   half_life_full |   wf_pnl_total |   wf_sharpe_mean |   wf_sharpe_min |   wf_trades | pass_walkforward   |
|:-------------|:-----------------------|:--------------------|----------------:|-----------------:|-------------:|-----------------:|---------------:|-----------------:|----------------:|------------:|:-------------------|
| SNACKPACK    | SNACKPACK_CHOCOLATE    | SNACKPACK_PISTACHIO |          0.4704 |          200.089 |      -3.7342 |          804.489 |         1746.5 |           1.6815 |          1.6599 |          10 | True               |
| OXYGEN_SHAKE | OXYGEN_SHAKE_CHOCOLATE | OXYGEN_SHAKE_GARLIC |          0.6458 |          729.955 |      -3.133  |         2827.73  |         2790.5 |           1.084  |          1.0751 |          10 | True               |
| SNACKPACK    | SNACKPACK_PISTACHIO    | SNACKPACK_RASPBERRY |         -0.4974 |          309.288 |      -3.5589 |          811.441 |         2440   |           1.3744 |          1.0237 |          10 | True               |

## Top 30 by min walk-forward Sharpe

| group         | a                           | b                           |   corr_mid_full |   spread_sd_full |   adf_t_full |   half_life_full |   wf_pnl_total |   wf_sharpe_mean |   wf_sharpe_min |   wf_trades | pass_walkforward   |
|:--------------|:----------------------------|:----------------------------|----------------:|-----------------:|-------------:|-----------------:|---------------:|-----------------:|----------------:|------------:|:-------------------|
| SNACKPACK     | SNACKPACK_CHOCOLATE         | SNACKPACK_PISTACHIO         |          0.4704 |          200.089 |      -3.7342 |          804.489 |         1746.5 |           1.6815 |          1.6599 |          10 | True               |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_CHOCOLATE      | OXYGEN_SHAKE_GARLIC         |          0.6458 |          729.955 |      -3.133  |         2827.73  |         2790.5 |           1.084  |          1.0751 |          10 | True               |
| SNACKPACK     | SNACKPACK_PISTACHIO         | SNACKPACK_RASPBERRY         |         -0.4974 |          309.288 |      -3.5589 |          811.441 |         2440   |           1.3744 |          1.0237 |          10 | True               |
| TRANSLATOR    | TRANSLATOR_GRAPHITE_MIST    | TRANSLATOR_VOID_BLUE        |          0.0979 |          726.903 |      -1.644  |         3390.78  |         2951   |           1.3928 |          1.317  |           1 | False              |
| ROBOT         | ROBOT_VACUUMING             | ROBOT_IRONING               |          0.7842 |          483.393 |      -2.5754 |         1687.26  |         1652   |           1.1474 |          1.1141 |           2 | False              |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS   | GALAXY_SOUNDS_SOLAR_FLAMES  |         -0.3352 |          811.616 |      -1.7278 |         3916.16  |         3785   |           1.6702 |          0.9393 |           6 | False              |
| SNACKPACK     | SNACKPACK_VANILLA           | SNACKPACK_RASPBERRY         |          0.0219 |          243.663 |      -3.6666 |          773.454 |         2151   |           1.7846 |          0.9334 |           9 | False              |
| SLEEP_POD     | SLEEP_POD_SUEDE             | SLEEP_POD_POLYESTER         |          0.8596 |          503.003 |      -2.8775 |         1293.24  |         2727.5 |           1.0162 |          0.9318 |           6 | False              |
| SNACKPACK     | SNACKPACK_CHOCOLATE         | SNACKPACK_VANILLA           |         -0.9259 |          372.172 |      -2.9189 |         1169.79  |         2456   |           1.4104 |          0.9115 |           9 | False              |
| SNACKPACK     | SNACKPACK_STRAWBERRY        | SNACKPACK_RASPBERRY         |         -0.4136 |          460.53  |      -3.1481 |         1160.85  |         2290   |           1.0582 |          0.8835 |           7 | False              |
| UV_VISOR      | UV_VISOR_YELLOW             | UV_VISOR_ORANGE             |         -0.0175 |          883.834 |      -1.5363 |         4720.06  |         1225.5 |           0.8668 |          0.8668 |           1 | False              |
| GALAXY_SOUNDS | GALAXY_SOUNDS_DARK_MATTER   | GALAXY_SOUNDS_SOLAR_FLAMES  |         -0.0225 |          564.532 |      -2.5341 |         1945.33  |         1760.5 |           1.0295 |          0.8473 |           5 | False              |
| SNACKPACK     | SNACKPACK_CHOCOLATE         | SNACKPACK_RASPBERRY         |          0.0461 |          256.879 |      -3.3438 |          867.212 |         1362   |           1.0556 |          0.8194 |           7 | False              |
| ROBOT         | ROBOT_MOPPING               | ROBOT_DISHES                |          0.4391 |          723.402 |      -2.65   |         1637.86  |         1161   |           0.8035 |          0.8035 |           2 | False              |
| TRANSLATOR    | TRANSLATOR_ECLIPSE_CHARCOAL | TRANSLATOR_VOID_BLUE        |          0.4673 |          519.111 |      -2.6233 |         1733.53  |         2488.5 |           0.971  |          0.7511 |          10 | False              |
| PANEL         | PANEL_1X4                   | PANEL_4X4                   |         -0.2279 |         1038.37  |      -1.1256 |         7904.81  |         2037.5 |           0.852  |          0.7224 |           2 | False              |
| TRANSLATOR    | TRANSLATOR_SPACE_GRAY       | TRANSLATOR_ECLIPSE_CHARCOAL |         -0.1509 |          658.125 |      -1.5623 |         3262.42  |         1917.5 |           1.5209 |          0.6813 |           3 | False              |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_MORNING_BREATH | OXYGEN_SHAKE_EVENING_BREATH |         -0.3216 |          868.248 |      -1.5205 |         4735.32  |          607   |           0.6218 |          0.6218 |           1 | False              |
| OXYGEN_SHAKE  | OXYGEN_SHAKE_EVENING_BREATH | OXYGEN_SHAKE_MINT           |         -0.3053 |          736.263 |      -1.811  |         3460.8   |         1446   |           0.9226 |          0.61   |           1 | False              |
| GALAXY_SOUNDS | GALAXY_SOUNDS_DARK_MATTER   | GALAXY_SOUNDS_SOLAR_WINDS   |         -0.0157 |          638.562 |      -1.9922 |         2613.45  |         1392   |           0.8069 |          0.5973 |           3 | False              |
| SLEEP_POD     | SLEEP_POD_POLYESTER         | SLEEP_POD_COTTON            |          0.8752 |          473.912 |      -3.0705 |         1112.96  |         2326.5 |           0.8338 |          0.4794 |           6 | False              |
| PEBBLES       | PEBBLES_M                   | PEBBLES_XL                  |          0.3505 |         1665.12  |      -2.221  |         2376.14  |         5063   |           0.8626 |          0.4605 |           2 | False              |
| PANEL         | PANEL_2X2                   | PANEL_1X4                   |          0.6443 |          652.48  |      -1.7964 |         3259.38  |          502   |           0.4251 |          0.4251 |           1 | False              |
| TRANSLATOR    | TRANSLATOR_ECLIPSE_CHARCOAL | TRANSLATOR_GRAPHITE_MIST    |         -0.0375 |          623.967 |      -1.9654 |         2720.59  |         1563.5 |           0.788  |          0.3826 |           1 | False              |
| MICROCHIP     | MICROCHIP_OVAL              | MICROCHIP_TRIANGLE          |          0.8705 |          922.686 |      -2.0285 |         3229.9   |         2261   |           0.8492 |          0.3802 |           5 | False              |
| PEBBLES       | PEBBLES_S                   | PEBBLES_L                   |         -0.136  |         1105.76  |      -1.8445 |         3779.84  |         1735.5 |           0.4737 |          0.3621 |           4 | False              |
| SLEEP_POD     | SLEEP_POD_SUEDE             | SLEEP_POD_COTTON            |          0.701  |          691.323 |      -1.9836 |         2479.98  |         1541   |           0.4802 |          0.2813 |           2 | False              |
| ROBOT         | ROBOT_VACUUMING             | ROBOT_LAUNDRY               |          0.7874 |          382.165 |      -3.2409 |         1111.34  |         1615.5 |           0.6592 |          0.2776 |           7 | False              |
| SNACKPACK     | SNACKPACK_VANILLA           | SNACKPACK_STRAWBERRY        |          0.2843 |          356.568 |      -2.7842 |         1674.04  |         1462.5 |           1.1483 |          0.1631 |           8 | False              |
| SNACKPACK     | SNACKPACK_CHOCOLATE         | SNACKPACK_STRAWBERRY        |         -0.541  |          501.44  |      -2.1264 |         3239.66  |          627.5 |           0.3431 |          0.1559 |           5 | False              |