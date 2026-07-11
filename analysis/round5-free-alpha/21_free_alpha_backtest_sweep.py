import csv
import os
import re
import subprocess
from collections import defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
STRATEGY = "strategies/round5/free_alpha_path_active_v1.py"

PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def run_case(entry_edge, exit_edge, limit):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["FREE_ALPHA_ENTRY_EDGE"] = str(entry_edge)
    env["FREE_ALPHA_EXIT_EDGE"] = str(exit_edge)
    env["FREE_ALPHA_LIMIT"] = str(limit)
    cmd = [
        "prosperity4btx",
        STRATEGY,
        "5",
        "--merge-pnl",
        "--no-progress",
        "--no-out",
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout[-4000:])

    rows = []
    summary = {}
    current_day = None
    for line in result.stdout.splitlines():
        m = DAY_RE.match(line)
        if m:
            current_day = int(m.group(1))
            continue
        m = SUMMARY_RE.match(line)
        if m:
            summary[int(m.group(1))] = parse_int(m.group(2))
            continue
        m = PRODUCT_RE.match(line)
        if m and current_day is not None and m.group(1) != "Total":
            rows.append(
                {
                    "entry_edge": entry_edge,
                    "exit_edge": exit_edge,
                    "limit": limit,
                    "day": current_day,
                    "product": m.group(1),
                    "pnl": parse_int(m.group(2)),
                }
            )
    return rows, summary


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    cases = []
    for limit in (3, 5, 10):
        for entry in (10, 20, 40, 80, 120, 200):
            cases.append((entry, 5, limit))

    all_rows = []
    summaries = []
    for entry, exit_edge, limit in cases:
        print("running entry=%s limit=%s" % (entry, limit))
        rows, summary = run_case(entry, exit_edge, limit)
        all_rows.extend(rows)
        summaries.append(
            {
                "entry_edge": entry,
                "exit_edge": exit_edge,
                "limit": limit,
                "day2": summary.get(2, 0),
                "day3": summary.get(3, 0),
                "day4": summary.get(4, 0),
                "total": sum(summary.values()),
                "min_day": min(summary.values()) if summary else 0,
            }
        )

    write_csv(
        os.path.join(OUT_DIR, "free_alpha_sweep_summary.csv"),
        ["entry_edge", "exit_edge", "limit", "day2", "day3", "day4", "total", "min_day"],
        summaries,
    )
    write_csv(
        os.path.join(OUT_DIR, "free_alpha_sweep_product_day.csv"),
        ["entry_edge", "exit_edge", "limit", "day", "product", "pnl"],
        all_rows,
    )

    # Product stability table for the default full-size case.
    selected = [r for r in all_rows if r["entry_edge"] == 20 and r["limit"] == 10]
    by_product = defaultdict(lambda: defaultdict(int))
    for row in selected:
        by_product[row["product"]][row["day"]] += row["pnl"]
    product_rows = []
    for product, days in sorted(by_product.items()):
        vals = [days.get(day, 0) for day in (2, 3, 4)]
        product_rows.append(
            {
                "product": product,
                "day2": vals[0],
                "day3": vals[1],
                "day4": vals[2],
                "total": sum(vals),
                "min_day": min(vals),
                "positive_days": sum(1 for value in vals if value > 0),
            }
        )
    product_rows.sort(key=lambda row: (row["positive_days"], row["min_day"], row["total"]), reverse=True)
    write_csv(
        os.path.join(OUT_DIR, "free_alpha_default_product_stability.csv"),
        ["product", "day2", "day3", "day4", "total", "min_day", "positive_days"],
        product_rows,
    )

    best = max(summaries, key=lambda row: row["total"])
    print("best total=%s entry=%s limit=%s days=%s/%s/%s" % (best["total"], best["entry_edge"], best["limit"], best["day2"], best["day3"], best["day4"]))


if __name__ == "__main__":
    main()
