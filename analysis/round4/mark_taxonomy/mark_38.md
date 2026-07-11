# Mark 38 taxonomy

Data: `data/ROUND4` days 1-3. Markouts are signed for Mark 38: buy = future mid - trade price, sell = trade price - future mid. Forward mid is the first price row at timestamp >= event timestamp + horizon.

## Executive read
- Mark 38 appears only in `HYDROGEL_PACK, VEV_4000, VEV_4500, VEV_5000, VEV_5100, VEV_5200, VEV_5300` with 1478 total prints: 733 buys and 745 sells.
- 1464 / 1478 prints (99.1%) are in HYDROGEL_PACK or VEV_4000; 1442 of those (98.5%) are directly against Mark 14.
- HYDROGEL_PACK t+200 mean markout by side is buy -8.074, sell -7.954.
- VEV_4000 t+200 mean markout by side is buy -10.285, sell -10.180.
- Current-mid t+200 markouts on the two real products are small: HYDROGEL_PACK buy -0.201, HYDROGEL_PACK sell -0.057, VEV_4000 buy 0.038, VEV_4000 sell 0.264. The large negative trade-price edge is mostly spread paid at execution.
- Interpretation: Mark 38 is a spread-paying liquidity taker/noise source, usually trading against Mark 14. Do not follow Mark 38 directionally.
- Classification: liquidity taker / noise. Not a market maker, not informed in mid-price direction, and not adverse to passive contra quotes at the measured horizons.

## Products, side bias, and markouts
| symbol | side | trades | qty_sum | qty_mean | px_adv_mid_mean | spread_mean | at_or_through_best_pct | inside_spread_pct | t10_mean | t50_mean | t200_mean | t500_mean | t200_mid_mean | t500_mid_mean | t200_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 515 | 2065 | 4.010 | -7.873 | 15.746 | 100 | 0 | -7.937 | -7.937 | -8.074 | -7.992 | -0.201 | -0.119 | -4158 |
| HYDROGEL_PACK | sell | 507 | 2031 | 4.006 | -7.896 | 15.793 | 100 | 0 | -8.017 | -8.017 | -7.954 | -7.908 | -0.057 | -0.012 | -4032.500 |
| VEV_4000 | buy | 209 | 415 | 1.986 | -10.323 | 20.646 | 100 | 0 | -10.282 | -10.282 | -10.285 | -10.148 | 0.038 | 0.175 | -2149.500 |
| VEV_4000 | sell | 233 | 461 | 1.979 | -10.444 | 20.888 | 100 | 0 | -10.382 | -10.382 | -10.180 | -10.275 | 0.264 | 0.170 | -2372 |
| VEV_4500 | buy | 2 | 3 | 1.500 | -3.500 | 7 | 100 | 0 | 2 | 2 | 0 | -0.500 | 3.500 | 3 | 0 |
| VEV_4500 | sell | 1 | 3 | 3 | -4 | 8 | 100 | 0 | 0.500 | 0.500 | -2 | -4 | 2 | 0 | -2 |
| VEV_5000 | buy | 2 | 3 | 1.500 | -1 | 2 | 100 | 0 | 0.750 | 0.750 | 0.250 | -0.250 | 1.250 | 0.750 | 0.500 |
| VEV_5000 | sell | 1 | 3 | 3 | -1.500 | 3 | 100 | 0 | 0 | 0 | -2 | -4 | -0.500 | -2.500 | -2 |
| VEV_5100 | buy | 2 | 3 | 1.500 | -0.750 | 1.500 | 100 | 0 | 0.500 | 0.500 | 0 | -0.500 | 0.750 | 0.250 | 0 |
| VEV_5100 | sell | 1 | 3 | 3 | -1.500 | 3 | 100 | 0 | 0 | 0 | -2 | -4 | -0.500 | -2.500 | -2 |
| VEV_5200 | buy | 2 | 3 | 1.500 | -0.500 | 1 | 100 | 0 | 0 | 0 | -0.500 | -0.250 | 0 | 0.250 | -1 |
| VEV_5200 | sell | 1 | 3 | 3 | -1 | 2 | 100 | 0 | 0 | 0 | -1.500 | -3 | -0.500 | -2 | -1.500 |
| VEV_5300 | buy | 1 | 1 | 1 | -0.500 | 1 | 100 | 0 | 0.500 | 0.500 | 0 | 0 | 0.500 | 0.500 | 0 |
| VEV_5300 | sell | 1 | 3 | 3 | -0.500 | 1 | 100 | 0 | 0 | 0 | -1 | -1 | -0.500 | -0.500 | -1 |

