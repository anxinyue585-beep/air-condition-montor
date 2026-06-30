$ErrorActionPreference = "Stop"

docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -f /workspace/sql/hive_air_quality.sql
docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SHOW TABLES;"
docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SELECT COUNT(*) AS total_rows FROM air_quality_clean_csv;"
docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SELECT city, avg_aqi, good_rate FROM air_quality_city_topn LIMIT 10;"
