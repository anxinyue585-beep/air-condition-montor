"""Run data-analysis algorithms for the course rubric.

Implemented algorithms:
1. Top-N risk ranking, a basic analysis algorithm.
2. K-Means clustering for city pollution profiles, a data-mining algorithm.
3. Logistic Regression for next-month pollution risk, an explicit ML algorithm.
4. Ridge Regression for next-month AQI prediction, a time-series prediction task.

The implementation is dependency-free so the results are reproducible in the
course environment.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CITY_MONTH = ROOT / "data" / "warehouse" / "air_quality_city_month.csv"
RESULT_DIR = ROOT / "data" / "analysis_results"

REPORT_JSON = RESULT_DIR / "analysis_algorithm_report.json"
CITY_RANKING_CSV = RESULT_DIR / "city_risk_ranking.csv"
KMEANS_PARAM_CSV = RESULT_DIR / "kmeans_parameter_eval.csv"
KMEANS_ASSIGN_CSV = RESULT_DIR / "city_cluster_assignments.csv"
KMEANS_SUMMARY_CSV = RESULT_DIR / "cluster_summary.csv"
LOGISTIC_PARAM_CSV = RESULT_DIR / "logistic_parameter_eval.csv"
LOGISTIC_PRED_CSV = RESULT_DIR / "logistic_predictions.csv"
RIDGE_PARAM_CSV = RESULT_DIR / "ridge_parameter_eval.csv"
RIDGE_PRED_CSV = RESULT_DIR / "aqi_prediction_predictions.csv"
RIDGE_COEF_CSV = RESULT_DIR / "ridge_coefficients.csv"

PROFILE_FEATURES = ["avg_aqi", "max_aqi", "polluted_rate", "avg_pm25", "avg_pm10", "avg_so2", "avg_no2"]
SUPERVISED_NUMERIC_FEATURES = ["avg_aqi", "max_aqi", "good_rate", "avg_pm25", "avg_pm10", "avg_so2", "avg_no2"]


@dataclass
class Metrics:
    mae: float
    rmse: float
    r2: float


def ensure_dirs() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def read_city_month_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with CITY_MONTH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            parsed: dict[str, Any] = dict(row)
            for field in ["record_count", "avg_aqi", "max_aqi", "good_rate", "avg_pm25", "avg_pm10", "avg_so2", "avg_no2"]:
                parsed[field] = float(row[field])
            parsed["month"] = int(row["year_month"].split("-")[1])
            rows.append(parsed)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def minmax(values: list[float], value: float) -> float:
    lo = min(values)
    hi = max(values)
    return 0.0 if hi == lo else (value - lo) / (hi - lo)


def build_city_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        city = row["city"]
        if city not in grouped:
            grouped[city] = {
                "city": city,
                "province": row["province"],
                "region": row["region"],
                "record_count": 0.0,
                "sum_aqi": 0.0,
                "max_aqi": 0.0,
                "good_records": 0.0,
                "sum_pm25": 0.0,
                "sum_pm10": 0.0,
                "sum_so2": 0.0,
                "sum_no2": 0.0,
            }
        bucket = grouped[city]
        count = row["record_count"]
        bucket["record_count"] += count
        bucket["sum_aqi"] += row["avg_aqi"] * count
        bucket["max_aqi"] = max(bucket["max_aqi"], row["max_aqi"])
        bucket["good_records"] += row["good_rate"] * count
        bucket["sum_pm25"] += row["avg_pm25"] * count
        bucket["sum_pm10"] += row["avg_pm10"] * count
        bucket["sum_so2"] += row["avg_so2"] * count
        bucket["sum_no2"] += row["avg_no2"] * count

    profiles = []
    for bucket in grouped.values():
        count = bucket["record_count"]
        good_rate = bucket["good_records"] / count
        profiles.append(
            {
                "city": bucket["city"],
                "province": bucket["province"],
                "region": bucket["region"],
                "record_count": int(count),
                "avg_aqi": round(bucket["sum_aqi"] / count, 4),
                "max_aqi": round(bucket["max_aqi"], 4),
                "good_rate": round(good_rate, 6),
                "polluted_rate": round(1 - good_rate, 6),
                "avg_pm25": round(bucket["sum_pm25"] / count, 4),
                "avg_pm10": round(bucket["sum_pm10"] / count, 4),
                "avg_so2": round(bucket["sum_so2"] / count, 4),
                "avg_no2": round(bucket["sum_no2"] / count, 4),
            }
        )
    return sorted(profiles, key=lambda item: item["city"])


def build_risk_ranking(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    avg_values = [row["avg_aqi"] for row in profiles]
    max_values = [row["max_aqi"] for row in profiles]
    pollution_values = [row["polluted_rate"] for row in profiles]
    pm25_values = [row["avg_pm25"] for row in profiles]

    ranking = []
    for row in profiles:
        score = 100 * (
            0.35 * minmax(avg_values, row["avg_aqi"])
            + 0.2 * minmax(max_values, row["max_aqi"])
            + 0.25 * minmax(pollution_values, row["polluted_rate"])
            + 0.2 * minmax(pm25_values, row["avg_pm25"])
        )
        ranking.append(
            {
                "rank": 0,
                "city": row["city"],
                "province": row["province"],
                "region": row["region"],
                "risk_score": round(score, 4),
                "avg_aqi": round(row["avg_aqi"], 2),
                "max_aqi": round(row["max_aqi"], 2),
                "polluted_rate": round(row["polluted_rate"], 4),
                "avg_pm25": round(row["avg_pm25"], 2),
            }
        )
    ranking.sort(key=lambda item: item["risk_score"], reverse=True)
    for index, row in enumerate(ranking, start=1):
        row["rank"] = index
    write_csv(CITY_RANKING_CSV, ranking, ["rank", "city", "province", "region", "risk_score", "avg_aqi", "max_aqi", "polluted_rate", "avg_pm25"])
    return ranking


def mean_std(matrix: list[list[float]]) -> tuple[list[float], list[float]]:
    cols = len(matrix[0])
    means = [sum(row[j] for row in matrix) / len(matrix) for j in range(cols)]
    stds = []
    for j in range(cols):
        variance = sum((row[j] - means[j]) ** 2 for row in matrix) / len(matrix)
        stds.append(math.sqrt(variance) or 1.0)
    return means, stds


def standardize(matrix: list[list[float]], means: list[float] | None = None, stds: list[float] | None = None) -> tuple[list[list[float]], list[float], list[float]]:
    if means is None or stds is None:
        means, stds = mean_std(matrix)
    return [[(value - means[j]) / stds[j] for j, value in enumerate(row)] for row in matrix], means, stds


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def init_centroids(points: list[list[float]], profiles: list[dict[str, Any]], k: int) -> list[list[float]]:
    ordered = sorted(range(len(points)), key=lambda index: profiles[index]["avg_aqi"])
    if k == 1:
        return [points[ordered[len(ordered) // 2]][:]]
    centroids = []
    for i in range(k):
        pos = round(i * (len(ordered) - 1) / (k - 1))
        centroids.append(points[ordered[pos]][:])
    return centroids


def run_kmeans(points: list[list[float]], profiles: list[dict[str, Any]], k: int, max_iter: int = 100) -> tuple[list[int], list[list[float]], float, int]:
    centroids = init_centroids(points, profiles, k)
    labels = [0 for _ in points]

    for iteration in range(1, max_iter + 1):
        changed = False
        for i, point in enumerate(points):
            label = min(range(k), key=lambda idx: distance(point, centroids[idx]))
            if labels[i] != label:
                labels[i] = label
                changed = True

        new_centroids = []
        for cluster_id in range(k):
            members = [points[i] for i, label in enumerate(labels) if label == cluster_id]
            if not members:
                new_centroids.append(centroids[cluster_id])
                continue
            new_centroids.append([sum(row[j] for row in members) / len(members) for j in range(len(points[0]))])
        centroids = new_centroids
        if not changed:
            break

    inertia = sum(distance(point, centroids[labels[i]]) ** 2 for i, point in enumerate(points))
    return labels, centroids, inertia, iteration


def silhouette(points: list[list[float]], labels: list[int], k: int) -> float:
    scores = []
    for i, point in enumerate(points):
        own_label = labels[i]
        same = [points[j] for j, label in enumerate(labels) if label == own_label and j != i]
        if not same:
            scores.append(0.0)
            continue
        a = sum(distance(point, other) for other in same) / len(same)
        b_values = []
        for cluster_id in range(k):
            if cluster_id == own_label:
                continue
            others = [points[j] for j, label in enumerate(labels) if label == cluster_id]
            if others:
                b_values.append(sum(distance(point, other) for other in others) / len(others))
        b = min(b_values) if b_values else 0.0
        scores.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return sum(scores) / len(scores)


def kmeans_analysis(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = [[float(row[field]) for field in PROFILE_FEATURES] for row in profiles]
    scaled, _, _ = standardize(matrix)
    eval_rows = []
    model_cache: dict[int, tuple[list[int], list[list[float]], float, int, float]] = {}

    for k in range(2, 7):
        labels, centroids, inertia, iterations = run_kmeans(scaled, profiles, k)
        sil = silhouette(scaled, labels, k)
        model_cache[k] = (labels, centroids, inertia, iterations, sil)
        eval_rows.append(
            {
                "k": k,
                "inertia_sse": round(inertia, 6),
                "silhouette": round(sil, 6),
                "iterations": iterations,
            }
        )

    selected_k = 3
    labels, _, inertia, iterations, sil = model_cache[selected_k]
    cluster_avg_aqi = defaultdict(list)
    for label, profile in zip(labels, profiles):
        cluster_avg_aqi[label].append(profile["avg_aqi"])
    cluster_order = sorted(cluster_avg_aqi, key=lambda label: sum(cluster_avg_aqi[label]) / len(cluster_avg_aqi[label]))
    cluster_names = {}
    base_names = ["低污染稳定型", "中等波动型", "高污染风险型"]
    for order, label in enumerate(cluster_order):
        cluster_names[label] = base_names[order] if order < len(base_names) else f"污染画像{order + 1}"

    assign_rows = []
    for profile, label in zip(profiles, labels):
        assign_rows.append(
            {
                "city": profile["city"],
                "province": profile["province"],
                "region": profile["region"],
                "cluster_id": label,
                "cluster_name": cluster_names[label],
                "avg_aqi": round(profile["avg_aqi"], 2),
                "max_aqi": round(profile["max_aqi"], 2),
                "good_rate": round(profile["good_rate"], 4),
                "polluted_rate": round(profile["polluted_rate"], 4),
                "avg_pm25": round(profile["avg_pm25"], 2),
            }
        )

    summary_rows = []
    for label in sorted(set(labels), key=lambda item: cluster_names[item]):
        members = [profile for profile, assigned in zip(profiles, labels) if assigned == label]
        summary_rows.append(
            {
                "cluster_id": label,
                "cluster_name": cluster_names[label],
                "city_count": len(members),
                "avg_aqi": round(sum(item["avg_aqi"] for item in members) / len(members), 2),
                "max_aqi": round(max(item["max_aqi"] for item in members), 2),
                "avg_polluted_rate": round(sum(item["polluted_rate"] for item in members) / len(members), 4),
                "representative_cities": "、".join(item["city"] for item in sorted(members, key=lambda x: x["avg_aqi"], reverse=True)[:5]),
            }
        )

    write_csv(KMEANS_PARAM_CSV, eval_rows, ["k", "inertia_sse", "silhouette", "iterations"])
    write_csv(KMEANS_ASSIGN_CSV, assign_rows, ["city", "province", "region", "cluster_id", "cluster_name", "avg_aqi", "max_aqi", "good_rate", "polluted_rate", "avg_pm25"])
    write_csv(KMEANS_SUMMARY_CSV, summary_rows, ["cluster_id", "cluster_name", "city_count", "avg_aqi", "max_aqi", "avg_polluted_rate", "representative_cities"])

    return {
        "algorithm": "K-Means",
        "selected_k": selected_k,
        "selected_k_reason": "k=3 对应低污染、中等波动、高污染风险三类业务画像，便于课程报告解释；同时保留 k=2..6 的参数对比。",
        "selected_inertia": round(inertia, 6),
        "selected_silhouette": round(sil, 6),
        "iterations": iterations,
        "parameter_eval": str(KMEANS_PARAM_CSV.relative_to(ROOT)),
        "assignments": str(KMEANS_ASSIGN_CSV.relative_to(ROOT)),
        "summary": str(KMEANS_SUMMARY_CSV.relative_to(ROOT)),
    }


def month_features(row: dict[str, Any], regions: list[str]) -> list[float]:
    month = int(row["year_month"].split("-")[1])
    values = [float(row[field]) for field in SUPERVISED_NUMERIC_FEATURES]
    values.extend([math.sin(2 * math.pi * month / 12), math.cos(2 * math.pi * month / 12)])
    values.extend([1.0 if row["region"] == region else 0.0 for region in regions])
    return values


def build_supervised_dataset(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    regions = sorted({row["region"] for row in rows})
    by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_city[row["city"]].append(row)

    samples = []
    for city, city_rows in by_city.items():
        city_rows.sort(key=lambda item: item["year_month"])
        for current, target in zip(city_rows, city_rows[1:]):
            samples.append(
                {
                    "city": city,
                    "province": current["province"],
                    "region": current["region"],
                    "source_month": current["year_month"],
                    "target_month": target["year_month"],
                    "features": month_features(current, regions),
                    "target_aqi": float(target["avg_aqi"]),
                    "target_polluted": 1 if float(target["avg_aqi"]) >= 100 else 0,
                    "current_aqi": float(current["avg_aqi"]),
                }
            )
    return samples, [*SUPERVISED_NUMERIC_FEATURES, "month_sin", "month_cos", *[f"region_{region}" for region in regions]]


def temporal_train_validation_test_split(
    samples: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split by target month so future observations never influence the past.

    Target months February-August are used for training, September-October for
    hyperparameter selection, and November-December for the final one-time
    test evaluation.
    """

    train, validation, test = [], [], []
    for sample in samples:
        target_month = int(sample["target_month"].split("-")[1])
        if target_month <= 8:
            train.append(sample)
        elif target_month <= 10:
            validation.append(sample)
        else:
            test.append(sample)
    if not train or not validation or not test:
        raise ValueError("temporal split requires non-empty train, validation, and test sets")
    return train, validation, test


