# Mark 49 Counterparty Taxonomy

Data: `data/ROUND4/prices_round_4_day_1..3.csv` and `trades_round_4_day_1..3.csv`.
Method: exact `buyer == "Mark 49"` / `seller == "Mark 49"` filter, joined to same-timestamp visible book. Forward marks use first price row with timestamp >= `event_ts + horizon`. Trade markout is side-signed from Mark 49's trade price: buy = future_mid - trade_price; sell = trade_price - future_mid. `mid_move` is raw future_mid - current_mid.

## Executive Read

- Mark 49 appears in 122 trades / 1186 units across days 1-3. Products: VELVETFRUIT_EXTRACT. There are no Mark 49 trades in HYDROGEL_PACK or any VEV option in the Round 4 trade CSVs.
- Side mix is not neutral: see side table below. VFE is the strategy-relevant product.
- VFE Mark 49 **seller** prints have positive raw forward mid moves at t+200 on every day, matching the direction behind v314159's sell-suppression rule. Mark 49 **buyer** prints do not justify symmetric buy suppression from these data.
- Book relation is mostly passive/price-improved for Mark 49: sells are usually at/above ask and buys at/below bid, so Mark 49 looks more like a visible liquidity provider than a liquidity taker.
- The evidence supports `suppress_sell` or a temporary ask-side skew/widen after Mark 49 VFE seller prints. It does not support tightening asks into the signal. The sample is small, so prefer the current conservative overlay over a larger directional take.

## Products And Side Bias

| symbol | trades | qty | trade_pct | qty_pct |
| --- | --- | --- | --- | --- |
| VELVETFRUIT_EXTRACT | 122 | 1186 | 100 | 100 |

| mark49_side | trades | qty | trade_pct | qty_pct |
| --- | --- | --- | --- | --- |
| buy | 17 | 115 | 13.934 | 9.696 |
| sell | 105 | 1071 | 86.066 | 90.304 |

By product/side:

| product | side | trades | total_qty | mean_qty | median_qty | max_qty |
| --- | --- | --- | --- | --- | --- | --- |
| VELVETFRUIT_EXTRACT | buy | 17 | 115 | 6.765 | 7 | 10 |
| VELVETFRUIT_EXTRACT | sell | 105 | 1071 | 10.200 | 10 | 15 |

## Size Distributions

| product | side | n | mean | p25 | median | p75 | p90 | max | top_sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VELVETFRUIT_EXTRACT | buy | 17 | 6.765 | 5 | 7 | 8 | 9.400 | 10 | 7x4; 5x3; 8x3; 10x2; 6x2 |
| VELVETFRUIT_EXTRACT | sell | 105 | 10.200 | 8 | 10 | 12 | 14 | 15 | 8x19; 9x16; 11x12; 12x11; 14x11 |

## Timing, Periodicity, Repeats

Timing gaps by day/product/side:

| day | product | side | n | first_ts | last_ts | mean_gap | median_gap | p10_gap | p90_gap | top_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VELVETFRUIT_EXTRACT | buy | 6 | 131300 | 887800 | 151300 | 68800 | 17100 | 328840 | 34200x1; 348600x1; 68800x1; 5700x1; 299200x1 |
| 2 | VELVETFRUIT_EXTRACT | buy | 6 | 205000 | 992900 | 157580 | 107000 | 51920 | 293720 | 77600x1; 107000x1; 331600x1; 34800x1; 236900x1 |
| 3 | VELVETFRUIT_EXTRACT | buy | 5 | 111600 | 956900 | 211325 | 169350 | 135710 | 320520 | 178000x1; 160700x1; 125000x1; 381600x1 |
| 1 | VELVETFRUIT_EXTRACT | sell | 34 | 9400 | 985600 | 29581.818 | 17900 | 1240 | 69720 | 0x2; 54300x2; 1000x1; 29000x1; 34000x1 |
| 2 | VELVETFRUIT_EXTRACT | sell | 37 | 900 | 993500 | 27572.222 | 21750 | 2400 | 62700 | 44000x1; 67700x1; 16700x1; 0x1; 5000x1 |
| 3 | VELVETFRUIT_EXTRACT | sell | 34 | 77300 | 984300 | 27484.848 | 20200 | 1980 | 41260 | 9700x3; 0x2; 22100x2; 4300x1; 13700x1 |

