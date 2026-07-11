# Round 5 Lens 3 - Event Lead-Lag and Regime Signals

Data: `data/ROUND5` prices, days 2, 3, and 4. Markouts are midpoint-to-midpoint after the leader move is observable: if a leader return from `t` to `t+1` has sign `s`, follower markout is `s * (mid[t+1+lag] - mid[t+1])`.
Large-move events are product/day moves at or above the 95% absolute-return quantile. Volatility regimes use a 100-tick rolling mean absolute return split at each product/day median.

## Actionable Read

- Strongest delayed residual-shock candidate is TRANSLATOR_VOID_BLUE (TRANSLATOR) at lag 200: mean residual reversion 223.4511, target-only markout 113.4080, good_pct 0.812, n=1201, positive on 3/3 days. This is a slow 100-200 tick research candidate, not the first implementation.
- Best fast PEBBLES residual shock is PEBBLES_XS at lag 20: mean residual reversion 16.5779, target-only markout 3.5147, good_pct 0.529, n=853, ADF t -170.96. This supports the existing PEBBLES basket-arb priority.
- Best persistent large-move follower pair is SNACKPACK_VANILLA -> PEBBLES_XL at lag 200: mean markout 23.5069, good_pct 0.524, n=1530, but only 1.383x follower median spread.
- Best sign-only pair is TRANSLATOR_VOID_BLUE -> PEBBLES_XL at lag 200: mean markout 5.2078, good_pct 0.504, n=28615; this is too small versus spread for standalone crossing.

## Persistent Large-Move Pair Markouts

|   lag | leader                     | follower                  | leader_group   | follower_group   |    n |   mean_markout |   good_pct |   min_day_mean |   follower_median_spread |   markout_to_spread |
|------:|:---------------------------|:--------------------------|:---------------|:-----------------|-----:|---------------:|-----------:|---------------:|-------------------------:|--------------------:|
|   200 | SNACKPACK_VANILLA          | PEBBLES_XL                | SNACKPACK      | PEBBLES          | 1530 |        23.5069 |     0.5242 |         5.9266 |                       17 |              1.3828 |
|   100 | SLEEP_POD_NYLON            | PEBBLES_XL                | SLEEP_POD      | PEBBLES          | 1582 |        19.1261 |     0.5341 |        17.0297 |                       17 |              1.1251 |
|   200 | GALAXY_SOUNDS_SOLAR_FLAMES | PEBBLES_XL                | GALAXY_SOUNDS  | PEBBLES          | 1543 |        18.6944 |     0.5308 |         6.4098 |                       17 |              1.0997 |
|   200 | SLEEP_POD_NYLON            | PEBBLES_XL                | SLEEP_POD      | PEBBLES          | 1565 |        18.0869 |     0.5182 |        10.4101 |                       17 |              1.0639 |
|   100 | TRANSLATOR_VOID_BLUE       | PEBBLES_XL                | TRANSLATOR     | PEBBLES          | 1569 |        17.9538 |     0.5271 |        14.9934 |                       17 |              1.0561 |
|   200 | GALAXY_SOUNDS_BLACK_HOLES  | PEBBLES_XL                | GALAXY_SOUNDS  | PEBBLES          | 1498 |        17.3431 |     0.5187 |         8.335  |                       17 |              1.0202 |
|   200 | TRANSLATOR_VOID_BLUE       | PEBBLES_XL                | TRANSLATOR     | PEBBLES          | 1550 |        17.2297 |     0.5129 |        10.8446 |                       17 |              1.0135 |
|    50 | GALAXY_SOUNDS_SOLAR_FLAMES | PEBBLES_XL                | GALAXY_SOUNDS  | PEBBLES          | 1570 |        16.6478 |     0.5344 |        12.1706 |                       17 |              0.9793 |
|   200 | PANEL_2X4                  | PEBBLES_XL                | PANEL          | PEBBLES          | 1510 |        15.2877 |     0.5152 |         4.3523 |                       17 |              0.8993 |
|   100 | GALAXY_SOUNDS_SOLAR_FLAMES | PEBBLES_XL                | GALAXY_SOUNDS  | PEBBLES          | 1565 |        14.5748 |     0.5137 |         6.5675 |                       17 |              0.8573 |
|   200 | MICROCHIP_OVAL             | PEBBLES_XS                | MICROCHIP      | PEBBLES          | 1510 |        13.9189 |     0.5172 |        10.8279 |                        9 |              1.5465 |
|   200 | MICROCHIP_SQUARE           | PEBBLES_XL                | MICROCHIP      | PEBBLES          | 1512 |        13.6481 |     0.4934 |         7.3327 |                       17 |              0.8028 |
|   200 | GALAXY_SOUNDS_SOLAR_FLAMES | MICROCHIP_SQUARE          | GALAXY_SOUNDS  | MICROCHIP        | 1543 |        13.5321 |     0.5113 |         2.4528 |                       12 |              1.1277 |
|   200 | PEBBLES_XL                 | PEBBLES_XS                | PEBBLES        | PEBBLES          | 1491 |        13.2233 |     0.5298 |        11.587  |                        9 |              1.4693 |
|   200 | MICROCHIP_TRIANGLE         | GALAXY_SOUNDS_SOLAR_WINDS | MICROCHIP      | GALAXY_SOUNDS    | 1576 |        12.9962 |     0.5159 |         3.7778 |                       14 |              0.9283 |

