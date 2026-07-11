# Round 5 Lens 4 - Trade Flow, Participants, Timing

Data: `data/ROUND5/trades_round_5_day_*.csv` joined to same-day `prices_round_5_day_*.csv` on `(day, timestamp, product)`.
Side is inferred from book touch: prints at or above best ask are buyer-initiated; prints at or below best bid are seller-initiated.

## Actionable Findings

- **No named counterparty signal exists in Round 5 trade CSVs.** Buyer/seller non-blank count is 0 out of 35,385 rows, so there is no direct `Mark`/`Olivia` participant to copy or fade.
- **Every trade is part of a synchronized 5-product group basket.** Full group basket events account for 35,385 / 35,385 rows; events are 3,485 all-buy and 3,592 all-sell with 0 mixed-side events. Treat public flow as group-level inventory pressure, not single-name informed flow.
- **All prints occur exactly at best bid or best ask and all rows join to the book.** Crossing immediately after these prints is not supported by t+200 evidence: both inferred sides still have negative average trade-price edge after spread at t+200.
- **PEBBLES trade flow does not improve the confirmed PEBBLES basket-arb thesis.** PEBBLES group basket markouts are near flat at t+200 (`buy_at_ask` +0.023, `sell_at_bid` +0.071 mid points) and t+1000 (`buy_at_ask` -0.022, `sell_at_bid` +0.038), so use basket residuals rather than public-trade side as the main trigger.
- **Opening/closing flow is not a special regime.** First/last 100k timestamps are close to calendar share: most groups are about 10.2% open and 10.9% close; PEBBLES is 10.4% / 11.2%. No open/close-only rule is justified from flow counts.
- **Weak hidden-flow watchlist, not promotion:** persistent t+1000 mid-direction examples exist, but spread-adjusted edge is inconsistent. `PEBBLES_M buy_at_ask` has +7.396 average t+1000 mid markout across all 3 days, while `PEBBLES_XL buy_at_ask` has -5.244 across all 3 days; these are better used as quote-suppression/context filters than crossing signals.

## Coverage

|   day |   trades |   products |   timestamps |   first_ts |   last_ts |   book_join_rate |   quantity |
|------:|---------:|-----------:|-------------:|-----------:|----------:|-----------------:|-----------:|
|     2 |    11090 |         50 |          603 |       1700 |    998400 |                1 |      27960 |
|     3 |    12320 |         50 |          668 |       1000 |    999500 |                1 |      32020 |
|     4 |    11975 |         50 |          637 |        800 |    999400 |                1 |      29230 |

## Counterparty Availability

| field   |   rows |   non_blank |   unique_non_blank |
|:--------|-------:|------------:|-------------------:|
| buyer   |  35385 |           0 |                  0 |
| seller  |  35385 |           0 |                  0 |

No non-blank buyer or seller names appear in any Round 5 trade row.

## Book Join And Touch Relation

| side        |     n |   qty |   avg_qty |   median_half_spread |   mean_mid_markout_200 |   mean_price_edge_200 |
|:------------|------:|------:|----------:|---------------------:|-----------------------:|----------------------:|
| sell_at_bid | 17960 | 45345 |   2.52478 |                  5.5 |               0.006013 |              -5.66587 |
| buy_at_ask  | 17425 | 43865 |   2.51736 |                  5.5 |               0.151076 |              -5.53288 |

Interpretation: every joined print is a touch print. `mean_price_edge_200` is negative for both inferred sides, so blindly crossing in the same direction after observing a trade does not pay the spread at t+200.

## Group Cadence

| group         |   trades |   avg_trades_per_product_day |   median_product_gap |   p10_product_gap |   p90_product_gap |   same_product_same_ts_extra |
|:--------------|---------:|-----------------------------:|---------------------:|------------------:|------------------:|-----------------------------:|
| GALAXY_SOUNDS |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| OXYGEN_SHAKE  |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| PANEL         |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| ROBOT         |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| SLEEP_POD     |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| SNACKPACK     |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| TRANSLATOR    |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| UV_VISOR      |     3665 |                      244.333 |                 2900 |               600 |              9060 |                            0 |
| PEBBLES       |     3220 |                      214.667 |                 3000 |               700 |             10600 |                            0 |
| MICROCHIP     |     2845 |                      189.667 |                 3800 |               600 |             12780 |                            0 |

