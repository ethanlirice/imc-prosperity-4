# Round 5 wall-mid / permanent-MM fair research

Scope: Round 5 price books only, days 2, 3, and 4, all 50 products. The tested fairs are:

- `wall_mid`: midpoint of the largest displayed bid-side wall price and largest displayed ask-side wall price in the current book.
- `popular_mid`: midpoint of the trailing 1000-row quote-volume modes on bid and ask, using only prior rows after 200 rows of warmup.
- `depth_vwap_mid`: depth-weighted quote midpoint across the three displayed levels, included as a control.

For markouts, positive means `fair - mid` correctly predicted the future mid move. For crossing, buys cross the ask when `fair > ask_1` and sells cross the bid when `fair < bid_1`; edge is future mid less the paid spread. Passive edge assumes a fill at the current best bid/ask, so it is useful as a quoting-value diagnostic, not a fill-rate backtest.

## Headline

`wall_mid` has a sparse but broad all-day structural signal. Its best aggregate horizon is 500: 45380 active observations, signed mid markout 3.944, hit rate 0.5069, cross edge 3.637 over 16312 crossing events, and passive edge 6.828.

The trailing `popular_mid` idea is not a short-horizon crossing fair: aggregate crossing edge is negative through horizon 100. It does produce strong product-specific horizon-500 anchors, with aggregate signed mid markout 9.816 and cross edge 4.459, so the usable interpretation is slow popular-price anchoring rather than immediate wall-following.

## Aggregate fair results

| fair | horizon | active_events | signed_mid_markout | hit_rate | cross_events | cross_edge | passive_events | passive_edge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| depth_vwap_mid | 1 | 47477 | 2.951 | 0.6146 | 14932 | 0.729 | 47477 | 5.847 |
| depth_vwap_mid | 5 | 47477 | 3.035 | 0.5533 | 14932 | 0.711 | 47477 | 5.931 |
| depth_vwap_mid | 20 | 47432 | 3.146 | 0.5301 | 14931 | 1.128 | 47432 | 6.042 |
| depth_vwap_mid | 100 | 47088 | 2.982 | 0.5117 | 14856 | 0.166 | 47088 | 5.878 |
| depth_vwap_mid | 500 | 44880 | 3.829 | 0.5067 | 14096 | 4.090 | 44880 | 6.724 |
| popular_mid | 1 | 1458087 | 0.040 | 0.4781 | 1414410 | -5.597 | 1458087 | 5.698 |
| popular_mid | 5 | 1457496 | 0.127 | 0.4909 | 1413837 | -5.513 | 1457496 | 5.785 |
| popular_mid | 20 | 1455283 | 0.368 | 0.4972 | 1411707 | -5.258 | 1455283 | 6.025 |
| popular_mid | 100 | 1443392 | 1.777 | 0.5025 | 1400146 | -3.797 | 1443392 | 7.435 |
| popular_mid | 500 | 1383823 | 9.816 | 0.5129 | 1342572 | 4.459 | 1383823 | 15.473 |
| wall_mid | 1 | 47995 | 2.929 | 0.6140 | 17252 | 0.725 | 47995 | 5.814 |
| wall_mid | 5 | 47995 | 3.010 | 0.5531 | 17252 | 0.646 | 47995 | 5.895 |
| wall_mid | 20 | 47950 | 3.132 | 0.5299 | 17251 | 0.993 | 47950 | 6.017 |
| wall_mid | 100 | 47600 | 2.985 | 0.5118 | 17167 | 0.713 | 47600 | 5.870 |
| wall_mid | 500 | 45380 | 3.944 | 0.5069 | 16312 | 3.637 | 45380 | 6.828 |

## Top robust candidates

Criteria: at least 100 active events, at least 25 events on each of the three days, positive signed markout on every day, and either positive crossing edge on every day or positive passive edge on every day.

