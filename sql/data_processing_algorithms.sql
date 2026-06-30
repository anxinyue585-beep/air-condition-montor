-- Hive SQL evidence for the data-processing algorithm design rubric.
-- Run after sql/hive_air_quality.sql has created air_quality.air_quality_clean_csv.

USE air_quality;

-- 1. Data cleaning: remove duplicate record ids and normalize obvious invalid values.
DROP TABLE IF EXISTS air_quality_clean_dedup;
CREATE TABLE air_quality_clean_dedup AS
SELECT
  record_id,
  city,
  province,
  region,
  station_id,
  station_name,
  collect_time,
  collect_date,
  hour,
  year_month,
  CASE
    WHEN aqi < 0 THEN 0
    WHEN aqi > 500 THEN 500
    ELSE aqi
  END AS aqi,
  CASE
    WHEN aqi <= 50 THEN '优'
    WHEN aqi <= 100 THEN '良'
    ELSE '污染'
  END AS level,
  primary_pollutant,
  CASE WHEN pm25 < 0 THEN 0 ELSE pm25 END AS pm25,
  CASE WHEN pm10 < 0 THEN 0 ELSE pm10 END AS pm10,
  CASE WHEN so2 < 0 THEN 0 ELSE so2 END AS so2,
  CASE WHEN no2 < 0 THEN 0 ELSE no2 END AS no2,
  CASE WHEN co < 0 THEN 0 ELSE co END AS co,
  CASE WHEN o3 < 0 THEN 0 ELSE o3 END AS o3,
  temperature,
  humidity,
  wind_speed,
  source
FROM (
  SELECT
    t.*,
    ROW_NUMBER() OVER (PARTITION BY record_id ORDER BY collect_time) AS rn
  FROM air_quality_clean_csv t
) ranked
WHERE rn = 1
  AND city IS NOT NULL
  AND collect_date IS NOT NULL
  AND aqi IS NOT NULL
  AND pm25 IS NOT NULL
  AND pm10 IS NOT NULL;

-- 2. Data transformation: encode levels and derive analysis features.
DROP TABLE IF EXISTS air_quality_feature_view;
CREATE TABLE air_quality_feature_view AS
SELECT
  record_id,
  city,
  region,
  collect_time,
  collect_date,
  year_month,
  hour,
  aqi,
  (aqi - MIN(aqi) OVER ()) / (MAX(aqi) OVER () - MIN(aqi) OVER ()) AS aqi_minmax,
  CASE level WHEN '优' THEN 0 WHEN '良' THEN 1 ELSE 2 END AS level_code,
  CASE WHEN hour IN (7, 8, 18, 19) THEN 1 ELSE 0 END AS is_rush_hour,
  CASE WHEN aqi > 150 THEN 1 ELSE 0 END AS is_heavy_pollution
FROM air_quality_clean_dedup;

-- 3. Data aggregation: city and region statistics.
DROP TABLE IF EXISTS air_quality_region_month;
CREATE TABLE air_quality_region_month AS
SELECT
  region,
  year_month,
  COUNT(*) AS record_count,
  ROUND(AVG(aqi), 2) AS avg_aqi,
  MAX(aqi) AS max_aqi,
  ROUND(SUM(CASE WHEN aqi <= 100 THEN 1 ELSE 0 END) / COUNT(*), 4) AS good_rate,
  ROUND(AVG(pm25), 2) AS avg_pm25,
  ROUND(AVG(pm10), 2) AS avg_pm10
FROM air_quality_clean_dedup
GROUP BY region, year_month;

-- 4. Data filtering: multi-condition high-pollution subset.
DROP TABLE IF EXISTS air_quality_high_pollution;
CREATE TABLE air_quality_high_pollution AS
SELECT *
FROM air_quality_clean_dedup
WHERE aqi >= 101
  AND pm25 >= 75;

-- 5. Data optimization: partitioned table for frequent month/region queries.
DROP TABLE IF EXISTS air_quality_partitioned;
CREATE TABLE air_quality_partitioned (
  record_id STRING,
  city STRING,
  province STRING,
  station_id STRING,
  station_name STRING,
  collect_time STRING,
  collect_date STRING,
  hour INT,
  aqi INT,
  level STRING,
  primary_pollutant STRING,
  pm25 INT,
  pm10 INT,
  so2 INT,
  no2 INT,
  co DOUBLE,
  o3 INT,
  temperature DOUBLE,
  humidity INT,
  wind_speed DOUBLE,
  source STRING
)
PARTITIONED BY (year_month STRING, region STRING)
STORED AS PARQUET;

SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

INSERT OVERWRITE TABLE air_quality_partitioned PARTITION (year_month, region)
SELECT
  record_id,
  city,
  province,
  station_id,
  station_name,
  collect_time,
  collect_date,
  hour,
  aqi,
  level,
  primary_pollutant,
  pm25,
  pm10,
  so2,
  no2,
  co,
  o3,
  temperature,
  humidity,
  wind_speed,
  source,
  year_month,
  region
FROM air_quality_clean_dedup;