Cross-day repeated exact timestamps:

| product | side | unique_timestamps | repeated_2plus_days | repeated_all_3_days |
| --- | --- | --- | --- | --- |
| VELVETFRUIT_EXTRACT | buy | 17 | 0 | 0 |
| VELVETFRUIT_EXTRACT | sell | 100 | 0 | 0 |

Same-day repeat timestamps are sparse; full rows are in `mark_49_same_timestamp_repeats.csv`.

## Price Relation To Book And Regime

Percent columns are percentages of Mark 49 events in that day/product/side bucket. `aggressive_pct` means Mark 49 bought at/above ask or sold at/below bid. `passive_or_price_improved_pct` means Mark 49 bought at/below bid or sold at/above ask.

| day | product | side | n | avg_px_minus_mid | avg_spread | aggressive_pct | passive_or_price_improved_pct | inside_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VELVETFRUIT_EXTRACT | buy | 6 | -1 | 2.667 | 16.667 | 83.333 | 0 |
| 2 | VELVETFRUIT_EXTRACT | buy | 6 | -1.583 | 2.500 | 0 | 100 | 0 |
| 3 | VELVETFRUIT_EXTRACT | buy | 5 | -2 | 2.800 | 0 | 100 | 0 |
| 1 | VELVETFRUIT_EXTRACT | sell | 34 | 0.735 | 1.294 | 0 | 100 | 0 |
| 2 | VELVETFRUIT_EXTRACT | sell | 37 | 0.622 | 1.405 | 2.703 | 97.297 | 0 |
| 3 | VELVETFRUIT_EXTRACT | sell | 34 | 0.662 | 1.265 | 0 | 100 | 0 |

Event-time spread/depth versus full-day product regimes:

| day | product | side | event_spread_mean | full_spread_mean | event_bid_depth_3_mean | full_bid_depth_3_mean | event_ask_depth_3_mean | full_ask_depth_3_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VELVETFRUIT_EXTRACT | buy | 2.667 | 4.985 | 68.667 | 60.447 | 63.167 | 60.465 |
| 2 | VELVETFRUIT_EXTRACT | buy | 2.500 | 4.986 | 66.833 | 60.338 | 59 | 60.325 |
| 3 | VELVETFRUIT_EXTRACT | buy | 2.800 | 4.976 | 61.200 | 60.451 | 56.600 | 60.427 |
| 1 | VELVETFRUIT_EXTRACT | sell | 1.294 | 4.985 | 62.441 | 60.447 | 71.853 | 60.465 |
| 2 | VELVETFRUIT_EXTRACT | sell | 1.405 | 4.986 | 62.784 | 60.338 | 73.243 | 60.325 |
| 3 | VELVETFRUIT_EXTRACT | sell | 1.265 | 4.976 | 63.471 | 60.451 | 74.147 | 60.427 |

## Markouts By Product / Side / Day

Trade-price markouts are side-signed for Mark 49. Positive means Mark 49's historical execution was profitable versus the future mid. `mid_move_200_mean` is included because v314159 uses Mark 49 seller prints as a raw VFE-up signal for our sell suppression.

