"""Deterministic city-level spatial autocorrelation analysis.

Input is the verified Spark city-month export. The script aggregates 2025
monthly AQI to city means, creates a row-standardized KNN spatial weights
matrix, then computes global Moran's I and local Moran (LISA) statistics with
Monte Carlo permutation pseudo p-values.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/platform_exports/spark/air_quality_city_month.csv"
DEFAULT_COORDS = ROOT / "data/reference/city_coordinates.csv"
DEFAULT_OUTPUT = ROOT / "data/analysis_results/spatial_analysis_2025.json"
DEFAULT_CSV = ROOT / "data/analysis_results/spatial_city_lisa_2025.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(value))


def aggregate_2025(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row["year_month"].startswith("2025-"):
            grouped.setdefault(row["city"], []).append(row)
    result: dict[str, dict[str, object]] = {}
    for city, items in grouped.items():
        weights = [float(item["record_count"]) for item in items]
        total = sum(weights)
        weighted = lambda key: sum(float(item[key]) * weight for item, weight in zip(items, weights)) / total
        result[city] = {
            "city": city,
            "province": items[0]["province"],
            "region": items[0]["region"],
            "avg_aqi": weighted("avg_aqi"),
            "avg_pm25": weighted("avg_pm25"),
            "avg_pm10": weighted("avg_pm10"),
            "record_count": int(total),
            "month_count": len(items),
        }
    return result


def knn_weights(points: list[tuple[float, float]], k: int) -> tuple[list[list[int]], list[list[float]]]:
    neighbors: list[list[int]] = []
    weights: list[list[float]] = []
    for i, point in enumerate(points):
        distances = sorted((haversine_km(point, other), j) for j, other in enumerate(points) if i != j)
        selected = [j for _, j in distances[:k]]
        neighbors.append(selected)
        weights.append([1.0 / k] * k)
    return neighbors, weights


def spatial_lag(values: list[float], neighbors: list[list[int]], weights: list[list[float]]) -> list[float]:
    return [sum(weight * values[j] for j, weight in zip(nbrs, row_weights)) for nbrs, row_weights in zip(neighbors, weights)]


def global_moran(z: list[float], neighbors: list[list[int]], weights: list[list[float]]) -> float:
    lag = spatial_lag(z, neighbors, weights)
    denominator = sum(value * value for value in z)
    return len(z) / len(z) * sum(value * lag_value for value, lag_value in zip(z, lag)) / denominator


def cluster_label(z_value: float, lag_value: float, p_value: float) -> str:
    if p_value >= 0.05:
        return "Not significant"
    if z_value >= 0 and lag_value >= 0:
        return "High-High"
    if z_value < 0 and lag_value < 0:
        return "Low-Low"
    if z_value >= 0 and lag_value < 0:
        return "High-Low"
    return "Low-High"


def analyze(monthly_path: Path, coords_path: Path, k: int, permutations: int, seed: int) -> dict[str, object]:
    aggregated = aggregate_2025(read_csv(monthly_path))
    coordinates = {row["city"]: (float(row["longitude"]), float(row["latitude"])) for row in read_csv(coords_path)}
    missing = sorted(set(aggregated) - set(coordinates))
    if missing:
        raise ValueError(f"Missing coordinates: {', '.join(missing)}")
    cities = sorted(aggregated)
    if len(cities) != 60:
        raise ValueError(f"Expected 60 cities, found {len(cities)}")
    if not 1 <= k < len(cities):
        raise ValueError("k must be between 1 and city_count - 1")

    values = [float(aggregated[city]["avg_aqi"]) for city in cities]
    mean = sum(values) / len(values)
    std = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
    z = [(value - mean) / std for value in values]
    points = [coordinates[city] for city in cities]
    neighbors, weights = knn_weights(points, k)
    lag = spatial_lag(z, neighbors, weights)
    observed_global = global_moran(z, neighbors, weights)
    local_observed = [value * lag_value for value, lag_value in zip(z, lag)]

    rng = random.Random(seed)
    global_extreme = 0
    local_extreme = [0] * len(cities)
    permutations_global: list[float] = []
    for _ in range(permutations):
        permuted = z[:]
        rng.shuffle(permuted)
        perm_lag = spatial_lag(permuted, neighbors, weights)
        perm_global = global_moran(permuted, neighbors, weights)
        permutations_global.append(perm_global)
        if abs(perm_global) >= abs(observed_global):
            global_extreme += 1
        for i, statistic in enumerate(local_observed):
            perm_statistic = permuted[i] * perm_lag[i]
            if abs(perm_statistic) >= abs(statistic):
                local_extreme[i] += 1

    global_p = (global_extreme + 1) / (permutations + 1)
    expected = -1 / (len(cities) - 1)
    city_results = []
    for i, city in enumerate(cities):
        p_value = (local_extreme[i] + 1) / (permutations + 1)
        lon, lat = coordinates[city]
        item = dict(aggregated[city])
        item.update({
            "longitude": lon,
            "latitude": lat,
            "z_aqi": round(z[i], 6),
            "spatial_lag_z": round(lag[i], 6),
            "local_moran_i": round(local_observed[i], 6),
            "p_value": round(p_value, 6),
            "significant": p_value < 0.05,
            "cluster": cluster_label(z[i], lag[i], p_value),
            "neighbors": [cities[j] for j in neighbors[i]],
        })
        for key in ("avg_aqi", "avg_pm25", "avg_pm10"):
            item[key] = round(float(item[key]), 2)
        city_results.append(item)

    counts = Counter(str(item["cluster"]) for item in city_results)
    return {
        "status": "passed",
        "method": {
            "year": 2025,
            "indicator": "annual_mean_aqi",
            "city_count": len(cities),
            "spatial_weights": "row-standardized K-nearest neighbors",
            "k": k,
            "distance": "Haversine great-circle distance",
            "permutations": permutations,
            "random_seed": seed,
            "significance_threshold": 0.05,
            "source": str(monthly_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "global_moran": {
            "observed_i": round(observed_global, 6),
            "expected_i": round(expected, 6),
            "pseudo_p_value": round(global_p, 6),
            "significant": global_p < 0.05,
            "interpretation": "positive spatial clustering" if observed_global > expected and global_p < 0.05 else "no significant positive spatial clustering",
            "permutation_mean": round(sum(permutations_global) / permutations, 6),
        },
        "cluster_counts": dict(sorted(counts.items())),
        "cities": city_results,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def write_outputs(result: dict[str, object], json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    cities = result["cities"]
    assert isinstance(cities, list)
    fields = ["city", "province", "region", "longitude", "latitude", "avg_aqi", "avg_pm25", "avg_pm10", "z_aqi", "spatial_lag_z", "local_moran_i", "p_value", "significant", "cluster", "neighbors"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for item in cities:
            row = {field: item[field] for field in fields}
            row["neighbors"] = "|".join(row["neighbors"])
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--coordinates", type=Path, default=DEFAULT_COORDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=2025)
    args = parser.parse_args()
    result = analyze(args.input, args.coordinates, args.k, args.permutations, args.seed)
    write_outputs(result, args.output, args.csv_output)
    print(json.dumps({"status": result["status"], "global_moran": result["global_moran"], "cluster_counts": result["cluster_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
