# Mark 55 Counterparty Taxonomy

Scope: Round 4 days 1-3, `data/ROUND4` prices/trades. Markout convention is from Mark 55's perspective: buy = `future_mid - trade_price`, sell = `trade_price - future_mid`. Forward mid uses the first book row with timestamp >= `trade_timestamp + horizon`, matching the convention used in current project validation.

## Files Created
- `notebooks/round4/mark_taxonomy/mark_55.py`
- `notebooks/round4/mark_taxonomy/mark_55_events.csv`
- `notebooks/round4/mark_taxonomy/mark_55_product_side_day.csv`
- `notebooks/round4/mark_taxonomy/mark_55_markouts_product_side_day.csv`
- `notebooks/round4/mark_taxonomy/mark_55_markouts_product_side.csv`
- `notebooks/round4/mark_taxonomy/mark_55_counterparties.csv`
- `notebooks/round4/mark_taxonomy/mark_55_timing_gaps.csv`
- `notebooks/round4/mark_taxonomy/mark_55_repeat_timestamps.csv`
- `notebooks/round4/mark_taxonomy/mark_55_cross_day_recurrence.csv`
- `notebooks/round4/mark_taxonomy/mark_55_side_transitions.csv`
- `notebooks/round4/mark_taxonomy/mark_55_same_timestamp_participants.csv`
- `notebooks/round4/mark_taxonomy/mark_55_book_baselines.csv`

## Executive Read
- Mark 55 appears in 1198 trades across 1 products: VELVETFRUIT_EXTRACT.
- No Mark 55 trades in: HYDROGEL_PACK, VEV_4000, VEV_4500, VEV_5000, VEV_5100, VEV_5200, VEV_5300, VEV_5400, VEV_5500, VEV_6000, VEV_6500.
- Side mix is balanced: 598 buys / 600 sells, 3254 buy qty / 3297 sell qty. Every buy printed at same-timestamp ask and every sell printed at same-timestamp bid, so Mark 55 is a displayed-touch liquidity taker under the book-snapshot proxy.
- Mean signed mid move is near zero at t+200: +0.085 for buys and +0.008 for sells. Mark 55's negative edge is almost entirely spread paid, not directional follow-through.
- Worst t+200 Mark 55 edge is VELVETFRUIT_EXTRACT sell: mean -2.460, quantity-weighted -2.453, total unit edge -8087.0 over n=600. Negative edge for Mark 55 means favorable for the counterparty at the historical trade price.
- No product/side has positive Mark 55 edge at t+200. There is no evidence here for suppressing VFE after Mark 55 flow.
- Same-timestamp book relation is only a proxy for aggressor/passive status because trade prints and book rows are replay snapshots, not an explicit aggressor flag.

## Product And Side Inventory
| symbol              | mark_side   |   day |   trades |   qty |   avg_qty |   median_qty |   min_qty |   max_qty |   mean_price_vs_mid |   mean_spread |   mean_top_depth |   mean_spread_pctile |   mean_depth_pctile |
|:--------------------|:------------|------:|---------:|------:|----------:|-------------:|----------:|----------:|--------------------:|--------------:|-----------------:|---------------------:|--------------------:|
| VELVETFRUIT_EXTRACT | buy         |     1 |      186 |  1011 |     5.435 |            5 |         3 |         8 |               2.484 |         4.968 |           70.199 |                0.792 |               0.451 |
| VELVETFRUIT_EXTRACT | buy         |     2 |      218 |  1190 |     5.459 |            5 |         3 |         8 |               2.509 |         5.018 |           75.275 |                0.802 |               0.51  |
| VELVETFRUIT_EXTRACT | buy         |     3 |      194 |  1053 |     5.428 |            5 |         3 |         8 |               2.49  |         4.979 |           73.83  |                0.801 |               0.491 |
| VELVETFRUIT_EXTRACT | sell        |     1 |      198 |  1098 |     5.545 |            6 |         3 |         8 |              -2.447 |         4.894 |           73.126 |                0.774 |               0.492 |
| VELVETFRUIT_EXTRACT | sell        |     2 |      193 |  1099 |     5.694 |            6 |         3 |         8 |              -2.451 |         4.902 |           76.078 |                0.766 |               0.521 |
| VELVETFRUIT_EXTRACT | sell        |     3 |      209 |  1100 |     5.263 |            5 |         1 |         8 |              -2.505 |         5.01  |           73.196 |                0.808 |               0.484 |