## Persistent Sign-Only Pair Markouts

|   lag | leader                        | follower            | leader_group   | follower_group   |     n |   mean_markout |   good_pct |   min_day_mean |   follower_median_spread |   markout_to_spread |
|------:|:------------------------------|:--------------------|:---------------|:-----------------|------:|---------------:|-----------:|---------------:|-------------------------:|--------------------:|
|   200 | TRANSLATOR_VOID_BLUE          | PEBBLES_XL          | TRANSLATOR     | PEBBLES          | 28615 |         5.2078 |     0.5044 |         2.2884 |                       17 |              0.3063 |
|   200 | ROBOT_DISHES                  | PEBBLES_XL          | ROBOT          | PEBBLES          | 21374 |         4.878  |     0.503  |         1.2335 |                       17 |              0.2869 |
|   200 | MICROCHIP_CIRCLE              | PEBBLES_XL          | MICROCHIP      | PEBBLES          | 28564 |         4.6739 |     0.5038 |         1.4178 |                       17 |              0.2749 |
|   100 | UV_VISOR_AMBER                | PEBBLES_XL          | UV_VISOR       | PEBBLES          | 28725 |         3.9251 |     0.5043 |         3.1361 |                       17 |              0.2309 |
|   100 | MICROCHIP_CIRCLE              | PEBBLES_XL          | MICROCHIP      | PEBBLES          | 28859 |         3.4506 |     0.5054 |         0.0277 |                       17 |              0.203  |
|   200 | OXYGEN_SHAKE_GARLIC           | MICROCHIP_TRIANGLE  | OXYGEN_SHAKE   | MICROCHIP        | 28729 |         3.4365 |     0.506  |         0.2786 |                        9 |              0.3818 |
|   200 | SLEEP_POD_POLYESTER           | PEBBLES_M           | SLEEP_POD      | PEBBLES          | 28780 |         3.4008 |     0.5096 |         2.8871 |                       13 |              0.2616 |
|   100 | TRANSLATOR_VOID_BLUE          | PEBBLES_XL          | TRANSLATOR     | PEBBLES          | 28908 |         3.3869 |     0.5029 |         1.5461 |                       17 |              0.1992 |
|   200 | PANEL_1X2                     | SLEEP_POD_POLYESTER | PANEL          | SLEEP_POD        | 28584 |         3.376  |     0.5057 |         1.0591 |                       11 |              0.3069 |
|   200 | GALAXY_SOUNDS_PLANETARY_RINGS | SLEEP_POD_POLYESTER | GALAXY_SOUNDS  | SLEEP_POD        | 28709 |         3.3273 |     0.5105 |         1.372  |                       11 |              0.3025 |
|   200 | GALAXY_SOUNDS_SOLAR_FLAMES    | MICROCHIP_SQUARE    | GALAXY_SOUNDS  | MICROCHIP        | 28716 |         3.2082 |     0.503  |         0.8853 |                       12 |              0.2674 |
|    50 | MICROCHIP_CIRCLE              | PEBBLES_XL          | MICROCHIP      | PEBBLES          | 29005 |         3.2034 |     0.5063 |         1.609  |                       17 |              0.1884 |
|   200 | UV_VISOR_RED                  | PEBBLES_L           | UV_VISOR       | PEBBLES          | 28712 |         3.2032 |     0.5082 |         0.6831 |                       13 |              0.2464 |
|   200 | TRANSLATOR_ASTRO_BLACK        | PEBBLES_L           | TRANSLATOR     | PEBBLES          | 28545 |         3.1327 |     0.5063 |         1.4186 |                       13 |              0.241  |
|   200 | SLEEP_POD_SUEDE               | SLEEP_POD_COTTON    | SLEEP_POD      | SLEEP_POD        | 28682 |         3.0453 |     0.5099 |         0.7576 |                       10 |              0.3045 |