| day | product | side | n | trade_mo_10_mean | trade_mo_50_mean | trade_mo_200_mean | trade_mo_500_mean | mid_move_200_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VELVETFRUIT_EXTRACT | buy | 6 | 0.417 | 0.417 | 0.167 | 0.917 | -0.833 |
| 2 | VELVETFRUIT_EXTRACT | buy | 6 | 0.167 | 0.167 | 0.500 | -0.417 | -1.083 |
| 3 | VELVETFRUIT_EXTRACT | buy | 5 | 0.100 | 0.100 | 0.100 | -1.700 | -1.900 |
| 1 | VELVETFRUIT_EXTRACT | sell | 34 | -1.147 | -1.147 | -1.132 | -1.279 | 1.868 |
| 2 | VELVETFRUIT_EXTRACT | sell | 37 | -1.135 | -1.135 | -1.162 | -0.959 | 1.784 |
| 3 | VELVETFRUIT_EXTRACT | sell | 34 | -1.412 | -1.412 | -1.441 | -1.221 | 2.103 |

## VFE Signal Validation For v314159

Current v314159 logic:

- Trigger: any VFE trade with `buyer == "Mark 67"` or `seller == "Mark 49"`.
- Action: suppress VFE sells for `SIGNAL_WINDOW = 2000` timestamp units.

Event-time raw VFE mid moves after Mark 49 VFE prints:

| trigger | day | n | mid_move_10_mean | mid_move_50_mean | mid_move_200_mean | mid_move_500_mean | mid_move_1000_mean | mid_move_2000_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M49_buy | 1 | 6 | -0.583 | -0.583 | -0.833 | -0.083 | 0.083 | -2 |
| M49_buy | 2 | 6 | -1.417 | -1.417 | -1.083 | -2 | -1.250 | 0.250 |
| M49_buy | 3 | 5 | -1.900 | -1.900 | -1.900 | -3.700 | -5.300 | -5.700 |
| M49_sell | 1 | 34 | 1.882 | 1.882 | 1.868 | 2.015 | 2.515 | 1.809 |
| M49_sell | 2 | 37 | 1.757 | 1.757 | 1.784 | 1.581 | 1.784 | 1.568 |
| M49_sell | 3 | 34 | 2.074 | 2.074 | 2.103 | 1.882 | 2.162 | 2.029 |

Validation of the actual 2000-unit active windows, measured on every VFE price tick inside each window:

| day | window_label | ticks | mid_move_10_mean | mid_move_50_mean | mid_move_200_mean | mid_move_500_mean |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | active_M49_sell_only | 649 | 0.107 | 0.107 | 0.125 | 0.156 |
| 2 | active_M49_sell_only | 734 | 0.094 | 0.094 | 0.110 | 0.082 |
| 3 | active_M49_sell_only | 648 | 0.079 | 0.079 | 0.053 | -0.014 |
| 1 | active_v314159_M49_sell_or_M67_buy | 1263 | 0.105 | 0.105 | 0.127 | 0.160 |
| 2 | active_v314159_M49_sell_or_M67_buy | 1245 | 0.076 | 0.076 | 0.069 | 0.020 |
| 3 | active_v314159_M49_sell_or_M67_buy | 979 | 0.101 | 0.101 | 0.093 | 0.090 |
| 1 | inactive_vs_M49_sell | 9351 | -0.005 | -0.005 | -0.004 | 0.001 |
| 2 | inactive_vs_M49_sell | 9266 | -0.004 | -0.004 | -0.002 | 0.010 |
| 3 | inactive_vs_M49_sell | 9352 | -0.012 | -0.012 | -0.017 | -0.033 |

Window coverage / overlap:

| trigger | day | events | events_with_next_within_2000 | active_ticks | active_tick_pct |
| --- | --- | --- | --- | --- | --- |
| M49_sell | 1 | 34 | 4 | 649 | 6.490 |
| M49_sell | 2 | 37 | 4 | 734 | 7.340 |
| M49_sell | 3 | 34 | 4 | 648 | 6.480 |
| M67_buy | 1 | 58 | 5 | 1165 | 11.650 |
| M67_buy | 2 | 61 | 6 | 1236 | 12.360 |
| M67_buy | 3 | 46 | 6 | 895 | 8.950 |
| v314159_combined | 1 | 66 | 9 | 1263 | 12.630 |
| v314159_combined | 2 | 63 | 8 | 1245 | 12.450 |
| v314159_combined | 3 | 52 | 8 | 979 | 9.790 |