## Overall Side Bias
| mark_side   |   trades |   qty |   avg_qty |   median_qty |
|:------------|---------:|------:|----------:|-------------:|
| buy         |      598 |  3254 |     5.441 |            5 |
| sell        |      600 |  3297 |     5.495 |            6 |

## Price Relation To Same-Timestamp Book
| symbol              | mark_side   | book_relation   |   trades |   qty |
|:--------------------|:------------|:----------------|---------:|------:|
| VELVETFRUIT_EXTRACT | buy         | at_ask          |      598 |  3254 |
| VELVETFRUIT_EXTRACT | sell        | at_bid          |      600 |  3297 |

## Liquidity Proxy
| symbol              | mark_side   | liquidity_proxy   |   trades |   qty |
|:--------------------|:------------|:------------------|---------:|------:|
| VELVETFRUIT_EXTRACT | buy         | taker_proxy       |      598 |  3254 |
| VELVETFRUIT_EXTRACT | sell        | taker_proxy       |      600 |  3297 |

## Book Regimes
Event spread/depth percentiles are computed within the same product-day book distribution; 0.50 is median regime, high spread percentile means wider-than-usual displayed spread.
| symbol              | mark_side   |   day |   trades |   mean_spread |   mean_top_depth |   mean_spread_pctile |   mean_depth_pctile |
|:--------------------|:------------|------:|---------:|--------------:|-----------------:|---------------------:|--------------------:|
| VELVETFRUIT_EXTRACT | buy         |     1 |      186 |         4.968 |           70.199 |                0.792 |               0.451 |
| VELVETFRUIT_EXTRACT | buy         |     2 |      218 |         5.018 |           75.275 |                0.802 |               0.51  |
| VELVETFRUIT_EXTRACT | buy         |     3 |      194 |         4.979 |           73.83  |                0.801 |               0.491 |
| VELVETFRUIT_EXTRACT | sell        |     1 |      198 |         4.894 |           73.126 |                0.774 |               0.492 |
| VELVETFRUIT_EXTRACT | sell        |     2 |      193 |         4.902 |           76.078 |                0.766 |               0.521 |
| VELVETFRUIT_EXTRACT | sell        |     3 |      209 |         5.01  |           73.196 |                0.808 |               0.484 |

Book baselines for traded products:
| product             |   day |   book_rows |   median_spread |   mean_spread |   p90_spread |   median_top_depth |   mean_top_depth |
|:--------------------|------:|------------:|----------------:|--------------:|-------------:|-------------------:|-----------------:|
| VELVETFRUIT_EXTRACT |     1 |       10000 |               5 |         4.985 |            6 |                 78 |           75.559 |
| VELVETFRUIT_EXTRACT |     2 |       10000 |               5 |         4.986 |            6 |                 77 |           75.583 |
| VELVETFRUIT_EXTRACT |     3 |       10000 |               5 |         4.976 |            6 |                 77 |           75.48  |

