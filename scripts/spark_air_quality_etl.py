"""Spark ETL job for the air-quality big-data platform."""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType


NUMERIC_INT_COLUMNS = ["hour", "aqi", "pm25", "pm10", "so2", "no2", "o3", "humidity"]
NUMERIC_DOUBLE_COLUMNS = ["co", "temperature", "wind_speed"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Air quality Spark ETL")
    parser.add_argument("--input", required=True, help="Input CSV path on HDFS")
    parser.add_argument("--output", required=True, help="Output directory on HDFS")
    return parser.parse_args()


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("air-quality-spark-etl")
        .config("spark.sql.shuffle.partitions", "24")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .getOrCreate()
    )


def clean_frame(df):
    clean = df.dropDuplicates(["record_id"])
    clean = clean.dropna(subset=["city", "datetime", "date", "aqi", "pm25", "pm10"])

    for column in NUMERIC_INT_COLUMNS:
        clean = clean.withColumn(column, F.col(column).cast(IntegerType()))
    for column in NUMERIC_DOUBLE_COLUMNS:
        clean = clean.withColumn(column, F.col(column).cast(DoubleType()))

    clean = clean.withColumn("aqi", F.when(F.col("aqi") < 0, 0).when(F.col("aqi") > 500, 500).otherwise(F.col("aqi")))
    for column in ["pm25", "pm10", "so2", "no2", "co", "o3", "humidity", "wind_speed"]:
        clean = clean.withColumn(column, F.when(F.col(column) < 0, 0).otherwise(F.col(column)))

    clean = clean.withColumn(
        "level",
        F.when(F.col("aqi") <= 50, F.lit("优")).when(F.col("aqi") <= 100, F.lit("良")).otherwise(F.lit("污染")),
    )
    clean = clean.withColumn("collect_date", F.to_date("date"))
    clean = clean.withColumn("year_month", F.date_format("collect_date", "yyyy-MM"))
    return clean.repartition("year_month", "region").cache()


def aggregate_city_day(clean):
    return (
        clean.groupBy("city", "province", "region", "date")
        .agg(
            F.count("*").alias("record_count"),
            F.round(F.avg("aqi"), 2).alias("avg_aqi"),
            F.max("aqi").alias("max_aqi"),
            F.round(F.sum(F.when(F.col("aqi") <= 100, 1).otherwise(0)) / F.count("*"), 4).alias("good_rate"),
            F.round(F.avg("pm25"), 2).alias("avg_pm25"),
            F.round(F.avg("pm10"), 2).alias("avg_pm10"),
            F.round(F.avg("so2"), 2).alias("avg_so2"),
            F.round(F.avg("no2"), 2).alias("avg_no2"),
        )
        .orderBy("city", "date")
    )


def aggregate_city_month(clean):
    return (
        clean.groupBy("city", "province", "region", "year_month")
        .agg(
            F.count("*").alias("record_count"),
            F.round(F.avg("aqi"), 2).alias("avg_aqi"),
            F.max("aqi").alias("max_aqi"),
            F.round(F.sum(F.when(F.col("aqi") <= 100, 1).otherwise(0)) / F.count("*"), 4).alias("good_rate"),
            F.round(F.avg("pm25"), 2).alias("avg_pm25"),
            F.round(F.avg("pm10"), 2).alias("avg_pm10"),
            F.round(F.avg("so2"), 2).alias("avg_so2"),
            F.round(F.avg("no2"), 2).alias("avg_no2"),
        )
        .orderBy("city", "year_month")
    )


def build_city_topn(clean):
    return (
        clean.groupBy("city", "province", "region")
        .agg(
            F.round(F.avg("aqi"), 2).alias("avg_aqi"),
            F.max("aqi").alias("max_aqi"),
            F.round(F.sum(F.when(F.col("aqi") <= 100, 1).otherwise(0)) / F.count("*"), 4).alias("good_rate"),
        )
        .orderBy(F.desc("avg_aqi"))
        .limit(20)
    )


def build_quality_summary(clean):
    return clean.agg(
        F.count("*").alias("row_count"),
        F.countDistinct("city").alias("city_count"),
        F.countDistinct("station_id").alias("station_count"),
        F.min("date").alias("min_date"),
        F.max("date").alias("max_date"),
        F.round(F.avg("aqi"), 2).alias("avg_aqi"),
        F.max("aqi").alias("max_aqi"),
    )


def main() -> None:
    args = parse_args()
    spark = build_spark()

    raw = spark.read.option("header", True).option("encoding", "UTF-8").csv(args.input)
    clean = clean_frame(raw)

    clean.write.mode("overwrite").partitionBy("year_month", "region").parquet(f"{args.output}/clean_parquet")
    aggregate_city_day(clean).write.mode("overwrite").parquet(f"{args.output}/city_day_parquet")
    aggregate_city_month(clean).write.mode("overwrite").parquet(f"{args.output}/city_month_parquet")
    build_city_topn(clean).coalesce(1).write.mode("overwrite").option("header", True).csv(f"{args.output}/city_topn_csv")
    build_quality_summary(clean).coalesce(1).write.mode("overwrite").option("header", True).csv(f"{args.output}/quality_summary_csv")

    clean.unpersist()
    spark.stop()


if __name__ == "__main__":
    main()
