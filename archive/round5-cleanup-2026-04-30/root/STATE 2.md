# STATE.md
Read this second, after AGENTS.md. Keep under 60 lines. Delete old content.

---

## Status
Active round: **Round 5**.

## Current Best
Root `trader.py` is promoted to
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v11.py`.
`strategies/round5/current.py` remains the prior v7 baseline.

Primary evaluation:
`prosperity4btx trader.py 5 --merge-pnl`

Result: **+1,349,478** with day split **+440,342 / +401,360 / +507,776**.
Line count: **480**.

Diagnostics:
- `--match-trades none`: **+832,689**, day split **+240,644 / +232,934 / +359,111**
- `--match-trades worse`: **+832,689**, day split **+240,644 / +232,934 / +359,111**

Saved versions:
- Prior root before v11: `strategies/round5/trader_v8.py`
- Current promoted copy: `strategies/round5/trader_v9.py`

## Current Findings
Baseline v7 was **+1,196,202**. Validated improvements:
- MM refinement v8: quote size map plus `ROBOT_LAUNDRY` touch-MM coexistence,
  **+1,234,316**.
- Re-anchored hidden-path v10 for `ROBOT_DISHES`, `OXYGEN_SHAKE_MINT`,
  `SNACKPACK_STRAWBERRY`, `SNACKPACK_CHOCOLATE`, **+1,323,819**.
- v11 adds `PEBBLES_L` flat bucket-0 re-anchor replacement, **+1,349,478**.

The `PEBBLES_L` result came from combining the original hidden-path proxy with
Phase D's anchor-vs-shape finding. Full Tier 2 flat-anchor bundle regressed to
**+1,207,514**, so only `PEBBLES_L` was promoted. Best tested `PEBBLES_L`
flat edge was 80.

Rejected recently:
- Shared `EVENT_TARGETS` hardcoded schedule: **+877,992**.
- Naive/broad re-anchor additions: `PEBBLES_S`, `UV_VISOR_ORANGE`,
  `SLEEP_POD_NYLON`, `PANEL_4X4`, `OXYGEN_SHAKE_EVENING_BREATH`, `PANEL_1X2`.
- Rolling TLS/rolling-beta pair-fair tests: best active **+1,408**, best
  passive **+2,146**, below promotion bar.

## Next Step
Continue from v11. Highest-value next work:
1. Tune current re-anchor overlays one product at a time, especially exit edge,
   anchor update rule, and side gating.
2. Test owned-product replacements, not additions, for `MICROCHIP_SQUARE`,
   `UV_VISOR_RED`, `SLEEP_POD_LAMB_WOOL`, `SNACKPACK_RASPBERRY`, and
   `UV_VISOR_MAGENTA`.
3. Keep broad neural-net/black-box ideas as hypotheses only; require integrated
   `prosperity4btx trader.py 5 --merge-pnl` improvement before promotion.
