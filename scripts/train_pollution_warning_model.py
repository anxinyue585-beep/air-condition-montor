"""Train and explain the six-hour pollution-process warning model."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/warning_results/pollution_warning_features.csv"
OUTPUT = ROOT / "data/warning_results/pollution_warning_model.json"
PREDICTIONS = ROOT / "data/warning_results/pollution_warning_test_predictions.csv"
FEATURES = [
    "current_aqi", "pm25", "pm10", "no2", "so2", "temperature", "humidity", "wind_speed",
    "aqi_lag1", "aqi_lag3", "aqi_lag6", "aqi_roll6", "aqi_change3", "neighbor_aqi",
]
FEATURE_LABELS = {
    "current_aqi": "当前 AQI", "pm25": "PM2.5", "pm10": "PM10", "no2": "NO₂", "so2": "SO₂",
    "temperature": "温度", "humidity": "湿度", "wind_speed": "风速", "aqi_lag1": "1 小时前 AQI",
    "aqi_lag3": "3 小时前 AQI", "aqi_lag6": "6 小时前 AQI", "aqi_roll6": "近 6 小时平均 AQI",
    "aqi_change3": "3 小时 AQI 变化", "neighbor_aqi": "邻近城市 AQI",
}


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-min(value, 40))
        return 1 / (1 + z)
    z = math.exp(max(value, -40))
    return z / (1 + z)


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with INPUT.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            parsed: dict[str, object] = dict(row)
            parsed["features"] = [float(row[name]) for name in FEATURES]
            parsed["target"] = int(row["target_process_next_6h"])
            rows.append(parsed)
    return rows


def scaling(rows: list[dict[str, object]]) -> tuple[list[float], list[float]]:
    matrix = [row["features"] for row in rows]
    assert all(isinstance(item, list) for item in matrix)
    means = [sum(float(row[j]) for row in matrix) / len(matrix) for j in range(len(FEATURES))]
    stds = [math.sqrt(sum((float(row[j]) - means[j]) ** 2 for row in matrix) / len(matrix)) or 1.0 for j in range(len(FEATURES))]
    return means, stds


def transform(rows: list[dict[str, object]], means: list[float], stds: list[float]) -> list[list[float]]:
    return [[(float(value) - means[j]) / stds[j] for j, value in enumerate(row["features"])] for row in rows]


def fit_sgd(x: list[list[float]], y: list[int], reg_lambda: float, epochs: int = 32) -> list[float]:
    weights = [0.0] * (len(FEATURES) + 1)
    positives = sum(y)
    positive_weight = (len(y) - positives) / positives
    order = list(range(len(y)))
    rng = random.Random(2025)
    for epoch in range(epochs):
        rng.shuffle(order)
        rate = 0.035 / math.sqrt(epoch + 1)
        for i in order:
            row = x[i]
            probability = sigmoid(weights[0] + sum(weight * value for weight, value in zip(weights[1:], row)))
            error = (probability - y[i]) * (positive_weight if y[i] else 1.0)
            weights[0] -= rate * error
            for j, value in enumerate(row, 1):
                weights[j] -= rate * (error * value + reg_lambda * weights[j] / len(y))
    return weights


def probabilities(x: list[list[float]], weights: list[float]) -> list[float]:
    return [sigmoid(weights[0] + sum(weight * value for weight, value in zip(weights[1:], row))) for row in x]


def metrics(y: list[int], probs: list[float], threshold: float) -> dict[str, float | int]:
    predicted = [int(value >= threshold) for value in probs]
    tp = sum(a == b == 1 for a, b in zip(y, predicted))
    tn = sum(a == b == 0 for a, b in zip(y, predicted))
    fp = sum(a == 0 and b == 1 for a, b in zip(y, predicted))
    fn = sum(a == 1 and b == 0 for a, b in zip(y, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"accuracy": (tp + tn) / len(y), "precision": precision, "recall": recall, "f1": f1, "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def warning_level(probability: float) -> str:
    if probability >= 0.9:
        return "red"
    if probability >= 0.75:
        return "orange"
    if probability >= 0.6:
        return "yellow"
    if probability >= 0.4:
        return "blue"
    return "none"


def explain(row: dict[str, object], scaled: list[float], weights: list[float]) -> list[dict[str, object]]:
    contributions = []
    original = row["features"]
    assert isinstance(original, list)
    for name, value, scaled_value, coefficient in zip(FEATURES, original, scaled, weights[1:]):
        contribution = scaled_value * coefficient
        contributions.append({
            "feature": name,
            "label": FEATURE_LABELS[name],
            "value": round(float(value), 3),
            "contribution": round(contribution, 5),
            "direction": "increase" if contribution >= 0 else "decrease",
        })
    return sorted(contributions, key=lambda item: abs(float(item["contribution"])), reverse=True)[:6]


def round_metrics(values: dict[str, float | int]) -> dict[str, float | int]:
    return {key: round(value, 5) if isinstance(value, float) else value for key, value in values.items()}


def main() -> None:
    rows = load_rows()
    train = [row for row in rows if row["split"] == "train"]
    validation = [row for row in rows if row["split"] == "validation"]
    test = [row for row in rows if row["split"] == "test"]
    means, stds = scaling(train)
    train_x, validation_x = transform(train, means, stds), transform(validation, means, stds)
    train_y = [int(row["target"]) for row in train]
    validation_y = [int(row["target"]) for row in validation]
    candidates = []
    best: tuple[float, float, float, float, float] | None = None
    for reg_lambda in (0.01, 0.1, 1.0):
        weights = fit_sgd(train_x, train_y, reg_lambda)
        probs = probabilities(validation_x, weights)
        for threshold in (0.4, 0.5, 0.6):
            score = metrics(validation_y, probs, threshold)
            candidates.append({"lambda": reg_lambda, "threshold": threshold, **round_metrics(score)})
            rank = (float(score["f1"]), float(score["recall"]), float(score["precision"]))
            if best is None or rank > best:
                best = (*rank, reg_lambda, threshold)  # type: ignore[assignment]
    assert best is not None
    best_lambda, best_threshold = best[-2], best[-1]

    final_train = train + validation
    means, stds = scaling(final_train)
    final_x = transform(final_train, means, stds)
    final_y = [int(row["target"]) for row in final_train]
    weights = fit_sgd(final_x, final_y, best_lambda)
    test_x = transform(test, means, stds)
    test_probs = probabilities(test_x, weights)
    test_metrics = metrics([int(row["target"]) for row in test], test_probs, best_threshold)

    prediction_rows = []
    latest_by_city: dict[str, dict[str, object]] = {}
    timeline_by_city: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row, scaled, probability in zip(test, test_x, test_probs):
        item = {
            "datetime": row["datetime"], "city": row["city"], "province": row["province"], "region": row["region"],
            "current_aqi": float(row["current_aqi"]), "current_stage": row["current_stage"],
            "probability": round(probability, 6), "warning_level": warning_level(probability),
            "predicted": int(probability >= best_threshold), "actual": int(row["target"]),
            "explanations": explain(row, scaled, weights),
        }
        prediction_rows.append({key: value for key, value in item.items() if key != "explanations"})
        latest_by_city[str(row["city"])] = item
        timeline_by_city[str(row["city"])].append({"datetime": row["datetime"], "probability": round(probability, 4), "actual": int(row["target"])})

    latest = sorted(latest_by_city.values(), key=lambda item: float(item["probability"]), reverse=True)
    for item in latest:
        item["timeline"] = timeline_by_city[str(item["city"])][-20:]
        positive = [factor["label"] for factor in item["explanations"] if factor["direction"] == "increase"][:3]
        item["explanation_text"] = f"未来 6 小时污染过程概率为 {float(item['probability']) * 100:.1f}%。主要风险抬升因素：{'、'.join(positive) if positive else '无明显抬升因素'}。"

    with PREDICTIONS.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(prediction_rows[0]))
        writer.writeheader()
        writer.writerows(prediction_rows)

    level_counts = Counter(str(item["warning_level"]) for item in latest)
    output = {
        "status": "passed",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task": "next 6 hours contain at least 3 consecutive city-hours with AQI > 100",
        "model": {
            "algorithm": "class-weighted L2 Logistic Regression",
            "split": "Jan-Aug train, Sep-Oct validation, Nov-Dec isolated test",
            "selection_metric": "validation F1, then recall and precision",
            "selected_lambda": best_lambda,
            "selected_threshold": best_threshold,
            "features": FEATURES,
            "feature_labels": FEATURE_LABELS,
            "means": [round(value, 6) for value in means],
            "stds": [round(value, 6) for value in stds],
            "weights": [round(value, 8) for value in weights],
            "validation_candidates": candidates,
            "test_metrics": round_metrics(test_metrics),
        },
        "warning_rule": {"blue": [0.4, 0.6], "yellow": [0.6, 0.75], "orange": [0.75, 0.9], "red": [0.9, 1.0]},
        "summary": {"city_count": len(latest), "warning_level_counts": dict(level_counts), "highest_risk_city": latest[0]["city"], "highest_probability": latest[0]["probability"]},
        "cities": latest,
        "prediction_output": str(PREDICTIONS.relative_to(ROOT)).replace("\\", "/"),
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "passed", "selected_lambda": best_lambda, "selected_threshold": best_threshold, "test_metrics": round_metrics(test_metrics), "summary": output["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
