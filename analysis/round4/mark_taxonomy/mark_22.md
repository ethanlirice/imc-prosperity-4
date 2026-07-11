# Mark 22 Counterparty Taxonomy
Data: `data/ROUND4` days 1-3. Markout sign convention: `mark22_mo` is favorable to Mark 22; `contra_mo` is favorable to the counterparty. Forward mid is first book mid at timestamp >= event timestamp + horizon. Because book timestamps are 100 units apart, t+10 and t+50 both resolve to the next book update for these events.
## Executive Read
- Mark 22 appears in 1584 trade rows, 5889 total contracts: 1439 option rows / 4972 contracts and 145 VFE/HGP rows / 917 contracts.
- Behavior is dominated by scheduled, multi-strike option selling. The dominant option role is selling at the displayed bid, so the historical option print stream looks like liquidity-taking sell flow rather than passive market making.
- Raw seller-to-buyer option markouts are positive on VEV_5200/5300/5400/5500 at t+200. VEV_5200 is the largest non-dead strike signal; VEV_5400/5500 are consistent but mostly half-tick to one-tick effects in tight high-gamma books.
- Recommendation versus v314159: keep Mark22 buy-edge reduction on VEV_5200/VEV_5500; treat VEV_5400 and VEV_5300 as test-only because they are already in the high-gamma tight-edge path and the baseline notes VEV_5400 hurt in sim; ignore 6000/6500 due zero/one-tick dead-market mechanics; no sell suppression is supported by this taxonomy.
## Side Bias
| mark22_side   |   trades |   qty |
|:--------------|---------:|------:|
| buy           |       42 |   206 |
| sell          |     1542 |  5683 |
## Product And Side Inventory
| product             | side   |   trades |   total_qty |   avg_qty |   median_qty |   p90_qty |   avg_price_vs_mid | avg_price_vs_fair   |   median_spread | dominant_role       |   dominant_role_share |
|:--------------------|:-------|---------:|------------:|----------:|-------------:|----------:|-------------------:|:--------------------|----------------:|:--------------------|----------------------:|
| HYDROGEL_PACK       | buy    |       11 |          42 |     3.818 |          4   |       5   |             -4.091 |                     |             8   | passive_buy_at_bid  |                 1     |
| HYDROGEL_PACK       | sell   |        8 |          32 |     4     |          3.5 |       6   |              3.562 |                     |             7   | passive_sell_at_ask |                 1     |
| VELVETFRUIT_EXTRACT | buy    |       25 |         146 |     5.84  |          5   |       8   |             -0.88  |                     |             3   | passive_buy_at_bid  |                 0.76  |
| VELVETFRUIT_EXTRACT | sell   |      101 |         697 |     6.901 |          7   |      10   |              0.708 |                     |             2   | passive_sell_at_ask |                 0.891 |
| VEV_4000            | buy    |        1 |           3 |     3     |          3   |       3   |             -5.5   | -24.000             |            11   | passive_buy_at_bid  |                 1     |
| VEV_4000            | sell   |        2 |           3 |     1.5   |          1.5 |       1.9 |              5     | -14.000             |            10   | passive_sell_at_ask |                 1     |
| VEV_4500            | buy    |        1 |           3 |     3     |          3   |       3   |             -4     | -24.000             |             8   | passive_buy_at_bid  |                 1     |
| VEV_4500            | sell   |        2 |           3 |     1.5   |          1.5 |       1.9 |              3.5   | -14.000             |             7   | passive_sell_at_ask |                 1     |
| VEV_5000            | buy    |        1 |           3 |     3     |          3   |       3   |             -1.5   | -22.341             |             3   | passive_buy_at_bid  |                 1     |
| VEV_5000            | sell   |        2 |           3 |     1.5   |          1.5 |       1.9 |              1     | -13.330             |             2   | passive_sell_at_ask |                 1     |
| VEV_5100            | buy    |        1 |           3 |     3     |          3   |       3   |             -1.5   | -19.000             |             3   | passive_buy_at_bid  |                 1     |
| VEV_5100            | sell   |        2 |           3 |     1.5   |          1.5 |       1.9 |              0.75  | -11.314             |             1.5 | passive_sell_at_ask |                 1     |
| VEV_5200            | buy    |        1 |           3 |     3     |          3   |       3   |             -1     | -11.644             |             2   | passive_buy_at_bid  |                 1     |
| VEV_5200            | sell   |       46 |         159 |     3.457 |          3.5 |       5   |             -0.935 | -8.861              |             2   | taker_sell_at_bid   |                 0.957 |
| VEV_5300            | buy    |        1 |           3 |     3     |          3   |       3   |             -0.5   | -2.648              |             1   | passive_buy_at_bid  |                 1     |
| VEV_5300            | sell   |      163 |         545 |     3.344 |          3   |       5   |             -0.871 | -0.646              |             2   | taker_sell_at_bid   |                 0.982 |
| VEV_5400            | sell   |      276 |         959 |     3.475 |          4   |       5   |             -0.589 | -1.677              |             1   | taker_sell_at_bid   |                 0.996 |
| VEV_5500            | sell   |      306 |        1069 |     3.493 |          4   |       5   |             -0.526 | 0.413               |             1   | taker_sell_at_bid   |                 1     |
| VEV_6000            | sell   |      317 |        1105 |     3.486 |          4   |       5   |             -0.5   | -0.000              |             1   | taker_sell_at_bid   |                 1     |
| VEV_6500            | sell   |      317 |        1105 |     3.486 |          4   |       5   |             -0.5   | -0.000              |             1   | taker_sell_at_bid   |                 1     |
## Markouts By Product, Side, Day
Positive values below favor the counterparty trading against Mark 22.
|   day | product             | side   |   trades |   total_qty |   contra_mean_t10 |   contra_mean_t50 |   contra_mean_t200 |   contra_mean_t500 |   contra_win_rate_t200 |
|------:|:--------------------|:-------|---------:|------------:|------------------:|------------------:|-------------------:|-------------------:|-----------------------:|
|     1 | HYDROGEL_PACK       | buy    |        3 |          11 |            -1     |            -1     |             -1.667 |             -3.333 |                  0     |
|     1 | HYDROGEL_PACK       | sell   |        2 |           7 |            -2.5   |            -2.5   |             -1     |             -4.5   |                  0     |
|     2 | HYDROGEL_PACK       | buy    |        4 |          15 |            -0.25  |            -0.25  |             -0.75  |             -0.875 |                  0.25  |
|     2 | HYDROGEL_PACK       | sell   |        4 |          17 |             0.5   |             0.5   |              1     |              0.25  |                  0.5   |
|     3 | HYDROGEL_PACK       | buy    |        4 |          16 |            -1.75  |            -1.75  |              0.25  |             -0.5   |                  0.5   |
|     3 | HYDROGEL_PACK       | sell   |        2 |           8 |             0     |             0     |              0.5   |              2.5   |                  0.5   |
|     1 | VELVETFRUIT_EXTRACT | buy    |       10 |          61 |            -0.2   |            -0.2   |             -0.15  |             -0.3   |                  0.4   |
|     1 | VELVETFRUIT_EXTRACT | sell   |       40 |         274 |             0.812 |             0.812 |              0.662 |              1.238 |                  0.725 |
|     2 | VELVETFRUIT_EXTRACT | buy    |        9 |          51 |            -0.611 |            -0.611 |              0     |              0.222 |                  0.444 |
|     2 | VELVETFRUIT_EXTRACT | sell   |       37 |         241 |             0.73  |             0.73  |              0.959 |              0.757 |                  0.838 |
|     3 | VELVETFRUIT_EXTRACT | buy    |        6 |          34 |            -1     |            -1     |             -1.167 |             -1.833 |                  0.167 |
|     3 | VELVETFRUIT_EXTRACT | sell   |       24 |         182 |             0.875 |             0.875 |              0.583 |              0.292 |                  0.625 |
|     1 | VEV_4000            | sell   |        1 |           1 |             5.5   |             5.5   |              0     |             -1     |                  0     |
|     3 | VEV_4000            | buy    |        1 |           3 |             0.5   |             0.5   |             -2     |             -4     |                  0     |
|     3 | VEV_4000            | sell   |        1 |           2 |            -0.5   |            -0.5   |             -0.5   |              0.5   |                  0     |
|     1 | VEV_4500            | sell   |        1 |           1 |             4     |             4     |              0     |             -1     |                  0     |
|     3 | VEV_4500            | buy    |        1 |           3 |             0.5   |             0.5   |             -2     |             -4     |                  0     |
|     3 | VEV_4500            | sell   |        1 |           2 |             0     |             0     |              0     |              0     |                  0     |
|     1 | VEV_5000            | sell   |        1 |           1 |             2     |             2     |              0.5   |             -0.5   |                  1     |
|     3 | VEV_5000            | buy    |        1 |           3 |             0     |             0     |             -2     |             -4     |                  0     |
|     3 | VEV_5000            | sell   |        1 |           2 |            -0.5   |            -0.5   |              0     |              0     |                  0     |
|     1 | VEV_5100            | sell   |        1 |           1 |             1     |             1     |              0     |             -1     |                  0     |
|     3 | VEV_5100            | buy    |        1 |           3 |             0     |             0     |             -2     |             -4     |                  0     |
|     3 | VEV_5100            | sell   |        1 |           2 |             0     |             0     |              0     |              0     |                  0     |
|     1 | VEV_5200            | sell   |        7 |          22 |             1.286 |             1.286 |              0.571 |              0.357 |                  0.714 |
|     2 | VEV_5200            | sell   |        8 |          26 |             1.312 |             1.312 |              1.062 |              1     |                  0.875 |
|     3 | VEV_5200            | buy    |        1 |           3 |             0     |             0     |             -1.5   |             -3     |                  0     |
|     3 | VEV_5200            | sell   |       31 |         111 |             0.919 |             0.919 |              0.919 |              0.742 |                  0.774 |
|     1 | VEV_5300            | sell   |       39 |         130 |             0.821 |             0.821 |              0.808 |              0.718 |                  0.769 |
|     2 | VEV_5300            | sell   |       45 |         162 |             0.7   |             0.7   |              0.633 |              0.656 |                  0.622 |
|     3 | VEV_5300            | buy    |        1 |           3 |             0     |             0     |             -1     |             -1     |                  0     |
|     3 | VEV_5300            | sell   |       79 |         253 |             0.715 |             0.715 |              0.696 |              0.671 |                  0.772 |
|     1 | VEV_5400            | sell   |       81 |         286 |             0.543 |             0.543 |              0.549 |              0.593 |                  0.84  |
|     2 | VEV_5400            | sell   |       80 |         283 |             0.581 |             0.581 |              0.562 |              0.581 |                  0.838 |
|     3 | VEV_5400            | sell   |      115 |         390 |             0.522 |             0.522 |              0.53  |              0.517 |                  0.93  |
|     1 | VEV_5500            | sell   |       92 |         321 |             0.505 |             0.505 |              0.522 |              0.516 |                  0.935 |
|     2 | VEV_5500            | sell   |       94 |         335 |             0.516 |             0.516 |              0.495 |              0.495 |                  0.957 |
|     3 | VEV_5500            | sell   |      120 |         413 |             0.5   |             0.5   |              0.508 |              0.492 |                  0.992 |
|     1 | VEV_6000            | sell   |       98 |         345 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
|     2 | VEV_6000            | sell   |       95 |         337 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
|     3 | VEV_6000            | sell   |      124 |         423 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
|     1 | VEV_6500            | sell   |       98 |         345 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
|     2 | VEV_6500            | sell   |       95 |         337 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
|     3 | VEV_6500            | sell   |      124 |         423 |             0.5   |             0.5   |              0.5   |              0.5   |                  1     |
## Option-Selling Focus
Aggregate buyer markout when Mark 22 sells:
| product   |   trades |   qty |   buyer_mean_t10 |   buyer_mean_t50 |   buyer_mean_t200 |   buyer_mean_t500 |   buyer_win_t200 |
|:----------|---------:|------:|-----------------:|-----------------:|------------------:|------------------:|-----------------:|
| VEV_4000  |        2 |     3 |            2.5   |            2.5   |            -0.25  |            -0.25  |            0     |
| VEV_4500  |        2 |     3 |            2     |            2     |             0     |            -0.5   |            0     |
| VEV_5000  |        2 |     3 |            0.75  |            0.75  |             0.25  |            -0.25  |            0.5   |
| VEV_5100  |        2 |     3 |            0.5   |            0.5   |             0     |            -0.5   |            0     |
| VEV_5200  |       46 |   159 |            1.043 |            1.043 |             0.891 |             0.728 |            0.783 |
| VEV_5300  |      163 |   545 |            0.736 |            0.736 |             0.706 |             0.678 |            0.73  |
| VEV_5400  |      276 |   959 |            0.545 |            0.545 |             0.545 |             0.558 |            0.877 |
| VEV_5500  |      306 |  1069 |            0.507 |            0.507 |             0.508 |             0.5   |            0.964 |
| VEV_6000  |      317 |  1105 |            0.5   |            0.5   |             0.5   |             0.5   |            1     |
| VEV_6500  |      317 |  1105 |            0.5   |            0.5   |             0.5   |             0.5   |            1     |
Day slices for v314159-relevant strikes:
|   day | product   | side   |   trades |   total_qty |   contra_mean_t10 |   contra_mean_t50 |   contra_mean_t200 |   contra_mean_t500 |   contra_win_rate_t200 |
|------:|:----------|:-------|---------:|------------:|------------------:|------------------:|-------------------:|-------------------:|-----------------------:|
|     1 | VEV_5200  | sell   |        7 |          22 |             1.286 |             1.286 |              0.571 |              0.357 |                  0.714 |
|     2 | VEV_5200  | sell   |        8 |          26 |             1.312 |             1.312 |              1.062 |              1     |                  0.875 |
|     3 | VEV_5200  | sell   |       31 |         111 |             0.919 |             0.919 |              0.919 |              0.742 |                  0.774 |
|     1 | VEV_5400  | sell   |       81 |         286 |             0.543 |             0.543 |              0.549 |              0.593 |                  0.84  |
|     2 | VEV_5400  | sell   |       80 |         283 |             0.581 |             0.581 |              0.562 |              0.581 |                  0.838 |
|     3 | VEV_5400  | sell   |      115 |         390 |             0.522 |             0.522 |              0.53  |              0.517 |                  0.93  |
|     1 | VEV_5500  | sell   |       92 |         321 |             0.505 |             0.505 |              0.522 |              0.516 |                  0.935 |
|     2 | VEV_5500  | sell   |       94 |         335 |             0.516 |             0.516 |              0.495 |              0.495 |                  0.957 |
|     3 | VEV_5500  | sell   |      120 |         413 |             0.5   |             0.5   |              0.508 |              0.492 |                  0.992 |
## Book Relation And Regimes
| mark22_side   | role                |   trades |
|:--------------|:--------------------|---------:|
| buy           | passive_buy_at_bid  |       36 |
| buy           | taker_buy_at_ask    |        6 |
| sell          | inside_spread       |        3 |
| sell          | passive_sell_at_ask |      109 |
| sell          | taker_sell_at_bid   |     1430 |
Average percentile columns compare Mark 22 event books to the same product/day full-book distribution.
| product             | side   |   trades |   median_spread |   avg_spread_pctile |   avg_top_depth |   avg_top_depth_pctile | dominant_role       |
|:--------------------|:-------|---------:|----------------:|--------------------:|----------------:|-----------------------:|:--------------------|
| HYDROGEL_PACK       | buy    |       11 |             8   |                2.63 |           20.27 |                  19.62 | passive_buy_at_bid  |
| HYDROGEL_PACK       | sell   |        8 |             7   |                1.02 |           18.5  |                  11.42 | passive_sell_at_ask |
| VELVETFRUIT_EXTRACT | buy    |       25 |             3   |                6.09 |           47.68 |                  19.73 | passive_buy_at_bid  |
| VELVETFRUIT_EXTRACT | sell   |      101 |             2   |                4.42 |           60.97 |                  30.53 | passive_sell_at_ask |
| VEV_4000            | buy    |        1 |            11   |                2.21 |           15    |                  12.36 | passive_buy_at_bid  |
| VEV_4000            | sell   |        2 |            10   |                1.16 |           13.5  |                  17.13 | passive_sell_at_ask |
| VEV_4500            | buy    |        1 |             8   |                1.89 |           13    |                  15.42 | passive_buy_at_bid  |
| VEV_4500            | sell   |        2 |             7   |                0.67 |           10.5  |                   8.03 | passive_sell_at_ask |
| VEV_5000            | buy    |        1 |             3   |                1.8  |           13    |                   5.91 | passive_buy_at_bid  |
| VEV_5000            | sell   |        2 |             2   |                0.64 |           10.5  |                   3.44 | passive_sell_at_ask |
| VEV_5100            | buy    |        1 |             3   |               14.02 |           30    |                  22.58 | passive_buy_at_bid  |
| VEV_5100            | sell   |        2 |             1.5 |                1.01 |           22    |                  20.63 | passive_sell_at_ask |
| VEV_5200            | buy    |        1 |             2   |               46.15 |           30    |                  10.86 | passive_buy_at_bid  |
| VEV_5200            | sell   |       46 |             2   |               35.04 |           34.24 |                  27.36 | taker_sell_at_bid   |
| VEV_5300            | buy    |        1 |             1   |               25.07 |           26    |                   5.98 | passive_buy_at_bid  |
| VEV_5300            | sell   |      163 |             2   |               76.42 |           37.78 |                  41.64 | taker_sell_at_bid   |
| VEV_5400            | sell   |      276 |             1   |               76.68 |           39.91 |                  39    | taker_sell_at_bid   |
| VEV_5500            | sell   |      306 |             1   |               90.26 |           40.74 |                  38.48 | taker_sell_at_bid   |
| VEV_6000            | sell   |      317 |             1   |              100    |           41.19 |                  38.28 | taker_sell_at_bid   |
| VEV_6500            | sell   |      317 |             1   |              100    |           27.75 |                  36.72 | taker_sell_at_bid   |
## Timing And Periodicity
|   day |   trade_rows |   unique_timestamps |   first_ts |   last_ts |   median_gap |   mean_gap | top_gap_counts                                                                                 |   max_rows_same_ts |   median_rows_same_ts |
|------:|-------------:|--------------------:|-----------:|----------:|-------------:|-----------:|:-----------------------------------------------------------------------------------------------|-------------------:|----------------------:|
|     1 |          474 |                 152 |       4500 |    990300 |         4500 |     6528.5 | 4500x6; 2000x5; 600x5; 1300x5; 700x4; 900x3; 4400x3; 100x3; 5800x3; 5500x3; 1800x3; 5900x2     |                 10 |                     4 |
|     2 |          471 |                 148 |       9900 |    993800 |         4700 |     6693.2 | 500x5; 1000x5; 2100x4; 2500x3; 1700x3; 3300x3; 12000x3; 2800x3; 8500x3; 10800x3; 300x3; 1100x3 |                  6 |                     4 |
|     3 |          639 |                 161 |      31400 |    997100 |         4000 |     6035.6 | 3400x6; 2500x5; 200x5; 3200x4; 500x4; 1600x4; 6500x4; 5100x4; 2300x4; 2100x4; 1200x3; 4000x3   |                 10 |                     5 |
- Unique day/timestamps: 461; calendar timestamps by number of days observed: {1: 447, 2: 7}.
- Timestamp+product+side keys: 1561; repeated on 2+ days: 23; repeated on all 3 days: 0.
Most repeated timestamp basket signatures:
| basket                                                                              |   days_seen |
|:------------------------------------------------------------------------------------|------------:|
| buy:HYDROGEL_PACK                                                                   |           3 |
| sell:VEV_5200,sell:VEV_5300,sell:VEV_5400,sell:VEV_5500,sell:VEV_6000,sell:VEV_6500 |           3 |
| sell:VEV_5400,sell:VEV_5500,sell:VEV_6000,sell:VEV_6500                             |           3 |
| sell:VEV_5300,sell:VEV_5500,sell:VEV_6000,sell:VEV_6500                             |           3 |
| sell:VEV_5300,sell:VEV_5400,sell:VEV_5500,sell:VEV_6000,sell:VEV_6500               |           3 |
| buy:VELVETFRUIT_EXTRACT                                                             |           3 |
| sell:VEV_5500,sell:VEV_6000,sell:VEV_6500                                           |           3 |
| sell:VELVETFRUIT_EXTRACT                                                            |           3 |
## Interactions With Other Marks
Direct counterparties in Mark 22 rows:
| counterparty   | symbol              | mark22_side   |   trades |   qty |
|:---------------|:--------------------|:--------------|---------:|------:|
| Mark 01        | VEV_6000            | sell          |      317 |  1105 |
| Mark 01        | VEV_6500            | sell          |      317 |  1105 |
| Mark 01        | VEV_5500            | sell          |      299 |  1042 |
| Mark 01        | VEV_5400            | sell          |      263 |   911 |
| Mark 01        | VEV_5300            | sell          |      132 |   439 |
| Mark 67        | VELVETFRUIT_EXTRACT | sell          |       75 |   546 |
| Mark 14        | VEV_5200            | sell          |       33 |   122 |
| Mark 14        | VEV_5300            | sell          |       30 |   105 |
| Mark 55        | VELVETFRUIT_EXTRACT | buy           |       18 |    92 |
| Mark 55        | VELVETFRUIT_EXTRACT | sell          |       14 |    62 |
| Mark 14        | VEV_5400            | sell          |       13 |    48 |
| Mark 49        | VELVETFRUIT_EXTRACT | sell          |       12 |    89 |
| Mark 38        | HYDROGEL_PACK       | buy           |       11 |    42 |
| Mark 01        | VEV_5200            | sell          |       11 |    34 |
| Mark 38        | HYDROGEL_PACK       | sell          |        8 |    32 |
| Mark 49        | VELVETFRUIT_EXTRACT | buy           |        7 |    54 |
| Mark 14        | VEV_5500            | sell          |        7 |    27 |
| Mark 38        | VEV_4000            | sell          |        2 |     3 |
| Mark 38        | VEV_4500            | sell          |        2 |     3 |
| Mark 38        | VEV_5000            | sell          |        2 |     3 |
Other Mark IDs appearing at the same timestamp as at least one Mark 22 trade:
| other_mark   |   timestamp_count |
|:-------------|------------------:|
| Mark 01      |               321 |
| Mark 14      |                97 |
| Mark 67      |                79 |
| Mark 55      |                49 |
| Mark 38      |                42 |
| Mark 49      |                19 |
- Same-timestamp rows: 461 Mark22 timestamps; median all trade rows at those timestamps = 4.0; median non-Mark22 rows = 0.0.
## Classification
- Market-maker: weak fit. Mark 22 does not trade both sides broadly; side is dominated by sells, and prints are concentrated in option baskets.
- Liquidity-taker: strong fit for the observed print mechanics; most Mark 22 sells occur at the displayed bid.
- Informed/adverse: mixed by strike. Counterparties buying from Mark 22 have positive t+200/t+500 markouts in the listed vulnerable strikes, especially 5200/5500, but the signal is not clean enough to blanket-follow all strikes.
- Noise/dead-market flow: 6000/6500 prints mostly occur at zero against one-tick books; they should not drive strategy changes.
## v314159 Comparison
- Current overlay: `MARK22_VULNERABLE_STRIKES = {VEV_5200, VEV_5500}`, buy edge reduction 1.5 with floor 0.5.
- Keep/skew: VEV_5200 remains the clearest Mark22-specific buy-tighten target by raw markout magnitude. VEV_5500 remains acceptable because it is already validated in v314159 despite the raw edge being mostly half a tick.
- VEV_5300/5400: raw buyer markouts after Mark 22 sells are positive and stable, but both strikes already use `HIGH_GAMMA_EDGE = 1`; classify additional Mark22 reduction as `test-only`, not a direct promote. This especially applies to VEV_5400 because the baseline comment records an about 10k R4 loss when included in the mask.
- Widen/suppress: no evidence here supports suppressing our option buys after Mark 22 sells; if anything, the counterparty side is the favorable historical side on selected strikes. No evidence supports making our sell side more aggressive due solely to Mark 22.
## Generated Files
- `notebooks/round4/mark_taxonomy/mark_22.py`
- `notebooks/round4/mark_taxonomy/mark_22.events.csv`
- `notebooks/round4/mark_taxonomy/mark_22.product_side.csv`
- `notebooks/round4/mark_taxonomy/mark_22.markouts_by_day.csv`
- `notebooks/round4/mark_taxonomy/mark_22.timing.csv`
- `notebooks/round4/mark_taxonomy/mark_22.direct_counterparties.csv`
- `notebooks/round4/mark_taxonomy/mark_22.same_timestamp.csv`
- `notebooks/round4/mark_taxonomy/mark_22.cooccurring_marks.csv`
- `notebooks/round4/mark_taxonomy/mark_22.md`