## Product + side + day markouts
| symbol | side | day | quantity_count | quantity_sum | quantity_mean | spread_mean | mark_price_adv_vs_mid_mean | markout_trade_t10_mean | markout_trade_t50_mean | markout_trade_t200_mean | markout_trade_t500_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 1 | 189 | 745 | 3.942 | 15.825 | -7.913 | -8.159 | -8.159 | -8.392 | -8.230 |
| HYDROGEL_PACK | buy | 2 | 165 | 658 | 3.988 | 15.618 | -7.809 | -7.791 | -7.791 | -8.127 | -7.827 |
| HYDROGEL_PACK | buy | 3 | 161 | 662 | 4.112 | 15.783 | -7.891 | -7.826 | -7.826 | -7.646 | -7.882 |
| HYDROGEL_PACK | sell | 1 | 186 | 740 | 3.978 | 15.812 | -7.906 | -8.124 | -8.124 | -8.110 | -8.223 |
| HYDROGEL_PACK | sell | 2 | 146 | 586 | 4.014 | 15.774 | -7.887 | -7.849 | -7.849 | -7.959 | -7.952 |
| HYDROGEL_PACK | sell | 3 | 175 | 705 | 4.029 | 15.789 | -7.894 | -8.043 | -8.043 | -7.783 | -7.537 |
| VEV_4000 | buy | 1 | 73 | 148 | 2.027 | 20.644 | -10.322 | -10.384 | -10.384 | -10.411 | -10.534 |
| VEV_4000 | buy | 2 | 64 | 124 | 1.938 | 20.875 | -10.438 | -10.414 | -10.414 | -10.367 | -10.203 |
| VEV_4000 | buy | 3 | 72 | 143 | 1.986 | 20.444 | -10.222 | -10.062 | -10.062 | -10.083 | -9.708 |
| VEV_4000 | sell | 1 | 91 | 185 | 2.033 | 20.901 | -10.451 | -10.698 | -10.698 | -10.505 | -10.269 |
| VEV_4000 | sell | 2 | 64 | 132 | 2.062 | 21.078 | -10.539 | -10.273 | -10.273 | -9.930 | -10.008 |
| VEV_4000 | sell | 3 | 78 | 144 | 1.846 | 20.718 | -10.359 | -10.103 | -10.103 | -10.006 | -10.500 |
| VEV_4500 | buy | 1 | 1 | 1 | 1 | 7 | -3.500 | 4 | 4 | 0 | -1 |
| VEV_4500 | buy | 3 | 1 | 2 | 2 | 7 | -3.500 | 0 | 0 | 0 | 0 |
| VEV_4500 | sell | 3 | 1 | 3 | 3 | 8 | -4 | 0.500 | 0.500 | -2 | -4 |
| VEV_5000 | buy | 1 | 1 | 1 | 1 | 2 | -1 | 2 | 2 | 0.500 | -0.500 |
| VEV_5000 | buy | 3 | 1 | 2 | 2 | 2 | -1 | -0.500 | -0.500 | 0 | 0 |
| VEV_5000 | sell | 3 | 1 | 3 | 3 | 3 | -1.500 | 0 | 0 | -2 | -4 |
| VEV_5100 | buy | 1 | 1 | 1 | 1 | 2 | -1 | 1 | 1 | 0 | -1 |
| VEV_5100 | buy | 3 | 1 | 2 | 2 | 1 | -0.500 | 0 | 0 | 0 | 0 |
| VEV_5100 | sell | 3 | 1 | 3 | 3 | 3 | -1.500 | 0 | 0 | -2 | -4 |
| VEV_5200 | buy | 1 | 1 | 1 | 1 | 1 | -0.500 | 0.500 | 0.500 | -0.500 | -0.500 |
| VEV_5200 | buy | 3 | 1 | 2 | 2 | 1 | -0.500 | -0.500 | -0.500 | -0.500 | 0 |
| VEV_5200 | sell | 3 | 1 | 3 | 3 | 2 | -1 | 0 | 0 | -1.500 | -3 |
| VEV_5300 | buy | 1 | 1 | 1 | 1 | 1 | -0.500 | 0.500 | 0.500 | 0 | 0 |
| VEV_5300 | sell | 3 | 1 | 3 | 3 | 1 | -0.500 | 0 | 0 | -1 | -1 |

