from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]


class FileCache:
    """Small mtime-aware cache so scheduled data updates become visible."""

    def __init__(self) -> None:
        self._entries: dict[Path, tuple[int, Any]] = {}
        self._lock = RLock()

    def load(self, path: Path, loader: Callable[[Path], Any]) -> Any:
        if not path.exists():
            raise FileNotFoundError(path)
        mtime = path.stat().st_mtime_ns
        with self._lock:
            cached = self._entries.get(path)
            if cached and cached[0] == mtime:
                return cached[1]
            value = loader(path)
            self._entries[path] = (mtime, value)
            return value


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def aqi_level(aqi: float) -> str:
    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    return "污染"


class DataRepository:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self.cache = FileCache()
        self.manifest_path = root / "data" / "processed" / "dataset_manifest.json"
        self.city_day_path = root / "data" / "warehouse" / "air_quality_city_day.csv"
        self.spark_city_day_path = root / "data" / "platform_exports" / "spark" / "air_quality_city_day.csv"
        self.spark_city_month_path = root / "data" / "platform_exports" / "spark" / "air_quality_city_month.csv"
        self.hive_city_month_path = root / "data" / "platform_exports" / "hive" / "air_quality_city_month.csv"
        self.platform_manifest_path = root / "data" / "platform_exports" / "platform_run_manifest.json"
        self.verification_root = root / "reports" / "platform_verification"
        self.risk_path = root / "data" / "analysis_results" / "city_risk_ranking.csv"
        self.ridge_path = root / "data" / "analysis_results" / "aqi_prediction_predictions.csv"
        self.logistic_path = root / "data" / "analysis_results" / "logistic_predictions.csv"
        self.spatial_path = root / "data" / "analysis_results" / "spatial_analysis_2025.json"
        self.warning_path = root / "data" / "warning_results" / "pollution_warning_model.json"
        self.live_latest_path = root / "data" / "live" / "open_meteo_latest.json"
        self.live_history_path = root / "data" / "live" / "open_meteo_observations.csv"

    def _json(self, path: Path) -> Any:
        return self.cache.load(path, load_json)

    def _csv(self, path: Path) -> list[dict[str, str]]:
        return self.cache.load(path, load_csv)

    def health(self) -> dict[str, Any]:
        files = {
            "manifest": self.manifest_path,
            "city_day": self.city_day_path,
            "risk_ranking": self.risk_path,
            "ridge_predictions": self.ridge_path,
            "logistic_predictions": self.logistic_path,
            "spatial_analysis": self.spatial_path,
            "pollution_warning": self.warning_path,
            "live_latest": self.live_latest_path,
            "spark_export": self.spark_city_day_path,
            "hive_export": self.hive_city_month_path,
        }
        availability = {name: path.exists() for name, path in files.items()}
        return {
            "status": "ok" if all(availability[name] for name in ["manifest", "city_day", "risk_ranking", "ridge_predictions", "logistic_predictions", "live_latest"]) else "degraded",
            "files": availability,
        }

    @staticmethod
    def _modified_at(path: Path) -> str | None:
        if not path.exists():
            return None
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")

    def _city_day_source(self) -> tuple[Path, str]:
        if self.spark_city_day_path.exists() and self.platform_manifest_path.exists():
            manifest = self._json(self.platform_manifest_path)
            if manifest.get("status") == "passed":
                return self.spark_city_day_path, "spark_export"
        return self.city_day_path, "local_warehouse_fallback"

    def _latest_verification(self) -> dict[str, Any] | None:
        if not self.verification_root.exists():
            return None
        summaries = sorted(self.verification_root.glob("*/verification-summary.json"), reverse=True)
        return self._json(summaries[0]) if summaries else None

    def overview(self) -> dict[str, Any]:
        manifest = self._json(self.manifest_path)
        summary = manifest["summary"]
        return {
            "dataset": manifest["dataset"],
            "version": manifest["version"],
            "generated_at": manifest["generated_at"],
            "clean_rows": summary["clean_rows"],
            "city_count": summary["city_count"],
            "station_count": summary["station_count"],
            "date_range": summary["date_range"],
            "city_day_rows": summary["city_day_rows"],
            "city_month_rows": summary["city_month_rows"],
            "data_source": "generated_experiment_dataset",
            "query_source": self._city_day_source()[1],
        }

    def cities(self) -> list[str]:
        source_path, _ = self._city_day_source()
        return sorted({row["city"] for row in self._csv(source_path)})

    @staticmethod
    def _record(row: dict[str, str]) -> dict[str, Any]:
        aqi = round(float(row["avg_aqi"]))
        return {
            "id": f"AQD-{row['date']}-{row['city']}",
            "city": row["city"],
            "date": row["date"],
            "aqi": aqi,
            "level": aqi_level(aqi),
            "pm25": round(float(row["avg_pm25"])),
            "pm10": round(float(row["avg_pm10"])),
            "so2": round(float(row["avg_so2"])),
            "no2": round(float(row["avg_no2"])),
            "trend": [],
            "region": row["region"],
            "province": row["province"],
            "record_count": int(float(row["record_count"])),
            "good_rate": float(row["good_rate"]),
        }

    def records(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str = "",
        city: str = "",
        level: str = "",
        quarter: str = "",
        sort_key: str = "date",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        source_path, source_name = self._city_day_source()
        records = [self._record(row) for row in self._csv(source_path)]
        query = keyword.strip().casefold()
        if query:
            records = [
                row
                for row in records
                if query in row["id"].casefold()
                or query in row["city"].casefold()
                or query in row["date"].casefold()
            ]
        if city:
            records = [row for row in records if row["city"] == city]
        if level:
            records = [row for row in records if row["level"] == level]
        if quarter:
            bounds = {"Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12)}
            start_month, end_month = bounds[quarter]
            records = [row for row in records if start_month <= int(row["date"][5:7]) <= end_month]

        records.sort(key=lambda row: row[sort_key], reverse=sort_order == "desc")
        total = len(records)
        start = (page - 1) * page_size
        items = records[start : start + page_size]
        manifest = self._json(self.manifest_path)["summary"]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "meta": {
                "latestDate": max((row["date"] for row in records), default="-"),
                "cityCount": manifest["city_count"],
                "totalRecords": manifest["clean_rows"],
                "queryGranularity": "city_day",
                "querySource": source_name,
                "sourceUpdatedAt": self._modified_at(source_path),
            },
        }

    def processing_status(self) -> dict[str, Any]:
        verification = self._latest_verification()
        platform_manifest = self._json(self.platform_manifest_path) if self.platform_manifest_path.exists() else None
        source_path, source_name = self._city_day_source()
        return {
            "current_query_source": source_name,
            "current_query_updated_at": self._modified_at(source_path),
            "platform_export_available": source_name == "spark_export",
            "platform_manifest": platform_manifest,
            "latest_platform_verification": verification,
            "open_meteo": {
                "available": self.live_latest_path.exists(),
                "updated_at": self._modified_at(self.live_latest_path),
            },
        }

    def lineage(self) -> dict[str, Any]:
        status = self.processing_status()
        platform_ready = status["platform_export_available"]
        verification = status["latest_platform_verification"] or {}
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "current_query_source": status["current_query_source"],
            "nodes": [
                {"id": "source", "label": "数据源", "detail": "实验数据 + Open-Meteo", "status": "passed"},
                {"id": "processed", "label": "清洗与仓库", "detail": "1,051,200小时记录 / 21,900城市日", "status": "passed"},
                {"id": "hdfs", "label": "HDFS", "detail": "百万级CSV存储", "status": "passed" if platform_ready else "pending"},
                {"id": "hive", "label": "Hive", "detail": "城市月度SQL输出", "status": "passed" if self.hive_city_month_path.exists() else "pending"},
                {"id": "spark", "label": "Spark", "detail": "城市日/月ETL导出", "status": "passed" if platform_ready else "pending"},
                {"id": "backend", "label": "FastAPI", "detail": f"查询源：{status['current_query_source']}", "status": "passed"},
                {"id": "frontend", "label": "Vue可视化", "detail": "分页、血缘与处理状态", "status": "passed"},
            ],
            "edges": [
                ["source", "processed"], ["processed", "hdfs"], ["hdfs", "hive"], ["hdfs", "spark"],
                ["hive", "backend"], ["spark", "backend"], ["processed", "backend"], ["backend", "frontend"],
            ],
            "last_verified_at": verification.get("completed_at_utc"),
            "verification_status": verification.get("status", "not_run"),
            "verification_message": verification.get("message", "No platform verification record"),
        }

    def hive_monthly(self, city: str, limit: int) -> dict[str, Any]:
        if not self.hive_city_month_path.exists():
            return {"available": False, "source": "hive_export", "updated_at": None, "items": [], "total": 0}
        rows = self._csv(self.hive_city_month_path)
        if city:
            rows = [row for row in rows if row["city"] == city]
        return {
            "available": True,
            "source": "hive_export",
            "updated_at": self._modified_at(self.hive_city_month_path),
            "items": rows[:limit],
            "total": len(rows),
        }

    def risk_ranking(self, limit: int) -> list[dict[str, Any]]:
        rows = self._csv(self.risk_path)[:limit]
        numeric_fields = {"rank": int, "risk_score": float, "avg_aqi": float, "max_aqi": float, "polluted_rate": float, "avg_pm25": float}
        result: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = dict(row)
            for field, converter in numeric_fields.items():
                item[field] = converter(row[field])
            result.append(item)
        return result

    def predictions(self, model: str, city: str, limit: int) -> list[dict[str, Any]]:
        path = self.ridge_path if model == "ridge" else self.logistic_path
        rows = self._csv(path)
        if city:
            rows = [row for row in rows if row["city"] == city]
        return rows[:limit]

    def spatial_analysis(self) -> dict[str, Any]:
        return self._json(self.spatial_path)

    def pollution_warning(self, city: str = "") -> dict[str, Any]:
        payload = self._json(self.warning_path)
        if not city:
            return payload
        matched = [item for item in payload["cities"] if item["city"] == city]
        return {**payload, "cities": matched, "summary": {**payload["summary"], "filtered_city": city}}

    def live_latest(self) -> dict[str, Any]:
        return self._json(self.live_latest_path)

    def live_history(self, page: int, page_size: int, city: str) -> dict[str, Any]:
        rows = self._csv(self.live_history_path)
        if city:
            rows = [row for row in rows if row["city"] == city]
        rows.sort(key=lambda row: (row["weather_observed_at"], row["city_code"]), reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        return {"items": rows[start : start + page_size], "total": total, "page": page, "page_size": page_size}