def normalize_samples(train: list[dict[str, Any]], test: list[dict[str, Any]]) -> tuple[list[list[float]], list[list[float]], list[float], list[float]]:
    train_x = [sample["features"] for sample in train]
    test_x = [sample["features"] for sample in test]
    train_scaled, means, stds = standardize(train_x)
    test_scaled, _, _ = standardize(test_x, means, stds)
    return train_scaled, test_scaled, means, stds


def select_best_ridge_alpha(models: dict[float, tuple[list[float], Metrics, list[float]]]) -> float:
    return min(models, key=lambda alpha: (models[alpha][1].rmse, models[alpha][1].mae, alpha))


def select_best_logistic_lambda(models: dict[float, tuple[list[float], dict[str, float], list[float]]]) -> float:
    return max(
        models,
        key=lambda value: (
            models[value][1]["f1"],
            models[value][1]["recall"],
            models[value][1]["accuracy"],
            -value,
        ),
    )


def add_intercept(matrix: list[list[float]]) -> list[list[float]]:
    return [[1.0, *row] for row in matrix]


def solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            aug[pivot][col] = 1e-12
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_value = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pivot_value
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def fit_ridge(x: list[list[float]], y: list[float], alpha: float) -> list[float]:
    x_i = add_intercept(x)
    cols = len(x_i[0])
    xtx = [[0.0 for _ in range(cols)] for _ in range(cols)]
    xty = [0.0 for _ in range(cols)]
    for row, target in zip(x_i, y):
        for i in range(cols):
            xty[i] += row[i] * target
            for j in range(cols):
                xtx[i][j] += row[i] * row[j]
    for i in range(1, cols):
        xtx[i][i] += alpha
    xtx[0][0] += 1e-8
    return solve_linear_system(xtx, xty)


