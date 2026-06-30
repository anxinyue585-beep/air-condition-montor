$ErrorActionPreference = "Stop"

docker compose -f platform/docker-compose.yml up -d
docker compose -f platform/docker-compose.yml ps

Write-Host ""
Write-Host "Hadoop NameNode: http://localhost:9870"
Write-Host "YARN ResourceManager: http://localhost:8088"
Write-Host "Spark Master: http://localhost:8080"
Write-Host "HiveServer2 JDBC: jdbc:hive2://localhost:10000"
