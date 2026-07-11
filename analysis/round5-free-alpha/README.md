# Round 5 Free Alpha Probe

The supplied table appears to be a five-bucket fair path:

`fair_path = [base, base+d1, base+d2, base+d3, base+d4]`

`20_free_alpha_probe.py` compares that shape against actual Round 5 mid paths.
The path has real signal, but it is not safe as a broad active strategy.

Backtest results:

| strategy | result | note |
|---|---:|---|
| `free_alpha_path_active_v1.py`, entry 20 | +478,380 | broad rule; weak day 4 |
| same, entry 200 | +742,005 | day 4 only +23,686 |
| `base-strategy-free-alpha-selected-v1.py` | +822,226 | stable selected overlay |
| `base-strategy-free-alpha-selected-v2.py` | +823,611 | adds small stable names |
| `base-strategy-free-alpha-selected-v3.py` | +841,042 | adds per-product thresholds |
| `base-strategy-free-alpha-selected-v5.py` | +868,478 | standalone best current |

Selected free-alpha products in v5:

- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_SOLAR_FLAMES`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `PANEL_2X2`
- `PEBBLES_L`
- `SLEEP_POD_COTTON`
- `SLEEP_POD_LAMB_WOOL`
- `SNACKPACK_PISTACHIO`
- `SNACKPACK_RASPBERRY`
- `SNACKPACK_VANILLA`
- `TRANSLATOR_GRAPHITE_MIST`
- `UV_VISOR_MAGENTA`
- `UV_VISOR_YELLOW`

Outputs:

- `free_alpha_shape_probe.csv`
- `free_alpha_sweep_summary.csv`
- `free_alpha_sweep_product_day.csv`
- `free_alpha_default_product_stability.csv`
