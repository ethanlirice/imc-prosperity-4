import csv
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
STRATEGY = "strategies/round5/v11-mm-configurable.py"
BASE_TOTAL = 1349478
PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def csv_text(values):
    return ",".join(values)


def product_size_map(items):
    return ",".join("%s:%s" % (product, value) for product, value in items)


def run_case(case, match_mode=""):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    for key, value in case.get("env", {}).items():
        env[key] = value
    cmd = ["prosperity4btx", STRATEGY, "5", "--merge-pnl", "--no-progress", "--no-out"]
    if match_mode:
        cmd.extend(["--match-trades", match_mode])
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    base = {
        "case": case.get("case", ""),
        "kind": case.get("kind", ""),
        "product": case.get("product", ""),
        "param": case.get("param", ""),
        "match_mode": match_mode or "default",
    }
    if result.returncode != 0:
        row = dict(base)
        row.update({"day2": 0, "day3": 0, "day4": 0, "total": 0, "delta": -BASE_TOTAL, "min_day": 0, "status": "failed", "error": result.stdout[-1000:]})
        return row, []
    current_day = None
    summary = {}
    product_rows = []
    for line in result.stdout.splitlines():
        match = DAY_RE.match(line)
        if match:
            current_day = int(match.group(1))
            continue
        match = SUMMARY_RE.match(line)
        if match:
            summary[int(match.group(1))] = parse_int(match.group(2))
            continue
        match = PRODUCT_RE.match(line)
        if match and current_day is not None and match.group(1) != "Total":
            product_rows.append(
                {
                    "case": base["case"],
                    "kind": base["kind"],
                    "product_under_test": base["product"],
                    "param": base["param"],
                    "match_mode": base["match_mode"],
                    "day": current_day,
                    "product": match.group(1),
                    "pnl": parse_int(match.group(2)),
                }
            )
    total = sum(summary.values())
    row = dict(base)
    row.update(
        {
            "day2": summary.get(2, 0),
            "day3": summary.get(3, 0),
            "day4": summary.get(4, 0),
            "total": total,
            "delta": total - BASE_TOTAL,
            "min_day": min(summary.values()) if summary else 0,
            "status": "ok",
            "error": "",
        }
    )
    return row, product_rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
