import csv
import math
import os
from collections import defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, "raw-data", "ROUND5")

FREE_ALPHA = {
    "GALAXY_SOUNDS_BLACK_HOLES": (11193.8333, -68.0000, 241.3333, 36.3333, 1151.8333),
    "GALAXY_SOUNDS_DARK_MATTER": (10428.5000, -201.5000, -346.1667, -438.5000, 89.3333),
    "GALAXY_SOUNDS_PLANETARY_RINGS": (10888.3333, -155.1667, -291.6667, 25.3333, -120.0000),
    "GALAXY_SOUNDS_SOLAR_FLAMES": (10660.5000, 290.0000, 485.5000, 537.8333, 277.3333),
    "GALAXY_SOUNDS_SOLAR_WINDS": (10115.8333, -5.5000, 457.5000, 305.5000, 83.5000),
    "MICROCHIP_CIRCLE": (9140.8333, -154.1667, -31.8333, 6.8333, 127.3333),
    "MICROCHIP_OVAL": (8889.6667, -186.0000, -385.1667, -686.8333, -1488.5000),
    "MICROCHIP_RECTANGLE": (9080.6667, -268.1667, -85.0000, -334.0000, -403.5000),
    "MICROCHIP_SQUARE": (12789.5000, -77.3333, 270.1667, 1295.3333, 1205.3333),
    "MICROCHIP_TRIANGLE": (9911.5000, -84.5000, -30.3333, -405.6667, -693.3333),
    "OXYGEN_SHAKE_CHOCOLATE": (9599.6667, -51.3333, -327.3333, -100.1667, 240.6667),
    "OXYGEN_SHAKE_EVENING_BREATH": (9286.6667, 136.6667, 160.0000, 53.3333, -193.3333),
    "OXYGEN_SHAKE_GARLIC": (11250.3333, 80.8333, 134.1667, 837.6667, 1299.3333),
    "OXYGEN_SHAKE_MINT": (9939.6667, -60.8333, -251.0000, -304.6667, 52.1667),
    "OXYGEN_SHAKE_MORNING_BREATH": (10178.3333, 223.6667, 156.3333, -142.5000, -149.6667),
    "PANEL_1X2": (9092.6667, -391.0000, -339.5000, -409.1667, -99.0000),
    "PANEL_1X4": (9939.6667, -387.8333, -425.3333, -538.3333, -269.8333),
    "PANEL_2X2": (9762.1667, -231.1667, -417.1667, 114.6667, -192.0000),
    "PANEL_2X4": (10726.6667, -52.3333, 181.8333, 531.1667, 790.1667),
    "PANEL_4X4": (9977.8333, 402.5000, 233.3333, -322.3333, -291.6667),
    "PEBBLES_L": (10381.6667, -27.0000, 159.1667, -231.8333, -297.0000),
    "PEBBLES_M": (10028.6667, -336.0000, -28.8333, 421.5000, 229.8333),
    "PEBBLES_S": (9386.8333, -189.1667, -214.3333, -458.5000, -651.3333),
    "PEBBLES_XL": (11894.3333, 551.5000, 302.1667, 1300.0000, 2045.3333),
    "PEBBLES_XS": (8308.1667, 0.8333, -217.8333, -1030.6667, -1326.1667),
    "ROBOT_DISHES": (10015.6667, -126.0000, -235.1667, 41.0000, 405.5000),
    "ROBOT_IRONING": (9000.0000, 170.0000, 176.6667, -310.0000, -720.0000),
    "ROBOT_LAUNDRY": (9903.5000, -60.0000, -68.5000, 24.6667, -239.5000),
    "ROBOT_MOPPING": (10661.5000, 120.0000, -7.3333, 392.0000, 530.1667),
    "ROBOT_VACUUMING": (9550.5000, -255.3333, -440.0000, -322.8333, -570.5000),
    "SLEEP_POD_COTTON": (11105.1667, 265.3333, 277.3333, 463.3333, 471.5000),
    "SLEEP_POD_LAMB_WOOL": (10396.3333, 32.0000, 207.6667, 457.5000, 272.0000),
    "SLEEP_POD_NYLON": (9529.0000, -75.6667, 79.5000, 218.5000, 242.0000),
    "SLEEP_POD_POLYESTER": (11555.5000, -63.1667, 439.1667, 71.5000, 655.6667),
    "SLEEP_POD_SUEDE": (11074.5000, 190.5000, -64.0000, 370.0000, 603.0000),
    "SNACKPACK_CHOCOLATE": (9921.3333, -7.6667, 21.5000, 36.1667, -113.6667),
    "SNACKPACK_PISTACHIO": (9634.8333, -41.3333, -22.5000, -243.8333, -298.1667),
    "SNACKPACK_RASPBERRY": (10120.3333, 2.5000, -79.3333, 53.1667, 103.1667),
    "SNACKPACK_STRAWBERRY": (10413.8333, 89.3333, 260.1667, 178.1667, 297.0000),
    "SNACKPACK_VANILLA": (10023.0000, 23.1667, -26.1667, -74.0000, 109.3333),
    "TRANSLATOR_ASTRO_BLACK": (9774.5000, -53.0000, -237.3333, -417.5000, -352.6667),
    "TRANSLATOR_ECLIPSE_CHARCOAL": (9954.0000, 41.5000, 22.3333, -280.5000, -88.1667),
    "TRANSLATOR_GRAPHITE_MIST": (10130.3333, 327.6667, 311.0000, -148.8333, -70.0000),
    "TRANSLATOR_SPACE_GRAY": (9869.3333, -297.5000, -562.6667, -472.8333, -519.6667),
    "TRANSLATOR_VOID_BLUE": (10596.3333, 178.1667, 19.8333, 214.1667, 509.1667),
    "UV_VISOR_AMBER": (8627.3333, -410.3333, -487.1667, -629.5000, -954.5000),
    "UV_VISOR_MAGENTA": (10969.6667, -95.6667, 12.1667, -169.5000, 501.5000),
    "UV_VISOR_ORANGE": (10152.0000, 164.8333, 314.0000, 558.3333, -226.5000),
    "UV_VISOR_RED": (10624.5000, 323.1667, 487.6667, 637.8333, 574.0000),
    "UV_VISOR_YELLOW": (11211.6667, -56.0000, -301.1667, -491.1667, 16.0000),
}


