# Round 5 Passive Fill / Hidden Taker Research

Scope: Round 5 prices and public trades for days 2, 3, and 4 across all 50 products. Quotes are evaluated at `best_touch`, `one_tick_inside`, `book_mid`, `wall_mid`, and leave-one-day-out `residual_fair`. Conservative fills require a future public trade through the submitted quote; `book_or_trade` fill columns also count future top-of-book movement through the quote.

PnL decomposition: for a buy fill, `edge = future_mid - quote`; for a sell fill, `edge = quote - future_mid`. `spread_capture` is quote-vs-current-mid and `adverse_selection` is current-mid-vs-future-mid. `cross_liq_edge` marks forced liquidation at the future opposite touch, which is the relevant zero-edge / 10-cap stress check.

## Headline Findings

- Best conservative filled-edge row is **SNACKPACK_PISTACHIO sell best_touch h1**: fill_rate 0.006434, mean_edge_if_filled 4.222798, EV/quote 0.027169, positive days 3/3, fills 193.
- The same row fails 10-cap forced liquidation: cross_liq_edge -3.818653, or -38.186528 for a full 10-lot inventory.
- No quote row with at least 20 conservative fills has positive forced cross-liquidation edge on all three days.
- Best average forced-liquidation row is **OXYGEN_SHAKE_GARLIC buy residual_fair h500**: cross_liq_edge 14.946937, fill_rate 0.792175, but only 2/3 positive days.
- Hidden-taker pattern is broad rather than product-specific: average best-touch match rate is 1.000000; the top repeated size is usually 2 with share 0.263302. Wall-mid and residual-fair matches are sparse.
- Synchronized basket prints are common but not directly monetizable by passive quotes alone: 7077 full-group same-timestamp events, including 7077 same-quantity events.
- Explicit rejection: positive midpoint markouts are not enough under the 10-position cap. Rows with positive `mean_edge_if_filled` but negative `mean_cross_liq_edge_if_filled` can accumulate inventory whose forced flattening gives back the apparent spread capture.

## Top Passive Quote Candidates

| group     | product             | quote_mode      | side   |   horizon |   trade_fill_rate |   mean_edge_if_filled |   mean_cross_liq_edge_if_filled |   ev_per_quote |   positive_edge_days |   trade_fill_count |
|:----------|:--------------------|:----------------|:-------|----------:|------------------:|----------------------:|--------------------------------:|---------------:|---------------------:|-------------------:|
| SNACKPACK | SNACKPACK_PISTACHIO | best_touch      | sell   |         1 |          0.006434 |               4.2228  |                        -3.81865 |       0.027169 |                    3 |                193 |
| SNACKPACK | SNACKPACK_PISTACHIO | best_touch      | buy    |         1 |          0.007101 |               3.85446 |                        -4.07512 |       0.027369 |                    3 |                213 |
| SNACKPACK | SNACKPACK_PISTACHIO | one_tick_inside | sell   |         1 |          0.007434 |               3.88117 |                        -4.1704  |       0.028853 |                    3 |                223 |
| SNACKPACK | SNACKPACK_VANILLA   | best_touch      | buy    |         1 |          0.006534 |               3.81378 |                        -4.66837 |       0.024919 |                    3 |                196 |
| SNACKPACK | SNACKPACK_VANILLA   | best_touch      | sell   |         1 |          0.006267 |               3.625   |                        -4.93617 |       0.022719 |                    3 |                188 |
| SNACKPACK | SNACKPACK_PISTACHIO | one_tick_inside | buy    |         1 |          0.007834 |               3.21915 |                        -4.69787 |       0.025219 |                    3 |                235 |
| SNACKPACK | SNACKPACK_CHOCOLATE | best_touch      | buy    |         1 |          0.007134 |               3.32009 |                        -4.98131 |       0.023686 |                    3 |                214 |
| SNACKPACK | SNACKPACK_VANILLA   | one_tick_inside | buy    |         1 |          0.007201 |               3.27315 |                        -5.22222 |       0.023569 |                    3 |                216 |
| SNACKPACK | SNACKPACK_CHOCOLATE | best_touch      | sell   |         1 |          0.006701 |               3.16667 |                        -5.12935 |       0.021219 |                    3 |                201 |
| SNACKPACK | SNACKPACK_VANILLA   | one_tick_inside | sell   |         1 |          0.007034 |               3.20616 |                        -5.36967 |       0.022552 |                    3 |                211 |
| SNACKPACK | SNACKPACK_CHOCOLATE | one_tick_inside | buy    |         1 |          0.007934 |               2.85294 |                        -5.44538 |       0.022636 |                    3 |                238 |
| SNACKPACK | SNACKPACK_CHOCOLATE | one_tick_inside | sell   |         1 |          0.007301 |               2.52283 |                        -5.74429 |       0.018419 |                    3 |                219 |

