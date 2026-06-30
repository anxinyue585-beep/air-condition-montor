$ErrorActionPreference = "Stop"

$inputPath = "hdfs://namenode:9000/warehouse/air_quality/clean/air_quality_clean.csv"
$outputPath = "hdfs://namenode:9000/warehouse/air_quality/spark"

docker exec aq-spark-master spark-submit `
  --master spark://spark-master:7077 `
  --deploy-mode client `
  /workspace/scripts/spark_air_quality_etl.py `
  --input $inputPath `
  --output $outputPath

docker exec aq-namenode hdfs dfs -ls -R /warehouse/air_quality/spark
