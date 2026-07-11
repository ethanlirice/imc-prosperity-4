# Mark 14 Counterparty Taxonomy

Scope: Round 4 raw `data/ROUND4` days 1-3. Forward markouts use first product mid at timestamp >= event timestamp + horizon, signed from Mark 14's side: buy = future_mid - trade_price, sell = trade_price - future_mid. Book relation uses same timestamp top of book.

## Executive read

- Mark 14 appears in 2,172 trade rows, total quantity 8,718, across 7 products.
- The historical trade-price signal is real on HYDROGEL_PACK, VELVETFRUIT_EXTRACT, and VEV_4000, but the same raw-data recheck shows next-tick crossing loses after spread/slippage. This matches the prior rejected copy-strategy backtests in `DATA.md` / `TRADING.md`.
- The edge is mostly spread capture / price selection: main-product buys print at bid and sells print at ask, while t+200 side-signed mid-to-mid markouts are tiny (HGP +0.14/+0.27; VFE -0.09/-0.16; VEV_4000 -0.25/+0.01).
- Behavior is best classified as passive adverse selection of liquidity takers, not a visible-book liquidity-taker signal we can chase after the ID appears.
- Strategy implication for v314159: ignore direct copy and do not tighten in response. Mark 14 does not justify a reactive active sleeve; any use should be passive-only/widening and must pass both backtest modes.

## Products and side bias

| symbol | events | qty | t200 |
| --- | --- | --- | --- |
| HYDROGEL_PACK | 1003 | 4022 | 8.162 |
| VELVETFRUIT_EXTRACT | 647 | 3524 | 2.321 |
| VEV_4000 | 439 | 870 | 10.294 |
| VEV_5200 | 33 | 122 | 0.909 |
| VEV_5300 | 30 | 105 | 0.567 |
| VEV_5400 | 13 | 48 | 0.077 |
| VEV_5500 | 7 | 27 | 0.286 |

| symbol | side | n | qty_mean | edge_t10_mean | edge_t50_mean | edge_t200_mean | edge_t500_mean | midmo_t200_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 496 | 4.010 | 8.172 | 8.172 | 8.116 | 8.052 | 0.135 |
| HYDROGEL_PACK | sell | 507 | 4.010 | 8.056 | 8.056 | 8.207 | 8.112 | 0.266 |
| VELVETFRUIT_EXTRACT | buy | 316 | 5.573 | 2.244 | 2.244 | 2.339 | 2.397 | -0.092 |
| VELVETFRUIT_EXTRACT | sell | 331 | 5.326 | 2.390 | 2.390 | 2.304 | 2.201 | -0.159 |
| VEV_4000 | buy | 232 | 1.974 | 10.429 | 10.429 | 10.216 | 10.302 | -0.250 |
| VEV_4000 | sell | 207 | 1.990 | 10.406 | 10.406 | 10.382 | 10.244 | 0.007 |
| VEV_5200 | buy | 33 | 3.697 | 1.121 | 1.121 | 0.909 | 0.758 | -0.091 |
| VEV_5300 | buy | 30 | 3.500 | 0.500 | 0.500 | 0.567 | 0.333 | -0.183 |
| VEV_5400 | buy | 13 | 3.692 | 0.154 | 0.154 | 0.077 | 0.077 | -0.385 |
| VEV_5500 | buy | 7 | 3.857 | 0.286 | 0.286 | 0.286 | 0.214 | -0.214 |

## Product + side + day markouts