## Markouts By Product Side Day
| symbol              | mark_side   |   day |   n |   qty |   mean_edge_vs_trade |   median_edge_vs_trade |   total_unit_edge |   mean_unit_edge |   win_rate |   mean_signed_mid_move |   median_signed_mid_move |   horizon |
|:--------------------|:------------|------:|----:|------:|---------------------:|-----------------------:|------------------:|-----------------:|-----------:|-----------------------:|-------------------------:|----------:|
| VELVETFRUIT_EXTRACT | buy         |     1 | 186 |  1011 |               -2.618 |                   -2.5 |           -2665.5 |           -2.636 |      0.027 |                 -0.134 |                      0   |        10 |
| VELVETFRUIT_EXTRACT | buy         |     1 | 186 |  1011 |               -2.618 |                   -2.5 |           -2665.5 |           -2.636 |      0.027 |                 -0.134 |                      0   |        50 |
| VELVETFRUIT_EXTRACT | buy         |     1 | 186 |  1011 |               -2.495 |                   -2.5 |           -2561.5 |           -2.534 |      0.065 |                 -0.011 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | buy         |     1 | 186 |  1011 |               -2.409 |                   -2.5 |           -2461   |           -2.434 |      0.145 |                  0.075 |                      0   |       500 |
| VELVETFRUIT_EXTRACT | buy         |     2 | 218 |  1190 |               -2.438 |                   -2.5 |           -2946.5 |           -2.476 |      0.023 |                  0.071 |                      0   |        10 |
| VELVETFRUIT_EXTRACT | buy         |     2 | 218 |  1190 |               -2.438 |                   -2.5 |           -2946.5 |           -2.476 |      0.023 |                  0.071 |                      0   |        50 |
| VELVETFRUIT_EXTRACT | buy         |     2 | 218 |  1190 |               -2.415 |                   -2.5 |           -2887   |           -2.426 |      0.073 |                  0.094 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | buy         |     2 | 218 |  1190 |               -2.287 |                   -2.5 |           -2728.5 |           -2.293 |      0.142 |                  0.222 |                      0   |       500 |
| VELVETFRUIT_EXTRACT | buy         |     3 | 194 |  1053 |               -2.41  |                   -2.5 |           -2505.5 |           -2.379 |      0.041 |                  0.08  |                      0   |        10 |
| VELVETFRUIT_EXTRACT | buy         |     3 | 194 |  1053 |               -2.41  |                   -2.5 |           -2505.5 |           -2.379 |      0.041 |                  0.08  |                      0   |        50 |
| VELVETFRUIT_EXTRACT | buy         |     3 | 194 |  1053 |               -2.322 |                   -2.5 |           -2421.5 |           -2.3   |      0.052 |                  0.168 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | buy         |     3 | 194 |  1053 |               -2.198 |                   -2.5 |           -2272   |           -2.158 |      0.129 |                  0.291 |                      0   |       500 |
| VELVETFRUIT_EXTRACT | sell        |     1 | 198 |  1098 |               -2.545 |                   -2.5 |           -2766   |           -2.519 |      0.035 |                 -0.098 |                      0   |        10 |
| VELVETFRUIT_EXTRACT | sell        |     1 | 198 |  1098 |               -2.545 |                   -2.5 |           -2766   |           -2.519 |      0.035 |                 -0.098 |                      0   |        50 |
| VELVETFRUIT_EXTRACT | sell        |     1 | 198 |  1098 |               -2.654 |                   -2.5 |           -2942   |           -2.679 |      0.025 |                 -0.207 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | sell        |     1 | 198 |  1098 |               -2.737 |                   -2.5 |           -3036.5 |           -2.765 |      0.106 |                 -0.29  |                     -0.5 |       500 |
| VELVETFRUIT_EXTRACT | sell        |     2 | 193 |  1099 |               -2.218 |                   -2.5 |           -2425   |           -2.207 |      0.021 |                  0.233 |                      0   |        10 |
| VELVETFRUIT_EXTRACT | sell        |     2 | 193 |  1099 |               -2.218 |                   -2.5 |           -2425   |           -2.207 |      0.021 |                  0.233 |                      0   |        50 |
| VELVETFRUIT_EXTRACT | sell        |     2 | 193 |  1099 |               -2.145 |                   -2.5 |           -2333.5 |           -2.123 |      0.078 |                  0.306 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | sell        |     2 | 193 |  1099 |               -2.187 |                   -2.5 |           -2406   |           -2.189 |      0.13  |                  0.264 |                      0   |       500 |
| VELVETFRUIT_EXTRACT | sell        |     3 | 209 |  1100 |               -2.524 |                   -2.5 |           -2774   |           -2.522 |      0.01  |                 -0.019 |                      0   |        10 |
| VELVETFRUIT_EXTRACT | sell        |     3 | 209 |  1100 |               -2.524 |                   -2.5 |           -2774   |           -2.522 |      0.01  |                 -0.019 |                      0   |        50 |
| VELVETFRUIT_EXTRACT | sell        |     3 | 209 |  1100 |               -2.567 |                   -2.5 |           -2811.5 |           -2.556 |      0.038 |                 -0.062 |                      0   |       200 |
| VELVETFRUIT_EXTRACT | sell        |     3 | 209 |  1100 |               -2.622 |                   -2.5 |           -2893.5 |           -2.63  |      0.096 |                 -0.117 |                      0   |       500 |

