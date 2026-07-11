# Round 5 PEBBLES Leg Fair Proxy

Uses the identity `sum(PEBBLES mids) ~= 50000`. For each leg, synthetic fair is `mid_i - (sum_mid - 50000)`.
`edge_to_ask = synthetic_fair - best_ask`; `edge_to_bid = best_bid - synthetic_fair`.

## Event Summary

| mode         |   threshold |   horizon |    n |   mean_mo |   good_pct |   qty_proxy_edge |
|:-------------|------------:|----------:|-----:|----------:|-----------:|-----------------:|
| active_buy   |           0 |        10 | 2235 |  0.453244 |   0.50604  |           1013   |
| active_buy   |           0 |        20 | 2235 |  0.558613 |   0.510067 |           1248.5 |
| active_buy   |           0 |        50 | 2230 |  0.439013 |   0.497758 |            979   |
| active_buy   |           2 |        10 | 2235 |  0.453244 |   0.50604  |           1013   |
| active_buy   |           2 |        20 | 2235 |  0.558613 |   0.510067 |           1248.5 |
| active_buy   |           2 |        50 | 2230 |  0.439013 |   0.497758 |            979   |
| active_buy   |           4 |        10 | 2235 |  0.453244 |   0.50604  |           1013   |
| active_buy   |           4 |        20 | 2235 |  0.558613 |   0.510067 |           1248.5 |
| active_buy   |           4 |        50 | 2230 |  0.439013 |   0.497758 |            979   |
| active_buy   |           6 |        10 | 2235 |  0.453244 |   0.50604  |           1013   |
| active_buy   |           6 |        20 | 2235 |  0.558613 |   0.510067 |           1248.5 |
| active_buy   |           6 |        50 | 2230 |  0.439013 |   0.497758 |            979   |
| active_buy   |           8 |        10 | 2235 |  0.453244 |   0.50604  |           1013   |
| active_buy   |           8 |        20 | 2235 |  0.558613 |   0.510067 |           1248.5 |
| active_buy   |           8 |        50 | 2230 |  0.439013 |   0.497758 |            979   |
| active_sell  |           0 |        10 | 2030 | -0.447783 |   0.491133 |           -909   |
| active_sell  |           0 |        20 | 2030 | -0.451478 |   0.508374 |           -916.5 |
| active_sell  |           0 |        50 | 2030 | -0.500493 |   0.50936  |          -1016   |
| active_sell  |           2 |        10 | 2030 | -0.447783 |   0.491133 |           -909   |
| active_sell  |           2 |        20 | 2030 | -0.451478 |   0.508374 |           -916.5 |
| active_sell  |           2 |        50 | 2030 | -0.500493 |   0.50936  |          -1016   |
| active_sell  |           4 |        10 | 2030 | -0.447783 |   0.491133 |           -909   |
| active_sell  |           4 |        20 | 2030 | -0.451478 |   0.508374 |           -916.5 |
| active_sell  |           4 |        50 | 2030 | -0.500493 |   0.50936  |          -1016   |
| active_sell  |           6 |        10 | 2030 | -0.447783 |   0.491133 |           -909   |
| active_sell  |           6 |        20 | 2030 | -0.451478 |   0.508374 |           -916.5 |
| active_sell  |           6 |        50 | 2030 | -0.500493 |   0.50936  |          -1016   |
| active_sell  |           8 |        10 | 2030 | -0.447783 |   0.491133 |           -909   |
| active_sell  |           8 |        20 | 2030 | -0.451478 |   0.508374 |           -916.5 |
| active_sell  |           8 |        50 | 2030 | -0.500493 |   0.50936  |          -1016   |
| passive_buy  |           0 |        10 | 2235 |  5.46174  |   0.541387 |          12207   |
| passive_buy  |           0 |        20 | 2235 |  5.56711  |   0.530649 |          12442.5 |
| passive_buy  |           0 |        50 | 2230 |  5.44753  |   0.519283 |          12148   |
| passive_buy  |           2 |        10 | 2235 |  5.46174  |   0.541387 |          12207   |
| passive_buy  |           2 |        20 | 2235 |  5.56711  |   0.530649 |          12442.5 |
| passive_buy  |           2 |        50 | 2230 |  5.44753  |   0.519283 |          12148   |
| passive_buy  |           4 |        10 | 2235 |  5.46174  |   0.541387 |          12207   |
| passive_buy  |           4 |        20 | 2235 |  5.56711  |   0.530649 |          12442.5 |
| passive_buy  |           4 |        50 | 2230 |  5.44753  |   0.519283 |          12148   |
| passive_buy  |           6 |        10 | 2235 |  5.46174  |   0.541387 |          12207   |
| passive_buy  |           6 |        20 | 2235 |  5.56711  |   0.530649 |          12442.5 |
| passive_buy  |           6 |        50 | 2230 |  5.44753  |   0.519283 |          12148   |
| passive_buy  |           8 |        10 | 2235 |  5.46174  |   0.541387 |          12207   |
| passive_buy  |           8 |        20 | 2235 |  5.56711  |   0.530649 |          12442.5 |
| passive_buy  |           8 |        50 | 2230 |  5.44753  |   0.519283 |          12148   |
| passive_sell |           0 |        10 | 2030 |  5.54187  |   0.536946 |          11250   |
| passive_sell |           0 |        20 | 2030 |  5.53818  |   0.538916 |          11242.5 |
| passive_sell |           0 |        50 | 2030 |  5.48916  |   0.528079 |          11143   |
| passive_sell |           2 |        10 | 2030 |  5.54187  |   0.536946 |          11250   |
| passive_sell |           2 |        20 | 2030 |  5.53818  |   0.538916 |          11242.5 |
| passive_sell |           2 |        50 | 2030 |  5.48916  |   0.528079 |          11143   |
| passive_sell |           4 |        10 | 2030 |  5.54187  |   0.536946 |          11250   |
| passive_sell |           4 |        20 | 2030 |  5.53818  |   0.538916 |          11242.5 |
| passive_sell |           4 |        50 | 2030 |  5.48916  |   0.528079 |          11143   |
| passive_sell |           6 |        10 | 2030 |  5.54187  |   0.536946 |          11250   |
| passive_sell |           6 |        20 | 2030 |  5.53818  |   0.538916 |          11242.5 |
| passive_sell |           6 |        50 | 2030 |  5.48916  |   0.528079 |          11143   |
| passive_sell |           8 |        10 | 2030 |  5.54187  |   0.536946 |          11250   |
| passive_sell |           8 |        20 | 2030 |  5.53818  |   0.538916 |          11242.5 |
| passive_sell |           8 |        50 | 2030 |  5.48916  |   0.528079 |          11143   |