## Volatility-Regime Conditioned Large Moves

High-volatility leader events:

|   lag | leader                        | follower           |   n |   mean_markout |   good_pct |   min_day_mean |   markout_to_spread |
|------:|:------------------------------|:-------------------|----:|---------------:|-----------:|---------------:|--------------------:|
|   100 | TRANSLATOR_VOID_BLUE          | PEBBLES_XL         | 975 |        32.179  |     0.5395 |        20.7814 |              1.8929 |
|   200 | TRANSLATOR_VOID_BLUE          | PEBBLES_XL         | 962 |        31.7375 |     0.5291 |        24.6115 |              1.8669 |
|   100 | SLEEP_POD_NYLON               | PEBBLES_XL         | 965 |        28.1632 |     0.5565 |        21.1852 |              1.6567 |
|   200 | TRANSLATOR_GRAPHITE_MIST      | PEBBLES_L          | 976 |        24.1926 |     0.5615 |        17.2108 |              1.861  |
|   200 | SLEEP_POD_NYLON               | PEBBLES_XL         | 951 |        21.6041 |     0.5195 |         7.7849 |              1.2708 |
|   200 | MICROCHIP_SQUARE              | PEBBLES_XL         | 982 |        20.7882 |     0.501  |        11.0701 |              1.2228 |
|   200 | PEBBLES_XS                    | MICROCHIP_SQUARE   | 924 |        20.4957 |     0.5271 |         0.8213 |              1.708  |
|   200 | SNACKPACK_STRAWBERRY          | MICROCHIP_TRIANGLE | 959 |        19.3196 |     0.561  |        17.0589 |              2.1466 |
|   200 | PANEL_2X4                     | PEBBLES_XL         | 934 |        18.5064 |     0.5096 |         1.1019 |              1.0886 |
|   200 | GALAXY_SOUNDS_PLANETARY_RINGS | MICROCHIP_SQUARE   | 989 |        17.5915 |     0.5197 |         8.3262 |              1.466  |

Low-volatility leader events:

|   lag | leader                     | follower            |   n |   mean_markout |   good_pct |   min_day_mean |   markout_to_spread |
|------:|:---------------------------|:--------------------|----:|---------------:|-----------:|---------------:|--------------------:|
|   200 | SNACKPACK_VANILLA          | PEBBLES_XL          | 613 |        43.3018 |     0.5368 |        30.651  |              2.5472 |
|   200 | GALAXY_SOUNDS_BLACK_HOLES  | PEBBLES_XL          | 590 |        30.622  |     0.5204 |         7.2857 |              1.8013 |
|   100 | GALAXY_SOUNDS_DARK_MATTER  | PEBBLES_XL          | 605 |        23.7463 |     0.5066 |         5.7932 |              1.3968 |
|   200 | UV_VISOR_RED               | PEBBLES_XL          | 608 |        22.7903 |     0.5149 |         4.9571 |              1.3406 |
|   200 | GALAXY_SOUNDS_DARK_MATTER  | PEBBLES_XL          | 598 |        22.4181 |     0.5261 |        13.4523 |              1.3187 |
|   200 | PEBBLES_M                  | PEBBLES_XL          | 590 |        22.0229 |     0.529  |         3.1381 |              1.2955 |
|   200 | PEBBLES_S                  | SLEEP_POD_LAMB_WOOL | 622 |        19.9678 |     0.5494 |        15.4677 |              1.9968 |
|   200 | OXYGEN_SHAKE_GARLIC        | MICROCHIP_TRIANGLE  | 640 |        19.6961 |     0.5524 |         2.1522 |              2.1885 |
|   100 | GALAXY_SOUNDS_SOLAR_FLAMES | PEBBLES_XL          | 587 |        19.4736 |     0.5239 |         3.6887 |              1.1455 |
|   200 | UV_VISOR_YELLOW            | PEBBLES_M           | 581 |        19.08   |     0.5423 |         6.1373 |              1.4677 |

