from __future__ import annotations

import csv
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, List


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "strategies/round5/nn-cross-mm-ret50-v13-candidate.py"
TRADER = ROOT / "trader.py"
OUT = ROOT / "neural-networks/round5-nn-research-initial/47_nn_mm_side_gate_summary.csv"
VARIANT_DIR = ROOT / "strategies/round5/nn-mm-side-sweep-generated"


def add_to_set(text: str, set_name: str, product: str) -> str:
    pattern = re.compile(rf"({set_name} = \{{\n)(.*?)(\n\}})", re.S)
    match = pattern.search(text)
    if match is None:
        raise RuntimeError(f"missing set {set_name}")
    body = match.group(2)
    line = f'    "{product}",'
    if line in body:
        return text
    return text[: match.start()] + match.group(1) + body + "\n" + line + match.group(3) + text[match.end() :]


def remove_from_set(text: str, set_name: str, product: str) -> str:
    pattern = re.compile(rf"({set_name} = \{{\n)(.*?)(\n\}})", re.S)
    match = pattern.search(text)
    if match is None:
        raise RuntimeError(f"missing set {set_name}")
    body = re.sub(rf'\n    "{re.escape(product)}",', "", match.group(2))
    return text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]


def add_mm_product(text: str, product: str) -> str:
    marker = 'MM_PRODUCTS.update({"PEBBLES_L", "SNACKPACK_CHOCOLATE", "ROBOT_DISHES"})'
    if f'MM_PRODUCTS.add("{product}")' in text:
        return text
    return text.replace(marker, marker + f'\nMM_PRODUCTS.add("{product}")')


def set_size(text: str, product: str, size: int) -> str:
    if f'    "{product}": ' in text:
        return re.sub(rf'    "{re.escape(product)}": [0-9]+,', f'    "{product}": {size},', text)
    marker = "MM_SIZE_BY_PRODUCT = {\n"
    return text.replace(marker, marker + f'    "{product}": {size},\n')


def long_only(text: str, product: str) -> str:
    text = remove_from_set(text, "MM_BID_OFF_PRODUCTS", product)
    return add_to_set(text, "MM_ASK_OFF_PRODUCTS", product)


def short_only(text: str, product: str) -> str:
    text = remove_from_set(text, "MM_ASK_OFF_PRODUCTS", product)
    return add_to_set(text, "MM_BID_OFF_PRODUCTS", product)


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


def build_variant(name: str, edit: Callable[[str], str]) -> Path:
    text = edit(BASE.read_text())
    text = text.replace(
        "# Candidate v12 research: v11 plus owned-product passive MM coexistence and MICROCHIP_CIRCLE imbalance filter.",
        f"# Generated NN-directed MM side-gate research variant: {name}.",
    )
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    path = VARIANT_DIR / f"{name}.py"
    path.write_text(text)
    return path


CANDIDATES: List[tuple[str, Callable[[str], str]]] = [
    ("microchip_square_short_only", lambda t: short_only(t, "MICROCHIP_SQUARE")),
    ("pebbles_s_short_only", lambda t: short_only(t, "PEBBLES_S")),
    ("panel_1x4_short_only", lambda t: short_only(t, "PANEL_1X4")),
    ("oxygen_chocolate_long_only", lambda t: long_only(t, "OXYGEN_SHAKE_CHOCOLATE")),
    ("oxygen_evening_long_only", lambda t: long_only(t, "OXYGEN_SHAKE_EVENING_BREATH")),
    ("snack_chocolate_short_only", lambda t: short_only(t, "SNACKPACK_CHOCOLATE")),
    ("panel_2x4_long_size2", lambda t: set_size(t, "PANEL_2X4", 2)),
    ("panel_2x4_long_size5", lambda t: set_size(t, "PANEL_2X4", 5)),
    ("oxygen_garlic_long_size2", lambda t: set_size(t, "OXYGEN_SHAKE_GARLIC", 2)),
    ("oxygen_garlic_long_size5", lambda t: set_size(t, "OXYGEN_SHAKE_GARLIC", 5)),
    ("add_pebbles_m_long_only", lambda t: long_only(add_mm_product(t, "PEBBLES_M"), "PEBBLES_M")),
    ("add_translator_space_gray_short_only", lambda t: short_only(add_mm_product(t, "TRANSLATOR_SPACE_GRAY"), "TRANSLATOR_SPACE_GRAY")),
]


def main() -> None:
    original = TRADER.read_text()
    rows: List[Dict[str, object]] = []
    try:
        base_scores = run_backtest(BASE)
        rows.append({"name": "base_v13", **base_scores})
        for name, edit in CANDIDATES:
            path = build_variant(name, edit)
            scores = run_backtest(path)
            rows.append({"name": name, **scores})
            print(f"{name}: {scores['total']:,} ({scores['day2']:,}/{scores['day3']:,}/{scores['day4']:,})", flush=True)
    finally:
        TRADER.write_text(original)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "day2", "day3", "day4", "total"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
