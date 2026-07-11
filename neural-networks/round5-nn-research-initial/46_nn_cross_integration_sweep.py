from __future__ import annotations

import csv
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "strategies/round5/nn-cross-microchip-oval-v12-candidate.py"
TRADER = ROOT / "trader.py"
OUT = ROOT / "analysis/round5-nn-research/46_nn_cross_integration_summary.csv"
VARIANT_DIR = ROOT / "strategies/round5/nn-cross-sweep-generated"


EVENTS: List[Dict[str, object]] = [
    {
        "name": "oxygen_chocolate_ret100_low_garlic_long_h1000",
        "source": "OXYGEN_SHAKE_CHOCOLATE",
        "target": "OXYGEN_SHAKE_GARLIC",
        "lookback": 100,
        "trigger": "low",
        "threshold": -150.0,
        "direction": 1,
        "hold": 1000,
    },
    {
        "name": "galaxy_dark_ret100_high_black_holes_long_h1000",
        "source": "GALAXY_SOUNDS_DARK_MATTER",
        "target": "GALAXY_SOUNDS_BLACK_HOLES",
        "lookback": 100,
        "trigger": "high",
        "threshold": 171.5,
        "direction": 1,
        "hold": 1000,
    },
    {
        "name": "galaxy_rings_ret100_low_black_holes_long_h1000",
        "source": "GALAXY_SOUNDS_PLANETARY_RINGS",
        "target": "GALAXY_SOUNDS_BLACK_HOLES",
        "lookback": 100,
        "trigger": "low",
        "threshold": -142.0,
        "direction": 1,
        "hold": 1000,
    },
    {
        "name": "sleep_cotton_ret100_high_polyester_long_h1000",
        "source": "SLEEP_POD_COTTON",
        "target": "SLEEP_POD_POLYESTER",
        "lookback": 100,
        "trigger": "high",
        "threshold": 202.5,
        "direction": 1,
        "hold": 1000,
    },
    {
        "name": "microchip_square_ret50_low_oval_short_h1000",
        "source": "MICROCHIP_SQUARE",
        "target": "MICROCHIP_OVAL",
        "lookback": 50,
        "trigger": "low",
        "threshold": -180.0,
        "direction": -1,
        "hold": 1000,
    },
    {
        "name": "microchip_rectangle_ret100_low_oval_short_h1000",
        "source": "MICROCHIP_RECTANGLE",
        "target": "MICROCHIP_OVAL",
        "lookback": 100,
        "trigger": "low",
        "threshold": -215.0,
        "direction": -1,
        "hold": 1000,
    },
    {
        "name": "robot_mopping_ret50_high_ironing_short_h1000",
        "source": "ROBOT_MOPPING",
        "target": "ROBOT_IRONING",
        "lookback": 50,
        "trigger": "high",
        "threshold": 131.0,
        "direction": -1,
        "hold": 1000,
    },
    {
        "name": "sleep_cotton_ret100_low_suede_long_h1000",
        "source": "SLEEP_POD_COTTON",
        "target": "SLEEP_POD_SUEDE",
        "lookback": 100,
        "trigger": "low",
        "threshold": -148.0,
        "direction": 1,
        "hold": 1000,
    },
    {
        "name": "galaxy_black_holes_ret100_high_flames_short_h1000",
        "source": "GALAXY_SOUNDS_BLACK_HOLES",
        "target": "GALAXY_SOUNDS_SOLAR_FLAMES",
        "lookback": 100,
        "trigger": "high",
        "threshold": 204.0,
        "direction": -1,
        "hold": 1000,
    },
]


BUNDLES: List[Dict[str, object]] = [
    {"name": "bundle_top3_distinct", "events": [0, 1, 4]},
    {"name": "bundle_oxygen_galaxy_microchip_sleep", "events": [0, 1, 4, 7]},
    {"name": "bundle_all_non_free_alpha_targets", "events": [0, 1, 2, 4, 5, 6, 7]},
]


SPEC_RE = re.compile(r"NN_CROSS_SPECS = \[.*?\]\nMM_BID_OFF_PRODUCTS =", re.S)
METHOD_OLD = """        if position != 0 or move > float(spec[\"threshold\"]):
            return []
        order = self.entry_order(state, target, int(spec[\"direction\"]))
"""
METHOD_NEW = """        threshold = float(spec[\"threshold\"])
        trigger = str(spec.get(\"trigger\", \"low\"))
        hit = move <= threshold if trigger == \"low\" else move >= threshold
        if position != 0 or not hit:
            return []
        order = self.entry_order(state, target, int(spec[\"direction\"]))
"""


def spec_block(specs: Iterable[Dict[str, object]]) -> str:
    lines = ["NN_CROSS_SPECS = ["]
    for spec in specs:
        lines.append("    {")
        for key in ("source", "target", "lookback", "trigger", "threshold", "direction", "hold"):
            value = spec[key]
            if isinstance(value, str):
                lines.append(f'        "{key}": "{value}",')
            else:
                lines.append(f'        "{key}": {value},')
        lines.append("    },")
    lines.append("]")
    lines.append("MM_BID_OFF_PRODUCTS =")
    return "\n".join(lines)


def build_variant(name: str, specs: List[Dict[str, object]]) -> Path:
    text = BASE.read_text()
    text = SPEC_RE.sub(spec_block(specs), text)
    if METHOD_OLD not in text:
        raise RuntimeError("nn_cross_orders trigger block did not match template")
    text = text.replace(METHOD_OLD, METHOD_NEW)
    text = text.replace(
        "# Candidate v12 research: v11 plus one NN-discovered cross-pressure sleeve.",
        f"# Generated NN cross-pressure research variant: {name}.",
    )
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    path = VARIANT_DIR / f"{name}.py"
    path.write_text(text)
    return path


def parse_profit(output: str) -> Dict[str, int]:
    days = {int(day): int(value.replace(",", "")) for day, value in re.findall(r"Round 5 day ([234]): ([-0-9,]+)", output)}
    totals = [int(value.replace(",", "")) for value in re.findall(r"Total profit: ([-0-9,]+)", output)]
    if not totals or any(day not in days for day in (2, 3, 4)):
        raise RuntimeError("could not parse prosperity4btx output")
    return {"day2": days[2], "day3": days[3], "day4": days[4], "total": totals[-1]}


def run_backtest(path: Path) -> Dict[str, int]:
    shutil.copyfile(path, TRADER)
    proc = subprocess.run(
        ["prosperity4btx", "trader.py", "5", "--merge-pnl", "--no-progress", "--no-out"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return parse_profit(proc.stdout)


def main() -> None:
    base_text = TRADER.read_text()
    rows: List[Dict[str, object]] = []
    try:
        base_scores = run_backtest(BASE)
        rows.append({"name": "base_nn_microchip_oval_v12", "spec_count": 1, **base_scores})
        candidates: List[tuple[str, List[Dict[str, object]]]] = [(str(event["name"]), [event]) for event in EVENTS]
        for bundle in BUNDLES:
            specs = [EVENTS[int(idx)] for idx in bundle["events"]]  # type: ignore[index]
            candidates.append((str(bundle["name"]), specs))
        for name, specs in candidates:
            path = build_variant(name, specs)
            scores = run_backtest(path)
            rows.append({"name": name, "spec_count": len(specs), **scores})
            print(f"{name}: {scores['total']:,} ({scores['day2']:,}/{scores['day3']:,}/{scores['day4']:,})", flush=True)
    finally:
        TRADER.write_text(base_text)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "spec_count", "day2", "day3", "day4", "total"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