| product | fair | horizon | active_events | signed_mid_markout | min_day_markout | cross_events | cross_edge | passive_events | passive_edge |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MICROCHIP_TRIANGLE | popular_mid | 500 | 27831 | 105.471 | 87.091 | 27385 | 102.433 | 27831 | 109.795 |
| MICROCHIP_RECTANGLE | popular_mid | 500 | 27779 | 60.536 | 1.478 | 27263 | 57.647 | 27779 | 64.480 |
| PEBBLES_XL | popular_mid | 500 | 27842 | 49.901 | 0.756 | 27359 | 42.874 | 27842 | 58.215 |
| SLEEP_POD_NYLON | popular_mid | 500 | 27748 | 35.731 | 4.986 | 27009 | 32.220 | 27748 | 40.013 |
| GALAXY_SOUNDS_DARK_MATTER | popular_mid | 500 | 27775 | 32.725 | 7.369 | 26805 | 27.442 | 27775 | 39.241 |
| PEBBLES_XL | wall_mid | 500 | 814 | 30.238 | 19.455 | 316 | 103.008 | 814 | 34.435 |
| PEBBLES_XL | depth_vwap_mid | 500 | 814 | 30.238 | 19.455 | 172 | 60.474 | 814 | 34.435 |
| MICROCHIP_SQUARE | popular_mid | 500 | 27834 | 25.395 | 1.922 | 27424 | 19.543 | 27834 | 31.258 |
| PEBBLES_S | popular_mid | 500 | 27798 | 24.843 | 10.823 | 27220 | 19.645 | 27798 | 30.622 |
| PEBBLES_XL | popular_mid | 100 | 29041 | 22.562 | 18.218 | 28545 | 14.545 | 29041 | 30.889 |
| TRANSLATOR_VOID_BLUE | popular_mid | 500 | 27762 | 22.232 | 9.756 | 26919 | 17.838 | 27762 | 26.992 |
| UV_VISOR_ORANGE | wall_mid | 500 | 941 | 19.884 | 16.700 | 332 | 14.562 | 941 | 23.273 |
| UV_VISOR_ORANGE | depth_vwap_mid | 500 | 941 | 19.884 | 16.700 | 317 | 12.161 | 941 | 23.273 |
| OXYGEN_SHAKE_EVENING_BREATH | depth_vwap_mid | 500 | 941 | 16.349 | 1.430 | 0 | NA | 941 | 19.359 |
| OXYGEN_SHAKE_EVENING_BREATH | wall_mid | 500 | 941 | 16.349 | 1.430 | 0 | NA | 941 | 19.359 |
| UV_VISOR_YELLOW | popular_mid | 500 | 27801 | 16.110 | 2.180 | 26825 | 9.271 | 27801 | 23.057 |
| ROBOT_LAUNDRY | popular_mid | 500 | 27775 | 14.233 | 2.181 | 27253 | 10.823 | 27775 | 17.816 |
| SNACKPACK_STRAWBERRY | depth_vwap_mid | 500 | 941 | 14.195 | 3.729 | 341 | 29.270 | 941 | 18.736 |
| SNACKPACK_STRAWBERRY | wall_mid | 500 | 941 | 14.195 | 3.729 | 351 | 28.407 | 941 | 18.736 |
| GALAXY_SOUNDS_SOLAR_FLAMES | popular_mid | 500 | 27772 | 14.177 | 8.994 | 26744 | 7.380 | 27772 | 21.225 |

## MM-style wall candidates only

