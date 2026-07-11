# Phase 3 — v1 PnL attribution

Log: `backtests/2026-04-28_21-35-41.log`

## Layer totals (all days)

- **mm**: 103,310
- **mr**: 10,286
- **stat**: -34,083
- **grand total**: 79,513

## Per-day totals (sanity-check vs backtester)
- day 2: -31,391
- day 3: 35,924
- day 4: 74,980

## Per pair (legs aggregated, includes other layers if leg is shared)

| pair                                         |   leg_a_pnl |   leg_b_pnl |   pair_total |
|:---------------------------------------------|------------:|------------:|-------------:|
| SNACKPACK_CHOCOLATE / SNACKPACK_PISTACHIO    |       -7302 |      -16892 |       -24194 |
| OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC |         797 |       -5622 |        -4826 |
| SNACKPACK_PISTACHIO / SNACKPACK_RASPBERRY    |      -16892 |       -5063 |       -21955 |

## Per product (sorted by total PnL ascending)

| product                       |     mm |    mr |   stat |   total |
|:------------------------------|-------:|------:|-------:|--------:|
| PEBBLES_XL                    | -20802 |     0 |      0 |  -20802 |
| SNACKPACK_PISTACHIO           |      0 |     0 | -16892 |  -16892 |
| PANEL_2X4                     | -15112 |     0 |      0 |  -15112 |
| PANEL_1X2                     | -13470 |     0 |      0 |  -13470 |
| ROBOT_VACUUMING               | -21392 |  9466 |      0 |  -11926 |
| PANEL_4X4                     | -10762 |     0 |      0 |  -10762 |
| TRANSLATOR_SPACE_GRAY         | -10716 |     0 |      0 |  -10716 |
| MICROCHIP_SQUARE              |  -9385 |     0 |      0 |   -9385 |
| PEBBLES_XS                    |  -8886 |     0 |      0 |   -8886 |
| PANEL_2X2                     |  -8886 |     0 |      0 |   -8886 |
| GALAXY_SOUNDS_SOLAR_WINDS     |  -8652 |     0 |      0 |   -8652 |
| SNACKPACK_CHOCOLATE           |      0 |     0 |  -7302 |   -7302 |
| ROBOT_MOPPING                 |  -6556 |     0 |      0 |   -6556 |
| OXYGEN_SHAKE_GARLIC           |      0 |     0 |  -5622 |   -5622 |
| UV_VISOR_RED                  |  -5601 |     0 |      0 |   -5601 |
| SNACKPACK_RASPBERRY           |      0 |     0 |  -5063 |   -5063 |
| UV_VISOR_YELLOW               |  -4389 |     0 |      0 |   -4389 |
| SLEEP_POD_NYLON               |  -3664 |     0 |      0 |   -3664 |
| GALAXY_SOUNDS_BLACK_HOLES     |  -2806 |     0 |      0 |   -2806 |
| TRANSLATOR_ECLIPSE_CHARCOAL   |  -1392 |     0 |      0 |   -1392 |
| UV_VISOR_AMBER                |   -836 |     0 |      0 |    -836 |
| PEBBLES_M                     |   -124 |     0 |      0 |    -124 |
| MICROCHIP_RECTANGLE           |     34 |     0 |      0 |      34 |
| SLEEP_POD_SUEDE               |    184 |     0 |      0 |     184 |
| SNACKPACK_STRAWBERRY          |    450 |     0 |      0 |     450 |
| ROBOT_LAUNDRY                 |   2798 | -2192 |      0 |     606 |
| OXYGEN_SHAKE_CHOCOLATE        |      0 |     0 |    797 |     797 |
| ROBOT_DISHES                  |  11320 | -9677 |      0 |    1643 |
| TRANSLATOR_VOID_BLUE          |   1958 |     0 |      0 |    1958 |
| UV_VISOR_MAGENTA              |   2384 |     0 |      0 |    2384 |
| SLEEP_POD_LAMB_WOOL           |   2628 |     0 |      0 |    2628 |
| SLEEP_POD_POLYESTER           |   3010 |     0 |      0 |    3010 |
| PANEL_1X4                     |   4101 |     0 |      0 |    4101 |
| ROBOT_IRONING                 |   5029 |     0 |      0 |    5029 |
| OXYGEN_SHAKE_MINT             |   5330 |     0 |      0 |    5330 |
| SNACKPACK_VANILLA             |   5661 |     0 |      0 |    5661 |
| GALAXY_SOUNDS_SOLAR_FLAMES    |   8012 |     0 |      0 |    8012 |
| TRANSLATOR_ASTRO_BLACK        |   8946 |     0 |      0 |    8946 |
| SLEEP_POD_COTTON              |   9166 |     0 |      0 |    9166 |
| OXYGEN_SHAKE_EVENING_BREATH   |   9767 |     0 |      0 |    9767 |
| PEBBLES_L                     |  12243 |     0 |      0 |   12243 |
| GALAXY_SOUNDS_DARK_MATTER     |  12450 |     0 |      0 |   12450 |
| MICROCHIP_OVAL                |     -1 | 12690 |      0 |   12688 |
| MICROCHIP_CIRCLE              |  13499 |     0 |      0 |   13499 |
| OXYGEN_SHAKE_MORNING_BREATH   |  16733 |     0 |      0 |   16733 |
| PEBBLES_S                     |  16790 |     0 |      0 |   16790 |
| MICROCHIP_TRIANGLE            |  16837 |     0 |      0 |   16837 |
| TRANSLATOR_GRAPHITE_MIST      |  18036 |     0 |      0 |   18036 |
| UV_VISOR_ORANGE               |  32115 |     0 |      0 |   32115 |
| GALAXY_SOUNDS_PLANETARY_RINGS |  37260 |     0 |      0 |   37260 |