Read: Mark 49 seller windows are directionally aligned with avoiding short VFE exposure at short horizons, especially t+200. The t+500+ signal is weaker/mixed, and the number of Mark 49 VFE seller events is small. This supports the current suppress-sell overlay more than an aggressive buy-follow rule. A narrower 200-500 window is empirically cleaner than 2000 from event-time marks, but the tick-window table should be used before changing code because v314159 suppresses at every tick inside the 2000 window, not only at event time.

## Interactions With Other Marks

Direct counterparties to Mark 49:

| product | side | other_party | trades | qty | avg_qty |
| --- | --- | --- | --- | --- | --- |
| VELVETFRUIT_EXTRACT | sell | Mark 67 | 89 | 963 | 10.820 |
| VELVETFRUIT_EXTRACT | buy | Mark 22 | 12 | 89 | 7.417 |
| VELVETFRUIT_EXTRACT | sell | Mark 55 | 9 | 54 | 6 |
| VELVETFRUIT_EXTRACT | sell | Mark 22 | 7 | 54 | 7.714 |
| VELVETFRUIT_EXTRACT | buy | Mark 55 | 5 | 26 | 5.200 |

Other Marks appearing at the same timestamp as Mark 49 events:

| co_mark | events | mentions |
| --- | --- | --- |
| Mark 55 | 5 | 5 |
| Mark 22 | 4 | 4 |
| Mark 67 | 4 | 4 |
| Mark 01 | 2 | 2 |
| Mark 14 | 2 | 2 |
| Mark 38 | 1 | 1 |

## Behavioral Classification

- **VFE role:** Mark 49 is mostly a passive/price-improved liquidity provider in VFE, not a liquidity taker. The clearest signature is selling VFE, frequently to Mark 67, at tight-spread timestamps.
- **Adverseness:** Mark 49 seller prints look adverse to our own selling into the next ~200 timestamps because raw VFE mid change after seller prints is positive by day. From Mark 49's own trade price, those sells are negative on average, so the useful feature is better described as an adverse-selection/liquidity-warning signal than a clean informed-trader copy signal.
- **Other products:** no Mark 49 HGP or VEV option trades exist in these files, so ignore Mark 49 outside VFE.
- **Microstructure:** Price relation is mostly at book/touch rather than a clean hidden periodic schedule. Timing gaps show clustered bursts and repeated exact timestamps are limited, so there is no reliable timestamp replay rule here.

## Recommendation Versus v314159

- Keep Mark 49 treatment asymmetric: **suppress or widen/skew VFE asks after Mark 49 seller prints**.
- Do **not** add symmetric suppression after Mark 49 buyer prints; the side evidence is weaker and does not match the current risk.
- Ignore Mark 49 outside VFE because there are zero observed HGP/VEV option prints.
- Do **not** chase Mark 49 by crossing after observation; historical print prices and visible next book are different execution problems.
- If testing one factor, test shorter sell-suppression windows around 200/500/1000 versus current 2000, with both `--match-trades none` and `worse`.

## Files Created

- `mark_49.py`
- `mark_49_events_enriched.csv`
- `mark_49_product_side_summary.csv`
- `mark_49_day_side_summary.csv`
- `mark_49_size_distribution.csv`
- `mark_49_timing_gaps.csv`
- `mark_49_gap_counts.csv`
- `mark_49_repeat_timestamps.csv`
- `mark_49_same_timestamp_repeats.csv`
- `mark_49_price_relation.csv`
- `mark_49_spread_depth_regimes.csv`
- `mark_49_markouts_by_product_side_day.csv`
- `mark_49_direct_counterparties.csv`
- `mark_49_same_timestamp_marks.csv`
- `mark_49_vfe_trigger_forward_mid_moves.csv`
- `mark_49_vfe_suppression_window_validation.csv`
- `mark_49_vfe_signal_window_coverage.csv`
- `mark_49.md`