## Markouts Aggregated Across Days
| symbol              | mark_side   |   n |   qty |   mean_edge_vs_trade |   median_edge_vs_trade |   total_unit_edge |   mean_unit_edge |   win_rate |   mean_signed_mid_move |   median_signed_mid_move |   horizon |
|:--------------------|:------------|----:|------:|---------------------:|-----------------------:|------------------:|-----------------:|-----------:|-----------------------:|-------------------------:|----------:|
| VELVETFRUIT_EXTRACT | buy         | 598 |  3254 |               -2.485 |                   -2.5 |           -8117.5 |           -2.495 |      0.03  |                  0.01  |                        0 |        10 |
| VELVETFRUIT_EXTRACT | buy         | 598 |  3254 |               -2.485 |                   -2.5 |           -8117.5 |           -2.495 |      0.03  |                  0.01  |                        0 |        50 |
| VELVETFRUIT_EXTRACT | buy         | 598 |  3254 |               -2.41  |                   -2.5 |           -7870   |           -2.419 |      0.064 |                  0.085 |                        0 |       200 |
| VELVETFRUIT_EXTRACT | buy         | 598 |  3254 |               -2.296 |                   -2.5 |           -7461.5 |           -2.293 |      0.139 |                  0.199 |                        0 |       500 |
| VELVETFRUIT_EXTRACT | sell        | 600 |  3297 |               -2.433 |                   -2.5 |           -7965   |           -2.416 |      0.022 |                  0.036 |                        0 |        10 |
| VELVETFRUIT_EXTRACT | sell        | 600 |  3297 |               -2.433 |                   -2.5 |           -7965   |           -2.416 |      0.022 |                  0.036 |                        0 |        50 |
| VELVETFRUIT_EXTRACT | sell        | 600 |  3297 |               -2.46  |                   -2.5 |           -8087   |           -2.453 |      0.047 |                  0.008 |                        0 |       200 |
| VELVETFRUIT_EXTRACT | sell        | 600 |  3297 |               -2.52  |                   -2.5 |           -8336   |           -2.528 |      0.11  |                 -0.052 |                        0 |       500 |

## Size Distributions
| symbol              | mark_side   |   trades |   qty |   mean_qty |   median_qty |   min_qty |   p25_qty |   p75_qty |   max_qty | unique_qty    |   mode_qty |
|:--------------------|:------------|---------:|------:|-----------:|-------------:|----------:|----------:|----------:|----------:|:--------------|-----------:|
| VELVETFRUIT_EXTRACT | buy         |      598 |  3254 |      5.441 |            5 |         3 |         4 |         7 |         8 | 3,4,5,6,7,8   |          5 |
| VELVETFRUIT_EXTRACT | sell        |      600 |  3297 |      5.495 |            6 |         1 |         4 |         7 |         8 | 1,3,4,5,6,7,8 |          6 |

## Timing Gaps And Periodicity
| symbol              | mark_side   |   day |   events |   gap_n |   mean_gap |   median_gap |   min_gap |   max_gap | top_gap_counts                         |
|:--------------------|:------------|------:|---------:|--------:|-----------:|-------------:|----------:|----------:|:---------------------------------------|
| VELVETFRUIT_EXTRACT | buy         |     1 |      186 |     185 |    5307.57 |         3300 |       100 |     37500 | 900x12, 3000x6, 800x6, 3100x5, 2000x5  |
| VELVETFRUIT_EXTRACT | buy         |     2 |      218 |     217 |    4572.35 |         3300 |       100 |     22500 | 400x8, 2500x7, 4400x6, 2400x6, 800x6   |
| VELVETFRUIT_EXTRACT | buy         |     3 |      194 |     193 |    5113.47 |         3500 |       100 |     30200 | 100x7, 1600x6, 3400x5, 2700x5, 1200x5  |
| VELVETFRUIT_EXTRACT | sell        |     1 |      198 |     197 |    4958.38 |         3300 |       100 |     25500 | 2200x10, 1800x6, 700x6, 3700x5, 1500x5 |
| VELVETFRUIT_EXTRACT | sell        |     2 |      193 |     192 |    5176.04 |         3650 |       100 |     27900 | 1500x9, 1200x5, 600x5, 5700x4, 4400x4  |
| VELVETFRUIT_EXTRACT | sell        |     3 |      209 |     208 |    4702.89 |         3000 |         0 |     27900 | 2400x6, 1800x6, 700x6, 200x6, 5300x5   |

