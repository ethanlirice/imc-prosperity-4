# Round 5 Phase 1 - Group Tradeability

Composite score uses `intra_group_corr * spread_to_vol * depth * lively_ticks_pct`.
`spread_to_vol` is implemented as return-volatility divided by median spread, so higher means the group moves enough to pay crossing costs.
Validation requirement: ranking should be stable across days 2, 3, and 4; unstable high-score groups are treated as lower confidence.

## Ranked Groups

| group         |   stable_tradeability_score |   score_mean |   score_min |   rank_mean |   rank_worst |   intra_group_corr |   spread_to_vol |    depth |   lively_ticks_pct |
|:--------------|----------------------------:|-------------:|------------:|------------:|-------------:|-------------------:|----------------:|---------:|-------------------:|
| SNACKPACK     |                   23.2173   |    23.3736   |   23.2173   |     1       |            1 |           0.374163 |        0.406472 | 160      |           0.960536 |
| PEBBLES       |                   10.6864   |    21.5796   |   21.3728   |     2       |            2 |           0.207132 |        1.39295  |  76      |           0.984125 |
| UV_VISOR      |                    0.108117 |     0.722312 |    0.648704 |     4       |            6 |           0.009902 |        0.75613  |  99.3333 |           0.973384 |
| TRANSLATOR    |                    0.076697 |     0.601173 |    0.536877 |     5.33333 |            7 |           0.009334 |        1.10354  |  60      |           0.972484 |
| SLEEP_POD     |                    0.05981  |     0.61651  |    0.538288 |     6       |            9 |           0.00919  |        1.1433   |  60      |           0.976211 |
| MICROCHIP     |                    0.0518   |     0.530108 |    0.466204 |     6.66667 |            9 |           0.010065 |        1.67527  |  32      |           0.978324 |
| PANEL         |                    0.038101 |     0.443035 |    0.381009 |     8.33333 |           10 |           0.006706 |        1.09576  |  62      |           0.973084 |
| GALAXY_SOUNDS |                    0.033463 |     0.546174 |    0.30117  |     6.33333 |            9 |           0.007136 |        0.793104 |  99.3333 |           0.975811 |
| OXYGEN_SHAKE  |                    0.028697 |     0.593985 |    0.286971 |     6.66667 |           10 |           0.007878 |        0.849648 |  99.3333 |           0.875208 |
| ROBOT         |                    0.028144 |     0.381397 |    0.281435 |     8.66667 |           10 |           0.008754 |        1.60592  |  32      |           0.850158 |

## Selected For Phase 2/3

- **SNACKPACK**: stable score 23.217253, mean rank 1.00, worst rank 1; corr 0.3742, vol/spread 0.4065, depth 160.0, lively 0.961.
- **PEBBLES**: stable score 10.686380, mean rank 2.00, worst rank 2; corr 0.2071, vol/spread 1.3929, depth 76.0, lively 0.984.
- **UV_VISOR**: stable score 0.108117, mean rank 4.00, worst rank 6; corr 0.0099, vol/spread 0.7561, depth 99.3, lively 0.973.
- **TRANSLATOR**: stable score 0.076697, mean rank 5.33, worst rank 7; corr 0.0093, vol/spread 1.1035, depth 60.0, lively 0.972.

## Excluded Groups

- **SLEEP_POD**: rejected for weak worst-day rank 9, below-median return co-movement.
- **MICROCHIP**: rejected for weak worst-day rank 9, low minimum day score.
- **PANEL**: rejected for weak worst-day rank 10, low minimum day score, below-median return co-movement, movement is thin versus spread.
- **GALAXY_SOUNDS**: rejected for weak worst-day rank 9, low minimum day score, below-median return co-movement, movement is thin versus spread.
- **OXYGEN_SHAKE**: rejected for weak worst-day rank 10, low minimum day score, below-median return co-movement, movement is thin versus spread.
- **ROBOT**: rejected for weak worst-day rank 10, low minimum day score, below-median return co-movement.

## Per-Day Scores