| symbol | side | day | n | edge_t10_mean | edge_t50_mean | edge_t200_mean | edge_t500_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 1 | 183 | 8.240 | 8.240 | 8.216 | 8.303 |
| HYDROGEL_PACK | buy | 2 | 142 | 8.063 | 8.063 | 8.162 | 8.151 |
| HYDROGEL_PACK | buy | 3 | 171 | 8.190 | 8.190 | 7.971 | 7.702 |
| HYDROGEL_PACK | sell | 1 | 187 | 8.219 | 8.219 | 8.471 | 8.270 |
| HYDROGEL_PACK | sell | 2 | 161 | 7.997 | 7.997 | 8.354 | 8.028 |
| HYDROGEL_PACK | sell | 3 | 159 | 7.925 | 7.925 | 7.748 | 8.013 |
| VELVETFRUIT_EXTRACT | buy | 1 | 114 | 2.351 | 2.351 | 2.539 | 2.605 |
| VELVETFRUIT_EXTRACT | buy | 2 | 92 | 2.016 | 2.016 | 2.043 | 2.158 |
| VELVETFRUIT_EXTRACT | buy | 3 | 110 | 2.323 | 2.323 | 2.377 | 2.382 |
| VELVETFRUIT_EXTRACT | sell | 1 | 97 | 2.562 | 2.562 | 2.284 | 2.325 |
| VELVETFRUIT_EXTRACT | sell | 2 | 118 | 2.271 | 2.271 | 2.220 | 2.136 |
| VELVETFRUIT_EXTRACT | sell | 3 | 116 | 2.366 | 2.366 | 2.405 | 2.164 |
| VEV_4000 | buy | 1 | 91 | 10.698 | 10.698 | 10.505 | 10.269 |
| VEV_4000 | buy | 2 | 64 | 10.273 | 10.273 | 9.930 | 10.008 |
| VEV_4000 | buy | 3 | 77 | 10.240 | 10.240 | 10.110 | 10.584 |
| VEV_4000 | sell | 1 | 72 | 10.604 | 10.604 | 10.556 | 10.667 |
| VEV_4000 | sell | 2 | 64 | 10.414 | 10.414 | 10.367 | 10.203 |
| VEV_4000 | sell | 3 | 71 | 10.197 | 10.197 | 10.218 | 9.852 |
| VEV_5200 | buy | 1 | 6 | 1.417 | 1.417 | 0.750 | 0.500 |
| VEV_5200 | buy | 2 | 8 | 1.312 | 1.312 | 1.062 | 1 |
| VEV_5200 | buy | 3 | 19 | 0.947 | 0.947 | 0.895 | 0.737 |
| VEV_5300 | buy | 1 | 6 | 0.833 | 0.833 | 1.167 | 0.833 |
| VEV_5300 | buy | 2 | 14 | 0.393 | 0.393 | 0.429 | 0.036 |
| VEV_5300 | buy | 3 | 10 | 0.450 | 0.450 | 0.400 | 0.450 |
| VEV_5400 | buy | 1 | 5 | 0.100 | 0.100 | 0 | 0.100 |
| VEV_5400 | buy | 2 | 2 | 0 | 0 | -0.250 | -0.250 |
| VEV_5400 | buy | 3 | 6 | 0.250 | 0.250 | 0.250 | 0.167 |
| VEV_5500 | buy | 1 | 3 | 0.333 | 0.333 | 0.167 | 0.500 |
| VEV_5500 | buy | 2 | 3 | 0.333 | 0.333 | 0.500 | 0.167 |
| VEV_5500 | buy | 3 | 1 | 0 | 0 | 0 | -0.500 |

## Size signature

| symbol | side | n | qty_mean | qty_p50 | qty_p90 | qty_min | qty_max | top_sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 496 | 4.010 | 4 | 6 | 2 | 6 | 3x109, 5x102, 6x101, 2x95, 4x89 |
| HYDROGEL_PACK | sell | 507 | 4.010 | 4 | 6 | 2 | 6 | 6x110, 4x106, 2x104, 3x97, 5x90 |
| VELVETFRUIT_EXTRACT | buy | 316 | 5.573 | 6 | 8 | 3 | 8 | 7x57, 8x55, 4x54, 6x54, 3x49 |
| VELVETFRUIT_EXTRACT | sell | 331 | 5.326 | 5 | 8 | 3 | 8 | 3x63, 5x62, 4x59, 7x50, 6x49 |
| VEV_4000 | buy | 232 | 1.974 | 2 | 3 | 1 | 3 | 1x84, 3x78, 2x70 |
| VEV_4000 | sell | 207 | 1.990 | 2 | 3 | 1 | 3 | 2x71, 1x69, 3x67 |
| VEV_5200 | buy | 33 | 3.697 | 4 | 5 | 2 | 5 | 5x12, 2x8, 4x7, 3x6 |
| VEV_5300 | buy | 30 | 3.500 | 3.500 | 5 | 2 | 5 | 2x9, 5x9, 3x6, 4x6 |
| VEV_5400 | buy | 13 | 3.692 | 4 | 5 | 2 | 5 | 3x4, 5x4, 4x3, 2x2 |
| VEV_5500 | buy | 7 | 3.857 | 4 | 5 | 2 | 5 | 5x3, 2x2, 4x2 |

