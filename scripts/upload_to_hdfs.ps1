$ErrorActionPreference = "Stop"

$inputFile = "/workspace/data/processed/air_quality_clean.csv"
$hdfsDir = "/warehouse/air_quality/clean"
$hdfsFile = "$hdfsDir/air_quality_clean.csv"

docker exec aq-namenode hdfs dfs -mkdir -p $hdfsDir
docker exec aq-namenode hdfs dfs -put -f $inputFile $hdfsFile
docker exec aq-namenode hdfs dfs -mkdir -p /warehouse/air_quality/spark
docker exec aq-namenode hdfs dfs -ls -h $hdfsDir
docker exec aq-namenode hdfs dfs -du -h $hdfsFile