There are no duplicate timestamps within the same product/day; repeated timestamps are cross-product basket events.

## Synchronized Basket Events

| group         |   full_group_events |   all_buy_events |   all_sell_events |   mixed_events |   days |   avg_event_qty |   median_event_qty |   mean_mid_markout_200 |   mean_mid_markout_1000 |
|:--------------|--------------------:|-----------------:|------------------:|---------------:|-------:|----------------:|-------------------:|-----------------------:|------------------------:|
| GALAXY_SOUNDS |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                -0.5797 |                 -0.9888 |
| OXYGEN_SHAKE  |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                 0.3277 |                 -0.0981 |
| PANEL         |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                -0.198  |                  0.0685 |
| ROBOT         |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                -0.0172 |                  0.3044 |
| SLEEP_POD     |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                 0.0258 |                 -1.6669 |
| SNACKPACK     |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                 0.0659 |                  0.0847 |
| TRANSLATOR    |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                 0.6296 |                 -0.0732 |
| UV_VISOR      |                 733 |              358 |               375 |              0 |      3 |         12.3124 |                 10 |                 0.567  |                  0.6056 |
| PEBBLES       |                 644 |              321 |               323 |              0 |      3 |         17.7252 |                 20 |                 0.0474 |                  0.0084 |
| MICROCHIP     |                 569 |              300 |               269 |              0 |      3 |          9.833  |                 10 |                -0.1482 |                 -0.3506 |

## Cross-Group Timestamp Repetition

|   products |   groups | side_mix        |   timestamps |   avg_qty |
|-----------:|---------:|:----------------|-------------:|----------:|
|         45 |        9 | 5 buy / 40 sell |            8 |  113.75   |
|         45 |        9 | 40 buy / 5 sell |            7 |  104.286  |
|         45 |        9 | 45 buy / 0 sell |            7 |  125.714  |
|         45 |        9 | 0 buy / 45 sell |            4 |  106.25   |
|         40 |        8 | 0 buy / 40 sell |          363 |   98.7328 |
|         40 |        8 | 40 buy / 0 sell |          344 |   98.2558 |
|         10 |        2 | 5 buy / 5 sell  |            6 |   28.3333 |
|         10 |        2 | 10 buy / 0 sell |            4 |   25      |
|         10 |        2 | 0 buy / 10 sell |            2 |   30      |
|          5 |        1 | 5 buy / 0 sell  |          592 |   13.9611 |
|          5 |        1 | 0 buy / 5 sell  |          571 |   14.063  |

The common 40-product events are the eight non-PEBBLES/non-MICROCHIP groups firing together. PEBBLES and MICROCHIP have separate schedules and sometimes align with the larger synchronized block.

## Basket Size Pattern

| group         |   1 |   2 |   3 |   4 |   5 |
|:--------------|----:|----:|----:|----:|----:|
| GALAXY_SOUNDS | 190 | 193 | 171 | 179 |   0 |
| MICROCHIP     | 192 | 204 | 173 |   0 |   0 |
| OXYGEN_SHAKE  | 190 | 193 | 171 | 179 |   0 |
| PANEL         | 190 | 193 | 171 | 179 |   0 |
| PEBBLES       |   0 | 157 | 156 | 154 | 177 |
| ROBOT         | 190 | 193 | 171 | 179 |   0 |
| SLEEP_POD     | 190 | 193 | 171 | 179 |   0 |
| SNACKPACK     | 190 | 193 | 171 | 179 |   0 |
| TRANSLATOR    | 190 | 193 | 171 | 179 |   0 |
| UV_VISOR      | 190 | 193 | 171 | 179 |   0 |

PEBBLES baskets use per-product sizes 2-5; MICROCHIP uses 1-3; the other eight groups use 1-4. Within each group basket, all five products share the same size.

## Opening And Closing Rhythm

Window: first and last 100,000 timestamps.

