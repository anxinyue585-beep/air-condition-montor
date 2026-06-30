-- Hive external table design for the air-quality dataset.
-- Put data/processed/air_quality_clean.csv into HDFS first, for example:
-- hdfs dfs -mkdir -p /warehouse/air_quality/clean
-- hdfs dfs -put data/processed/air_quality_clean.csv /warehouse/air_quality/clean/

CREATE DATABASE IF NOT EXISTS air_quality;
USE air_quality;

DROP TABLE IF EXISTS air_quality_clean_csv;

CREATE EXTERNAL TABLE air_quality_clean_csv (
  record_id STRING,
  city STRING,
  province STRING,
  region STRING,
  station_id STRING,
  station_name STRING,
  collect_time STRING,
  collect_date STRING,
  hour INT,
  year_month STRING,
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
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION '/warehouse/air_quality/clean'
TBLPROPERTIES ("skip.header.line.count" = "1");

DROP TABLE IF EXISTS air_quality_city_month;

CREATE TABLE air_quality_city_month AS
SELECT
  city,
  province,
  region,
  year_month,
  COUNT(*) AS record_count,
  ROUND(AVG(aqi), 2) AS avg_aqi,
  MAX(aqi) AS max_aqi,
  ROUND(SUM(CASE WHEN aqi <= 100 THEN 1 ELSE 0 END) / COUNT(*), 4) AS good_rate,
  ROUND(AVG(pm25), 2) AS avg_pm25,
  ROUND(AVG(pm10), 2) AS avg_pm10,
  ROUND(AVG(so2), 2) AS avg_so2,
  ROUND(AVG(no2), 2) AS avg_no2
FROM air_quality_clean_csv
GROUP BY city, province, region, year_month;

DROP TABLE IF EXISTS air_quality_city_topn;

CREATE TABLE air_quality_city_topn AS
SELECT
  city,
  province,
  region,
  ROUND(AVG(aqi), 2) AS avg_aqi,
  MAX(aqi) AS max_aqi,
  ROUND(SUM(CASE WHEN aqi <= 100 THEN 1 ELSE 0 END) / COUNT(*), 4) AS good_rate
FROM air_quality_clean_csv
GROUP BY city, province, region
ORDER BY avg_aqi DESC
LIMIT 20;
