from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "analysis_algorithms",
    ROOT / "scripts" / "run_data_analysis_algorithms.py",
)
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYSIS
SPEC.loader.exec_module(ANALYSIS)


def sample(target_month: int) -> dict[str, object]:
    source_month = target_month - 1
    return {
        "source_month": f"2025-{source_month:02d}",
        "target_month": f"2025-{target_month:02d}",
        "features": [float(source_month)],
        "target_aqi": float(target_month),
        "target_polluted": int(target_month >= 10),
        "current_aqi": float(source_month),
    }


class AnalysisTrainingFlowTests(unittest.TestCase):
    def test_temporal_split_keeps_future_out_of_training(self) -> None:
        samples = [sample(month) for month in range(2, 13)]
        train, validation, test = ANALYSIS.temporal_train_validation_test_split(samples)

        self.assertEqual([row["target_month"] for row in train], [f"2025-{month:02d}" for month in range(2, 9)])
        self.assertEqual([row["target_month"] for row in validation], ["2025-09", "2025-10"])
        self.assertEqual([row["target_month"] for row in test], ["2025-11", "2025-12"])

    def test_temporal_split_rejects_missing_validation_period(self) -> None:
        with self.assertRaises(ValueError):
            ANALYSIS.temporal_train_validation_test_split([sample(2), sample(11)])

    def test_ridge_selection_uses_lowest_validation_error(self) -> None:
        models = {
            0.1: ([], ANALYSIS.Metrics(mae=2.0, rmse=3.0, r2=0.2), []),
            1.0: ([], ANALYSIS.Metrics(mae=1.5, rmse=2.0, r2=0.3), []),
        }
        self.assertEqual(ANALYSIS.select_best_ridge_alpha(models), 1.0)

    def test_logistic_selection_prioritizes_validation_f1_then_recall(self) -> None:
        models = {
            0.01: ([], {"f1": 0.8, "recall": 0.7, "accuracy": 0.9}, []),
            0.1: ([], {"f1": 0.8, "recall": 0.8, "accuracy": 0.85}, []),
        }
        self.assertEqual(ANALYSIS.select_best_logistic_lambda(models), 0.1)


if __name__ == "__main__":
    unittest.main()