def predict_linear(x: list[list[float]], weights: list[float]) -> list[float]:
    return [weights[0] + sum(weights[j + 1] * value for j, value in enumerate(row)) for row in x]


def regression_metrics(y_true: list[float], y_pred: list[float]) -> Metrics:
    n = len(y_true)
    mae = sum(abs(a - p) for a, p in zip(y_true, y_pred)) / n
    rmse = math.sqrt(sum((a - p) ** 2 for a, p in zip(y_true, y_pred)) / n)
    mean_y = sum(y_true) / n
    ss_tot = sum((a - mean_y) ** 2 for a in y_true)
    ss_res = sum((a - p) ** 2 for a, p in zip(y_true, y_pred))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return Metrics(mae=mae, rmse=rmse, r2=r2)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def fit_logistic(x: list[list[float]], y: list[int], reg_lambda: float, learning_rate: float = 0.08, epochs: int = 2500) -> list[float]:
    x_i = add_intercept(x)
    cols = len(x_i[0])
    weights = [0.0 for _ in range(cols)]
    n = len(x_i)
    for _ in range(epochs):
        grads = [0.0 for _ in range(cols)]
        for row, target in zip(x_i, y):
            pred = sigmoid(sum(w * v for w, v in zip(weights, row)))
            error = pred - target
            for j in range(cols):
                grads[j] += error * row[j]
        for j in range(cols):
            grads[j] /= n
            if j > 0:
                grads[j] += reg_lambda * weights[j] / n
            weights[j] -= learning_rate * grads[j]
    return weights