## Timing gaps
| symbol | side | day | events | first_ts | last_ts | unique_timestamps | repeat_ts_events | gap_median | gap_p10 | gap_p90 | most_common_gap | most_common_gap_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 1 | 189 | 5100 | 985800 | 189 | 0 | 3850 | 400 | 11610 | 400 | 9 |
| HYDROGEL_PACK | buy | 2 | 165 | 11200 | 993200 | 165 | 0 | 3600 | 500 | 14850 | 400 | 6 |
| HYDROGEL_PACK | buy | 3 | 161 | 4400 | 992400 | 161 | 0 | 4850 | 890 | 13510 | 2500 | 6 |
| HYDROGEL_PACK | sell | 1 | 186 | 22800 | 989000 | 186 | 0 | 3900 | 540 | 11480.000 | 2300 | 6 |
| HYDROGEL_PACK | sell | 2 | 146 | 10200 | 996500 | 146 | 0 | 5000 | 1000 | 14620.000 | 1100 | 5 |
| HYDROGEL_PACK | sell | 3 | 175 | 4500 | 982800 | 175 | 0 | 3600 | 530 | 13780 | 1100 | 7 |
| VEV_4000 | buy | 1 | 73 | 5300 | 998500 | 73 | 0 | 10650 | 1810 | 30710.000 | 1800 | 2 |
| VEV_4000 | buy | 2 | 64 | 9000 | 998800 | 64 | 0 | 11000 | 2400 | 33900 | 2400 | 2 |
| VEV_4000 | buy | 3 | 72 | 8700 | 993700 | 72 | 0 | 11000 | 1300 | 26900 | 1300 | 3 |
| VEV_4000 | sell | 1 | 91 | 16700 | 997300 | 91 | 0 | 7500 | 1470 | 26350 | 300 | 4 |
| VEV_4000 | sell | 2 | 64 | 1300 | 982500 | 64 | 0 | 10300 | 1400 | 36200 | 1400 | 2 |
| VEV_4000 | sell | 3 | 78 | 1700 | 972500 | 78 | 0 | 8600 | 960 | 31300 | 800 | 3 |
| VEV_4500 | buy | 1 | 1 | 437100 | 437100 | 1 | 0 |  |  |  |  |  |
| VEV_4500 | buy | 3 | 1 | 155400 | 155400 | 1 | 0 |  |  |  |  |  |
| VEV_4500 | sell | 3 | 1 | 370100 | 370100 | 1 | 0 |  |  |  |  |  |
| VEV_5000 | buy | 1 | 1 | 437100 | 437100 | 1 | 0 |  |  |  |  |  |
| VEV_5000 | buy | 3 | 1 | 155400 | 155400 | 1 | 0 |  |  |  |  |  |
| VEV_5000 | sell | 3 | 1 | 370100 | 370100 | 1 | 0 |  |  |  |  |  |
| VEV_5100 | buy | 1 | 1 | 437100 | 437100 | 1 | 0 |  |  |  |  |  |
| VEV_5100 | buy | 3 | 1 | 155400 | 155400 | 1 | 0 |  |  |  |  |  |
| VEV_5100 | sell | 3 | 1 | 370100 | 370100 | 1 | 0 |  |  |  |  |  |
| VEV_5200 | buy | 1 | 1 | 437100 | 437100 | 1 | 0 |  |  |  |  |  |
| VEV_5200 | buy | 3 | 1 | 155400 | 155400 | 1 | 0 |  |  |  |  |  |
| VEV_5200 | sell | 3 | 1 | 370100 | 370100 | 1 | 0 |  |  |  |  |  |
| VEV_5300 | buy | 1 | 1 | 437100 | 437100 | 1 | 0 |  |  |  |  |  |
| VEV_5300 | sell | 3 | 1 | 370100 | 370100 | 1 | 0 |  |  |  |  |  |