Timestamp modulo concentration:
|   mod_value |   trades | mod_field   |
|------------:|---------:|:------------|
|           0 |      133 | mod_1000    |
|         100 |      129 | mod_1000    |
|         400 |      126 | mod_1000    |
|         500 |      125 | mod_1000    |
|         300 |      123 | mod_1000    |
|         700 |      123 | mod_1000    |
|         600 |      117 | mod_1000    |
|         800 |      110 | mod_1000    |
|         200 |      109 | mod_1000    |
|         900 |      103 | mod_1000    |
|        2600 |       34 | mod_5000    |
|         100 |       32 | mod_5000    |
|        4800 |       31 | mod_5000    |
|        2400 |       31 | mod_5000    |
|        3000 |       31 | mod_5000    |
|        3400 |       29 | mod_5000    |
|        4900 |       28 | mod_5000    |
|        1700 |       28 | mod_5000    |
|        1000 |       28 | mod_5000    |
|         700 |       28 | mod_5000    |
|        1700 |       20 | mod_10000   |
|        3000 |       19 | mod_10000   |
|        2600 |       19 | mod_10000   |
|        7400 |       19 | mod_10000   |
|        5100 |       19 | mod_10000   |
|        6000 |       18 | mod_10000   |
|        6100 |       17 | mod_10000   |
|        9800 |       17 | mod_10000   |
|        8400 |       17 | mod_10000   |
|        2100 |       17 | mod_10000   |

Side transitions:
| day   |   events |   transitions |   same_side_next_rate |   buy_rate |
|:------|---------:|--------------:|----------------------:|-----------:|
| 1     |      384 |           383 |                 0.574 |      0.484 |
| 2     |      411 |           410 |                 0.507 |      0.53  |
| 3     |      403 |           402 |                 0.517 |      0.481 |
| all   |     1198 |          1197 |                 0.532 |      0.499 |

## Repeat Timestamps
|   day |   timestamp |   trades | products            | sides   |   qty |
|------:|------------:|---------:|:--------------------|:--------|------:|
|     3 |      896800 |        2 | VELVETFRUIT_EXTRACT | sell    |     6 |

Cross-day timestamp/product/side recurrence:
|   timestamp | symbol              | mark_side   | days   |   day_count |   trades |   qty |
|------------:|:--------------------|:------------|:-------|------------:|---------:|------:|
|       67600 | VELVETFRUIT_EXTRACT | buy         | 2,3    |           2 |        2 |    11 |
|       77300 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |    16 |
|       91700 | VELVETFRUIT_EXTRACT | sell        | 2,3    |           2 |        2 |    14 |
|       93700 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |    10 |
|      192600 | VELVETFRUIT_EXTRACT | sell        | 1,3    |           2 |        2 |     9 |
|      207600 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |     9 |
|      506200 | VELVETFRUIT_EXTRACT | sell        | 1,3    |           2 |        2 |     9 |
|      566100 | VELVETFRUIT_EXTRACT | sell        | 2,3    |           2 |        2 |     7 |
|      702500 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |     8 |
|      721200 | VELVETFRUIT_EXTRACT | sell        | 1,2    |           2 |        2 |     7 |
|      722300 | VELVETFRUIT_EXTRACT | buy         | 1,2    |           2 |        2 |    10 |
|      762800 | VELVETFRUIT_EXTRACT | buy         | 2,3    |           2 |        2 |    11 |
|      787700 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |    12 |
|      807400 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |     9 |
|      812400 | VELVETFRUIT_EXTRACT | sell        | 1,3    |           2 |        2 |    12 |
|      877600 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |    12 |
|      904000 | VELVETFRUIT_EXTRACT | buy         | 1,2    |           2 |        2 |    11 |
|      936600 | VELVETFRUIT_EXTRACT | sell        | 1,2    |           2 |        2 |    15 |
|      973300 | VELVETFRUIT_EXTRACT | buy         | 1,3    |           2 |        2 |    13 |

