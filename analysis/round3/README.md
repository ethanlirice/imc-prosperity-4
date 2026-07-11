# Round 3 Analysis

Round 3 analysis focused on reverse-engineering product behavior and building
the options/underlying model used in the final strategy.

Key highlights:

- `round3_00_data_foundation.ipynb`: data loading and baseline product behavior.
- `round3_01_product_reverse_engineering.ipynb`: product structure and candidate
  fair-value signals.
- `round3_02_hydrogel_four_bot_inference.ipynb`: Hydrogel trader/bot behavior.
- `round3_03_options_surface_and_bot_behavior.ipynb`: option surface and
  execution behavior.
- `round3_04_hidden_patterns_opportunity_map.ipynb`: hidden-pattern opportunity
  scan.
- `round3_05_forensic_bot_edges.ipynb`: deeper forensic checks on bot edges.

The main strategy outcome was the move toward online fair-value anchors and
option-surface execution logic, reflected in `archive/round3/traderfinal.py`.