def corr(xs, ys):
    n = len(xs)
    if n == 0:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return 0.0
    return sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / math.sqrt(vx * vy)


def load_rows():
    rows = []
    products = set(FREE_ALPHA)
    for day in (2, 3, 4):
        path = os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % day)
        with open(path, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            for row in reader:
                product = row["product"]
                if product in products:
                    rows.append(
                        {
                            "day": int(row["day"]),
                            "timestamp": int(row["timestamp"]),
                            "product": product,
                            "mid": float(row["mid_price"]),
                        }
                    )
    return rows


def main():
    rows = load_rows()
    by_product = defaultdict(list)
    by_product_day = defaultdict(list)
    max_ts = 0
    for row in rows:
        by_product[row["product"]].append(row)
        by_product_day[(row["product"], row["day"])].append(row)
        if row["timestamp"] > max_ts:
            max_ts = row["timestamp"]

    summary_rows = []
    for product, items in sorted(by_product.items()):
        items.sort(key=lambda row: (row["day"], row["timestamp"]))
        vals = FREE_ALPHA[product]
        anchor = vals[0]
        coeffs = vals[1:]
        mids = [row["mid"] for row in items]
        mean_mid = sum(mids) / len(mids)

        bucket_means = []
        bucket_devs = []
        for bucket in range(5):
            lo = bucket * (max_ts + 1) / 5.0
            hi = (bucket + 1) * (max_ts + 1) / 5.0
            bucket_vals = [row["mid"] for row in items if lo <= row["timestamp"] < hi]
            mean_val = sum(bucket_vals) / len(bucket_vals)
            bucket_means.append(mean_val)
            bucket_devs.append(mean_val - anchor)

        end_moves = []
        day_means = []
        for day in (2, 3, 4):
            day_items = sorted(by_product_day[(product, day)], key=lambda row: row["timestamp"])
            day_means.append(sum(row["mid"] for row in day_items) / len(day_items))
            end_moves.append(day_items[-1]["mid"] - day_items[0]["mid"])

        # Compare the four unknown numbers to common path summaries.
        options = {
            "bucket1_4_dev_from_anchor": bucket_devs[1:],
            "bucket1_4_dev_from_bucket0": [x - bucket_means[0] for x in bucket_means[1:]],
            "bucket1_4_dev_from_mean": [x - mean_mid for x in bucket_means[1:]],
            "first_4_bucket_step": [bucket_means[i + 1] - bucket_means[i] for i in range(4)],
            "day_end_moves_plus_mean": end_moves + [sum(end_moves) / 3.0],
            "day_means_dev_anchor_plus_mean": [x - anchor for x in day_means] + [mean_mid - anchor],
        }
        best_name = ""
        best_corr = -2.0
        best_mae = 0.0
        for name, candidate in options.items():
            c = corr(list(coeffs), list(candidate))
            mae = sum(abs(coeffs[i] - candidate[i]) for i in range(4)) / 4.0
            if abs(c) > abs(best_corr) if best_name else True:
                best_name = name
                best_corr = c
                best_mae = mae

        summary_rows.append(
            {
                "product": product,
                "alpha_anchor": round(anchor, 4),
                "mean_mid": round(mean_mid, 4),
                "anchor_minus_mean": round(anchor - mean_mid, 4),
                "alpha_coeffs": "|".join("%.4f" % x for x in coeffs),
                "bucket_means": "|".join("%.4f" % x for x in bucket_means),
                "bucket_devs_from_anchor": "|".join("%.4f" % x for x in bucket_devs),
                "day_end_moves": "|".join("%.4f" % x for x in end_moves),
                "day_means": "|".join("%.4f" % x for x in day_means),
                "best_shape_match": best_name,
                "best_shape_corr": round(best_corr, 6),
                "best_shape_mae": round(best_mae, 4),
            }
        )

    out_path = os.path.join(OUT_DIR, "free_alpha_shape_probe.csv")
    with open(out_path, "w", newline="") as handle:
        fieldnames = list(summary_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    anchor_mae = sum(abs(row["alpha_anchor"] - row["mean_mid"]) for row in summary_rows) / len(summary_rows)
    anchor_corr = corr([row["alpha_anchor"] for row in summary_rows], [row["mean_mid"] for row in summary_rows])
    shape_corr = sum(abs(row["best_shape_corr"]) for row in summary_rows) / len(summary_rows)
    print("wrote %s" % out_path)
    print("anchor_vs_mean_corr=%.6f anchor_vs_mean_mae=%.2f" % (anchor_corr, anchor_mae))
    print("avg_abs_best_shape_corr=%.6f" % shape_corr)


if __name__ == "__main__":
    main()