## Candidates Surviving Forced Cross Liquidation

No rows.

## Anchor Comparison Around Book Mid / Wall Mid / Residual Fair

| group         | quote_mode    |   horizon |   trade_fill_rate |   mean_edge_if_filled |   mean_cross_liq_edge_if_filled |   ev_per_quote |   positive_product_sides |
|:--------------|:--------------|----------:|------------------:|----------------------:|--------------------------------:|---------------:|-------------------------:|
| SNACKPACK     | wall_mid      |       100 |          0.609397 |              -25.0941 |                        -33.4859 |       -15.2819 |                        0 |
| SNACKPACK     | book_mid      |       100 |          0.609391 |              -25.1044 |                        -33.4963 |       -15.2883 |                        0 |
| SNACKPACK     | residual_fair |       100 |          0.601589 |              -25.8747 |                        -34.2676 |       -15.5879 |                        0 |
| TRANSLATOR    | residual_fair |       100 |          0.60096  |              -37.6868 |                        -42.0755 |       -22.6614 |                        0 |
| ROBOT         | residual_fair |       100 |          0.603943 |              -37.5527 |                        -41.1142 |       -22.7048 |                        0 |
| TRANSLATOR    | wall_mid      |       100 |          0.602465 |              -37.8085 |                        -42.1971 |       -22.8018 |                        0 |
| TRANSLATOR    | book_mid      |       100 |          0.602519 |              -37.8062 |                        -42.1948 |       -22.8026 |                        0 |
| ROBOT         | wall_mid      |       100 |          0.605141 |              -37.8659 |                        -41.4273 |       -22.9429 |                        0 |
| ROBOT         | book_mid      |       100 |          0.605071 |              -37.8748 |                        -41.4362 |       -22.9469 |                        0 |
| UV_VISOR      | residual_fair |       100 |          0.600963 |              -39.4492 |                        -46.0144 |       -23.8048 |                        0 |
| UV_VISOR      | book_mid      |       100 |          0.603337 |              -39.646  |                        -46.2118 |       -23.9911 |                        0 |
| UV_VISOR      | wall_mid      |       100 |          0.603545 |              -39.6496 |                        -46.2152 |       -24.0004 |                        0 |
| OXYGEN_SHAKE  | residual_fair |       100 |          0.602081 |              -39.8208 |                        -46.2651 |       -24.0266 |                        0 |
| OXYGEN_SHAKE  | wall_mid      |       100 |          0.603094 |              -40.0072 |                        -46.4533 |       -24.1767 |                        0 |
| OXYGEN_SHAKE  | book_mid      |       100 |          0.603111 |              -40.0343 |                        -46.4806 |       -24.1915 |                        0 |
| PANEL         | residual_fair |       100 |          0.595488 |              -41.3765 |                        -46.0723 |       -24.6431 |                        0 |
| PANEL         | wall_mid      |       100 |          0.597997 |              -41.2822 |                        -45.9786 |       -24.6837 |                        0 |
| PANEL         | book_mid      |       100 |          0.598013 |              -41.2848 |                        -45.9811 |       -24.6871 |                        0 |
| GALAXY_SOUNDS | residual_fair |       100 |          0.600572 |              -42.8673 |                        -49.7339 |       -25.7886 |                        0 |
| GALAXY_SOUNDS | book_mid      |       100 |          0.603145 |              -42.8225 |                        -49.6893 |       -25.8997 |                        0 |
| GALAXY_SOUNDS | wall_mid      |       100 |          0.603172 |              -42.8333 |                        -49.7002 |       -25.9065 |                        0 |
| SLEEP_POD     | residual_fair |       100 |          0.598912 |              -44.5626 |                        -49.395  |       -26.7481 |                        0 |
| SLEEP_POD     | book_mid      |       100 |          0.600751 |              -44.8243 |                        -49.6567 |       -26.9851 |                        0 |
| SLEEP_POD     | wall_mid      |       100 |          0.600663 |              -44.8311 |                        -49.6636 |       -26.9855 |                        0 |
| MICROCHIP     | residual_fair |       100 |          0.520175 |              -59.3542 |                        -63.7466 |       -31.036  |                        0 |
| MICROCHIP     | wall_mid      |       100 |          0.52136  |              -59.4725 |                        -63.8652 |       -31.135  |                        0 |
| MICROCHIP     | book_mid      |       100 |          0.521535 |              -59.4961 |                        -63.8883 |       -31.1546 |                        0 |
| PEBBLES       | residual_fair |       100 |          0.548542 |              -71.7875 |                        -78.1976 |       -39.4382 |                        0 |
| PEBBLES       | wall_mid      |       100 |          0.549529 |              -71.8048 |                        -78.2148 |       -39.515  |                        0 |
| PEBBLES       | book_mid      |       100 |          0.549646 |              -71.8278 |                        -78.2377 |       -39.5348 |                        0 |

