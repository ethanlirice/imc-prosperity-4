# Round 4 Analysis

Round 4 analysis extended the Round 3 options framework and focused on informed
trader behavior, mark taxonomy, and validation of option/underlying signals.

Key highlights:

- `candidate_ranking.py`: ranks tested candidates and strategy changes.
- `informed_trader_analysis.py`: analyzes trader/mark behavior and follow/fade
  opportunities.
- `executable_mark14_edge.py` and `mark14_pre_event_execution.py`: checks whether
  Mark 14 signals were executable after spread and timing.
- `v314159_validation.py`: validation script for a major Round 4 strategy
  candidate.
- `mark_taxonomy/`: compact per-mark summaries and supporting scripts for
  identifying useful/inert/adverse trader flows.
- `mark14/` and `mark67/`: targeted probes around specific marks.

The main strategy outcome was the layered Round 4 model in
`archive/round4/final.py`: OU fair values, option pricing, IV regime detection,
deep-ITM handling, and informed-flow adjustments.
