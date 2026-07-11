# Workspace Guide

This branch is organized as a cleaned research workspace.

## How To Read It

Start with the round folders in `strategies/` for Rounds 1-5. Root `trader.py`
remains the active Round 5 submission. Each round keeps the final model and enough
nearby variants to show what was tested.

Use `analysis/` for the research trail: notebooks, scanners, scripts, and small
summary artifacts that explain why a strategy changed. Raw competition data and
large backtest outputs are excluded from the GitHub version to keep the repo
lightweight.

Use `manual-challenge/` for the separate manual challenge notebooks, optimizers,
and final recommendations.

## What Was Removed Or Left Untracked

This branch avoids local machine files, agent settings, caches, huge backtest
logs, and copied external repositories. The intent is to preserve my project
workflow while keeping the GitHub view navigable.

## Results Policy

Published numbers should be either:

- documented directly in code comments or analysis notes,
- reproduced by the local backtester,
- or confirmed manually from my competition records.

Unconfirmed round totals are marked as needing confirmation instead of being
filled with guesses.