## Direct Counterparties
| counterparty   | symbol              | mark_side   |   trades |   qty |   avg_qty |   mean_edge_t200 |   win_t200 |
|:---------------|:--------------------|:------------|---------:|------:|----------:|-----------------:|-----------:|
| Mark 14        | VELVETFRUIT_EXTRACT | buy         |      331 |  1763 |     5.326 |           -2.304 |      0.06  |
| Mark 14        | VELVETFRUIT_EXTRACT | sell        |      316 |  1761 |     5.573 |           -2.339 |      0.028 |
| Mark 01        | VELVETFRUIT_EXTRACT | sell        |      260 |  1417 |     5.45  |           -2.804 |      0.035 |
| Mark 01        | VELVETFRUIT_EXTRACT | buy         |      244 |  1375 |     5.635 |           -2.83  |      0.012 |
| Mark 22        | VELVETFRUIT_EXTRACT | sell        |       18 |    92 |     5.111 |           -0.194 |      0.444 |
| Mark 22        | VELVETFRUIT_EXTRACT | buy         |       14 |    62 |     4.429 |            0.286 |      0.643 |
| Mark 49        | VELVETFRUIT_EXTRACT | buy         |        9 |    54 |     6     |            0.889 |      0.667 |
| Mark 49        | VELVETFRUIT_EXTRACT | sell        |        5 |    26 |     5.2   |           -0.5   |      0.4   |
| Mark 67        | VELVETFRUIT_EXTRACT | sell        |        1 |     1 |     1     |           -2     |      0     |

## Same-Timestamp Interactions
Other participants appearing in non-Mark-55 prints at timestamps where Mark 55 also traded:
| other_mark   | symbol              |   same_ts_trades |   same_ts_qty | role   |
|:-------------|:--------------------|-----------------:|--------------:|:-------|
| Mark 14      | HYDROGEL_PACK       |               20 |            88 | seller |
| Mark 38      | HYDROGEL_PACK       |               20 |            88 | buyer  |
| Mark 38      | HYDROGEL_PACK       |               13 |            55 | seller |
| Mark 14      | HYDROGEL_PACK       |               13 |            55 | buyer  |
| Mark 22      | VEV_6500            |               12 |            45 | seller |
| Mark 22      | VEV_6000            |               12 |            45 | seller |
| Mark 22      | VEV_5400            |               12 |            45 | seller |
| Mark 01      | VEV_6500            |               12 |            45 | buyer  |
| Mark 01      | VEV_6000            |               12 |            45 | buyer  |
| Mark 22      | VEV_5500            |               11 |            43 | seller |
| Mark 01      | VEV_5500            |               11 |            43 | buyer  |
| Mark 01      | VEV_5400            |               10 |            36 | buyer  |
| Mark 22      | VEV_5300            |                9 |            36 | seller |
| Mark 38      | VEV_4000            |                6 |            12 | seller |
| Mark 14      | VEV_4000            |                6 |            12 | buyer  |
| Mark 38      | VEV_4000            |                6 |            13 | buyer  |
| Mark 14      | VEV_4000            |                6 |            13 | seller |
| Mark 01      | VEV_5300            |                5 |            19 | buyer  |
| Mark 49      | VELVETFRUIT_EXTRACT |                4 |            35 | seller |
| Mark 67      | VELVETFRUIT_EXTRACT |                4 |            30 | buyer  |
| Mark 14      | VEV_5300            |                4 |            17 | buyer  |
| Mark 22      | VELVETFRUIT_EXTRACT |                3 |            23 | seller |
| Mark 22      | VELVETFRUIT_EXTRACT |                2 |            18 | buyer  |
| Mark 14      | VEV_5400            |                2 |             9 | buyer  |
| Mark 22      | VEV_5200            |                1 |             5 | seller |
| Mark 14      | VEV_5200            |                1 |             5 | buyer  |
| Mark 49      | VELVETFRUIT_EXTRACT |                1 |            10 | buyer  |