## Cross-Group Leader Categories

Top aggregate large-move cross-group markouts. `positive_pair_pct` is the share of product-pair cells inside the group pair with positive conditional mean.

|   lag | leader_group   | follower_group   |     n |   mean_markout |   positive_pair_pct |   positive_days_min |
|------:|:---------------|:-----------------|------:|---------------:|--------------------:|--------------------:|
|   200 | PANEL          | ROBOT            | 39285 |         2.0406 |                0.8  |                   0 |
|   200 | PEBBLES        | MICROCHIP        | 37950 |         1.6024 |                0.56 |                   0 |
|   100 | PANEL          | SLEEP_POD        | 39785 |         1.2837 |                0.68 |                   1 |
|   100 | PANEL          | ROBOT            | 39785 |         1.1257 |                0.68 |                   0 |
|   200 | UV_VISOR       | GALAXY_SOUNDS    | 38945 |         1.0962 |                0.52 |                   0 |
|   200 | GALAXY_SOUNDS  | OXYGEN_SHAKE     | 38680 |         1.0724 |                0.56 |                   0 |
|   200 | GALAXY_SOUNDS  | MICROCHIP        | 38680 |         1.0584 |                0.6  |                   0 |
|   200 | PEBBLES        | PANEL            | 37950 |         1.0343 |                0.64 |                   0 |
|   200 | ROBOT          | GALAXY_SOUNDS    | 47150 |         1.0094 |                0.6  |                   0 |
|   200 | TRANSLATOR     | MICROCHIP        | 38990 |         0.9285 |                0.6  |                   0 |
|   200 | PEBBLES        | SLEEP_POD        | 37950 |         0.9128 |                0.6  |                   0 |
|   200 | UV_VISOR       | PANEL            | 38945 |         0.8705 |                0.64 |                   0 |
|   200 | MICROCHIP      | UV_VISOR         | 38510 |         0.8116 |                0.68 |                   0 |
|   200 | UV_VISOR       | TRANSLATOR       | 38945 |         0.8113 |                0.64 |                   1 |
|   100 | TRANSLATOR     | MICROCHIP        | 39395 |         0.8089 |                0.6  |                   0 |
|   100 | MICROCHIP      | OXYGEN_SHAKE     | 38855 |         0.7829 |                0.64 |                   1 |
|   100 | SLEEP_POD      | OXYGEN_SHAKE     | 39820 |         0.7604 |                0.6  |                   0 |
|   100 | TRANSLATOR     | GALAXY_SOUNDS    | 39395 |         0.7145 |                0.6  |                   0 |
|   100 | MICROCHIP      | GALAXY_SOUNDS    | 38855 |         0.6998 |                0.56 |                   1 |
|   200 | SLEEP_POD      | OXYGEN_SHAKE     | 39345 |         0.6956 |                0.52 |                   0 |

## Within-Group Sequence Motifs

