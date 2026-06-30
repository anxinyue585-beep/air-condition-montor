$ErrorActionPreference = "Stop"

docker exec aq-namenode hdfs dfsadmin -report
docker exec aq-namenode hdfs dfs -ls -h /warehouse/air_quality/clean
docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SELECT COUNT(*) FROM air_quality_clean_csv;"
docker exec aq-spark-master spark-submit --version