## Book and spread relation

| symbol | side | n | spread_mean | all_spread_mean | spread_pctile_mean | side_touch_improve_mean | side_mid_edge_mean | at_bid | at_ask | inside |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 496 | 15.962 | 15.728 | 0.959 | 15.962 | 7.981 | 1 | 0 | 0 |
| HYDROGEL_PACK | sell | 507 | 15.882 | 15.728 | 0.945 | 15.882 | 7.941 | 0 | 1 | 0 |
| VELVETFRUIT_EXTRACT | buy | 316 | 4.861 | 4.982 | 0.786 | 4.861 | 2.430 | 1 | 0 | 0 |
| VELVETFRUIT_EXTRACT | sell | 331 | 4.924 | 4.982 | 0.795 | 4.924 | 2.462 | 0 | 1 | 0 |
| VEV_4000 | buy | 232 | 20.931 | 20.753 | 0.828 | 20.931 | 10.466 | 1 | 0 | 0 |
| VEV_4000 | sell | 207 | 20.749 | 20.753 | 0.809 | 20.749 | 10.374 | 0 | 1 | 0 |
| VEV_5200 | buy | 33 | 2 | 2.758 | 0.334 | 2 | 1 | 1 | 0 | 0 |
| VEV_5300 | buy | 30 | 1.633 | 1.973 | 0.616 | 1.567 | 0.750 | 0.933 | 0 | 0.067 |
| VEV_5400 | buy | 13 | 1.077 | 1.304 | 0.725 | 1 | 0.462 | 0.923 | 0 | 0.077 |
| VEV_5500 | buy | 7 | 1 | 1.109 | 0.877 | 1 | 0.500 | 1 | 0 | 0 |

## Counterparty interactions

| symbol | side | counterparty | n | qty_sum | edge_t200_mean | edge_t200_sum |
| --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | sell | Mark 38 | 507 | 2033 | 8.207 | 4161 |
| HYDROGEL_PACK | buy | Mark 38 | 496 | 1989 | 8.116 | 4025.500 |
| VEV_4000 | buy | Mark 38 | 232 | 458 | 10.216 | 2370 |
| VEV_4000 | sell | Mark 38 | 207 | 412 | 10.382 | 2149 |
| VELVETFRUIT_EXTRACT | sell | Mark 55 | 331 | 1763 | 2.304 | 762.500 |
| VELVETFRUIT_EXTRACT | buy | Mark 55 | 316 | 1761 | 2.339 | 739 |
| VEV_5200 | buy | Mark 22 | 33 | 122 | 0.909 | 30 |
| VEV_5300 | buy | Mark 22 | 30 | 105 | 0.567 | 17 |
| VEV_5500 | buy | Mark 22 | 7 | 27 | 0.286 | 2 |
| VEV_5400 | buy | Mark 22 | 13 | 48 | 0.077 | 1 |