## Top Product Anchor Comparison

| group        | product             | quote_mode    |   horizon |   trade_fill_rate |   mean_edge_if_filled |   mean_cross_liq_edge_if_filled |   ev_per_quote |   positive_side_days |   positive_cross_side_days |
|:-------------|:--------------------|:--------------|----------:|------------------:|----------------------:|--------------------------------:|---------------:|---------------------:|---------------------------:|
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | book_mid      |         1 |          0.012301 |              -6.71781 |                       -14.235   |      -0.082575 |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | wall_mid      |         1 |          0.012318 |              -6.73257 |                       -14.2523  |      -0.082942 |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | residual_fair |         1 |          0.012218 |              -8.27871 |                       -15.7916  |      -0.102602 |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | book_mid      |        20 |          0.211122 |             -26.3914  |                       -33.9368  |      -5.58633  |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | wall_mid      |        20 |          0.211506 |             -26.3905  |                       -33.9346  |      -5.59675  |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | residual_fair |        20 |          0.210387 |             -26.7552  |                       -34.295   |      -5.66133  |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | residual_fair |       100 |          0.596987 |             -47.8442  |                       -55.3664  |     -28.9261   |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | wall_mid      |       100 |          0.599832 |             -47.9851  |                       -55.5106  |     -29.088    |                    0 |                          0 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_GARLIC | book_mid      |       100 |          0.599192 |             -48.0694  |                       -55.5952  |     -29.1066   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | book_mid      |         1 |          0.012335 |              -2.05837 |                       -10.2889  |      -0.025369 |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | wall_mid      |         1 |          0.012318 |              -2.06416 |                       -10.294   |      -0.025419 |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | residual_fair |         1 |          0.012218 |              -5.19944 |                       -13.4329  |      -0.065748 |                    1 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | wall_mid      |        20 |          0.211707 |             -13.9788  |                       -22.2219  |      -2.9583   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | book_mid      |        20 |          0.211573 |             -13.9994  |                       -22.2421  |      -2.96056  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | residual_fair |        20 |          0.209586 |             -15.3241  |                       -23.5657  |      -3.22027  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | wall_mid      |       100 |          0.606532 |             -24.134   |                       -32.3681  |     -14.63     |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | book_mid      |       100 |          0.606246 |             -24.1561  |                       -32.3903  |     -14.6364   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_CHOCOLATE | residual_fair |       100 |          0.599613 |             -25.2057  |                       -33.4376  |     -15.1254   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | wall_mid      |         1 |          0.012401 |              -1.23556 |                        -9.17162 |      -0.015418 |                    1 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | book_mid      |         1 |          0.012368 |              -1.27692 |                        -9.21277 |      -0.015885 |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | residual_fair |         1 |          0.012218 |              -5.27378 |                       -13.2148  |      -0.067615 |                    2 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | wall_mid      |        20 |          0.216366 |             -10.8209  |                       -18.7872  |      -2.35012  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | book_mid      |        20 |          0.2165   |             -10.8378  |                       -18.8028  |      -2.35532  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | residual_fair |        20 |          0.21159  |             -12.4996  |                       -20.4647  |      -2.70213  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | wall_mid      |       100 |          0.618535 |             -18.1257  |                       -26.0823  |     -11.2377   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | book_mid      |       100 |          0.618721 |             -18.1404  |                       -26.0969  |     -11.2501   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_PISTACHIO | residual_fair |       100 |          0.604141 |             -19.2737  |                       -27.2304  |     -11.7947   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | wall_mid      |         1 |          0.012301 |              -1.70332 |                       -10.1494  |      -0.02096  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | book_mid      |         1 |          0.012268 |              -1.74087 |                       -10.1854  |      -0.02136  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | residual_fair |         1 |          0.012218 |              -5.53941 |                       -13.9805  |      -0.068007 |                    1 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | book_mid      |        20 |          0.212926 |             -13.2669  |                       -21.7114  |      -2.82554  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | wall_mid      |        20 |          0.213176 |             -13.254   |                       -21.6988  |      -2.82604  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | residual_fair |        20 |          0.210788 |             -14.5618  |                       -23.0053  |      -3.07791  |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | book_mid      |       100 |          0.607559 |             -24.4133  |                       -32.8407  |     -14.831    |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | wall_mid      |       100 |          0.60798  |             -24.4065  |                       -32.8336  |     -14.8372   |                    0 |                          0 |
| SNACKPACK    | SNACKPACK_VANILLA   | residual_fair |       100 |          0.600572 |             -25.3474  |                       -33.7757  |     -15.2221   |                    0 |                          0 |

