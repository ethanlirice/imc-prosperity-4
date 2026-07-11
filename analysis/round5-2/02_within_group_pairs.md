# Round 5 Phase 2.1 - Within-Group Pairs

Selected groups come from `01_group_tradeability_ranking.csv` top 4.
ADF is a lightweight ADF(0) t-statistic on OLS residuals; threshold used here is t < -2.8 on combined data and at least 2 of 3 days.
Half-life is estimated from residual lag-1 ACF; candidates require max daily half-life <= 300 ticks.

## Candidate Pairs

No pair passed the full candidate gate.

## Top Raw Pair Metrics

| group      | y                           | x                           | candidate   |   all_beta |   all_corr_mid |   all_corr_ret |   all_resid_sd |   all_adf_t |   adf_days_lt_-2_8 |   half_life_mean_day |   half_life_max_day |   beta_cv_day |
|:-----------|:----------------------------|:----------------------------|:------------|-----------:|---------------:|---------------:|---------------:|------------:|-------------------:|---------------------:|--------------------:|--------------:|
| SNACKPACK  | SNACKPACK_CHOCOLATE         | SNACKPACK_VANILLA           | False       |  -1.04111  |      -0.925873 |      -0.915926 |        75.8428 |    -3.13502 |                  2 |              265.244 |             435.959 |      0.093542 |
| UV_VISOR   | UV_VISOR_RED                | UV_VISOR_MAGENTA            | False       |   0.299668 |       0.312842 |       0.004502 |       558.206  |    -1.89816 |                  2 |              703.84  |             771.056 |      0.479075 |
| UV_VISOR   | UV_VISOR_AMBER              | UV_VISOR_ORANGE             | False       |  -1.28668  |      -0.710639 |       0.004498 |       701.377  |    -1.31372 |                  2 |             1200.51  |            1568.99  |      2.64156  |
| TRANSLATOR | TRANSLATOR_SPACE_GRAY       | TRANSLATOR_ECLIPSE_CHARCOAL | False       |  -0.213287 |      -0.150889 |       0.010401 |       496.942  |    -1.28118 |                  2 |             1016.3   |            1461.5   |     20.4982   |
| SNACKPACK  | SNACKPACK_VANILLA           | SNACKPACK_PISTACHIO         | False       |  -0.298143 |      -0.313141 |       0.039709 |       169.534  |    -3.42696 |                  1 |              689.755 |             893.645 |      1.75228  |
| UV_VISOR   | UV_VISOR_AMBER              | UV_VISOR_MAGENTA            | False       |  -1.40917  |      -0.867276 |       0.00613  |       496.284  |    -3.17406 |                  1 |              839.44  |             924.543 |      0.989436 |
| TRANSLATOR | TRANSLATOR_ECLIPSE_CHARCOAL | TRANSLATOR_VOID_BLUE        | False       |   0.286897 |       0.467292 |      -0.004271 |       314.414  |    -2.94111 |                  1 |              840.583 |            1349.76  |      1.55347  |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK      | TRANSLATOR_VOID_BLUE        | False       |  -0.562588 |      -0.665409 |       0.004672 |       365.579  |    -2.68115 |                  1 |             1312.36  |            2575.68  |      7.61571  |
| PEBBLES    | PEBBLES_S                   | PEBBLES_M                   | False       |  -0.74593  |      -0.615714 |       0.012586 |       656.59   |    -2.60242 |                  1 |              835.734 |            1121.5   |      2.82784  |
| SNACKPACK  | SNACKPACK_PISTACHIO         | SNACKPACK_RASPBERRY         | False       |  -0.549147 |      -0.497361 |      -0.830946 |       162.657  |    -2.43532 |                  1 |             1201.16  |            2287.98  |      0.247906 |
| TRANSLATOR | TRANSLATOR_ECLIPSE_CHARCOAL | TRANSLATOR_GRAPHITE_MIST    | False       |  -0.026709 |      -0.037516 |       0.006996 |       355.381  |    -2.4236  |                  1 |              650.416 |             902.161 |      1.37676  |
| SNACKPACK  | SNACKPACK_STRAWBERRY        | SNACKPACK_RASPBERRY         | False       |  -0.885545 |      -0.413611 |      -0.923785 |       331.011  |    -2.06595 |                  1 |             1666.76  |            3092.85  |      0.187132 |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK      | TRANSLATOR_ECLIPSE_CHARCOAL | False       |  -0.271079 |      -0.196848 |       0.003532 |       480.156  |    -1.92182 |                  1 |              680.986 |            1162.46  |      1.14033  |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK      | TRANSLATOR_GRAPHITE_MIST    | False       |  -0.188656 |      -0.192429 |      -0.003435 |       480.585  |    -1.81784 |                  1 |             1094.23  |            2400.81  |      1.64955  |
| UV_VISOR   | UV_VISOR_AMBER              | UV_VISOR_RED                | False       |  -0.998355 |      -0.588563 |      -0.000701 |       805.946  |    -1.73582 |                  1 |             1605.25  |            2848.94  |      0.985234 |
| TRANSLATOR | TRANSLATOR_GRAPHITE_MIST    | TRANSLATOR_VOID_BLUE        | False       |   0.084449 |       0.097925 |       0.01811  |       497.132  |    -1.69823 |                  1 |              625.376 |             828.701 |      0.384938 |
| PEBBLES    | PEBBLES_S                   | PEBBLES_L                   | False       |  -0.182139 |      -0.136029 |       0.006598 |       825.523  |    -1.59355 |                  1 |              740.509 |            1166.05  |      1.40491  |
| UV_VISOR   | UV_VISOR_YELLOW             | UV_VISOR_AMBER              | False       |  -0.081407 |      -0.119031 |      -0.002816 |       676.95   |    -1.3009  |                  1 |             1230.62  |            2670.71  |    149.034    |
| TRANSLATOR | TRANSLATOR_SPACE_GRAY       | TRANSLATOR_GRAPHITE_MIST    | False       |   0.029836 |       0.029648 |      -0.001611 |       502.477  |    -1.22122 |                  1 |              921.065 |            1199.11  |      0.349525 |
| SNACKPACK  | SNACKPACK_PISTACHIO         | SNACKPACK_STRAWBERRY        | False       |  -0.227547 |      -0.441237 |       0.913292 |       168.253  |    -3.5959  |                  0 |             2365.55  |            3690.62  |      0.801342 |
| SNACKPACK  | SNACKPACK_CHOCOLATE         | SNACKPACK_STRAWBERRY        | False       |  -0.298713 |      -0.541036 |       0.016797 |       168.814  |    -3.58661 |                  0 |              667.971 |             808.686 |      0.887171 |
| SNACKPACK  | SNACKPACK_CHOCOLATE         | SNACKPACK_PISTACHIO         | False       |   0.503653 |       0.470438 |       0.024862 |       177.131  |    -3.45613 |                  0 |              653.182 |             990.461 |      2.54825  |
| SNACKPACK  | SNACKPACK_VANILLA           | SNACKPACK_STRAWBERRY        | False       |   0.139606 |       0.284329 |       0.031106 |       171.144  |    -3.225   |                  0 |              804.969 |             842.369 |      0.718685 |
| SNACKPACK  | SNACKPACK_VANILLA           | SNACKPACK_RASPBERRY         | False       |   0.02307  |       0.021945 |       0.01443  |       178.469  |    -3.06035 |                  0 |              797.632 |             904.616 |      1.86203  |
| SNACKPACK  | SNACKPACK_CHOCOLATE         | SNACKPACK_RASPBERRY         | False       |   0.054471 |       0.046081 |       0.030729 |       200.517  |    -2.81532 |                  0 |              739.075 |             992.382 |     11.9564   |
| PEBBLES    | PEBBLES_XS                  | PEBBLES_S                   | False       |   1.38864  |       0.798272 |      -0.006583 |       873.042  |    -2.71485 |                  0 |             1253.99  |            2736.32  |      0.467247 |
| PEBBLES    | PEBBLES_XS                  | PEBBLES_M                   | False       |  -1.46274  |      -0.694076 |       0.014599 |      1043.51   |    -2.68431 |                  0 |             1268.8   |            1743.2   |      6.94199  |
| PEBBLES    | PEBBLES_S                   | PEBBLES_XL                  | False       |  -0.391352 |      -0.834357 |      -0.495626 |       459.318  |    -2.58668 |                  0 |              572.654 |             722.066 |      0.454522 |
| UV_VISOR   | UV_VISOR_YELLOW             | UV_VISOR_RED                | False       |  -0.513424 |      -0.442569 |       0.007382 |       611.39   |    -2.50407 |                  0 |             1859.19  |            4245.16  |      1.10699  |
| PEBBLES    | PEBBLES_M                   | PEBBLES_XL                  | False       |   0.13569  |       0.35047  |      -0.511539 |       644.181  |    -2.37263 |                  0 |             1411.65  |            3099.2   |      1.03125  |