| symbol | side | n | pct_any_other_same_ts | mean_other_trades_same_ts | pct_same_product_other |
| --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 496 | 0.034 | 0.093 | 0 |
| HYDROGEL_PACK | sell | 507 | 0.032 | 0.075 | 0 |
| VELVETFRUIT_EXTRACT | buy | 316 | 0.016 | 0.057 | 0.003 |
| VELVETFRUIT_EXTRACT | sell | 331 | 0.012 | 0.048 | 0 |
| VEV_4000 | buy | 232 | 0.022 | 0.039 | 0 |
| VEV_4000 | sell | 207 | 0.014 | 0.014 | 0 |
| VEV_5200 | buy | 33 | 1 | 4.455 | 0 |
| VEV_5300 | buy | 30 | 1 | 3.800 | 0 |
| VEV_5400 | buy | 13 | 1 | 3.385 | 0 |
| VEV_5500 | buy | 7 | 1 | 3 | 0 |

## Timing, periodicity, and repeated timestamps

| symbol | side | day | n | first_ts | last_ts | gap_mean | gap_p50 | gap_p10 | gap_p90 | gap_min | gap_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 1 | 183 | 22800 | 989000 | 5308.791 | 4150 | 510 | 11570 | 100 | 22600 |
| HYDROGEL_PACK | buy | 2 | 142 | 10200 | 996500 | 6995.035 | 5100 | 1000 | 14700 | 100 | 39400 |
| HYDROGEL_PACK | buy | 3 | 171 | 4500 | 982800 | 5754.706 | 3600 | 590 | 13940 | 100 | 31800 |
| HYDROGEL_PACK | sell | 1 | 187 | 6200 | 985800 | 5266.667 | 4050 | 400 | 11750 | 100 | 30000 |
| HYDROGEL_PACK | sell | 2 | 161 | 11200 | 992200 | 6131.250 | 3650 | 490 | 15010 | 100 | 28700 |
| HYDROGEL_PACK | sell | 3 | 159 | 4400 | 992400 | 6253.165 | 4950 | 1110 | 13630 | 100 | 41900 |
| VELVETFRUIT_EXTRACT | buy | 1 | 114 | 19300 | 991600 | 8604.425 | 5500 | 740 | 22160 | 100 | 42800 |
| VELVETFRUIT_EXTRACT | buy | 2 | 92 | 17400 | 996500 | 10759.341 | 6200 | 1100 | 26000 | 200 | 44900 |
| VELVETFRUIT_EXTRACT | buy | 3 | 110 | 28500 | 995300 | 8869.725 | 6100 | 1040 | 19720 | 200 | 36200 |
| VELVETFRUIT_EXTRACT | sell | 1 | 97 | 64200 | 984900 | 9590.625 | 5100 | 900 | 24350 | 100 | 57600 |
| VELVETFRUIT_EXTRACT | sell | 2 | 118 | 2900 | 995100 | 8480.342 | 5600 | 620 | 17840 | 100 | 38300 |
| VELVETFRUIT_EXTRACT | sell | 3 | 116 | 10600 | 997500 | 8581.739 | 7000 | 800 | 22000 | 100 | 33900 |
| VEV_4000 | buy | 1 | 91 | 16700 | 997300 | 10895.556 | 7500 | 1470 | 26350 | 300 | 44100 |
| VEV_4000 | buy | 2 | 64 | 1300 | 982500 | 15574.603 | 10300 | 1400 | 36200 | 200 | 94400 |
| VEV_4000 | buy | 3 | 77 | 1700 | 972500 | 12773.684 | 8700 | 950 | 31400 | 200 | 45800 |
| VEV_4000 | sell | 1 | 72 | 5300 | 998500 | 13988.732 | 10500 | 1800 | 30900 | 200 | 93100 |
| VEV_4000 | sell | 2 | 64 | 9000 | 998800 | 15711.111 | 11000 | 2400 | 33900 | 800 | 73700 |
| VEV_4000 | sell | 3 | 71 | 8700 | 993700 | 14071.429 | 11100 | 1280 | 27050 | 400 | 61500 |
| VEV_5200 | buy | 1 | 6 | 322600 | 988100 | 133100 | 60100 | 8280 | 304280 | 6000 | 346000 |
| VEV_5200 | buy | 2 | 8 | 414900 | 876500 | 65942.857 | 12600 | 9140 | 172140 | 8900 | 210000 |
| VEV_5200 | buy | 3 | 19 | 98900 | 878300 | 43300 | 23650 | 1400 | 122420 | 500 | 154500 |
| VEV_5300 | buy | 1 | 6 | 85300 | 848900 | 152720 | 128400 | 40080 | 282520 | 10000 | 332600 |
| VEV_5300 | buy | 2 | 14 | 79300 | 977300 | 69076.923 | 61400 | 22620 | 139400 | 4500 | 176900 |
| VEV_5300 | buy | 3 | 10 | 128700 | 983300 | 94955.556 | 78300 | 37160 | 155320 | 28200 | 215400 |
| VEV_5400 | buy | 1 | 5 | 206200 | 746300 | 135025 | 127100 | 39010 | 237380 | 11200 | 274700 |
| VEV_5400 | buy | 2 | 2 | 45100 | 102600 | 57500 | 57500 | 57500 | 57500 | 57500 | 57500 |
| VEV_5400 | buy | 3 | 6 | 33600 | 943900 | 182060 | 166300 | 58000 | 305380 | 6600 | 322300 |
| VEV_5500 | buy | 1 | 3 | 53400 | 848900 | 397750 | 397750 | 339470 | 456030 | 324900 | 470600 |
| VEV_5500 | buy | 2 | 3 | 294600 | 423800 | 64600 | 64600 | 50360 | 78840 | 46800 | 82400 |
| VEV_5500 | buy | 3 | 1 | 498100 | 498100 |  |  |  |  |  |  |

