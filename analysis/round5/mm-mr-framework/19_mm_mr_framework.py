import csv
import os
import re
import subprocess
from collections import defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)

VARIANTS = [
    ("baseline", "strategies/round5/base-strategy.py"),
    ("simple_mr_skew_all50", "strategies/round5/simple_mm_mr_all50_v1.py"),
    ("pure_inside_all50", "strategies/round5/simple_mm_all50_inside_v2.py"),
    ("pure_touch_all50", "strategies/round5/simple_mm_all50_touch_v3.py"),
    ("base_touch_selected", "strategies/round5/base-strategy-touch-mm-v1.py"),
    ("base_touch_target_select", "strategies/round5/base-strategy-touch-mm-target-select-v2.py"),
    ("base_touch_target_select_no_space", "strategies/round5/base-strategy-touch-mm-target-select-v3.py"),
]

PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def run_variant(name, path):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [
        "prosperity4btx",
        path,
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
        raise RuntimeError("%s failed:\n%s" % (name, result.stdout[-4000:]))

    rows = []
    summary = {}
    current_day = None
    for line in result.stdout.splitlines():
        day_match = DAY_RE.match(line)
        if day_match:
            current_day = int(day_match.group(1))
            continue
        summary_match = SUMMARY_RE.match(line)
        if summary_match:
            summary[int(summary_match.group(1))] = parse_int(summary_match.group(2))
            continue
        product_match = PRODUCT_RE.match(line)
        if product_match and current_day is not None and product_match.group(1) != "Total":
            rows.append(
                {
                    "variant": name,
                    "day": current_day,
                    "product": product_match.group(1),
                    "pnl": parse_int(product_match.group(2)),
                }
            )
    if not summary:
        by_day = defaultdict(int)
        for row in rows:
            by_day[row["day"]] += row["pnl"]
        summary = dict(by_day)
    return rows, summary


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    all_rows = []
    summaries = []
    product_totals = defaultdict(lambda: defaultdict(int))

    for name, path in VARIANTS:
        print("running %s" % name)
        rows, summary = run_variant(name, path)
        all_rows.extend(rows)
        total = sum(summary.values())
        summaries.append(
            {
                "variant": name,
                "day2": summary.get(2, 0),
                "day3": summary.get(3, 0),
                "day4": summary.get(4, 0),
                "total": total,
            }
        )
        for row in rows:
            product_totals[row["product"]][name] += row["pnl"]

    write_csv(
        os.path.join(OUT_DIR, "variant_product_day_pnl.csv"),
        ["variant", "day", "product", "pnl"],
        all_rows,
    )
    write_csv(
        os.path.join(OUT_DIR, "variant_summary.csv"),
        ["variant", "day2", "day3", "day4", "total"],
        summaries,
    )

    matrix_rows = []
    variants = [name for name, _ in VARIANTS]
    for product in sorted(product_totals.keys()):
        row = {"product": product}
        for variant in variants:
            row[variant] = product_totals[product].get(variant, 0)
        row["touch_minus_inside"] = row.get("pure_touch_all50", 0) - row.get("pure_inside_all50", 0)
        row["v3_minus_baseline"] = row.get("base_touch_target_select_no_space", 0) - row.get("baseline", 0)
        matrix_rows.append(row)
    write_csv(
        os.path.join(OUT_DIR, "product_variant_totals.csv"),
        ["product"] + variants + ["touch_minus_inside", "v3_minus_baseline"],
        matrix_rows,
    )

    best = max(summaries, key=lambda row: row["total"])
    print("best=%s total=%s days=%s/%s/%s" % (best["variant"], best["total"], best["day2"], best["day3"], best["day4"]))


if __name__ == "__main__":
    main()
