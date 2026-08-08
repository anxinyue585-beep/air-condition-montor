$ErrorActionPreference = "Stop"

$exportRoot = "data/platform_exports"
$sparkDir = Join-Path $exportRoot "spark"
$hiveDir = Join-Path $exportRoot "hive"
New-Item -ItemType Directory -Force -Path $sparkDir, $hiveDir | Out-Null

function Export-HdfsCsv {
  param([string]$HdfsPath, [string]$Destination)
  $global:LASTEXITCODE = 0
  docker exec aq-namenode hdfs dfs -cat "$HdfsPath/part-*" | Set-Content -LiteralPath $Destination -Encoding UTF8
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to export HDFS CSV: $HdfsPath"
  }
  if (-not (Test-Path -LiteralPath $Destination) -or (Get-Item -LiteralPath $Destination).Length -eq 0) {
    throw "Exported file is empty: $Destination"
  }
}

Export-HdfsCsv "/warehouse/air_quality/spark/city_day_csv" (Join-Path $sparkDir "air_quality_city_day.csv")
Export-HdfsCsv "/warehouse/air_quality/spark/city_month_csv" (Join-Path $sparkDir "air_quality_city_month.csv")
Export-HdfsCsv "/warehouse/air_quality/spark/city_topn_csv" (Join-Path $sparkDir "air_quality_city_topn.csv")
Export-HdfsCsv "/warehouse/air_quality/spark/quality_summary_csv" (Join-Path $sparkDir "quality_summary.csv")

$hiveMonthly = Join-Path $hiveDir "air_quality_city_month.csv"
$global:LASTEXITCODE = 0
docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root --silent=true --showHeader=true --outputformat=csv2 -e "USE air_quality; SELECT city, year_month, avg_aqi, max_aqi, good_rate, avg_pm25, avg_pm10, avg_so2, avg_no2 FROM air_quality_city_month ORDER BY city, year_month;" | Set-Content -LiteralPath $hiveMonthly -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
  throw "Failed to export Hive city-month result."
}

$manifest = [ordered]@{
  status = "passed"
  exported_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  source = [ordered]@{
    hdfs_root = "/warehouse/air_quality/spark"
    hive_database = "air_quality"
  }
  outputs = [ordered]@{
    spark_city_day = "data/platform_exports/spark/air_quality_city_day.csv"
    spark_city_month = "data/platform_exports/spark/air_quality_city_month.csv"
    spark_city_topn = "data/platform_exports/spark/air_quality_city_topn.csv"
    spark_quality_summary = "data/platform_exports/spark/quality_summary.csv"
    hive_city_month = "data/platform_exports/hive/air_quality_city_month.csv"
  }
  row_counts = [ordered]@{
    spark_city_day = [math]::Max(0, (Get-Content -LiteralPath (Join-Path $sparkDir "air_quality_city_day.csv")).Count - 1)
    spark_city_month = [math]::Max(0, (Get-Content -LiteralPath (Join-Path $sparkDir "air_quality_city_month.csv")).Count - 1)
    hive_city_month = [math]::Max(0, (Get-Content -LiteralPath $hiveMonthly).Count - 1)
  }
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $exportRoot "platform_run_manifest.json") -Encoding UTF8

Get-Content -Raw -Encoding UTF8 (Join-Path $exportRoot "platform_run_manifest.json")