| product | horizon | active_events | signed_mid_markout | min_day_markout | cross_edge | passive_edge |
|---|---:|---:|---:|---:|---:|---:|
| PEBBLES_XL | 500 | 814 | 30.238 | 19.455 | 103.008 | 34.435 |
| UV_VISOR_ORANGE | 500 | 941 | 19.884 | 16.700 | 14.562 | 23.273 |
| OXYGEN_SHAKE_EVENING_BREATH | 500 | 941 | 16.349 | 1.430 | NA | 19.359 |
| SNACKPACK_STRAWBERRY | 500 | 941 | 14.195 | 3.729 | 28.407 | 18.736 |
| SNACKPACK_PISTACHIO | 500 | 941 | 13.077 | 7.250 | -3.882 | 17.119 |
| PANEL_1X4 | 500 | 941 | 12.903 | 9.516 | 3.745 | 15.035 |
| SLEEP_POD_LAMB_WOOL | 500 | 941 | 12.463 | 0.113 | 25.912 | 14.841 |
| GALAXY_SOUNDS_PLANETARY_RINGS | 500 | 941 | 11.698 | 0.911 | -18.122 | 15.180 |
| SLEEP_POD_SUEDE | 500 | 941 | 10.510 | 1.200 | 51.005 | 13.054 |
| TRANSLATOR_VOID_BLUE | 500 | 941 | 10.166 | 5.043 | 19.961 | 12.600 |
| OXYGEN_SHAKE_MINT | 100 | 989 | 8.702 | 7.886 | -3.007 | 11.905 |
| ROBOT_MOPPING | 100 | 989 | 8.005 | 4.523 | 6.689 | 10.036 |
| TRANSLATOR_ECLIPSE_CHARCOAL | 500 | 941 | 7.980 | 2.032 | 10.045 | 10.195 |
| SNACKPACK_VANILLA | 500 | 941 | 7.438 | 1.331 | 17.708 | 11.730 |
| SLEEP_POD_NYLON | 100 | 989 | 7.431 | 0.735 | 13.807 | 9.614 |

## Strongest wall/dislocation microstructure

These are the products where the largest displayed wall most often moves the fair away from ordinary book mid.

| product | avg_spread | avg_book_depth | abs_wall_dev | nonzero_wall_dev_share | bid_wall_L1_share | ask_wall_L1_share | dominant_size | dominant_size_share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UV_VISOR_YELLOW | 13.910 | 99.135 | 0.374 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| GALAXY_SOUNDS_SOLAR_WINDS | 13.301 | 99.135 | 0.349 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| UV_VISOR_MAGENTA | 14.092 | 99.135 | 0.348 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| GALAXY_SOUNDS_SOLAR_FLAMES | 14.072 | 99.135 | 0.344 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| UV_VISOR_ORANGE | 13.284 | 99.135 | 0.343 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| GALAXY_SOUNDS_DARK_MATTER | 13.051 | 99.135 | 0.341 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| PEBBLES_L | 13.021 | 75.219 | 0.338 | 0.0284 | 0.0000 | 0.0000 | 11 | 0.0855 |
| UV_VISOR_RED | 14.039 | 99.135 | 0.332 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| OXYGEN_SHAKE_MINT | 12.594 | 99.135 | 0.328 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| OXYGEN_SHAKE_MORNING_BREATH | 12.783 | 99.135 | 0.324 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| GALAXY_SOUNDS_PLANETARY_RINGS | 13.690 | 99.135 | 0.320 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| PEBBLES_M | 13.121 | 75.219 | 0.319 | 0.0284 | 0.0000 | 0.0000 | 11 | 0.0855 |
| GALAXY_SOUNDS_BLACK_HOLES | 14.513 | 99.135 | 0.313 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| OXYGEN_SHAKE_GARLIC | 15.055 | 99.135 | 0.290 | 0.0332 | 0.0057 | 0.0057 | 25 | 0.0735 |
| PEBBLES_S | 11.552 | 75.219 | 0.286 | 0.0284 | 0.0000 | 0.0000 | 11 | 0.0855 |

## Explicit rejections

These had apparent aggregate signal but failed the three-day validation or the after-spread strategy requirement.

