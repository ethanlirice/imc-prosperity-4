# Round 5 NN Research

Research scripts here treat neural nets and tree models as alpha microscopes,
then emit deterministic candidate events for execution-aware validation.

## Outputs

- `41_*`: visible price suffix/modulo and timestamp/tick-index bucket scans.
- `42_*`: product-time, group residual/rank, microstructure, volatility,
  extrema, and path-motif event scans.
- `43_*`: same-group cross-product pressure / event-conditioned lead-lag scan.
- `44_*`: sampled ExtraTrees and compact GRU feature/target rankings.

Full `41_suffix_event_summary.csv`, `41_time_bucket_summary.csv`, and the
largest full `42_*` CSVs were removed after top-ranked CSVs were written because
local disk space was critically low. The top-ranked CSVs are the intended
research artifacts for this pass.

## Findings

- The specific `UV_VISOR_RED` visible price suffix `420` claim did not survive
  the strict all-day count/stability gate in this scan; `41_uv_red_420_detail.csv`
  is empty.
- Strong raw product-time/path rows exist, especially `PEBBLES_XL`,
  `PEBBLES_XS`, `GALAXY_SOUNDS_SOLAR_WINDS`, and `MICROCHIP_SQUARE`, but these
  are high leakage/overfit risk because they resemble hidden-path timing.
- More portable-looking deterministic leads:
  - `UV_VISOR_YELLOW` high group residual -> short, h500/h1000.
  - `PANEL_1X4` low group residual z -> long, h1000.
  - `MICROCHIP_OVAL` short after `MICROCHIP_SQUARE`/`MICROCHIP_TRIANGLE`
    pressure events.
  - `OXYGEN_SHAKE_GARLIC` long after `OXYGEN_SHAKE_CHOCOLATE` ret100 low.
  - `SLEEP_POD_POLYESTER` long after `SLEEP_POD_COTTON` ret100 high.
- Tree/GRU rankings independently highlighted `UV_VISOR_MAGENTA` long h1000,
  `OXYGEN_SHAKE_CHOCOLATE` long h1000, `MICROCHIP_SQUARE` short h1000, and
  `SLEEP_POD_NYLON` long h500. Treat these as candidate generators, not direct
  strategy rules.

## Strategy Test

Tested `strategies/round5/nn-cross-microchip-oval-v12-candidate.py`, a v11 copy
with one active cross-pressure sleeve:
`MICROCHIP_SQUARE` ret100 <= -259.5 -> short `MICROCHIP_OVAL`, hold 1000.

Result: default `--merge-pnl` tied v11 exactly at `+1,349,478`, so it was not
promoted. Diagnostics improved to `+868,618` for both `--match-trades none` and
`--match-trades worse`, so this is worth revisiting as a diagnostic-mode sleeve
or passive skew, but not as a primary submission change.

## v2 RNN/Stochastic Lab

`45_rnn_stochastic_lab.py` adds:

- Product-sequence GRU over all 50 products with product/group embeddings,
  cross-product context, and executable long/short targets.
- OU/local drift-vol/hitting diagnostics.
- Synthetic injection tests for suffix, time-bucket, and lead-lag mechanics.

Top stable GRU targets across d2->d3, d3->d4, and d23->d4:
`MICROCHIP_SQUARE` short h1000, `GALAXY_SOUNDS_SOLAR_WINDS` short h1000,
`PANEL_2X4` long h1000, `MICROCHIP_OVAL` short h1000/h500,
`SNACKPACK_CHOCOLATE` short h1000, `OXYGEN_SHAKE_GARLIC` long h1000, and
`UV_VISOR_RED` long h1000.

The provided NN reference files are incomplete and do not compile, so the local
implementation replicated their usable ideas instead of importing them.