| group         |    n |   open_n |   close_n |   open_share |   close_share |
|:--------------|-----:|---------:|----------:|-------------:|--------------:|
| PEBBLES       | 3220 |      335 |       360 |       0.104  |        0.1118 |
| GALAXY_SOUNDS | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| OXYGEN_SHAKE  | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| PANEL         | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| ROBOT         | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| SLEEP_POD     | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| SNACKPACK     | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| TRANSLATOR    | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| UV_VISOR      | 3665 |      375 |       400 |       0.1023 |        0.1091 |
| MICROCHIP     | 2845 |      275 |       300 |       0.0967 |        0.1054 |

## Forward Markouts By Group

Buyer/seller side is inferred from touch. `mean_mid_markout` ignores spread; `mean_price_edge` includes the historical trade price.

### Horizon 200

| group         | side        |    n |   mean_mid_markout |   mean_price_edge |   good_pct |
|:--------------|:------------|-----:|-------------------:|------------------:|-----------:|
| TRANSLATOR    | buy_at_ask  | 1790 |             1.1679 |           -3.233  |     0.5207 |
| OXYGEN_SHAKE  | buy_at_ask  | 1790 |             0.8075 |           -5.6559 |     0.4777 |
| UV_VISOR      | sell_at_bid | 1875 |             0.6584 |           -5.8923 |     0.5003 |
| UV_VISOR      | buy_at_ask  | 1790 |             0.4712 |           -6.105  |     0.5078 |
| MICROCHIP     | sell_at_bid | 1345 |             0.374  |           -4.0599 |     0.5026 |
| SLEEP_POD     | buy_at_ask  | 1790 |             0.2902 |           -4.5514 |     0.495  |
| SNACKPACK     | buy_at_ask  | 1790 |             0.1304 |           -8.2855 |     0.4872 |
| TRANSLATOR    | sell_at_bid | 1875 |             0.1157 |           -4.2613 |     0.4805 |
| ROBOT         | sell_at_bid | 1875 |             0.112  |           -3.4299 |     0.4459 |
| PANEL         | buy_at_ask  | 1790 |             0.1084 |           -4.5958 |     0.5034 |
| PEBBLES       | sell_at_bid | 1615 |             0.0712 |           -6.3731 |     0.4978 |
| PEBBLES       | buy_at_ask  | 1605 |             0.0234 |           -6.4246 |     0.496  |
| SNACKPACK     | sell_at_bid | 1875 |             0.0043 |           -8.3595 |     0.4843 |
| OXYGEN_SHAKE  | sell_at_bid | 1875 |            -0.1304 |           -6.5501 |     0.4501 |
| ROBOT         | buy_at_ask  | 1790 |            -0.1525 |           -3.7299 |     0.4257 |
| SLEEP_POD     | sell_at_bid | 1875 |            -0.2267 |           -5.0395 |     0.4923 |
| GALAXY_SOUNDS | sell_at_bid | 1875 |            -0.3149 |           -7.1653 |     0.4864 |
| PANEL         | sell_at_bid | 1875 |            -0.4904 |           -5.172  |     0.4944 |
| MICROCHIP     | buy_at_ask  | 1500 |            -0.6163 |           -5.0097 |     0.4633 |
| GALAXY_SOUNDS | buy_at_ask  | 1790 |            -0.857  |           -7.7455 |     0.4615 |

### Horizon 1000