| symbol | mod | top_buckets |
| --- | --- | --- |
| HYDROGEL_PACK | 1000 | 400:112, 800:111, 500:107, 700:101, 100:100 |
| HYDROGEL_PACK | 5000 | 1200:29, 4800:29, 4500:28, 1400:27, 100:27 |
| HYDROGEL_PACK | 10000 | 100:18, 4800:16, 600:16, 7100:16, 1400:16 |
| VELVETFRUIT_EXTRACT | 1000 | 100:77, 700:72, 400:71, 500:68, 300:66 |
| VELVETFRUIT_EXTRACT | 5000 | 100:19, 3400:18, 700:18, 2000:18, 2400:18 |
| VELVETFRUIT_EXTRACT | 10000 | 8400:13, 5700:11, 7400:11, 5100:11, 3700:10 |
| VEV_4000 | 1000 | 900:54, 300:53, 100:53, 200:46, 700:44 |
| VEV_4000 | 5000 | 4100:16, 2900:14, 900:14, 3100:14, 2300:13 |
| VEV_4000 | 10000 | 9100:10, 6800:9, 4200:8, 7900:8, 3100:8 |
| VEV_5200 | 1000 | 400:5, 100:5, 600:4, 200:4, 300:3 |
| VEV_5200 | 5000 | 4400:3, 1200:2, 4800:2, 4200:2, 1500:2 |
| VEV_5200 | 10000 | 4400:2, 9800:2, 6500:2, 8900:2, 6200:2 |
| VEV_5300 | 1000 | 300:8, 500:7, 900:3, 700:2, 200:2 |
| VEV_5300 | 5000 | 500:4, 4600:2, 3500:2, 1300:2, 4000:2 |
| VEV_5300 | 10000 | 500:3, 9300:2, 8500:2, 6300:1, 7900:1 |
| VEV_5400 | 1000 | 200:3, 100:3, 600:3, 400:1, 300:1 |
| VEV_5400 | 5000 | 100:3, 2600:2, 200:2, 1200:1, 400:1 |
| VEV_5400 | 10000 | 5100:2, 200:2, 6200:1, 100:1, 400:1 |
| VEV_5500 | 1000 | 400:2, 0:1, 900:1, 600:1, 800:1 |
| VEV_5500 | 5000 | 3400:1, 4000:1, 3900:1, 4600:1, 1400:1 |
| VEV_5500 | 10000 | 3400:1, 4000:1, 8900:1, 4600:1, 1400:1 |