Most crowded Mark 55 timestamps:
|   day |   timestamp |   all_trades |   mark55_trades_real |   other_trades |
|------:|------------:|-------------:|---------------------:|---------------:|
|     3 |      877600 |            7 |                    1 |              6 |
|     1 |       14800 |            6 |                    1 |              5 |
|     1 |      489700 |            6 |                    1 |              5 |
|     1 |      720500 |            6 |                    1 |              5 |
|     2 |      483400 |            6 |                    1 |              5 |
|     2 |      554600 |            6 |                    1 |              5 |
|     3 |      320200 |            6 |                    1 |              5 |
|     3 |      943900 |            6 |                    1 |              5 |
|     2 |      555700 |            5 |                    1 |              4 |
|     3 |      547600 |            5 |                    1 |              4 |
|     3 |      785100 |            5 |                    1 |              4 |
|     3 |      807400 |            5 |                    1 |              4 |
|     1 |       63200 |            2 |                    1 |              1 |
|     1 |       73400 |            2 |                    1 |              1 |
|     1 |       82300 |            2 |                    1 |              1 |
|     1 |      167600 |            2 |                    1 |              1 |
|     1 |      218900 |            2 |                    1 |              1 |
|     1 |      239600 |            2 |                    1 |              1 |
|     1 |      269300 |            2 |                    1 |              1 |
|     1 |      282200 |            2 |                    1 |              1 |
|     1 |      335300 |            2 |                    1 |              1 |
|     1 |      345700 |            2 |                    1 |              1 |
|     1 |      459900 |            2 |                    1 |              1 |
|     1 |      527700 |            2 |                    1 |              1 |
|     1 |      537500 |            2 |                    1 |              1 |
|     1 |      612900 |            2 |                    1 |              1 |
|     1 |      634800 |            2 |                    1 |              1 |
|     1 |      725800 |            2 |                    1 |              1 |
|     1 |      792200 |            2 |                    1 |              1 |
|     1 |      815000 |            2 |                    1 |              1 |
|     1 |      988000 |            2 |                    1 |              1 |
|     2 |       85500 |            2 |                    1 |              1 |
|     2 |       91700 |            2 |                    1 |              1 |
|     2 |      212100 |            2 |                    1 |              1 |
|     2 |      278800 |            2 |                    1 |              1 |
|     2 |      282600 |            2 |                    1 |              1 |
|     2 |      288000 |            2 |                    1 |              1 |
|     2 |      328700 |            2 |                    1 |              1 |
|     2 |      344600 |            2 |                    1 |              1 |
|     2 |      372300 |            2 |                    1 |              1 |

## Read Against v314159
- v314159 currently reacts to Mark 22 option selling and Mark 67/Mark 49 VFE flow. Mark 55 is not referenced.
- Mark 55 does not argue for suppressing or widening VFE after observed flow: the Mark 55 side itself is not directionally predictive, and its t+200/t+500 edge is negative for Mark 55 on both sides.
- Mark 55 is incremental support for passive VFE liquidity provision in general: counterparties to Mark 55 earn about +2.4 to +2.5 per unit at t+200 simply by being at the touch. v314159 already has a validated VFE passive sleeve, so this is not a standalone reason to change the baseline.
- Recommendation: ignore Mark 55 for reactive overlays. Do not add a Mark 55 suppress/skew rule without a separate executable test; if testing anything, the only plausible direction is a one-factor VFE passive-tightening/fill-capture experiment, not a risk-off filter.

## Classification
VFE-only balanced liquidity taker / noise flow. It pays the spread, trades small sizes, shows weak timestamp recurrence, and has near-zero signed mid movement after prints. It is not an informed/adverse counterparty in the historical trade-price data.