| product | fair | horizon | positive_days | signed_mid_markout | min_day_markout | cross_edge | passive_edge |
|---|---|---:|---:|---:|---:|---:|---:|
| ROBOT_DISHES | popular_mid | 500 | 2/3 | 37.941 | -8.933 | 34.922 | 41.588 |
| MICROCHIP_OVAL | popular_mid | 500 | 2/3 | 31.777 | -6.000 | 28.489 | 35.512 |
| OXYGEN_SHAKE_GARLIC | popular_mid | 500 | 2/3 | 25.341 | -3.909 | 18.943 | 32.856 |
| SNACKPACK_STRAWBERRY | popular_mid | 500 | 2/3 | 22.033 | -3.096 | 14.758 | 30.947 |
| SNACKPACK_VANILLA | popular_mid | 500 | 2/3 | 20.839 | -0.871 | 13.816 | 29.273 |
| SNACKPACK_PISTACHIO | popular_mid | 500 | 2/3 | 20.769 | -0.565 | 15.068 | 28.735 |
| TRANSLATOR_ASTRO_BLACK | popular_mid | 500 | 2/3 | 18.737 | -23.847 | 14.922 | 22.918 |
| PEBBLES_XL | wall_mid | 100 | 2/3 | 14.409 | -0.384 | 20.017 | 18.616 |
| PEBBLES_XL | depth_vwap_mid | 100 | 2/3 | 14.409 | -0.384 | -25.469 | 18.616 |
| UV_VISOR_RED | popular_mid | 500 | 2/3 | 14.298 | -28.102 | 7.724 | 21.317 |
| SNACKPACK_RASPBERRY | popular_mid | 500 | 2/3 | 14.243 | -7.741 | 6.862 | 22.661 |
| TRANSLATOR_GRAPHITE_MIST | popular_mid | 500 | 2/3 | 13.753 | -5.399 | 9.728 | 18.209 |

Strongest non-candidates by aggregate markout:

| product | fair | horizon | positive_days | active_events | signed_mid_markout | min_day_markout | robust_cross | robust_passive |
|---|---|---:|---:|---:|---:|---:|---|---|
| ROBOT_DISHES | popular_mid | 500 | 2/3 | 25773 | 37.941 | -8.933 | no | no |
| MICROCHIP_OVAL | popular_mid | 500 | 2/3 | 27790 | 31.777 | -6.000 | no | no |
| OXYGEN_SHAKE_GARLIC | popular_mid | 500 | 2/3 | 27819 | 25.341 | -3.909 | no | yes |
| SNACKPACK_STRAWBERRY | popular_mid | 500 | 2/3 | 27752 | 22.033 | -3.096 | no | yes |
| SNACKPACK_VANILLA | popular_mid | 500 | 2/3 | 27721 | 20.839 | -0.871 | no | yes |
| SNACKPACK_PISTACHIO | popular_mid | 500 | 2/3 | 27650 | 20.769 | -0.565 | no | yes |
| TRANSLATOR_ASTRO_BLACK | popular_mid | 500 | 2/3 | 27703 | 18.737 | -23.847 | no | no |
| PEBBLES_XL | wall_mid | 100 | 2/3 | 849 | 14.409 | -0.384 | yes | yes |
| PEBBLES_XL | depth_vwap_mid | 100 | 2/3 | 849 | 14.409 | -0.384 | no | yes |
| UV_VISOR_RED | popular_mid | 500 | 2/3 | 27810 | 14.298 | -28.102 | no | no |
| SNACKPACK_RASPBERRY | popular_mid | 500 | 2/3 | 27738 | 14.243 | -7.741 | no | yes |
| TRANSLATOR_GRAPHITE_MIST | popular_mid | 500 | 2/3 | 27760 | 13.753 | -5.399 | no | no |

## Files

- `16_wall_mid_product_summary.csv`: quote-size modes, top-of-book wall levels, max-volume price modes, spread/depth, and fair deviations by product/day.
- `16_wall_mid_markouts.csv`: product/day/fair/horizon predictive markouts and crossing/passive edge.
- `16_wall_mid_validation.csv`: three-day validation table used for candidate/rejection decisions.
- `16_wall_mid_fair_summary.csv`: aggregate fair/horizon results.
