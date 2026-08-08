"""Build a leakage-safe pollution-process early-warning dataset.

The source contains two stations per city-hour. This script first aggregates
stations to city-hour observations and then creates features using current and
past observations only. The target is whether the next six hours contain at
least three consecutive hours with city AQI > 100.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/air_quality_clean.csv"
SPATIAL = ROOT / "data/analysis_results/spatial_analysis_2025.json"
OUTPUT_DIR = ROOT / "data/warning_results"
FEATURE_CSV = OUTPUT_DIR / "pollution_warning_features.csv"
REPORT_JSON = OUTPUT_DIR / "pollution_warning_dataset_report.json"
FIELDS = ["aqi", "pm25", "pm10", "no2", "so2", "temperature", "humidity", "wind_speed"]


def finalize_city(rows: list[dict[str, str]]) -> dict[str, object]:
    first = rows[0]
    return {
        "datetime": first["datetime"],
        "city": first["city"],
        "province": first["province"],
        "region": first["region"],
        **{field: sum(float(row[field]) for row in rows) / len(rows) for field in FIELDS},
    }


def load_city_hours() -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = defaultdict(list)
    current_key: tuple[str, str] | None = None
    buffer: list[dict[str, str]] = []
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            key = (row["datetime"], row["city"])
            if current_key is not None and key != current_key:
                item = finalize_city(buffer)
                result[str(item["city"])].append(item)
                buffer = []
            current_key = key
            buffer.append(row)
    if buffer:
        item = finalize_city(buffer)
        result[str(item["city"])].append(item)
    return dict(result)


def has_future_process(items: list[dict[str, object]], start: int, horizon: int = 6, consecutive: int = 3) -> int:
    run = 0
    for item in items[start + 1 : start + horizon + 1]:
        run = run + 1 if float(item["aqi"]) > 100 else 0
        if run >= consecutive:
            return 1
    return 0


def process_stage(items: list[dict[str, object]], index: int) -> str:
    current = float(items[index]["aqi"])
    previous = float(items[index - 1]["aqi"])
    recent = [float(item["aqi"]) for item in items[max(0, index - 2) : index + 1]]
    if current > 100 and previous <= 100:
        return "forming"
    if len(recent) == 3 and all(value > 100 for value in recent):
        return "persistent"
    if current <= 100 < previous:
        return "dissipating"
    return "normal"


def build_samples(city_hours: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    spatial = json.loads(SPATIAL.read_text(encoding="utf-8"))
    neighbors = {item["city"]: item["neighbors"] for item in spatial["cities"]}
    lookup = {
        city: {str(item["datetime"]): float(item["aqi"]) for item in items}
        for city, items in city_hours.items()
    }
    samples: list[dict[str, object]] = []
    for city, items in city_hours.items():
        for index in range(6, len(items) - 6):
            current = items[index]
            timestamp = str(current["datetime"])
            hour = int(timestamp[11:13])
            # Four samples per day retain process dynamics while keeping the
            # dependency-free model training tractable.
            if hour % 6 != 0:
                continue
            lag1 = float(items[index - 1]["aqi"])
            lag3 = float(items[index - 3]["aqi"])
            lag6 = float(items[index - 6]["aqi"])
            rolling = sum(float(item["aqi"]) for item in items[index - 5 : index + 1]) / 6
            neighbor_values = [lookup[name][timestamp] for name in neighbors[city] if timestamp in lookup[name]]
            samples.append({
                "datetime": timestamp,
                "city": city,
                "province": current["province"],
                "region": current["region"],
                "current_aqi": round(float(current["aqi"]), 3),
                "pm25": round(float(current["pm25"]), 3),
                "pm10": round(float(current["pm10"]), 3),
                "no2": round(float(current["no2"]), 3),
                "so2": round(float(current["so2"]), 3),
                "temperature": round(float(current["temperature"]), 3),
                "humidity": round(float(current["humidity"]), 3),
                "wind_speed": round(float(current["wind_speed"]), 3),
                "aqi_lag1": round(lag1, 3),
                "aqi_lag3": round(lag3, 3),
                "aqi_lag6": round(lag6, 3),
                "aqi_roll6": round(rolling, 3),
                "aqi_change3": round(float(current["aqi"]) - lag3, 3),
                "neighbor_aqi": round(sum(neighbor_values) / len(neighbor_values), 3),
                "current_stage": process_stage(items, index),
                "target_process_next_6h": has_future_process(items, index),
            })
    return samples


def split_name(timestamp: str) -> str:
    month = int(timestamp[5:7])
    if month <= 8:
        return "train"
    if month <= 10:
        return "validation"
    return "test"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    city_hours = load_city_hours()
    samples = build_samples(city_hours)
    for sample in samples:
        sample["split"] = split_name(str(sample["datetime"]))
    fieldnames = list(samples[0])
    with FEATURE_CSV.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)
    split_counts = Counter(str(sample["split"]) for sample in samples)
    positive_counts = Counter(str(sample["split"]) for sample in samples if sample["target_process_next_6h"] == 1)
    stage_counts = Counter(str(sample["current_stage"]) for sample in samples)
    report = {
        "status": "passed",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "city_count": len(city_hours),
        "city_hour_rows": sum(len(items) for items in city_hours.values()),
        "sample_count": len(samples),
        "sampling_interval_hours": 6,
        "target": "next 6 hours contain >=3 consecutive city-hours with AQI > 100",
        "split_strategy": "chronological: Jan-Aug train, Sep-Oct validation, Nov-Dec test",
        "split_counts": dict(split_counts),
        "positive_counts": dict(positive_counts),
        "positive_rates": {key: round(positive_counts[key] / count, 6) for key, count in split_counts.items()},
        "stage_counts": dict(stage_counts),
        "spatial_feature": "mean current AQI of K=6 nearest cities",
        "output": str(FEATURE_CSV.relative_to(ROOT)).replace("\\", "/"),
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