## By Product, Horizon 20

| product    | side         |   threshold |   n |   mean_mo20 |   good_pct20 |
|:-----------|:-------------|------------:|----:|------------:|-------------:|
| PEBBLES_L  | buy          |           0 | 447 |   -1.79195  |     0.47651  |
| PEBBLES_L  | buy          |           2 | 447 |   -1.79195  |     0.47651  |
| PEBBLES_L  | buy          |           4 | 447 |   -1.79195  |     0.47651  |
| PEBBLES_L  | buy          |           6 | 447 |   -1.79195  |     0.47651  |
| PEBBLES_L  | buy          |           8 | 447 |   -1.79195  |     0.47651  |
| PEBBLES_L  | sell         |           0 | 406 |   -0.481527 |     0.529557 |
| PEBBLES_L  | sell         |           2 | 406 |   -0.481527 |     0.529557 |
| PEBBLES_L  | sell         |           4 | 406 |   -0.481527 |     0.529557 |
| PEBBLES_L  | sell         |           6 | 406 |   -0.481527 |     0.529557 |
| PEBBLES_L  | sell         |           8 | 406 |   -0.481527 |     0.529557 |
| PEBBLES_L  | passive_buy  |           0 | 447 |    3.29978  |     0.516779 |
| PEBBLES_L  | passive_buy  |           2 | 447 |    3.29978  |     0.516779 |
| PEBBLES_L  | passive_buy  |           4 | 447 |    3.29978  |     0.516779 |
| PEBBLES_L  | passive_buy  |           6 | 447 |    3.29978  |     0.516779 |
| PEBBLES_L  | passive_buy  |           8 | 447 |    3.29978  |     0.516779 |
| PEBBLES_L  | passive_sell |           0 | 406 |    5.63424  |     0.554187 |
| PEBBLES_L  | passive_sell |           2 | 406 |    5.63424  |     0.554187 |
| PEBBLES_L  | passive_sell |           4 | 406 |    5.63424  |     0.554187 |
| PEBBLES_L  | passive_sell |           6 | 406 |    5.63424  |     0.554187 |
| PEBBLES_L  | passive_sell |           8 | 406 |    5.63424  |     0.554187 |
| PEBBLES_M  | buy          |           0 | 447 |    4.25168  |     0.532438 |
| PEBBLES_M  | buy          |           2 | 447 |    4.25168  |     0.532438 |
| PEBBLES_M  | buy          |           4 | 447 |    4.25168  |     0.532438 |
| PEBBLES_M  | buy          |           6 | 447 |    4.25168  |     0.532438 |
| PEBBLES_M  | buy          |           8 | 447 |    4.25168  |     0.532438 |
| PEBBLES_M  | sell         |           0 | 406 |   -6.92488  |     0.463054 |
| PEBBLES_M  | sell         |           2 | 406 |   -6.92488  |     0.463054 |
| PEBBLES_M  | sell         |           4 | 406 |   -6.92488  |     0.463054 |
| PEBBLES_M  | sell         |           6 | 406 |   -6.92488  |     0.463054 |
| PEBBLES_M  | sell         |           8 | 406 |   -6.92488  |     0.463054 |
| PEBBLES_M  | passive_buy  |           0 | 447 |    9.42841  |     0.552573 |
| PEBBLES_M  | passive_buy  |           2 | 447 |    9.42841  |     0.552573 |
| PEBBLES_M  | passive_buy  |           4 | 447 |    9.42841  |     0.552573 |
| PEBBLES_M  | passive_buy  |           6 | 447 |    9.42841  |     0.552573 |
| PEBBLES_M  | passive_buy  |           8 | 447 |    9.42841  |     0.552573 |
| PEBBLES_M  | passive_sell |           0 | 406 |   -0.767241 |     0.495074 |
| PEBBLES_M  | passive_sell |           2 | 406 |   -0.767241 |     0.495074 |
| PEBBLES_M  | passive_sell |           4 | 406 |   -0.767241 |     0.495074 |
| PEBBLES_M  | passive_sell |           6 | 406 |   -0.767241 |     0.495074 |
| PEBBLES_M  | passive_sell |           8 | 406 |   -0.767241 |     0.495074 |
| PEBBLES_S  | buy          |           0 | 447 |   -2.65212  |     0.516779 |
| PEBBLES_S  | buy          |           2 | 447 |   -2.65212  |     0.516779 |
| PEBBLES_S  | buy          |           4 | 447 |   -2.65212  |     0.516779 |
| PEBBLES_S  | buy          |           6 | 447 |   -2.65212  |     0.516779 |
| PEBBLES_S  | buy          |           8 | 447 |   -2.65212  |     0.516779 |
| PEBBLES_S  | sell         |           0 | 406 |    1.64039  |     0.507389 |
| PEBBLES_S  | sell         |           2 | 406 |    1.64039  |     0.507389 |
| PEBBLES_S  | sell         |           4 | 406 |    1.64039  |     0.507389 |
| PEBBLES_S  | sell         |           6 | 406 |    1.64039  |     0.507389 |
| PEBBLES_S  | sell         |           8 | 406 |    1.64039  |     0.507389 |
| PEBBLES_S  | passive_buy  |           0 | 447 |    1.717    |     0.530201 |
| PEBBLES_S  | passive_buy  |           2 | 447 |    1.717    |     0.530201 |
| PEBBLES_S  | passive_buy  |           4 | 447 |    1.717    |     0.530201 |
| PEBBLES_S  | passive_buy  |           6 | 447 |    1.717    |     0.530201 |
| PEBBLES_S  | passive_buy  |           8 | 447 |    1.717    |     0.530201 |
| PEBBLES_S  | passive_sell |           0 | 406 |    6.97783  |     0.551724 |
| PEBBLES_S  | passive_sell |           2 | 406 |    6.97783  |     0.551724 |
| PEBBLES_S  | passive_sell |           4 | 406 |    6.97783  |     0.551724 |
| PEBBLES_S  | passive_sell |           6 | 406 |    6.97783  |     0.551724 |
| PEBBLES_S  | passive_sell |           8 | 406 |    6.97783  |     0.551724 |
| PEBBLES_XL | buy          |           0 | 447 |    5.33221  |     0.534676 |
| PEBBLES_XL | buy          |           2 | 447 |    5.33221  |     0.534676 |
| PEBBLES_XL | buy          |           4 | 447 |    5.33221  |     0.534676 |
| PEBBLES_XL | buy          |           6 | 447 |    5.33221  |     0.534676 |
| PEBBLES_XL | buy          |           8 | 447 |    5.33221  |     0.534676 |
| PEBBLES_XL | sell         |           0 | 406 |   -1.30296  |     0.5      |
| PEBBLES_XL | sell         |           2 | 406 |   -1.30296  |     0.5      |
| PEBBLES_XL | sell         |           4 | 406 |   -1.30296  |     0.5      |
| PEBBLES_XL | sell         |           6 | 406 |   -1.30296  |     0.5      |
| PEBBLES_XL | sell         |           8 | 406 |   -1.30296  |     0.5      |
| PEBBLES_XL | passive_buy  |           0 | 447 |   12.2696   |     0.541387 |
| PEBBLES_XL | passive_buy  |           2 | 447 |   12.2696   |     0.541387 |
| PEBBLES_XL | passive_buy  |           4 | 447 |   12.2696   |     0.541387 |
| PEBBLES_XL | passive_buy  |           6 | 447 |   12.2696   |     0.541387 |
| PEBBLES_XL | passive_buy  |           8 | 447 |   12.2696   |     0.541387 |
| PEBBLES_XL | passive_sell |           0 | 406 |    6.64039  |     0.522167 |
| PEBBLES_XL | passive_sell |           2 | 406 |    6.64039  |     0.522167 |
| PEBBLES_XL | passive_sell |           4 | 406 |    6.64039  |     0.522167 |
| PEBBLES_XL | passive_sell |           6 | 406 |    6.64039  |     0.522167 |
| PEBBLES_XL | passive_sell |           8 | 406 |    6.64039  |     0.522167 |
| PEBBLES_XS | buy          |           0 | 447 |   -2.34676  |     0.489933 |
| PEBBLES_XS | buy          |           2 | 447 |   -2.34676  |     0.489933 |
| PEBBLES_XS | buy          |           4 | 447 |   -2.34676  |     0.489933 |
| PEBBLES_XS | buy          |           6 | 447 |   -2.34676  |     0.489933 |
| PEBBLES_XS | buy          |           8 | 447 |   -2.34676  |     0.489933 |
| PEBBLES_XS | sell         |           0 | 406 |    4.81158  |     0.541872 |
| PEBBLES_XS | sell         |           2 | 406 |    4.81158  |     0.541872 |
| PEBBLES_XS | sell         |           4 | 406 |    4.81158  |     0.541872 |
| PEBBLES_XS | sell         |           6 | 406 |    4.81158  |     0.541872 |
| PEBBLES_XS | sell         |           8 | 406 |    4.81158  |     0.541872 |
| PEBBLES_XS | passive_buy  |           0 | 447 |    1.12081  |     0.512304 |
| PEBBLES_XS | passive_buy  |           2 | 447 |    1.12081  |     0.512304 |
| PEBBLES_XS | passive_buy  |           4 | 447 |    1.12081  |     0.512304 |
| PEBBLES_XS | passive_buy  |           6 | 447 |    1.12081  |     0.512304 |
| PEBBLES_XS | passive_buy  |           8 | 447 |    1.12081  |     0.512304 |
| PEBBLES_XS | passive_sell |           0 | 406 |    9.20566  |     0.571429 |
| PEBBLES_XS | passive_sell |           2 | 406 |    9.20566  |     0.571429 |
| PEBBLES_XS | passive_sell |           4 | 406 |    9.20566  |     0.571429 |
| PEBBLES_XS | passive_sell |           6 | 406 |    9.20566  |     0.571429 |
| PEBBLES_XS | passive_sell |           8 | 406 |    9.20566  |     0.571429 |
