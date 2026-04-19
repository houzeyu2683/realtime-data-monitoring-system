import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

CATEGORIES = ["temperature", "humidity", "pressure", "cpu_load", "memory_usage", "network_io"]
OUTPUT = Path(__file__).parent.parent / "sample_data.csv"
ROWS = 120
START = datetime(2026, 4, 15, 0, 0, 0)


def main() -> None:
    rows = [["title", "value", "category", "description", "threshold", "timestamp"]]
    for i in range(ROWS):
        cat = CATEGORIES[i % len(CATEGORIES)]
        ts = START + timedelta(hours=i)
        value = round(random.uniform(10, 100), 2)
        threshold = round(random.uniform(80, 120), 2)
        rows.append([f"Sensor {cat} {i}", value, cat, "", threshold, ts.strftime("%Y-%m-%dT%H:%M:%S")])

    with open(OUTPUT, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    print(f"Generated {len(rows) - 1} rows → {OUTPUT}")


if __name__ == "__main__":
    main()
