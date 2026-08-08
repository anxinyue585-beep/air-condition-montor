from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("open_meteo_ingest", ROOT / "scripts" / "fetch_open_meteo_daily.py")
assert SPEC and SPEC.loader
INGEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INGEST)


CITY = {
    "code": "beijing",
    "city": "北京",
    "province": "北京市",
    "latitude": 39.9042,
    "longitude": 116.4074,
}
WEATHER = {
    "latitude": 39.9,
    "longitude": 116.4,
    "current": {
        "time": "2026-07-11T12:00",
        "temperature_2m": 31.2,
        "relative_humidity_2m": 48,
        "precipitation": 0.0,
        "weather_code": 1,
        "wind_speed_10m": 8.1,
        "wind_direction_10m": 180,
        "surface_pressure": 999.4,
    },
}
AIR = {
    "latitude": 40.0,
    "longitude": 116.5,
    "current": {
        "time": "2026-07-11T12:00",
        "european_aqi": 72,
        "us_aqi": 88,
        "pm10": 38.2,
        "pm2_5": 26.4,
        "carbon_monoxide": 210.0,
        "nitrogen_dioxide": 17.1,
        "sulphur_dioxide": 4.2,
        "ozone": 91.0,
    },
}


class OpenMeteoIngestTests(unittest.TestCase):
    def test_normalizes_weather_and_air_quality(self) -> None:
        row = INGEST.normalized_record(
            CITY,
            WEATHER,
            AIR,
            "2026-07-11T04:01:00+00:00",
            "weather.json",
            "air.json",
        )
        self.assertEqual(row["city"], "北京")
        self.assertEqual(row["data_kind"], "forecast_model_current")
        self.assertEqual(row["temperature_c"], 31.2)
        self.assertEqual(row["pm25_ug_m3"], 26.4)
        self.assertEqual(len(row["raw_sha256"]), 64)

    def test_rejects_missing_required_pollutant(self) -> None:
        bad_air = {**AIR, "current": {**AIR["current"], "pm2_5": None}}
        with self.assertRaises(INGEST.IngestionError):
            INGEST.normalized_record(CITY, WEATHER, bad_air, "now", "weather.json", "air.json")

    def test_csv_upsert_is_idempotent(self) -> None:
        row = INGEST.normalized_record(CITY, WEATHER, AIR, "first", "weather.json", "air.json")
        updated = {**row, "fetched_at_utc": "second"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.csv"
            self.assertEqual(INGEST.upsert_csv(path, [row]), 1)
            self.assertEqual(INGEST.upsert_csv(path, [updated]), 1)
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]["fetched_at_utc"], "second")
            self.assertEqual(INGEST.count_csv_rows(path), 1)

    def test_count_csv_rows_returns_zero_for_missing_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(INGEST.count_csv_rows(Path(directory) / "missing.csv"), 0)

    def test_city_urls_use_shanghai_timezone_and_cams_global(self) -> None:
        weather_url, air_url = INGEST.build_urls(CITY)
        self.assertIn("timezone=Asia%2FShanghai", weather_url)
        self.assertIn("domains=cams_global", air_url)


if __name__ == "__main__":
    unittest.main()
