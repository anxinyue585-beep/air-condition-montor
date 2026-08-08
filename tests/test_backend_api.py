from __future__ import annotations

import unittest
import csv
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repository import DataRepository


class BackendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def test_health_and_overview(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        overview = self.client.get("/api/overview").json()
        self.assertEqual(overview["clean_rows"], 1_051_200)
        self.assertEqual(overview["city_count"], 60)

    def test_records_support_filters_sort_and_pagination(self) -> None:
        response = self.client.get(
            "/api/records",
            params={"city": "北京", "quarter": "Q1", "page_size": 5, "sort_key": "aqi", "sort_order": "desc"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 90)
        self.assertEqual(len(payload["items"]), 5)
        self.assertTrue(all(item["city"] == "北京" for item in payload["items"]))
        self.assertGreaterEqual(payload["items"][0]["aqi"], payload["items"][1]["aqi"])

    def test_query_validation_rejects_oversized_page(self) -> None:
        response = self.client.get("/api/records", params={"page_size": 101})
        self.assertEqual(response.status_code, 422)

    def test_analysis_and_live_endpoints(self) -> None:
        ranking = self.client.get("/api/analysis/risk-ranking", params={"limit": 3})
        self.assertEqual(ranking.status_code, 200)
        self.assertEqual(len(ranking.json()["items"]), 3)
        predictions = self.client.get("/api/analysis/predictions", params={"model": "ridge", "limit": 4})
        self.assertEqual(predictions.status_code, 200)
        self.assertEqual(len(predictions.json()["items"]), 4)
        live = self.client.get("/api/live/latest")
        self.assertEqual(live.status_code, 200)
        self.assertEqual(len(live.json()["records"]), 6)

    def test_spatial_analysis_endpoint(self) -> None:
        response = self.client.get("/api/analysis/spatial")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["method"]["year"], 2025)
        self.assertEqual(payload["method"]["city_count"], 60)
        self.assertEqual(payload["method"]["k"], 6)
        self.assertEqual(payload["method"]["permutations"], 999)
        self.assertEqual(len(payload["cities"]), 60)
        self.assertTrue(payload["global_moran"]["significant"])

    def test_pollution_warning_endpoint(self) -> None:
        response = self.client.get("/api/analysis/pollution-warning")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["city_count"], 60)
        self.assertEqual(payload["model"]["evaluation_split"] if "evaluation_split" in payload["model"] else "test", "test")
        self.assertGreater(payload["model"]["test_metrics"]["f1"], 0.8)
        filtered = self.client.get("/api/analysis/pollution-warning", params={"city": "北京"}).json()
        self.assertEqual(len(filtered["cities"]), 1)
        self.assertEqual(filtered["cities"][0]["city"], "北京")

    def test_lineage_reports_verified_platform_exports(self) -> None:
        lineage = self.client.get("/api/lineage")
        self.assertEqual(lineage.status_code, 200)
        self.assertEqual(lineage.json()["current_query_source"], "spark_export")
        self.assertEqual(lineage.json()["verification_status"], "passed")
        status = self.client.get("/api/processing/status").json()
        self.assertTrue(status["platform_export_available"])
        self.assertEqual(status["platform_manifest"]["status"], "passed")
        hive = self.client.get("/api/platform/hive/monthly").json()
        self.assertTrue(hive["available"])
        self.assertEqual(hive["source"], "hive_export")

    def test_repository_prefers_verified_spark_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "data/processed/dataset_manifest.json"
            spark_path = root / "data/platform_exports/spark/air_quality_city_day.csv"
            platform_manifest = root / "data/platform_exports/platform_run_manifest.json"
            manifest_path.parent.mkdir(parents=True)
            spark_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps({"summary": {"city_count": 1, "clean_rows": 48}, "dataset": "test", "version": "1", "generated_at": "now"}),
                encoding="utf-8",
            )
            platform_manifest.write_text(json.dumps({"status": "passed", "exported_at_utc": "now"}), encoding="utf-8")
            fields = ["city", "province", "region", "date", "record_count", "avg_aqi", "max_aqi", "good_rate", "avg_pm25", "avg_pm10", "avg_so2", "avg_no2"]
            with spark_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"city": "测试市", "province": "测试省", "region": "测试区", "date": "2026-01-01", "record_count": "48", "avg_aqi": "88", "max_aqi": "100", "good_rate": "1", "avg_pm25": "30", "avg_pm10": "50", "avg_so2": "5", "avg_no2": "10"})

            result = DataRepository(root).records(page=1, page_size=10)
            self.assertEqual(result["meta"]["querySource"], "spark_export")
            self.assertEqual(result["items"][0]["city"], "测试市")


if __name__ == "__main__":
    unittest.main()