def predict_logistic(x: list[list[float]], weights: list[float]) -> list[float]:
    return [sigmoid(weights[0] + sum(weights[j + 1] * value for j, value in enumerate(row))) for row in x]


def classification_metrics(y_true: list[int], probabilities: list[float], threshold: float = 0.5) -> dict[str, float]:
    preds = [1 if p >= threshold else 0 for p in probabilities]
    tp = sum(1 for y, p in zip(y_true, preds) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(y_true, preds) if y == 0 and p == 0)
    fp = sum(1 for y, p in zip(y_true, preds) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(y_true, preds) if y == 1 and p == 0)
    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def supervised_analysis(samples: list[dict[str, Any]], feature_names: list[str]) -> dict[str, Any]:
    train, validation, test = temporal_train_validation_test_split(samples)
    train_x, validation_x, _, _ = normalize_samples(train, validation)
    train_y_reg = [sample["target_aqi"] for sample in train]
    validation_y_reg = [sample["target_aqi"] for sample in validation]
    train_y_cls = [sample["target_polluted"] for sample in train]
    validation_y_cls = [sample["target_polluted"] for sample in validation]

    ridge_rows = []
    ridge_models: dict[float, tuple[list[float], Metrics, list[float]]] = {}
    for alpha in [0.0, 0.1, 1.0, 10.0, 100.0]:
        weights = fit_ridge(train_x, train_y_reg, alpha)
        predictions = predict_linear(validation_x, weights)
        metrics = regression_metrics(validation_y_reg, predictions)
        ridge_models[alpha] = (weights, metrics, predictions)
        ridge_rows.append(
            {
                "alpha": alpha,
                "evaluation_split": "validation",
                "mae": round(metrics.mae, 4),
                "rmse": round(metrics.rmse, 4),
                "r2": round(metrics.r2, 4),
            }
        )

    best_alpha = select_best_ridge_alpha(ridge_models)

    final_train = [*train, *validation]
    final_train_x, test_x, _, _ = normalize_samples(final_train, test)
    final_train_y_reg = [sample["target_aqi"] for sample in final_train]
    final_train_y_cls = [sample["target_polluted"] for sample in final_train]
    test_y_reg = [sample["target_aqi"] for sample in test]
    test_y_cls = [sample["target_polluted"] for sample in test]

    best_weights = fit_ridge(final_train_x, final_train_y_reg, best_alpha)
    best_predictions = predict_linear(test_x, best_weights)
    best_metrics = regression_metrics(test_y_reg, best_predictions)
    baseline_predictions = [sample["current_aqi"] for sample in test]
    baseline_metrics = regression_metrics(test_y_reg, baseline_predictions)

    pred_rows = []
    for sample, pred in zip(test, best_predictions):
        pred_rows.append(
            {
                "city": sample["city"],
                "region": sample["region"],
                "source_month": sample["source_month"],
                "target_month": sample["target_month"],
                "actual_next_avg_aqi": round(sample["target_aqi"], 4),
                "predicted_next_avg_aqi": round(pred, 4),
                "absolute_error": round(abs(sample["target_aqi"] - pred), 4),
                "baseline_previous_month_aqi": round(sample["current_aqi"], 4),
            }
        )

    coef_rows = [{"feature": "intercept", "coefficient": round(best_weights[0], 6)}]
    for feature, coef in zip(feature_names, best_weights[1:]):
        coef_rows.append({"feature": feature, "coefficient": round(coef, 6)})

    logistic_rows = []
    logistic_models: dict[float, tuple[list[float], dict[str, float], list[float]]] = {}
    for reg_lambda in [0.0, 0.001, 0.01, 0.1, 1.0]:
        weights = fit_logistic(train_x, train_y_cls, reg_lambda)
        probabilities = predict_logistic(validation_x, weights)
        metrics = classification_metrics(validation_y_cls, probabilities)
        logistic_models[reg_lambda] = (weights, metrics, probabilities)
        logistic_rows.append(
            {
                "lambda": reg_lambda,
                "evaluation_split": "validation",
                "accuracy": round(metrics["accuracy"], 4),
                "precision": round(metrics["precision"], 4),
                "recall": round(metrics["recall"], 4),
                "f1": round(metrics["f1"], 4),
                "tp": metrics["tp"],
                "tn": metrics["tn"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
            }
        )

    best_lambda = select_best_logistic_lambda(logistic_models)
    best_cls_weights = fit_logistic(final_train_x, final_train_y_cls, best_lambda)
    best_probabilities = predict_logistic(test_x, best_cls_weights)
    best_cls_metrics = classification_metrics(test_y_cls, best_probabilities)
    logistic_pred_rows = []
    for sample, probability in zip(test, best_probabilities):
        logistic_pred_rows.append(
            {
                "city": sample["city"],
                "region": sample["region"],
                "source_month": sample["source_month"],
                "target_month": sample["target_month"],
                "actual_polluted": sample["target_polluted"],
                "predicted_probability": round(probability, 6),
                "predicted_polluted": 1 if probability >= 0.5 else 0,
                "actual_next_avg_aqi": round(sample["target_aqi"], 4),
            }
        )

    write_csv(RIDGE_PARAM_CSV, ridge_rows, ["alpha", "evaluation_split", "mae", "rmse", "r2"])
    write_csv(RIDGE_PRED_CSV, pred_rows, ["city", "region", "source_month", "target_month", "actual_next_avg_aqi", "predicted_next_avg_aqi", "absolute_error", "baseline_previous_month_aqi"])
    write_csv(RIDGE_COEF_CSV, coef_rows, ["feature", "coefficient"])
    write_csv(LOGISTIC_PARAM_CSV, logistic_rows, ["lambda", "evaluation_split", "accuracy", "precision", "recall", "f1", "tp", "tn", "fp", "fn"])
    write_csv(LOGISTIC_PRED_CSV, logistic_pred_rows, ["city", "region", "source_month", "target_month", "actual_polluted", "predicted_probability", "predicted_polluted", "actual_next_avg_aqi"])

    return {
        "dataset": {
            "sample_count": len(samples),
            "train_count": len(train),
            "validation_count": len(validation),
            "test_count": len(test),
            "train_target_months": "2025-02..2025-08",
            "validation_target_months": "2025-09..2025-10",
            "test_target_months": "2025-11..2025-12",
            "split_strategy": "chronological_by_target_month",
            "validation_positive_count": sum(validation_y_cls),
            "test_positive_count": sum(test_y_cls),
            "target": "next_month_avg_aqi / next_month_polluted",
        },
        "ridge_regression": {
            "best_alpha": best_alpha,
            "selection_split": "validation",
            "selection_metric": "rmse",
            "validation_rmse": round(ridge_models[best_alpha][1].rmse, 4),
            "evaluation_split": "test",
            "mae": round(best_metrics.mae, 4),
            "rmse": round(best_metrics.rmse, 4),
            "r2": round(best_metrics.r2, 4),
            "baseline_mae": round(baseline_metrics.mae, 4),
            "baseline_rmse": round(baseline_metrics.rmse, 4),
            "parameter_eval": str(RIDGE_PARAM_CSV.relative_to(ROOT)),
            "predictions": str(RIDGE_PRED_CSV.relative_to(ROOT)),
            "coefficients": str(RIDGE_COEF_CSV.relative_to(ROOT)),
        },
        "logistic_regression": {
            "best_lambda": best_lambda,
            "selection_split": "validation",
            "selection_metric": "f1_then_recall",
            "validation_f1": round(logistic_models[best_lambda][1]["f1"], 4),
            "evaluation_split": "test",
            "accuracy": round(best_cls_metrics["accuracy"], 4),
            "precision": round(best_cls_metrics["precision"], 4),
            "recall": round(best_cls_metrics["recall"], 4),
            "f1": round(best_cls_metrics["f1"], 4),
            "parameter_eval": str(LOGISTIC_PARAM_CSV.relative_to(ROOT)),
            "predictions": str(LOGISTIC_PRED_CSV.relative_to(ROOT)),
        },
    }


def build_report(ranking: list[dict[str, Any]], kmeans: dict[str, Any], supervised: dict[str, Any]) -> dict[str, Any]:
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_dataset": str(CITY_MONTH.relative_to(ROOT)),
        "rubric_mapping": [
            {
                "level": "A 类基础算法",
                "algorithm": "Top-N 风险排名",
                "evidence": str(CITY_RANKING_CSV.relative_to(ROOT)),
            },
            {
                "level": "B 类数据挖掘算法",
                "algorithm": "K-Means 城市污染画像聚类",
                "evidence": [kmeans["parameter_eval"], kmeans["assignments"], kmeans["summary"]],
            },
            {
                "level": "C 类机器学习算法",
                "algorithm": "Logistic Regression 下月污染风险分类",
                "evidence": [supervised["logistic_regression"]["parameter_eval"], supervised["logistic_regression"]["predictions"]],
            },
            {
                "level": "时间序列预测创新项",
                "algorithm": "Ridge Regression 下月 AQI 预测",
                "evidence": [supervised["ridge_regression"]["parameter_eval"], supervised["ridge_regression"]["predictions"], supervised["ridge_regression"]["coefficients"]],
            },
        ],
        "top_risk_cities": ranking[:10],
        "kmeans": kmeans,
        "supervised_learning": supervised,
        "conclusion": "项目已实现基础排名、数据挖掘聚类、机器学习分类和时间序列预测，并提供参数对比与实验指标。",
    }
    with REPORT_JSON.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return report


def main() -> None:
    ensure_dirs()
    rows = read_city_month_rows()
    profiles = build_city_profiles(rows)
    ranking = build_risk_ranking(profiles)
    kmeans = kmeans_analysis(profiles)
    samples, feature_names = build_supervised_dataset(rows)
    supervised = supervised_analysis(samples, feature_names)
    report = build_report(ranking, kmeans, supervised)
    print(
        json.dumps(
            {
                "status": "ok",
                "report": str(REPORT_JSON.relative_to(ROOT)),
                "top_city": ranking[0]["city"],
                "kmeans_k": report["kmeans"]["selected_k"],
                "ridge_rmse": report["supervised_learning"]["ridge_regression"]["rmse"],
                "logistic_f1": report["supervised_learning"]["logistic_regression"]["f1"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
