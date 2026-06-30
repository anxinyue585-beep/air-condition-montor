# 平台部署验收记录

> 运行 Hadoop/Hive/Spark 平台后，可将实际命令输出或截图补到本文件中，作为课程报告证据。

## 1. 服务启动

命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_up.ps1
```

验收项：

- [ ] NameNode 页面可访问：http://localhost:9870
- [ ] YARN 页面可访问：http://localhost:8088
- [ ] Spark Master 页面可访问：http://localhost:8080
- [ ] HiveServer2 端口 10000 正常

## 2. HDFS 数据上传

命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\upload_to_hdfs.ps1
```

验收项：

- [ ] HDFS 路径 `/warehouse/air_quality/clean` 创建成功
- [ ] 文件 `air_quality_clean.csv` 上传成功
- [ ] 文件大小约 214 MB

## 3. Hive 查询

命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_hive_air_quality.ps1
```

验收项：

- [ ] 数据库 `air_quality` 创建成功
- [ ] 表 `air_quality_clean_csv` 创建成功
- [ ] 表 `air_quality_city_month` 创建成功
- [ ] 表 `air_quality_city_topn` 创建成功
- [ ] `SELECT COUNT(*)` 返回 1051200

## 4. Spark 作业

命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_spark_air_quality.ps1
```

验收项：

- [ ] Spark 作业 `air-quality-spark-etl` 提交成功
- [ ] 输出 `clean_parquet` 创建成功
- [ ] 输出 `city_day_parquet` 创建成功
- [ ] 输出 `city_month_parquet` 创建成功
- [ ] 输出 `city_topn_csv` 创建成功
- [ ] 输出 `quality_summary_csv` 创建成功
