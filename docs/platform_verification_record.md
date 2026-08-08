# 平台部署验收记录

> 运行 Hadoop/Hive/Spark 平台后，可将实际命令输出或截图补到本文件中，作为课程报告证据。

## 0. 2026-07-11 实际验收状态

- 数据集前置检查：通过。
- 主 CSV：`data/processed/air_quality_clean.csv`。
- 文件大小：224,981,786 bytes。
- SHA256：`28CABB6358C1C6D7491687BA39095427A989485AB780F9D1E111F5B05AF34F70`。
- 数据规模：1,051,200 条、60 个城市、120 个监测点。
- Docker 前置检查：失败；当前系统未安装或无法找到 Docker CLI，且没有可用 WSL。
- 本轮没有启动容器，因此下面的 HDFS、Hive、Spark 项目保持未勾选，不能视为验收通过。
- 最新证据目录：`reports/platform_verification/20260711-123557/`。

安装并启动 Docker Desktop 后，执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_verify_and_capture.ps1
```

脚本只有在 HDFS 上传、Hive 行数查询、Spark ETL 和最终检查全部成功时，才会生成 `status: passed` 的摘要。

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