| group         | leader                    |    n |   avg_responders_5t |   cascade2_pct |   cascade3_pct | top_first_responder         |   top_first_pct_avg |
|:--------------|:--------------------------|-----:|--------------------:|---------------:|---------------:|:----------------------------|--------------------:|
| PEBBLES       | PEBBLES_L                 | 1584 |              3.8668 |         0.9994 |         0.9968 | PEBBLES_M                   |              0.5085 |
| PANEL         | PANEL_2X2                 | 1707 |              3.8776 |         1      |         0.9965 | PANEL_1X2                   |              0.5442 |
| MICROCHIP     | MICROCHIP_CIRCLE          | 1584 |              3.8681 |         1      |         0.9962 | MICROCHIP_OVAL              |              0.5291 |
| TRANSLATOR    | TRANSLATOR_ASTRO_BLACK    | 1549 |              3.8844 |         1      |         0.9961 | TRANSLATOR_ECLIPSE_CHARCOAL |              0.5067 |
| PEBBLES       | PEBBLES_M                 | 1516 |              3.8635 |         1      |         0.996  | PEBBLES_L                   |              0.517  |
| SLEEP_POD     | SLEEP_POD_SUEDE           | 1620 |              3.8531 |         1      |         0.9944 | SLEEP_POD_COTTON            |              0.5219 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL       | 1605 |              3.8698 |         1      |         0.9944 | SLEEP_POD_COTTON            |              0.5451 |
| PANEL         | PANEL_1X4                 | 1597 |              3.8641 |         1      |         0.9944 | PANEL_1X2                   |              0.5233 |
| PEBBLES       | PEBBLES_XS                | 1550 |              3.8606 |         1      |         0.9942 | PEBBLES_L                   |              0.4883 |
| SLEEP_POD     | SLEEP_POD_COTTON          | 1596 |              3.8665 |         1      |         0.9937 | SLEEP_POD_LAMB_WOOL         |              0.515  |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE      | 1586 |              3.855  |         1      |         0.9937 | TRANSLATOR_ASTRO_BLACK      |              0.5292 |
| MICROCHIP     | MICROCHIP_RECTANGLE       | 1575 |              3.8737 |         1      |         0.9937 | MICROCHIP_CIRCLE            |              0.5447 |
| SLEEP_POD     | SLEEP_POD_NYLON           | 1596 |              3.8653 |         1      |         0.9931 | SLEEP_POD_COTTON            |              0.5237 |
| PEBBLES       | PEBBLES_S                 | 1571 |              3.8587 |         1      |         0.993  | PEBBLES_L                   |              0.4877 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_SOLAR_WINDS | 1570 |              3.8535 |         0.9994 |         0.993  | GALAXY_SOUNDS_BLACK_HOLES   |              0.5262 |
| MICROCHIP     | MICROCHIP_OVAL            | 1534 |              3.867  |         1      |         0.9928 | MICROCHIP_CIRCLE            |              0.5247 |
| PEBBLES       | PEBBLES_XL                | 1519 |              3.8644 |         1      |         0.9928 | PEBBLES_L                   |              0.533  |
| SNACKPACK     | SNACKPACK_STRAWBERRY      | 1643 |              3.8241 |         1      |         0.9927 | SNACKPACK_CHOCOLATE         |              0.4951 |
| SLEEP_POD     | SLEEP_POD_POLYESTER       | 1623 |              3.8478 |         0.9994 |         0.9926 | SLEEP_POD_COTTON            |              0.526  |
| TRANSLATOR    | TRANSLATOR_GRAPHITE_MIST  | 1599 |              3.848  |         0.9994 |         0.9925 | TRANSLATOR_ASTRO_BLACK      |              0.5237 |

## Delayed Mean Reversion After Basket Residual Shocks