## Repeat timestamps
- Timestamp-side keys recurring on multiple days: 14.
| symbol | side | timestamp | days_seen | days |
| --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 193400 | 2 | 1,2 |
| HYDROGEL_PACK | buy | 221200 | 2 | 1,2 |
| HYDROGEL_PACK | buy | 266300 | 2 | 1,3 |
| HYDROGEL_PACK | buy | 314800 | 2 | 2,3 |
| HYDROGEL_PACK | buy | 391700 | 2 | 2,3 |
| HYDROGEL_PACK | buy | 578300 | 2 | 2,3 |
| HYDROGEL_PACK | buy | 694500 | 2 | 2,3 |
| HYDROGEL_PACK | buy | 727700 | 2 | 2,3 |
| HYDROGEL_PACK | buy | 918200 | 2 | 2,3 |
| HYDROGEL_PACK | sell | 235900 | 2 | 1,3 |
| HYDROGEL_PACK | sell | 394800 | 2 | 1,3 |
| HYDROGEL_PACK | sell | 928000 | 2 | 1,3 |
| VEV_4000 | buy | 752300 | 2 | 2,3 |
| VEV_4000 | sell | 50200 | 2 | 1,2 |
- Same product/side/day repeated timestamp bursts: 0. Every Mark 38 product-side timestamp is a single print.

## Counterparties
| symbol | side | counterparty | trades | qty_sum | qty_mean | t200_mean | t200_sum | t500_mean | first_ts | last_ts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | Mark 14 | 507 | 2033 | 4.010 | -8.207 | -4161 | -8.112 | 4400 | 992400 |
| HYDROGEL_PACK | buy | Mark 22 | 8 | 32 | 4 | 0.375 | 3 | -0.375 | 5100 | 993200 |
| HYDROGEL_PACK | sell | Mark 14 | 496 | 1989 | 4.010 | -8.116 | -4025.500 | -8.052 | 4500 | 996500 |
| HYDROGEL_PACK | sell | Mark 22 | 11 | 42 | 3.818 | -0.636 | -7 | -1.409 | 49400 | 941900 |
| VEV_4000 | buy | Mark 14 | 207 | 412 | 1.990 | -10.382 | -2149 | -10.244 | 5300 | 998800 |
| VEV_4000 | buy | Mark 22 | 2 | 3 | 1.500 | -0.250 | -0.500 | -0.250 | 155400 | 437100 |
| VEV_4000 | sell | Mark 14 | 232 | 458 | 1.974 | -10.216 | -2370 | -10.302 | 1300 | 997300 |
| VEV_4000 | sell | Mark 22 | 1 | 3 | 3 | -2 | -2 | -4 | 370100 | 370100 |
| VEV_4500 | buy | Mark 22 | 2 | 3 | 1.500 | 0 | 0 | -0.500 | 155400 | 437100 |
| VEV_4500 | sell | Mark 22 | 1 | 3 | 3 | -2 | -2 | -4 | 370100 | 370100 |
| VEV_5000 | buy | Mark 22 | 2 | 3 | 1.500 | 0.250 | 0.500 | -0.250 | 155400 | 437100 |
| VEV_5000 | sell | Mark 22 | 1 | 3 | 3 | -2 | -2 | -4 | 370100 | 370100 |
| VEV_5100 | buy | Mark 22 | 2 | 3 | 1.500 | 0 | 0 | -0.500 | 155400 | 437100 |
| VEV_5100 | sell | Mark 22 | 1 | 3 | 3 | -2 | -2 | -4 | 370100 | 370100 |
| VEV_5200 | buy | Mark 22 | 2 | 3 | 1.500 | -0.500 | -1 | -0.250 | 155400 | 437100 |
| VEV_5200 | sell | Mark 22 | 1 | 3 | 3 | -1.500 | -1.500 | -3 | 370100 | 370100 |
| VEV_5300 | buy | Mark 22 | 1 | 1 | 1 | 0 | 0 | 0 | 437100 | 437100 |
| VEV_5300 | sell | Mark 22 | 1 | 3 | 3 | -1 | -1 | -1 | 370100 | 370100 |

