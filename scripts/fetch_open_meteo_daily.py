"""Fetch current weather and modelled air-quality data from Open-Meteo.

The script is dependency-free and designed for both local execution and a
scheduled GitHub Actions job. Raw provider responses are archived locally,
while normalized observations are upserted into a small tracked CSV and a
frontend-friendly latest snapshot.

Open-Meteo air-quality values come from CAMS atmospheric models. They are not
ground-monitoring-station measurements and must not be described as such.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "open_meteo_cities.json"
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "open_meteo"
DEFAULT_CSV = ROOT / "data" / "live" / "open_meteo_observations.csv"
DEFAULT_LATEST = ROOT / "data" / "live" / "open_meteo_latest.json"
DEFAULT_REPORT = ROOT / "data" / "live" / "open_meteo_run_report.json"

WEATHER_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_ENDPOINT = "https://air-quality-api.open-meteo.com/v1/air-quality"
LOCAL_TIMEZONE = "Asia/Shanghai"
SCHEMA_VERSION = "1.0"

WEATHER_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]
AIR_QUALITY_VARIABLES = [
    "european_aqi",
    "us_aqi",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
]

CSV_FIELDS = [
    "schema_version",
    "source",
    "data_kind",
    "city_code",
    "city",
    "province",
    "requested_latitude",
    "requested_longitude",
    "weather_grid_latitude",
    "weather_grid_longitude",
    "air_quality_grid_latitude",
    "air_quality_grid_longitude",
    "weather_observed_at",
    "air_quality_observed_at",
    "fetched_at_utc",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "weather_code_wmo",
    "wind_speed_kmh",
    "wind_direction_deg",
    "surface_pressure_hpa",
    "european_aqi",
    "us_aqi",
    "pm10_ug_m3",
    "pm25_ug_m3",
    "co_ug_m3",
    "no2_ug_m3",
    "so2_ug_m3",
    "o3_ug_m3",
    "raw_sha256",
    "raw_weather_path",
    "raw_air_quality_path",
]


class IngestionError(RuntimeError):
    """Raised when provider data cannot be safely normalized."""


def build_urls(city: dict[str, Any]) -> tuple[str, str]:
    common = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "timezone": LOCAL_TIMEZONE,
    }
    weather_query = {
        **common,
        "current": ",".join(WEATHER_VARIABLES),
    }
    air_query = {
        **common,
        "current": ",".join(AIR_QUALITY_VARIABLES),
        "domains": "cams_global",
    }
    return (
        f"{WEATHER_ENDPOINT}?{urlencode(weather_query)}",
        f"{AIR_QUALITY_ENDPOINT}?{urlencode(air_query)}",
    )


def fetch_json(url: str, timeout: float, max_retries: int) -> dict[str, Any]:
    last_error: Exception | None = None
    request = Request(url, headers={"User-Agent": "air-quality-course-project/1.0"})
    for attempt in range(max_retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise IngestionError("provider response is not a JSON object")
            if payload.get("error"):
                raise IngestionError(str(payload.get("reason", "provider returned an error")))
            return payload
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, IngestionError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(2**attempt)
    raise IngestionError(f"request failed after {max_retries + 1} attempts: {last_error}")


def load_cities(path: Path, selected_codes: set[str] | None = None) -> list[dict[str, Any]]:
    cities = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cities, list) or not cities:
        raise IngestionError("city configuration must be a non-empty JSON array")

    required = {"code", "city", "province", "latitude", "longitude"}
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for city in cities:
        if not isinstance(city, dict) or not required.issubset(city):
            raise IngestionError(f"invalid city configuration: {city!r}")
        code = str(city["code"])
        if code in seen:
            raise IngestionError(f"duplicate city code: {code}")
        seen.add(code)
        if selected_codes is None or code in selected_codes:
            result.append(city)

    if selected_codes:
        missing = selected_codes - {str(city["code"]) for city in result}
        if missing:
            raise IngestionError(f"unknown city codes: {', '.join(sorted(missing))}")
    if not result:
        raise IngestionError("no cities selected")
    return result


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def archive_raw(path: Path, payload: dict[str, Any]) -> None:
    write_json_atomic(path, payload)


def require_current(payload: dict[str, Any], label: str) -> dict[str, Any]:
    current = payload.get("current")
    if not isinstance(current, dict) or not current.get("time"):
        raise IngestionError(f"{label} response has no usable current data")
    return current


def numeric(current: dict[str, Any], key: str, required: bool = False) -> int | float | None:
    value = current.get(key)
    if value is None:
        if required:
            raise IngestionError(f"missing required field: {key}")
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IngestionError(f"field {key} is not numeric: {value!r}")
    return value


def normalized_record(
    city: dict[str, Any],
    weather: dict[str, Any],
    air_quality: dict[str, Any],
    fetched_at_utc: str,
    raw_weather_path: str,
    raw_air_path: str,
) -> dict[str, Any]:
    weather_current = require_current(weather, "weather")
    air_current = require_current(air_quality, "air-quality")

    digest_payload = json.dumps(
        {"weather": weather, "air_quality": air_quality},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    record = {
        "schema_version": SCHEMA_VERSION,
        "source": "open-meteo",
        "data_kind": "forecast_model_current",
        "city_code": city["code"],
        "city": city["city"],
        "province": city["province"],
        "requested_latitude": city["latitude"],
        "requested_longitude": city["longitude"],
        "weather_grid_latitude": weather.get("latitude"),
        "weather_grid_longitude": weather.get("longitude"),
        "air_quality_grid_latitude": air_quality.get("latitude"),
        "air_quality_grid_longitude": air_quality.get("longitude"),
        "weather_observed_at": weather_current["time"],
        "air_quality_observed_at": air_current["time"],
        "fetched_at_utc": fetched_at_utc,
        "temperature_c": numeric(weather_current, "temperature_2m", required=True),
        "relative_humidity_pct": numeric(weather_current, "relative_humidity_2m", required=True),
        "precipitation_mm": numeric(weather_current, "precipitation"),
        "weather_code_wmo": numeric(weather_current, "weather_code"),
        "wind_speed_kmh": numeric(weather_current, "wind_speed_10m"),
        "wind_direction_deg": numeric(weather_current, "wind_direction_10m"),
        "surface_pressure_hpa": numeric(weather_current, "surface_pressure"),
        "european_aqi": numeric(air_current, "european_aqi", required=True),
        "us_aqi": numeric(air_current, "us_aqi"),
        "pm10_ug_m3": numeric(air_current, "pm10", required=True),
        "pm25_ug_m3": numeric(air_current, "pm2_5", required=True),
        "co_ug_m3": numeric(air_current, "carbon_monoxide"),
        "no2_ug_m3": numeric(air_current, "nitrogen_dioxide"),
        "so2_ug_m3": numeric(air_current, "sulphur_dioxide"),
        "o3_ug_m3": numeric(air_current, "ozone"),
        "raw_sha256": hashlib.sha256(digest_payload).hexdigest(),
        "raw_weather_path": raw_weather_path,
        "raw_air_quality_path": raw_air_path,
    }
    return {field: record.get(field) for field in CSV_FIELDS}


def observation_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("source", "")),
        str(row.get("city_code", "")),
        str(row.get("weather_observed_at", "")),
        str(row.get("air_quality_observed_at", "")),
    )


def upsert_csv(path: Path, new_rows: list[dict[str, Any]]) -> int:
    rows_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                rows_by_key[observation_key(row)] = row
    for row in new_rows:
        rows_by_key[observation_key(row)] = row

    ordered = sorted(
        rows_by_key.values(),
        key=lambda row: (str(row.get("weather_observed_at", "")), str(row.get("city_code", ""))),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(path)
    return len(ordered)


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def latest_snapshot(rows: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "source": "Open-Meteo",
        "data_kind": "forecast_model_current",
        "disclaimer": "Air-quality values are CAMS model data, not ground-station measurements.",
        "records": sorted(rows, key=lambda row: str(row["city_code"])),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--latest-json", type=Path, default=DEFAULT_LATEST)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cities", help="Comma-separated city codes; default is all configured cities")
    parser.add_argument("--fixture-dir", type=Path, help="Read <city>_weather.json and <city>_air_quality.json instead of the network")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    selected = {value.strip() for value in args.cities.split(",") if value.strip()} if args.cities else None
    cities = load_cities(args.config, selected)
    now = datetime.now(timezone.utc)
    fetched_at = now.isoformat(timespec="seconds")
    local_date = now.astimezone(ZoneInfo(LOCAL_TIMEZONE)).date().isoformat()
    archive_dir = args.raw_dir / local_date

    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for city in cities:
        code = str(city["code"])
        raw_weather = archive_dir / f"{code}_weather.json"
        raw_air = archive_dir / f"{code}_air_quality.json"
        try:
            if args.fixture_dir:
                weather = json.loads((args.fixture_dir / f"{code}_weather.json").read_text(encoding="utf-8"))
                air_quality = json.loads((args.fixture_dir / f"{code}_air_quality.json").read_text(encoding="utf-8"))
            else:
                weather_url, air_url = build_urls(city)
                weather = fetch_json(weather_url, args.timeout, args.max_retries)
                air_quality = fetch_json(air_url, args.timeout, args.max_retries)

            archive_raw(raw_weather, weather)
            archive_raw(raw_air, air_quality)
            records.append(
                normalized_record(
                    city,
                    weather,
                    air_quality,
                    fetched_at,
                    raw_weather.relative_to(ROOT).as_posix() if raw_weather.is_relative_to(ROOT) else str(raw_weather),
                    raw_air.relative_to(ROOT).as_posix() if raw_air.is_relative_to(ROOT) else str(raw_air),
                )
            )
            print(f"OK {city['city']} weather={records[-1]['weather_observed_at']} air={records[-1]['air_quality_observed_at']}")
        except Exception as exc:  # keep a city-level failure report for scheduled runs
            errors.append({"city_code": code, "city": str(city["city"]), "error": str(exc)})
            print(f"ERROR {city['city']}: {exc}", file=sys.stderr)

    total_rows = upsert_csv(args.output_csv, records) if records else count_csv_rows(args.output_csv)
    if records:
        write_json_atomic(args.latest_json, latest_snapshot(records, fetched_at))
    report = {
        "schema_version": SCHEMA_VERSION,
        "started_at_utc": fetched_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_city_count": len(cities),
        "success_count": len(records),
        "failure_count": len(errors),
        "history_row_count": total_rows,
        "errors": errors,
    }
    write_json_atomic(args.report_json, report)
    print(json.dumps(report, ensure_ascii=False))

    if not records or (errors and not args.allow_partial):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