| group         | side        |    n |   mean_mid_markout |   mean_price_edge |   good_pct |
|:--------------|:------------|-----:|-------------------:|------------------:|-----------:|
| UV_VISOR      | buy_at_ask  | 1790 |             1.4364 |           -5.1406 |     0.5017 |
| MICROCHIP     | sell_at_bid | 1345 |             1.1063 |           -3.3275 |     0.5011 |
| PANEL         | buy_at_ask  | 1790 |             0.6053 |           -4.0989 |     0.5011 |
| TRANSLATOR    | buy_at_ask  | 1790 |             0.5563 |           -3.8448 |     0.5017 |
| ROBOT         | sell_at_bid | 1875 |             0.4099 |           -3.1318 |     0.4645 |
| ROBOT         | buy_at_ask  | 1790 |             0.1938 |           -3.3835 |     0.4587 |
| SNACKPACK     | sell_at_bid | 1875 |             0.1714 |           -8.1917 |     0.4944 |
| PEBBLES       | sell_at_bid | 1615 |             0.0384 |           -6.4059 |     0.4817 |
| SNACKPACK     | buy_at_ask  | 1790 |            -0.0062 |           -8.4218 |     0.4994 |
| OXYGEN_SHAKE  | buy_at_ask  | 1790 |            -0.007  |           -6.4692 |     0.4743 |
| PEBBLES       | buy_at_ask  | 1605 |            -0.0218 |           -6.4698 |     0.5022 |
| OXYGEN_SHAKE  | sell_at_bid | 1875 |            -0.185  |           -6.6048 |     0.4736 |
| UV_VISOR      | sell_at_bid | 1875 |            -0.1874 |           -6.738  |     0.4944 |
| PANEL         | sell_at_bid | 1875 |            -0.4439 |           -5.1249 |     0.5045 |
| TRANSLATOR    | sell_at_bid | 1875 |            -0.6741 |           -5.0508 |     0.4843 |
| GALAXY_SOUNDS | buy_at_ask  | 1790 |            -0.9644 |           -7.8521 |     0.4804 |
| GALAXY_SOUNDS | sell_at_bid | 1875 |            -1.012  |           -7.8618 |     0.4837 |
| SLEEP_POD     | buy_at_ask  | 1790 |            -1.3076 |           -6.1487 |     0.4793 |
| MICROCHIP     | buy_at_ask  | 1500 |            -1.657  |           -6.0503 |     0.484  |
| SLEEP_POD     | sell_at_bid | 1875 |            -2.0099 |           -6.8219 |     0.4704 |

## Persistent Product-Side Mid Markouts

These require at least 150 trades and the same markout sign on days 2, 3, and 4. They are directional mid moves after public prints, not guaranteed executable crossing edges.

### Positive t+1000 Examples

| product             | side        |   n |   mean_mid_markout |   mean_price_edge |   avg_good_pct |   d2_mid_markout |   d3_mid_markout |   d4_mid_markout |
|:--------------------|:------------|----:|-------------------:|------------------:|---------------:|-----------------:|-----------------:|-----------------:|
| PEBBLES_M           | buy_at_ask  | 321 |             7.3958 |            0.7945 |         0.5606 |           8.9567 |           7.2712 |           5.9596 |
| UV_VISOR_MAGENTA    | buy_at_ask  | 358 |             5.1155 |           -1.9333 |         0.5319 |           5.55   |           8.4846 |           1.312  |
| PEBBLES_XS          | sell_at_bid | 323 |             4.6279 |           -0.2582 |         0.5103 |          10.537  |           1.1429 |           2.2039 |
| UV_VISOR_RED        | buy_at_ask  | 358 |             4.1975 |           -2.8418 |         0.5473 |           7.0045 |           1.0538 |           4.5342 |
| MICROCHIP_TRIANGLE  | sell_at_bid | 269 |             3.5101 |           -0.8669 |         0.5353 |           2.9744 |           2.8778 |           4.6782 |
| UV_VISOR_YELLOW     | buy_at_ask  | 358 |             2.283  |           -4.6463 |         0.5107 |           2.95   |           3.3692 |           0.5299 |
| PEBBLES_L           | sell_at_bid | 323 |             2.0371 |           -4.5269 |         0.4681 |           1.0926 |           0.6205 |           4.3981 |
| ROBOT_MOPPING       | sell_at_bid | 375 |             1.8985 |           -2.072  |         0.5136 |           3.1429 |           2.2702 |           0.2824 |
| SNACKPACK_PISTACHIO | sell_at_bid | 375 |             1.4911 |           -6.4217 |         0.5168 |           1.3319 |           0.7903 |           2.3511 |
| MICROCHIP_RECTANGLE | sell_at_bid | 269 |             1.4795 |           -2.5119 |         0.4917 |           0.0385 |           3.6722 |           0.7277 |
| SNACKPACK_CHOCOLATE | buy_at_ask  | 358 |             1.454  |           -6.7992 |         0.4948 |           1.5864 |           1.75   |           1.0256 |
| SNACKPACK_CHOCOLATE | sell_at_bid | 375 |             0.6593 |           -7.5554 |         0.4964 |           0.3908 |           1.129  |           0.458  |

