from importlib.machinery import SourceFileLoader
import csv
import os
import subprocess


BASE = 1323819
STRATEGY = "strategies/round5/v10-tls-configurable.py"
OUT = "analysis/round5/tls-pair-spreads/tls_passive_summary.csv"
CASES = [
    ("oval_triangle", "oval_triangle"),
    ("circle_square_tls", "circle_square_tls"),
    ("nylon_lamb", "nylon_lamb"),
    ("vacuum_mopping_tls", "vacuum_mopping_tls"),
    ("strawberry_chocolate", "strawberry_chocolate"),
    ("oval_circle", "oval_triangle,circle_square_tls"),
    ("clean3", "oval_triangle,circle_square_tls,nylon_lamb"),
]
SIZES = [1, 2, 5, 10]

parser = SourceFileLoader("tls_sweep", "analysis/round5/tls-pair-spreads/39_tls_integration_sweep.py").load_module()


def run(name, cases, size):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["TLS_CASES"] = cases
    env["TLS_MODE"] = "passive"
    env["TLS_PASSIVE_SIZE"] = str(size)
    result = subprocess.run(
        ["prosperity4btx", STRATEGY, "5", "--merge-pnl", "--no-progress", "--no-out"],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    total, days = parser.parse(result.stdout)
    return {
        "case": name,
        "tls_cases": cases,
        "size": size,
        "total": total,
        "delta": total - BASE,
        "day2": days.get(2, 0),
        "day3": days.get(3, 0),
        "day4": days.get(4, 0),
    }


def main():
    rows = []
    for name, cases in CASES:
        for size in SIZES:
            print("running", name, cases, size, flush=True)
            row = run(name, cases, size)
            rows.append(row)
            print(row, flush=True)
            with open(OUT, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["case", "tls_cases", "size", "total", "delta", "day2", "day3", "day4"])
                writer.writeheader()
                writer.writerows(rows)


if __name__ == "__main__":
    main()