| symbol | side | unique_timestamp_keys | repeated_2plus_days | repeated_3_days |
| --- | --- | --- | --- | --- |
| HYDROGEL_PACK | buy | 493 | 3 | 0 |
| HYDROGEL_PACK | sell | 498 | 9 | 0 |
| VELVETFRUIT_EXTRACT | buy | 314 | 2 | 0 |
| VELVETFRUIT_EXTRACT | sell | 329 | 2 | 0 |
| VEV_4000 | buy | 231 | 1 | 0 |
| VEV_4000 | sell | 206 | 1 | 0 |
| VEV_5200 | buy | 33 | 0 | 0 |
| VEV_5300 | buy | 30 | 0 | 0 |
| VEV_5400 | buy | 13 | 0 | 0 |
| VEV_5500 | buy | 7 | 0 | 0 |

Within-day duplicate Mark 14 timestamps: 46 day/timestamp pairs with more than one Mark 14 event.
| day | timestamp | mark14_events | products | sides |
| --- | --- | --- | --- | --- |
| 2 | 423800 | 3 | HYDROGEL_PACK,VEV_5200,VEV_5500 | buy,sell |
| 3 | 943900 | 3 | VELVETFRUIT_EXTRACT,VEV_5300,VEV_5400 | buy,sell |
| 1 | 63200 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 1 | 218900 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 1 | 282200 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 1 | 323300 | 2 | HYDROGEL_PACK,VEV_4000 | sell |
| 1 | 345700 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 1 | 503500 | 2 | HYDROGEL_PACK,VEV_4000 | buy |
| 1 | 527700 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | sell |
| 1 | 720500 | 2 | VELVETFRUIT_EXTRACT,VEV_5300 | buy |
| 1 | 725800 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 1 | 772000 | 2 | HYDROGEL_PACK,VEV_4000 | sell |
| 1 | 815000 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | sell |
| 1 | 848900 | 2 | VEV_5300,VEV_5500 | buy |
| 2 | 45100 | 2 | HYDROGEL_PACK,VEV_5400 | buy,sell |
| 2 | 91700 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 2 | 169200 | 2 | HYDROGEL_PACK,VEV_4000 | buy,sell |
| 2 | 272900 | 2 | HYDROGEL_PACK,VEV_4000 | sell |
| 2 | 278800 | 2 | HYDROGEL_PACK,VELVETFRUIT_EXTRACT | buy,sell |
| 2 | 328700 | 2 | VELVETFRUIT_EXTRACT,VEV_4000 | buy,sell |

## Executability recheck

| symbol | side | n | historical_mean | executable_mean | mean_slippage |
| --- | --- | --- | --- | --- | --- |
| VEV_5500 | buy | 7 | 0.286 | -0.714 | 1 |
| VEV_5400 | buy | 13 | 0.077 | -0.923 | 1 |
| VEV_5300 | buy | 30 | 0.567 | -0.900 | 1.500 |
| VEV_5200 | buy | 33 | 0.909 | -1.500 | 2.424 |
| VELVETFRUIT_EXTRACT | buy | 316 | 2.339 | -2.332 | 4.728 |
| VELVETFRUIT_EXTRACT | sell | 331 | 2.304 | -2.663 | 4.921 |
| VEV_4000 | sell | 207 | 10.382 | -10.452 | 20.826 |
| VEV_4000 | buy | 232 | 10.216 | -10.565 | 20.802 |
| HYDROGEL_PACK | sell | 507 | 8.207 | -7.653 | 15.884 |
| HYDROGEL_PACK | buy | 496 | 8.116 | -7.911 | 15.966 |

Prior full strategy tests in shared docs: no-exit direct cross none=-2,024,289 / worse=-2,010,123; t+200 exit direct cross none=-5,428,091 / worse=-5,181,259; exact-quantity copy all none=worse=-1,175,572; exact-quantity copy on strong products none=worse=-1,179,912.