## Spread and depth regimes
| symbol | side | regime | trades | spread_mean | depth_mean | px_adv_mid_mean | t200_mean | t500_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | spread_le_median | 509 | 15.731 | 75.688 | -7.865 | -8.059 | -7.993 |
| HYDROGEL_PACK | buy | spread_gt_median | 6 | 17 | 77.333 | -8.500 | -9.333 | -7.917 |
| HYDROGEL_PACK | buy | depth_le_median | 287 | 15.892 | 70.439 | -7.946 | -8.362 | -8.078 |
| HYDROGEL_PACK | buy | depth_gt_median | 228 | 15.561 | 82.338 | -7.781 | -7.711 | -7.884 |
| HYDROGEL_PACK | sell | spread_le_median | 498 | 15.771 | 75.155 | -7.886 | -7.954 | -7.899 |
| HYDROGEL_PACK | sell | spread_gt_median | 9 | 17 | 75.778 | -8.500 | -7.944 | -8.444 |
| HYDROGEL_PACK | sell | depth_le_median | 292 | 15.938 | 70.027 | -7.969 | -8.217 | -8.216 |
| HYDROGEL_PACK | sell | depth_gt_median | 215 | 15.595 | 82.144 | -7.798 | -7.595 | -7.491 |
| VEV_4000 | buy | spread_le_median | 197 | 20.563 | 67.147 | -10.282 | -10.256 | -10.122 |
| VEV_4000 | buy | spread_gt_median | 12 | 22 | 74 | -11 | -10.750 | -10.583 |
| VEV_4000 | buy | depth_le_median | 107 | 20.664 | 58.738 | -10.332 | -10.299 | -10.154 |
| VEV_4000 | buy | depth_gt_median | 102 | 20.627 | 76.775 | -10.314 | -10.270 | -10.142 |
| VEV_4000 | sell | spread_le_median | 211 | 20.773 | 69.005 | -10.386 | -10.156 | -10.275 |
| VEV_4000 | sell | spread_gt_median | 22 | 22 | 61.364 | -11 | -10.409 | -10.273 |
| VEV_4000 | sell | depth_le_median | 120 | 20.983 | 59.433 | -10.492 | -10.304 | -10.408 |
| VEV_4000 | sell | depth_gt_median | 113 | 20.788 | 77.681 | -10.394 | -10.049 | -10.133 |
| VEV_4500 | buy | spread_le_median | 2 | 7 | 53 | -3.500 | 0 | -0.500 |
| VEV_4500 | buy | depth_le_median | 1 | 7 | 40 | -3.500 | 0 | 0 |
| VEV_4500 | buy | depth_gt_median | 1 | 7 | 66 | -3.500 | 0 | -1 |
| VEV_4500 | sell | spread_le_median | 1 | 8 | 56 | -4 | -2 | -4 |
| VEV_4500 | sell | depth_le_median | 1 | 8 | 56 | -4 | -2 | -4 |
| VEV_5000 | buy | spread_le_median | 2 | 2 | 53 | -1 | 0.250 | -0.250 |
| VEV_5000 | buy | depth_le_median | 1 | 2 | 40 | -1 | 0 | 0 |
| VEV_5000 | buy | depth_gt_median | 1 | 2 | 66 | -1 | 0.500 | -0.500 |
| VEV_5000 | sell | spread_le_median | 1 | 3 | 56 | -1.500 | -2 | -4 |
| VEV_5000 | sell | depth_le_median | 1 | 3 | 56 | -1.500 | -2 | -4 |
| VEV_5100 | buy | spread_le_median | 1 | 1 | 40 | -0.500 | 0 | 0 |
| VEV_5100 | buy | spread_gt_median | 1 | 2 | 66 | -1 | 0 | -1 |
| VEV_5100 | buy | depth_le_median | 1 | 1 | 40 | -0.500 | 0 | 0 |
| VEV_5100 | buy | depth_gt_median | 1 | 2 | 66 | -1 | 0 | -1 |
| VEV_5100 | sell | spread_le_median | 1 | 3 | 56 | -1.500 | -2 | -4 |
| VEV_5100 | sell | depth_le_median | 1 | 3 | 56 | -1.500 | -2 | -4 |
| VEV_5200 | buy | spread_le_median | 2 | 1 | 53 | -0.500 | -0.500 | -0.250 |
| VEV_5200 | buy | depth_le_median | 1 | 1 | 40 | -0.500 | -0.500 | 0 |
| VEV_5200 | buy | depth_gt_median | 1 | 1 | 66 | -0.500 | -0.500 | -0.500 |
| VEV_5200 | sell | spread_le_median | 1 | 2 | 56 | -1 | -1.500 | -3 |
| VEV_5200 | sell | depth_le_median | 1 | 2 | 56 | -1 | -1.500 | -3 |
| VEV_5300 | buy | spread_le_median | 1 | 1 | 36 | -0.500 | 0 | 0 |
| VEV_5300 | buy | depth_le_median | 1 | 1 | 36 | -0.500 | 0 | 0 |
| VEV_5300 | sell | spread_le_median | 1 | 1 | 48 | -0.500 | -1 | -1 |
| VEV_5300 | sell | depth_le_median | 1 | 1 | 48 | -0.500 | -1 | -1 |