### Negative t+1000 Examples

| product                       | side        |   n |   mean_mid_markout |   mean_price_edge |   avg_good_pct |   d2_mid_markout |   d3_mid_markout |   d4_mid_markout |
|:------------------------------|:------------|----:|-------------------:|------------------:|---------------:|-----------------:|-----------------:|-----------------:|
| PEBBLES_XL                    | buy_at_ask  | 321 |            -5.2437 |          -13.6268 |         0.4853 |          -5.1442 |          -6.5466 |          -4.0404 |
| SLEEP_POD_SUEDE               | sell_at_bid | 375 |            -4.2242 |           -9.1958 |         0.4465 |          -8.8866 |          -1.6371 |          -2.1489 |
| SLEEP_POD_COTTON              | sell_at_bid | 375 |            -2.966  |           -7.9835 |         0.488  |          -2.2479 |          -6.0242 |          -0.626  |
| SLEEP_POD_SUEDE               | buy_at_ask  | 358 |            -2.754  |           -7.7425 |         0.4534 |          -1      |          -5.5654 |          -1.6966 |
| GALAXY_SOUNDS_SOLAR_WINDS     | sell_at_bid | 375 |            -2.5277 |           -9.1574 |         0.4599 |          -0.5126 |          -3.4597 |          -3.6107 |
| GALAXY_SOUNDS_SOLAR_FLAMES    | buy_at_ask  | 358 |            -2.5014 |           -9.5255 |         0.44   |          -1.1682 |          -5.5538 |          -0.7821 |
| PANEL_4X4                     | sell_at_bid | 375 |            -2.2096 |           -6.5856 |         0.4881 |          -2.0966 |          -3.1008 |          -1.4313 |
| TRANSLATOR_ASTRO_BLACK        | sell_at_bid | 375 |            -2.1718 |           -6.3381 |         0.4522 |          -5.3025 |          -0.0565 |          -1.1565 |
| OXYGEN_SHAKE_EVENING_BREATH   | buy_at_ask  | 358 |            -2.0938 |           -8.0494 |         0.3882 |          -4.2773 |          -1.5    |          -0.5043 |
| SLEEP_POD_NYLON               | buy_at_ask  | 358 |            -1.9709 |           -6.2961 |         0.4722 |          -3.7182 |          -0.0962 |          -2.0983 |
| UV_VISOR_AMBER                | buy_at_ask  | 358 |            -1.7682 |           -6.9701 |         0.4504 |          -3.3273 |          -0.8192 |          -1.1581 |
| GALAXY_SOUNDS_PLANETARY_RINGS | sell_at_bid | 375 |            -1.7328 |           -8.553  |         0.4665 |          -3.7269 |          -0.4677 |          -1.0038 |

## Olivia / Mark-Like Signal Check

| group         |   d2_timestamps |   d3_timestamps |   d4_timestamps |   exact_timestamps_repeated_all_3_days |
|:--------------|----------------:|----------------:|----------------:|---------------------------------------:|
| GALAXY_SOUNDS |             229 |             255 |             249 |                                      0 |
| MICROCHIP     |             174 |             194 |             201 |                                      0 |
| OXYGEN_SHAKE  |             229 |             255 |             249 |                                      0 |
| PANEL         |             229 |             255 |             249 |                                      0 |
| PEBBLES       |             212 |             230 |             202 |                                      0 |
| ROBOT         |             229 |             255 |             249 |                                      0 |
| SLEEP_POD     |             229 |             255 |             249 |                                      0 |
| SNACKPACK     |             229 |             255 |             249 |                                      0 |
| TRANSLATOR    |             229 |             255 |             249 |                                      0 |
| UV_VISOR      |             229 |             255 |             249 |                                      0 |

No exact trade timestamp repeats across all 3 days for any group. Combined with blank participant IDs, this rejects a direct Olivia/Mark-style participant replay signal for Round 5. The only repeatable signature is structural: complete same-side group baskets at the touch.