## Pre-event oracle check

| symbol | offset | n | cross_mean | passive_fill_rate | passive_mean_if_filled | passive_edge_per_event |
| --- | --- | --- | --- | --- | --- | --- |
| VEV_4000 | 100 | 439 | -10.590 | 0.941 | 9.081 | 8.543 |
| HYDROGEL_PACK | 100 | 1003 | -7.678 | 0.801 | 6.335 | 5.072 |
| VELVETFRUIT_EXTRACT | 100 | 647 | -2.511 | 0.912 | 1.279 | 1.166 |
| VEV_5200 | 100 | 33 | -1.303 | 0.939 | 0.226 | 0.212 |
| VEV_5300 | 100 | 30 | -0.867 | 1 | -0.067 | -0.067 |
| VEV_5500 | 100 | 7 | -0.714 | 1 | -0.429 | -0.429 |
| VEV_5400 | 100 | 13 | -0.923 | 1 | -0.615 | -0.615 |

This is an oracle because it assumes side and timing before the Mark 14 print. It confirms the prior pattern: crossing before the event is still negative, while passive fill proxies can be positive because they approximate Mark 14's favorable historical trade prices.

## Classification

- Market-maker: partial/passive, but not a broad symmetric market maker. Mark 14 is two-sided only in HGP/VFE/VEV_4000 and only buys the smaller option samples.
- Liquidity-taker: no on the main products. Mark 14 buys at bid and sells at ask in the same-timestamp book, so the visible aggressor is the other Mark.
- Informed/adverse: adverse to counterparties at the trade price, mainly through spread capture. There is little evidence of exploitable post-event directional mid drift after the ID is observed.
- Noise: no for HGP/VFE/VEV_4000 as a historical fill-quality signal; weak/small-sample for VEV_5200 and smaller options.

## v314159 comparison

- HYDROGEL_PACK: keep v314159 behavior unless a one-factor test proves otherwise. Mark 14 trade-price edge is +8.16, but next-tick executable edge is -7.78 overall and mid-to-mid drift is only about +0.2, so do not copy or tighten.
- VELVETFRUIT_EXTRACT: v314159 already suppresses VFE sells after M67/M49, not Mark 14. Mark 14 adds no clear post-event directional edge (mid-to-mid is negative on both sides), so the default recommendation is ignore.
- VEV_4000: strong historical trade-price signal (+10.29) but entirely non-executable by chasing; v314159's deep-ITM structural sleeve should not be changed from this Mark alone.
- VEV_5200 and other options: small buy-only samples and weak markouts. Ignore for baseline changes; this does not alter the existing Mark 22 option mask.

## Files created

- `notebooks/round4/mark_taxonomy/mark_14.py`
- `notebooks/round4/mark_taxonomy/mark_14_events.csv`
- `notebooks/round4/mark_taxonomy/mark_14_product_side_day_markouts.csv`
- `notebooks/round4/mark_taxonomy/mark_14_product_side_summary.csv`
- `notebooks/round4/mark_taxonomy/mark_14_book_relation.csv`
- `notebooks/round4/mark_taxonomy/mark_14_size_distribution.csv`
- `notebooks/round4/mark_taxonomy/mark_14_timing_gaps.csv`
- `notebooks/round4/mark_taxonomy/mark_14_timing_modulo.csv`
- `notebooks/round4/mark_taxonomy/mark_14_repeat_timestamps.csv`
- `notebooks/round4/mark_taxonomy/mark_14_duplicate_timestamps.csv`
- `notebooks/round4/mark_taxonomy/mark_14_counterparties.csv`
- `notebooks/round4/mark_taxonomy/mark_14_cooccurrence.csv`
- `notebooks/round4/mark_taxonomy/mark_14_executable_next_tick.csv`
- `notebooks/round4/mark_taxonomy/mark_14_executable_next_tick_summary.csv`
- `notebooks/round4/mark_taxonomy/mark_14_pre_event_oracle.csv`
