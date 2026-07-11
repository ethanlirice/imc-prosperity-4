import csv
import os
import re
import subprocess


STRATEGY = "strategies/round5/v10-tls-configurable.py"
OUT = "analysis/round5-tls/tls_integration_summary.csv"
BASE = 1323819

CASES = [
    ("oval_triangle", "oval_triangle"),
    ("triangle_square", "triangle_square"),
    ("laundry_ironing", "laundry_ironing"),
    ("strawberry_chocolate", "strawberry_chocolate"),
    ("dishes_laundry", "dishes_laundry"),
    ("nylon_lamb", "nylon_lamb"),
    ("vacuum_mopping_tls", "vacuum_mopping_tls"),
    ("circle_square_tls", "circle_square_tls"),
    ("oval_triangle__nylon_lamb", "oval_triangle,nylon_lamb"),
    ("oval_triangle__circle_square_tls", "oval_triangle,circle_square_tls"),
    ("top_clean3", "oval_triangle,nylon_lamb,circle_square_tls"),
]

SUMMARY_RE = re.compile(r"Round 5 day (\d+):\s+(-?[\d,]+)")
TOTAL_RE = re.compile(r"Total profit:\s+(-?[\d,]+)")


def parse(text):
    days = {}
    total = None
    for line in text.splitlines():
        m = SUMMARY_RE.search(line)
        if m:
            days[int(m.group(1))] = int(m.group(2).replace(",", ""))
        m = TOTAL_RE.search(line)
        if m:
            total = int(m.group(1).replace(",", ""))
    return total, days


def run(name, cases):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["TLS_CASES"] = cases
    result = subprocess.run(
        ["prosperity4btx", STRATEGY, "5", "--merge-pnl", "--no-progress", "--no-out"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=True,
    )
    total, days = parse(result.stdout)
    return {
        "case": name,
        "tls_cases": cases,
        "total": total,
        "delta": total - BASE,
        "day2": days.get(2, 0),
        "day3": days.get(3, 0),
        "day4": days.get(4, 0),
    }


def main():
    rows = []
    for name, cases in CASES:
        print("running", name, cases, flush=True)
        row = run(name, cases)
        rows.append(row)
        print(row, flush=True)
        with open(OUT, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["case", "tls_cases", "total", "delta", "day2", "day3", "day4"])
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