## Hidden-Taker Signature Watchlist

| group         | product                     |   trades |   top_qty |   top_qty_share |   best_touch_match_rate |   inside_1_match_rate |   wall_mid_match_rate |   residual_fair_match_rate |   hidden_taker_score |
|:--------------|:----------------------------|---------:|----------:|----------------:|------------------------:|----------------------:|----------------------:|---------------------------:|---------------------:|
| GALAXY_SOUNDS | GALAXY_SOUNDS_BLACK_HOLES   |      733 |         2 |        0.263302 |                       1 |                     0 |              0.013643 |                   0        |               5.6916 |
| SLEEP_POD     | SLEEP_POD_LAMB_WOOL         |      733 |         2 |        0.263302 |                       1 |                     0 |              0.013643 |                   0        |               5.6916 |
| SLEEP_POD     | SLEEP_POD_POLYESTER         |      733 |         2 |        0.263302 |                       1 |                     0 |              0.017735 |                   0        |               5.6916 |
| SLEEP_POD     | SLEEP_POD_SUEDE             |      733 |         2 |        0.263302 |                       1 |                     0 |              0.0191   |                   0        |               5.6916 |
| GALAXY_SOUNDS | GALAXY_SOUNDS_DARK_MATTER   |      733 |         2 |        0.263302 |                       1 |                     0 |              0.015007 |                   0.001364 |               5.6916 |
| SNACKPACK     | SNACKPACK_PISTACHIO         |      733 |         2 |        0.263302 |                       1 |                     0 |              0.012278 |                   0.006821 |               5.6916 |
| SNACKPACK     | SNACKPACK_RASPBERRY         |      733 |         2 |        0.263302 |                       1 |                     0 |              0.017735 |                   0.002729 |               5.6916 |
| SNACKPACK     | SNACKPACK_STRAWBERRY        |      733 |         2 |        0.263302 |                       1 |                     0 |              0.016371 |                   0.002729 |               5.6916 |
| SNACKPACK     | SNACKPACK_VANILLA           |      733 |         2 |        0.263302 |                       1 |                     0 |              0.013643 |                   0.005457 |               5.6916 |
| TRANSLATOR    | TRANSLATOR_ASTRO_BLACK      |      733 |         2 |        0.263302 |                       1 |                     0 |              0.016371 |                   0        |               5.6916 |
| TRANSLATOR    | TRANSLATOR_ECLIPSE_CHARCOAL |      733 |         2 |        0.263302 |                       1 |                     0 |              0.016371 |                   0.001364 |               5.6916 |
| TRANSLATOR    | TRANSLATOR_GRAPHITE_MIST    |      733 |         2 |        0.263302 |                       1 |                     0 |              0.017735 |                   0        |               5.6916 |
| TRANSLATOR    | TRANSLATOR_SPACE_GRAY       |      733 |         2 |        0.263302 |                       1 |                     0 |              0.0191   |                   0.001364 |               5.6916 |
| TRANSLATOR    | TRANSLATOR_VOID_BLUE        |      733 |         2 |        0.263302 |                       1 |                     0 |              0.015007 |                   0.001364 |               5.6916 |
| UV_VISOR      | UV_VISOR_AMBER              |      733 |         2 |        0.263302 |                       1 |                     0 |              0.017735 |                   0        |               5.6916 |
| UV_VISOR      | UV_VISOR_MAGENTA            |      733 |         2 |        0.263302 |                       1 |                     0 |              0.017735 |                   0        |               5.6916 |
| UV_VISOR      | UV_VISOR_ORANGE             |      733 |         2 |        0.263302 |                       1 |                     0 |              0.013643 |                   0.005457 |               5.6916 |
| UV_VISOR      | UV_VISOR_RED                |      733 |         2 |        0.263302 |                       1 |                     0 |              0.0191   |                   0        |               5.6916 |
| UV_VISOR      | UV_VISOR_YELLOW             |      733 |         2 |        0.263302 |                       1 |                     0 |              0.016371 |                   0.002729 |               5.6916 |
| SLEEP_POD     | SLEEP_POD_NYLON             |      733 |         2 |        0.263302 |                       1 |                     0 |              0.0191   |                   0        |               5.6916 |