| group      | target                 |   lag |    n |   mean_resid_reversion |   mean_target_markout |   good_pct |   min_day_target_markout |   resid_sigma |     adf_t |
|:-----------|:-----------------------|------:|-----:|-----------------------:|----------------------:|-----------:|-------------------------:|--------------:|----------:|
| TRANSLATOR | TRANSLATOR_VOID_BLUE   |   200 | 1201 |               223.451  |              113.408  |     0.8118 |                  84.2828 |      329.156  |   -3.7204 |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK |   200 |  847 |               180.506  |              131.22   |     0.8347 |                 110.384  |      347.259  |   -3.1015 |
| UV_VISOR   | UV_VISOR_RED           |   200 | 1846 |               144.563  |               77.7771 |     0.7606 |                  62.4237 |      337.304  |   -3.8341 |
| UV_VISOR   | UV_VISOR_MAGENTA       |   200 | 1171 |               135.433  |              124.092  |     0.8352 |                  67.4808 |      264.083  |   -4.2117 |
| UV_VISOR   | UV_VISOR_AMBER         |   100 | 1279 |               106.588  |               31.7283 |     0.6325 |                   0.8035 |      320.944  |   -4.1256 |
| TRANSLATOR | TRANSLATOR_ASTRO_BLACK |   100 |  862 |               102.32   |               56.076  |     0.6891 |                  29.2824 |      347.259  |   -3.1015 |
| TRANSLATOR | TRANSLATOR_VOID_BLUE   |   100 | 1202 |                93.701  |               51.0283 |     0.703  |                  29.7802 |      329.156  |   -3.7204 |
| UV_VISOR   | UV_VISOR_MAGENTA       |   100 | 1171 |                83.0573 |               77.0149 |     0.7506 |                  36.5934 |      264.083  |   -4.2117 |
| UV_VISOR   | UV_VISOR_RED           |   100 | 1846 |                73.1116 |               40.6444 |     0.6441 |                  16.7305 |      337.304  |   -3.8341 |
| SNACKPACK  | SNACKPACK_STRAWBERRY   |   200 |  912 |                72.7248 |               64.6096 |     0.6798 |                  52.4681 |      163.084  |   -4.8628 |
| UV_VISOR   | UV_VISOR_AMBER         |    50 | 1279 |                46.7435 |               13.303  |     0.5841 |                   1.0299 |      320.944  |   -4.1256 |
| TRANSLATOR | TRANSLATOR_VOID_BLUE   |    50 | 1206 |                44.4785 |               26.4772 |     0.5879 |                   8.8874 |      329.156  |   -3.7204 |
| UV_VISOR   | UV_VISOR_MAGENTA       |    50 | 1171 |                44.0905 |               39.6234 |     0.6388 |                  11.6621 |      264.083  |   -4.2117 |
| SNACKPACK  | SNACKPACK_STRAWBERRY   |   100 |  912 |                38.6152 |               37.9529 |     0.6941 |                  33.1174 |      163.084  |   -4.8628 |
| UV_VISOR   | UV_VISOR_RED           |    50 | 1846 |                36.7873 |               22.2511 |     0.5785 |                   6.1656 |      337.304  |   -3.8341 |
| SNACKPACK  | SNACKPACK_PISTACHIO    |   200 |  632 |                27.7778 |               22.3157 |     0.5759 |                  20.5189 |       89.905  |   -3.3772 |
| UV_VISOR   | UV_VISOR_AMBER         |    20 | 1280 |                22.4065 |                4.859  |     0.5969 |                   1.4642 |      320.944  |   -4.1256 |
| SNACKPACK  | SNACKPACK_RASPBERRY    |   200 | 1235 |                22.0523 |               12.5417 |     0.5684 |                   6.3753 |       85.6577 |   -3.7588 |
| SNACKPACK  | SNACKPACK_STRAWBERRY   |    50 |  912 |                20.5429 |               18.7604 |     0.6294 |                  14.7666 |      163.084  |   -4.8628 |
| UV_VISOR   | UV_VISOR_MAGENTA       |    20 | 1171 |                20.4034 |               18.6896 |     0.6302 |                   8.0027 |      264.083  |   -4.2117 |
| SNACKPACK  | SNACKPACK_PISTACHIO    |   100 |  646 |                18.161  |               11.3344 |     0.5418 |                   0.5    |       89.905  |   -3.3772 |
| PEBBLES    | PEBBLES_XS             |    20 |  853 |                16.5779 |                3.5147 |     0.5287 |                   2.5857 |        2.7984 | -170.961  |
| PEBBLES    | PEBBLES_XL             |     2 |  853 |                16.4689 |                4.8763 |     0.5803 |                   3.5892 |        2.7984 | -170.963  |
| PEBBLES    | PEBBLES_XS             |     2 |  853 |                16.4689 |                2.7491 |     0.5487 |                   1.9306 |        2.7984 | -170.961  |
| PEBBLES    | PEBBLES_L              |     2 |  853 |                16.4688 |                2.5563 |     0.5346 |                   1.6451 |        2.7984 | -170.96   |

## Interpretation

- Large-move lead-lag effects can reach roughly one median spread at long lags, but hit rates are only slightly above coin-flip; sign-only effects are smaller. Treat them as inventory skew context unless a simulator confirms executable edge.
- Cross-group leader categories do not produce a clean tradable hierarchy; the best aggregate effects are diluted across product pairs, and hit rates stay close to coin-flip at the pair level.
- Within-group motifs are useful diagnostics for synchronized groups, not a standalone trigger: high cascade rates mostly identify simultaneous group movement after a large print.
- Residual shock reversion is the only lens here that produces persistent conditional markouts. Slow TRANSLATOR/UV/SNACKPACK shocks deserve follow-up, while fast PEBBLES shocks remain the cleanest implementation path because the basket relation is already structurally confirmed.