|   day | group         |   day_rank |   tradeability_score |   intra_group_corr |   spread_to_vol |   depth |   lively_ticks_pct |
|------:|:--------------|-----------:|---------------------:|-------------------:|----------------:|--------:|-------------------:|
|     2 | SNACKPACK     |          1 |            23.4915   |           0.374508 |        0.40853  |     160 |           0.959636 |
|     2 | PEBBLES       |          2 |            21.3728   |           0.205095 |        1.39373  |      76 |           0.983818 |
|     2 | UV_VISOR      |          3 |             0.648704 |           0.008467 |        0.787772 |     100 |           0.972617 |
|     2 | SLEEP_POD     |          4 |             0.623416 |           0.009193 |        1.1599   |      60 |           0.974457 |
|     2 | TRANSLATOR    |          5 |             0.536877 |           0.008392 |        1.09659  |      60 |           0.972357 |
|     2 | MICROCHIP     |          6 |             0.474602 |           0.009716 |        1.56174  |      32 |           0.977418 |
|     2 | PANEL         |          7 |             0.392861 |           0.005837 |        1.1146   |      62 |           0.973937 |
|     2 | ROBOT         |          8 |             0.349102 |           0.008073 |        1.50486  |      32 |           0.89803  |
|     2 | GALAXY_SOUNDS |          9 |             0.30117  |           0.003848 |        0.802581 |     100 |           0.975258 |
|     2 | OXYGEN_SHAKE  |         10 |             0.286971 |           0.004153 |        0.841828 |     100 |           0.820742 |
|     3 | SNACKPACK     |          1 |            23.4121   |           0.373953 |        0.406879 |     160 |           0.961696 |
|     3 | PEBBLES       |          2 |            21.7119   |           0.20791  |        1.39602  |      76 |           0.984278 |
|     3 | UV_VISOR      |          3 |             0.860342 |           0.011906 |        0.741565 |     100 |           0.974477 |
|     3 | TRANSLATOR    |          4 |             0.67628  |           0.010492 |        1.10566  |      60 |           0.971597 |
|     3 | MICROCHIP     |          5 |             0.649518 |           0.011593 |        1.78895  |      32 |           0.978658 |
|     3 | GALAXY_SOUNDS |          6 |             0.612418 |           0.008013 |        0.783462 |     100 |           0.975498 |
|     3 | OXYGEN_SHAKE  |          7 |             0.61113  |           0.008504 |        0.79406  |     100 |           0.90499  |
|     3 | PANEL         |          8 |             0.555236 |           0.008445 |        1.08979  |      62 |           0.973077 |
|     3 | SLEEP_POD     |          9 |             0.538288 |           0.008342 |        1.1001   |      60 |           0.977658 |
|     3 | ROBOT         |         10 |             0.281435 |           0.006781 |        1.43816  |      32 |           0.90183  |
|     4 | SNACKPACK     |          1 |            23.2173   |           0.374029 |        0.404008 |     160 |           0.960276 |
|     4 | PEBBLES       |          2 |            21.6542   |           0.208391 |        1.38909  |      76 |           0.984278 |
|     4 | OXYGEN_SHAKE  |          3 |             0.883852 |           0.010977 |        0.913056 |      98 |           0.89989  |
|     4 | GALAXY_SOUNDS |          4 |             0.724934 |           0.009548 |        0.793269 |      98 |           0.976678 |
|     4 | SLEEP_POD     |          5 |             0.687827 |           0.010035 |        1.16989  |      60 |           0.976518 |
|     4 | UV_VISOR      |          6 |             0.657891 |           0.009335 |        0.739053 |      98 |           0.973057 |
|     4 | TRANSLATOR    |          7 |             0.590362 |           0.009119 |        1.10835  |      60 |           0.973497 |
|     4 | ROBOT         |          8 |             0.513655 |           0.011407 |        1.87473  |      32 |           0.750615 |
|     4 | MICROCHIP     |          9 |             0.466204 |           0.008885 |        1.67511  |      32 |           0.978898 |
|     4 | PANEL         |         10 |             0.381009 |           0.005837 |        1.08291  |      62 |           0.972237 |