## Synchronized Basket Fills

| group         |   full_group_events |   same_qty_events |   avg_qty |   best_touch_match_rate |   inside_1_match_rate |   wall_mid_match_rate |   residual_fair_match_rate |
|:--------------|--------------------:|------------------:|----------:|------------------------:|----------------------:|----------------------:|---------------------------:|
| GALAXY_SOUNDS |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.014734 |                   0.000273 |
| OXYGEN_SHAKE  |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.017735 |                   0.000273 |
| PANEL         |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.01528  |                   0.001091 |
| ROBOT         |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.016371 |                   0.001091 |
| SLEEP_POD     |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.01719  |                   0        |
| SNACKPACK     |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.01528  |                   0.005457 |
| TRANSLATOR    |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.016917 |                   0.000819 |
| UV_VISOR      |                 733 |               733 |  12.3124  |                       1 |                     0 |              0.016917 |                   0.001637 |
| PEBBLES       |                 644 |               644 |  17.7252  |                       1 |                     0 |              0.006522 |                   0        |
| MICROCHIP     |                 569 |               569 |   9.83304 |                       1 |                     0 |              0.003515 |                   0.001757 |

## Explicit Rejections

High fill-rate rows with negative filled edge at h20 are adverse-selection traps:

| group     | product          | quote_mode      | side   |   trade_fill_rate |   mean_edge_if_filled |   mean_cross_liq_edge_if_filled |   trade_fill_count |
|:----------|:-----------------|:----------------|:-------|------------------:|----------------------:|--------------------------------:|-------------------:|
| PEBBLES   | PEBBLES_XL       | book_mid        | sell   |          0.185237 |              -71.5279 |                        -79.87   |               5546 |
| PEBBLES   | PEBBLES_XL       | wall_mid        | sell   |          0.185204 |              -71.4984 |                        -79.8406 |               5545 |
| PEBBLES   | PEBBLES_XL       | residual_fair   | sell   |          0.18477  |              -71.4501 |                        -79.7932 |               5532 |
| PEBBLES   | PEBBLES_XL       | one_tick_inside | sell   |          0.172846 |              -69.8424 |                        -78.183  |               5175 |
| PEBBLES   | PEBBLES_XL       | book_mid        | buy    |          0.189412 |              -69.6899 |                        -78.0155 |               5671 |
| PEBBLES   | PEBBLES_XL       | wall_mid        | buy    |          0.189412 |              -69.6237 |                        -77.9497 |               5671 |
| PEBBLES   | PEBBLES_XL       | residual_fair   | buy    |          0.189145 |              -69.4981 |                        -77.8243 |               5663 |
| PEBBLES   | PEBBLES_XL       | best_touch      | sell   |          0.171142 |              -69.2979 |                        -77.6393 |               5124 |
| PEBBLES   | PEBBLES_XL       | best_touch      | buy    |          0.175351 |              -68.9017 |                        -77.2204 |               5250 |
| PEBBLES   | PEBBLES_XL       | one_tick_inside | buy    |          0.177388 |              -68.7776 |                        -77.0964 |               5311 |
| MICROCHIP | MICROCHIP_SQUARE | residual_fair   | sell   |          0.179392 |              -48.9257 |                        -54.8421 |               5371 |
| MICROCHIP | MICROCHIP_SQUARE | wall_mid        | sell   |          0.183233 |              -48.6964 |                        -54.5815 |               5486 |
| MICROCHIP | MICROCHIP_SQUARE | book_mid        | sell   |          0.1833   |              -48.5836 |                        -54.4685 |               5488 |
| MICROCHIP | MICROCHIP_SQUARE | one_tick_inside | sell   |          0.170608 |              -47.9324 |                        -53.8173 |               5108 |
| MICROCHIP | MICROCHIP_SQUARE | best_touch      | sell   |          0.167936 |              -47.7391 |                        -53.6261 |               5028 |
| MICROCHIP | MICROCHIP_SQUARE | wall_mid        | buy    |          0.15314  |              -44.1092 |                        -50.0214 |               4585 |
| MICROCHIP | MICROCHIP_SQUARE | book_mid        | buy    |          0.153206 |              -44.0958 |                        -50.0081 |               4587 |
| MICROCHIP | MICROCHIP_SQUARE | residual_fair   | buy    |          0.156346 |              -43.1846 |                        -49.0628 |               4681 |
| MICROCHIP | MICROCHIP_SQUARE | one_tick_inside | buy    |          0.141717 |              -42.8959 |                        -48.8065 |               4243 |
| MICROCHIP | MICROCHIP_SQUARE | best_touch      | buy    |          0.139512 |              -42.5668 |                        -48.48   |               4177 |

CSV outputs: `18_quote_ev_by_day.csv`, `18_quote_ev_summary.csv`, `18_top_quote_candidates.csv`, `18_trade_price_offsets.csv`, `18_trade_offset_histogram.csv`, `18_sync_basket_events.csv`, `18_sync_basket_summary.csv`, `18_hidden_taker_signatures.csv`, `18_group_quote_anchor_comparison.csv`, and `18_top_product_anchor_comparison.csv`.