# Mark 49 Local Taxonomy

Events: 122; products: 1; days: 3; buys: 17; sells: 105.

## Product/Side Summary
            product side  events  days   avg_qty  touch_pct  mean_signed_price_vs_mid  edge_mean_50  edge_mean_200  edge_mean_500  good_pct_200  qty_edge_sum_200
VELVETFRUIT_EXTRACT  buy      17     3  6.764706   0.058824                 -1.500000      0.235294       0.264706      -0.323529      0.588235              24.5
VELVETFRUIT_EXTRACT sell     105     3 10.200000   0.009524                 -0.671429     -1.228571      -1.242857      -1.147619      0.161905           -1409.5

## Day Split
            product side  day  events   avg_qty  edge_mean_200  good_pct_200  qty_edge_sum_200
VELVETFRUIT_EXTRACT  buy    1       6  6.333333       0.166667      0.500000               4.0
VELVETFRUIT_EXTRACT  buy    2       6  6.666667       0.500000      0.666667              18.0
VELVETFRUIT_EXTRACT  buy    3       5  7.400000       0.100000      0.600000               2.5
VELVETFRUIT_EXTRACT sell    1      34 10.058824      -1.132353      0.117647            -440.5
VELVETFRUIT_EXTRACT sell    2      37 10.810811      -1.162162      0.081081            -489.5
VELVETFRUIT_EXTRACT sell    3      34  9.676471      -1.441176      0.294118            -479.5

## Timing Gaps
            product side  day  events  median_gap  pct_gap_le_1000  pct_gap_le_5000
VELVETFRUIT_EXTRACT  buy    1       6     68800.0         0.000000         0.000000
VELVETFRUIT_EXTRACT  buy    2       6    107000.0         0.000000         0.000000
VELVETFRUIT_EXTRACT  buy    3       5    169350.0         0.000000         0.000000
VELVETFRUIT_EXTRACT sell    1      34     17900.0         0.121212         0.212121
VELVETFRUIT_EXTRACT sell    2      37     21750.0         0.055556         0.194444
VELVETFRUIT_EXTRACT sell    3      34     20200.0         0.090909         0.151515

## Timestamp Recurrence Across Days
            product side  unique_timestamp_side  repeated_2plus_days  repeated_3_days
VELVETFRUIT_EXTRACT sell                    100                    0                0
VELVETFRUIT_EXTRACT  buy                     17                    0                0
