"""Build the course air-quality dataset.

The script is intentionally dependency-free so it can run on a normal Python
installation. It keeps a small raw seed, demonstrates cleaning on dirty raw
records, and creates a 1M+ row clean CSV for big-data coursework.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_DATASET = ROOT / "src" / "api" / "dataset.json"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
WAREHOUSE_DIR = ROOT / "data" / "warehouse"

RAW_SEED = RAW_DIR / "air_quality_seed.csv"
RAW_DIRTY = RAW_DIR / "air_quality_raw_dirty_sample.csv"
SEED_CLEAN = PROCESSED_DIR / "air_quality_seed_clean.csv"
CLEAN_CSV = PROCESSED_DIR / "air_quality_clean.csv"
FRONTEND_SAMPLE = PROCESSED_DIR / "air_quality_frontend_sample.json"
CITY_DAY = WAREHOUSE_DIR / "air_quality_city_day.csv"
CITY_MONTH = WAREHOUSE_DIR / "air_quality_city_month.csv"
REPORT = PROCESSED_DIR / "data_quality_report.json"
MANIFEST = PROCESSED_DIR / "dataset_manifest.json"


SEED_FIELDS = [
    "id",
    "city",
    "date",
    "aqi",
    "level",
    "pm25",
    "pm10",
    "so2",
    "no2",
]

FULL_FIELDS = [
    "record_id",
    "city",
    "province",
    "region",
    "station_id",
    "station_name",
    "datetime",
    "date",
    "hour",
    "year_month",
    "aqi",
    "level",
    "primary_pollutant",
    "pm25",
    "pm10",
    "so2",
    "no2",
    "co",
    "o3",
    "temperature",
    "humidity",
    "wind_speed",
    "source",
]

CITY_FIELDS = [
    "city",
    "province",
    "region",
    "date",
    "record_count",
    "avg_aqi",
    "max_aqi",
    "good_rate",
    "avg_pm25",
    "avg_pm10",
    "avg_so2",
    "avg_no2",
]

MONTH_FIELDS = [
    "city",
    "province",
    "region",
    "year_month",
    "record_count",
    "avg_aqi",
    "max_aqi",
    "good_rate",
    "avg_pm25",
    "avg_pm10",
    "avg_so2",
    "avg_no2",
]


CITY_PROFILES = [
    ("北京", "北京市", "华北", 82),
    ("天津", "天津市", "华北", 78),
    ("石家庄", "河北省", "华北", 104),
    ("太原", "山西省", "华北", 92),
    ("呼和浩特", "内蒙古自治区", "华北", 74),
    ("上海", "上海市", "华东", 58),
    ("南京", "江苏省", "华东", 71),
    ("杭州", "浙江省", "华东", 62),
    ("宁波", "浙江省", "华东", 55),
    ("合肥", "安徽省", "华东", 68),
    ("福州", "福建省", "华东", 49),
    ("厦门", "福建省", "华东", 43),
    ("南昌", "江西省", "华东", 64),
    ("济南", "山东省", "华东", 88),
    ("青岛", "山东省", "华东", 57),
    ("郑州", "河南省", "华中", 96),
    ("武汉", "湖北省", "华中", 72),
    ("长沙", "湖南省", "华中", 66),
    ("广州", "广东省", "华南", 54),
    ("深圳", "广东省", "华南", 50),
    ("珠海", "广东省", "华南", 45),
    ("佛山", "广东省", "华南", 63),
    ("南宁", "广西壮族自治区", "华南", 52),
    ("海口", "海南省", "华南", 38),
    ("重庆", "重庆市", "西南", 76),
    ("成都", "四川省", "西南", 84),
    ("贵阳", "贵州省", "西南", 47),
    ("昆明", "云南省", "西南", 44),
    ("拉萨", "西藏自治区", "西南", 36),
    ("西安", "陕西省", "西北", 93),
    ("兰州", "甘肃省", "西北", 86),
    ("西宁", "青海省", "西北", 59),
    ("银川", "宁夏回族自治区", "西北", 72),
    ("乌鲁木齐", "新疆维吾尔自治区", "西北", 97),
    ("沈阳", "辽宁省", "东北", 79),
    ("大连", "辽宁省", "东北", 53),
    ("长春", "吉林省", "东北", 75),
    ("哈尔滨", "黑龙江省", "东北", 81),
    ("苏州", "江苏省", "华东", 59),
    ("无锡", "江苏省", "华东", 61),
    ("常州", "江苏省", "华东", 65),
    ("温州", "浙江省", "华东", 51),
    ("绍兴", "浙江省", "华东", 58),
    ("金华", "浙江省", "华东", 56),
    ("泉州", "福建省", "华东", 50),
    ("烟台", "山东省", "华东", 60),
    ("潍坊", "山东省", "华东", 78),
    ("洛阳", "河南省", "华中", 89),
    ("宜昌", "湖北省", "华中", 58),
    ("株洲", "湖南省", "华中", 70),
    ("东莞", "广东省", "华南", 57),
    ("中山", "广东省", "华南", 52),
    ("惠州", "广东省", "华南", 49),
    ("桂林", "广西壮族自治区", "华南", 45),
    ("绵阳", "四川省", "西南", 63),
    ("遵义", "贵州省", "西南", 50),
    ("大理", "云南省", "西南", 39),
    ("宝鸡", "陕西省", "西北", 76),
    ("嘉峪关", "甘肃省", "西北", 68),
    ("齐齐哈尔", "黑龙江省", "东北", 73),
]


def ensure_dirs() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, WAREHOUSE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_app_seed() -> list[dict[str, Any]]:
    with SRC_DATASET.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def write_seed_csv(rows: list[dict[str, Any]]) -> None:
    with RAW_SEED.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SEED_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in SEED_FIELDS})


def write_dirty_sample(rows: list[dict[str, Any]]) -> dict[str, int]:
    dirty_rows = []
    for row in rows:
        dirty_rows.append({field: row[field] for field in SEED_FIELDS})

    duplicate = dict(dirty_rows[0])
    dirty_rows.append(duplicate)

    missing_pm = dict(dirty_rows[1])
    missing_pm["id"] = "AQ-DIRTY-MISSING-PM25"
    missing_pm["pm25"] = ""
    dirty_rows.append(missing_pm)

    missing_aqi = dict(dirty_rows[2])
    missing_aqi["id"] = "AQ-DIRTY-MISSING-AQI"
    missing_aqi["aqi"] = ""
    dirty_rows.append(missing_aqi)

    negative_pm10 = dict(dirty_rows[3])
    negative_pm10["id"] = "AQ-DIRTY-NEGATIVE-PM10"
    negative_pm10["pm10"] = "-9"
    dirty_rows.append(negative_pm10)

    outlier = dict(dirty_rows[4])
    outlier["id"] = "AQ-DIRTY-AQI-OUTLIER"
    outlier["aqi"] = "999"
    dirty_rows.append(outlier)

    with RAW_DIRTY.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SEED_FIELDS)
        writer.writeheader()
        writer.writerows(dirty_rows)

    return {
        "raw_rows": len(dirty_rows),
        "duplicate_rows_added": 1,
        "missing_rows_added": 2,
        "negative_rows_added": 1,
        "outlier_rows_added": 1,
    }


def as_number(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def aqi_level(aqi: float) -> str:
    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    return "污染"


def primary_pollutant(row: dict[str, Any]) -> str:
    values = {
        "PM2.5": row["pm25"] / 75,
        "PM10": row["pm10"] / 150,
        "SO2": row["so2"] / 150,
        "NO2": row["no2"] / 80,
        "O3": row.get("o3", 0) / 160,
        "CO": row.get("co", 0) / 4,
    }
    return max(values.items(), key=lambda item: item[1])[0]


def clean_dirty_seed() -> tuple[list[dict[str, Any]], dict[str, int]]:
    with RAW_DIRTY.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    numeric_fields = ["aqi", "pm25", "pm10", "so2", "no2"]
    medians: dict[tuple[str, str], float] = {}
    global_medians: dict[str, float] = {}

    for field in numeric_fields:
        values = [as_number(row[field]) for row in rows]
        valid_values = [value for value in values if value is not None and value >= 0]
        global_medians[field] = median(valid_values)
        for city in {row["city"] for row in rows}:
            city_values = [
                as_number(row[field])
                for row in rows
                if row["city"] == city and as_number(row[field]) is not None and as_number(row[field]) >= 0
            ]
            medians[(city, field)] = median(city_values) if city_values else global_medians[field]

    seen = set()
    cleaned: list[dict[str, Any]] = []
    stats = defaultdict(int)

    for row in rows:
        key = (row["city"], row["date"], row["id"])
        if key in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(key)

        clean_row = dict(row)
        for field in numeric_fields:
            value = as_number(clean_row[field])
            if value is None:
                value = medians[(clean_row["city"], field)]
                stats["missing_values_filled"] += 1
            if value < 0:
                value = 0
                stats["negative_values_fixed"] += 1
            if field == "aqi" and value > 500:
                value = 500
                stats["outliers_capped"] += 1
            clean_row[field] = int(round(value))

        if as_number(row.get("aqi")) is None:
            clean_row["aqi"] = int(round(clean_row["pm25"] * 1.25))
        clean_row["level"] = aqi_level(clean_row["aqi"])
        cleaned.append(clean_row)

    with SEED_CLEAN.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SEED_FIELDS)
        writer.writeheader()
        writer.writerows(cleaned)

    stats["clean_rows"] = len(cleaned)
    return cleaned, dict(stats)


def deterministic_noise(city_index: int, station_index: int, hour_index: int, scale: float) -> float:
    return (
        math.sin((hour_index + 1) * (city_index + 3) * 0.017) * scale
        + math.cos((hour_index + 5) * (station_index + 2) * 0.071) * scale * 0.45
    )


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def add_metric(bucket: dict[str, Any], row: dict[str, Any]) -> None:
    bucket["count"] += 1
    bucket["sum_aqi"] += row["aqi"]
    bucket["max_aqi"] = max(bucket["max_aqi"], row["aqi"])
    bucket["good_count"] += 1 if row["aqi"] <= 100 else 0
    for field in ("pm25", "pm10", "so2", "no2"):
        bucket[f"sum_{field}"] += row[field]


def empty_bucket(city: str, province: str, region: str, period: str) -> dict[str, Any]:
    return {
        "city": city,
        "province": province,
        "region": region,
        "period": period,
        "count": 0,
        "sum_aqi": 0,
        "max_aqi": 0,
        "good_count": 0,
        "sum_pm25": 0,
        "sum_pm10": 0,
        "sum_so2": 0,
        "sum_no2": 0,
    }


def bucket_to_row(bucket: dict[str, Any], period_name: str) -> dict[str, Any]:
    count = max(1, bucket["count"])
    return {
        "city": bucket["city"],
        "province": bucket["province"],
        "region": bucket["region"],
        period_name: bucket["period"],
        "record_count": bucket["count"],
        "avg_aqi": round(bucket["sum_aqi"] / count, 2),
        "max_aqi": bucket["max_aqi"],
        "good_rate": round(bucket["good_count"] / count, 4),
        "avg_pm25": round(bucket["sum_pm25"] / count, 2),
        "avg_pm10": round(bucket["sum_pm10"] / count, 2),
        "avg_so2": round(bucket["sum_so2"] / count, 2),
        "avg_no2": round(bucket["sum_no2"] / count, 2),
    }


def generate_big_dataset() -> dict[str, Any]:
    city_day = {}
    city_month = {}
    city_dates_for_frontend: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    level_counts = defaultdict(int)
    region_counts = defaultdict(int)
    pollutant_counts = defaultdict(int)

    start = datetime(2025, 1, 1, 0, 0, 0)
    hours = 365 * 24
    station_count = 2
    total_rows = 0

    with CLEAN_CSV.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FULL_FIELDS)
        writer.writeheader()

        for hour_index in range(hours):
            current = start + timedelta(hours=hour_index)
            date = current.date().isoformat()
            year_month = current.strftime("%Y-%m")
            hour = current.hour
            day_of_year = current.timetuple().tm_yday
            month = current.month

            for city_index, (city, province, region, base_aqi) in enumerate(CITY_PROFILES, start=1):
                region_factor = {
                    "华北": 1.13,
                    "华东": 0.92,
                    "华中": 1.02,
                    "华南": 0.78,
                    "西南": 0.86,
                    "西北": 1.06,
                    "东北": 1.0,
                }[region]
                seasonal = math.cos((day_of_year - 15) / 365 * math.tau) * 18
                rush_hour = 8 if hour in (7, 8, 18, 19) else 0
                weekend_relief = -5 if current.weekday() >= 5 else 0

                for station_index in range(1, station_count + 1):
                    station_shift = (station_index - 1.5) * 6
                    noise = deterministic_noise(city_index, station_index, hour_index, 7.5)
                    aqi = int(round(clamp((base_aqi + seasonal + rush_hour + weekend_relief + station_shift + noise) * region_factor, 18, 260)))
                    pm25 = int(round(clamp(aqi * 0.62 + deterministic_noise(city_index, station_index, hour_index + 11, 3.2), 5, 210)))
                    pm10 = int(round(clamp(aqi * 1.05 + deterministic_noise(city_index, station_index, hour_index + 23, 6.5), 10, 320)))
                    so2 = int(round(clamp(aqi * 0.08 + station_index + month % 3, 2, 80)))
                    no2 = int(round(clamp(aqi * 0.21 + rush_hour * 0.7 + deterministic_noise(city_index, station_index, hour_index + 29, 1.7), 6, 120)))
                    co = round(clamp(aqi / 85 + station_index * 0.08 + deterministic_noise(city_index, station_index, hour_index + 41, 0.05), 0.2, 6), 2)
                    o3 = int(round(clamp(118 - aqi * 0.18 + math.sin((hour - 14) / 24 * math.tau) * 28 + month * 1.4, 20, 220)))
                    temperature = round(clamp(14 + math.sin((day_of_year - 80) / 365 * math.tau) * 15 + math.sin(hour / 24 * math.tau) * 5, -18, 40), 1)
                    humidity = int(round(clamp(58 + math.cos((day_of_year - 20) / 365 * math.tau) * 15 - temperature * 0.4, 18, 95)))
                    wind_speed = round(clamp(2.1 + math.sin(hour_index * 0.031 + city_index) * 1.2 + station_index * 0.2, 0.2, 9.5), 1)

                    row = {
                        "record_id": f"AQ2025-{city_index:03d}-{station_index}-{hour_index + 1:05d}",
                        "city": city,
                        "province": province,
                        "region": region,
                        "station_id": f"{city_index:03d}-{station_index}",
                        "station_name": f"{city}监测点{station_index}",
                        "datetime": current.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": date,
                        "hour": hour,
                        "year_month": year_month,
                        "aqi": aqi,
                        "level": aqi_level(aqi),
                        "primary_pollutant": "",
                        "pm25": pm25,
                        "pm10": pm10,
                        "so2": so2,
                        "no2": no2,
                        "co": co,
                        "o3": o3,
                        "temperature": temperature,
                        "humidity": humidity,
                        "wind_speed": wind_speed,
                        "source": "course_reproducible_dataset_based_on_open_air_quality_schema",
                    }
                    row["primary_pollutant"] = primary_pollutant(row)
                    writer.writerow(row)

                    day_key = (city, date)
                    if day_key not in city_day:
                        city_day[day_key] = empty_bucket(city, province, region, date)
                    add_metric(city_day[day_key], row)

                    month_key = (city, year_month)
                    if month_key not in city_month:
                        city_month[month_key] = empty_bucket(city, province, region, year_month)
                    add_metric(city_month[month_key], row)

                    if len(city_dates_for_frontend[city]) < 42:
                        if date not in city_dates_for_frontend[city]:
                            city_dates_for_frontend[city][date] = empty_bucket(city, province, region, date)
                        add_metric(city_dates_for_frontend[city][date], row)

                    level_counts[row["level"]] += 1
                    region_counts[region] += 1
                    pollutant_counts[row["primary_pollutant"]] += 1
                    total_rows += 1

    with CITY_DAY.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CITY_FIELDS)
        writer.writeheader()
        for key in sorted(city_day):
            writer.writerow(bucket_to_row(city_day[key], "date"))

    with CITY_MONTH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MONTH_FIELDS)
        writer.writeheader()
        for key in sorted(city_month):
            writer.writerow(bucket_to_row(city_month[key], "year_month"))

    frontend_rows = build_frontend_sample(city_dates_for_frontend)
    with FRONTEND_SAMPLE.open("w", encoding="utf-8") as file:
        json.dump(frontend_rows, file, ensure_ascii=False, indent=2)
        file.write("\n")

    return {
        "clean_rows": total_rows,
        "city_count": len(CITY_PROFILES),
        "station_count": len(CITY_PROFILES) * station_count,
        "date_range": ["2025-01-01", "2025-12-31"],
        "level_counts": dict(level_counts),
        "region_counts": dict(region_counts),
        "primary_pollutant_counts": dict(pollutant_counts),
        "city_day_rows": len(city_day),
        "city_month_rows": len(city_month),
        "frontend_sample_rows": len(frontend_rows),
    }


def build_frontend_sample(city_dates: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    selected_cities = [item[0] for item in CITY_PROFILES[:12]]
    seq = 1

    for city in selected_cities:
        day_rows = [bucket_to_row(bucket, "date") for _, bucket in sorted(city_dates[city].items())]
        pm25_window: deque[int] = deque(maxlen=7)
        for day in day_rows:
            pm25 = int(round(day["avg_pm25"]))
            pm25_window.append(pm25)
            trend = list(pm25_window)
            if len(trend) < 7:
                trend = [trend[0]] * (7 - len(trend)) + trend
            aqi = int(round(day["avg_aqi"]))
            rows.append(
                {
                    "id": f"AQ-{5000 + seq:04d}",
                    "city": city,
                    "date": day["date"],
                    "aqi": aqi,
                    "level": aqi_level(aqi),
                    "pm25": pm25,
                    "pm10": int(round(day["avg_pm10"])),
                    "so2": int(round(day["avg_so2"])),
                    "no2": int(round(day["avg_no2"])),
                    "trend": trend,
                }
            )
            seq += 1

    return rows


def write_source_catalog() -> None:
    catalog = {
        "dataset_name": "城市空气质量小时级实验数据集",
        "base_sources": [
            {
                "name": "Beijing Multi-Site Air-Quality Data (UCI Machine Learning Repository)",
                "url": "https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data",
                "usage": "作为公开空气质量小时级字段结构、站点粒度和缺失值清洗流程参考。",
            },
            {
                "name": "环境空气质量指数(AQI)技术规定 HJ 633-2012",
                "url": "https://www.mee.gov.cn/",
                "usage": "作为 AQI 等级划分、污染物字段和指标解释依据。",
            },
        ],
        "project_seed": "src/api/dataset.json",
        "generated_scope": "2025 年 60 个城市、120 个监测点、逐小时记录。",
        "note": "课程环境未依赖外部数据库，完整数据由脚本按公开空气质量字段结构和项目样本可复现生成；后续可将真实下载数据替换到 raw 层后复用同一清洗流程。",
    }
    with (RAW_DIR / "source_catalog.json").open("w", encoding="utf-8") as file:
        json.dump(catalog, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_reports(seed_stats: dict[str, int], clean_stats: dict[str, int], big_stats: dict[str, Any]) -> None:
    quality_report = {
        "raw_dirty_sample": seed_stats,
        "cleaning_actions": clean_stats,
        "large_dataset": big_stats,
        "checks": {
            "row_count_meets_big_data_requirement": big_stats["clean_rows"] >= 1_000_000,
            "has_missing_values_after_cleaning": False,
            "aqi_range": "18-260",
            "storage_outputs": [
                str(CLEAN_CSV.relative_to(ROOT)),
                str(CITY_DAY.relative_to(ROOT)),
                str(CITY_MONTH.relative_to(ROOT)),
                str(FRONTEND_SAMPLE.relative_to(ROOT)),
            ],
        },
    }
    with REPORT.open("w", encoding="utf-8") as file:
        json.dump(quality_report, file, ensure_ascii=False, indent=2)
        file.write("\n")

    manifest = {
        "dataset": "air_quality_clean",
        "version": "2026-06-30",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": {
            "raw_seed": str(RAW_SEED.relative_to(ROOT)),
            "raw_dirty_sample": str(RAW_DIRTY.relative_to(ROOT)),
            "clean_seed": str(SEED_CLEAN.relative_to(ROOT)),
            "clean_full_csv": str(CLEAN_CSV.relative_to(ROOT)),
            "city_day_warehouse": str(CITY_DAY.relative_to(ROOT)),
            "city_month_warehouse": str(CITY_MONTH.relative_to(ROOT)),
            "frontend_sample": str(FRONTEND_SAMPLE.relative_to(ROOT)),
            "quality_report": str(REPORT.relative_to(ROOT)),
        },
        "summary": big_stats,
    }
    with MANIFEST.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    ensure_dirs()
    seed_rows = load_app_seed()
    write_seed_csv(seed_rows)
    seed_stats = write_dirty_sample(seed_rows)
    _, clean_stats = clean_dirty_seed()
    big_stats = generate_big_dataset()
    write_source_catalog()
    write_reports(seed_stats, clean_stats, big_stats)
    print(json.dumps({"status": "ok", "summary": big_stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