## Nearby interaction windows
Counts below are mentions of other participants in same product/day within +/-500 timestamp units of each Mark 38 event; they are not unique events.
| symbol | mark38_side | other_mark | other_side | window_mentions |
| --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | Mark 14 | sell | 614 |
| HYDROGEL_PACK | buy | Mark 14 | buy | 75 |
| HYDROGEL_PACK | buy | Mark 22 | sell | 9 |
| HYDROGEL_PACK | buy | Mark 22 | buy | 3 |
| HYDROGEL_PACK | sell | Mark 14 | buy | 594 |
| HYDROGEL_PACK | sell | Mark 14 | sell | 76 |
| HYDROGEL_PACK | sell | Mark 22 | buy | 13 |
| HYDROGEL_PACK | sell | Mark 22 | sell | 2 |
| VEV_4000 | buy | Mark 14 | sell | 215 |
| VEV_4000 | buy | Mark 14 | buy | 14 |
| VEV_4000 | buy | Mark 22 | sell | 2 |
| VEV_4000 | sell | Mark 14 | buy | 254 |
| VEV_4000 | sell | Mark 14 | sell | 14 |
| VEV_4000 | sell | Mark 22 | buy | 1 |
| VEV_4500 | buy | Mark 22 | sell | 2 |
| VEV_4500 | sell | Mark 22 | buy | 1 |
| VEV_5000 | buy | Mark 22 | sell | 2 |
| VEV_5000 | sell | Mark 22 | buy | 1 |
| VEV_5100 | buy | Mark 22 | sell | 2 |
| VEV_5100 | sell | Mark 22 | buy | 1 |
| VEV_5200 | buy | Mark 22 | sell | 2 |
| VEV_5200 | sell | Mark 14 | buy | 1 |
| VEV_5200 | sell | Mark 22 | buy | 1 |
| VEV_5200 | sell | Mark 22 | sell | 1 |
| VEV_5300 | buy | Mark 22 | sell | 1 |
| VEV_5300 | sell | Mark 01 | buy | 1 |
| VEV_5300 | sell | Mark 22 | buy | 1 |
| VEV_5300 | sell | Mark 22 | sell | 1 |

## Compare to v314159
- v314159 already trades HYDROGEL_PACK with tight buy edge 4 and wide sell edge 12. Mark 38's HYDROGEL_PACK flow does not justify following buys/sells; it mainly says takers are paying the spread.
- v314159's VEV_4000 deep-ITM module is built around structural fair and aggressive passive making. Mark 38's VEV_4000 prints support the value of being passive/contra at the touch, because Mark 38 loses about 10 points from trade price while current-mid t+200 is near flat.
- Practical recommendation: ignore Mark 38 as a directional overlay. Do not suppress passive contra quotes because of Mark 38 alone. The only testable sleeve idea is a one-factor passive-tightening/capture experiment on HYDROGEL_PACK or VEV_4000, but only in the simulator and only if both `none` and `worse` improve.

## Files created
- `mark_38_analysis.py`
- `mark_38_events.csv`
- `mark_38_summary_by_product_side.csv`
- `mark_38_summary_by_product_side_day.csv`
- `mark_38_timing_gaps.csv`
- `mark_38_repeat_timestamps.csv`
- `mark_38_repeat_bursts.csv`
- `mark_38_counterparties.csv`
- `mark_38_regimes.csv`
- `mark_38_interactions.csv`
- `mark_38.md`
