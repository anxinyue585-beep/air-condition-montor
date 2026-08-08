# Hadoop/Hive/Spark 平台部署设计与待验收说明

> 当前状态（2026-07-11）：百万级 CSV 已生成并完成文件校验；Docker CLI、Docker Engine 和 WSL 均不可用，因此尚未启动任何 Hadoop/Hive/Spark 容器。本文件描述目标架构与执行步骤，不作为平台已部署成功的证明。实际证据见 `docs/platform_verification_record.md` 和 `reports/platform_verification/`。

## 1. 部署目标

本项目为城市空气质量百万级数据集设计 Hadoop/Hive/Spark 一体化实验平台，目标是完成课程评分中的“平台部署 Hadoop/Hive/Spark”指标。平台计划承担以下职责：

- Hadoop HDFS：存储 `air_quality_clean.csv` 百万级清洗数据。
- Hive：建立外部表和聚合分析表，支持 SQL 查询。
- Spark：读取 HDFS 数据，执行分区清洗、缓存、聚合和 Top-N 计算。

## 2. 平台拓扑

部署配置文件：`platform/docker-compose.yml`

运行前置条件：

- 已安装 Docker Desktop 或 Docker Engine。
- 已启用 Docker Compose v2。
- 首次启动时需要联网拉取 Hadoop、Hive、Spark 镜像。
- 本项目根目录需要保留 `data/processed/air_quality_clean.csv`。

| 服务 | 容器名 | 作用 | 访问端口 |
|---|---|---|---|
| Hadoop NameNode | aq-namenode | HDFS 元数据管理 | 9870, 9000 |
| Hadoop DataNode | aq-datanode | HDFS 数据块存储 | 9864 |
| YARN ResourceManager | aq-resourcemanager | 资源调度 | 8088 |
| YARN NodeManager | aq-nodemanager | 任务执行节点 | - |
| Hadoop HistoryServer | aq-historyserver | 作业历史查看 | 8188 |
| Hive Metastore DB | aq-hive-postgres | Hive 元数据库 | 5432 |
| Hive Metastore | aq-hive-metastore | Hive 元数据服务 | 9083 |
| HiveServer2 | aq-hive-server | Hive SQL 服务 | 10000 |
| Spark Master | aq-spark-master | Spark 主节点 | 7077, 8080 |
| Spark Worker | aq-spark-worker | Spark 执行节点 | 8081 |

## 3. 部署步骤

### 3.1 启动平台

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_up.ps1
```

成功启动后应可访问：

- Hadoop NameNode：http://localhost:9870
- YARN ResourceManager：http://localhost:8088
- Spark Master：http://localhost:8080
- HiveServer2：`jdbc:hive2://localhost:10000`

### 3.2 上传数据到 HDFS

```powershell
powershell -ExecutionPolicy Bypass -File scripts\upload_to_hdfs.ps1
```

HDFS 目标路径：

```text
/warehouse/air_quality/clean/air_quality_clean.csv
```

### 3.3 创建 Hive 表并查询

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_hive_air_quality.ps1
```

Hive SQL 文件：

```text
sql/hive_air_quality.sql
```

计划创建的核心表：

| 表名 | 说明 |
|---|---|
| air_quality_clean_csv | 指向 HDFS 清洗数据的 Hive 外部表 |
| air_quality_city_month | 城市月度聚合表 |
| air_quality_city_topn | 城市平均 AQI Top-N 表 |

### 3.4 执行 Spark 作业

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_spark_air_quality.ps1
```

Spark 作业文件：

```text
scripts/spark_air_quality_etl.py
```

计划生成的 Spark 输出路径：

```text
/warehouse/air_quality/spark/clean_parquet
/warehouse/air_quality/spark/city_day_parquet
/warehouse/air_quality/spark/city_month_parquet
/warehouse/air_quality/spark/city_topn_csv
/warehouse/air_quality/spark/quality_summary_csv
```

## 4. 验收命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_smoke_check.ps1
```

平台实际跑通后，应在课程报告或答辩视频中展示以下结果；当前均无通过证据：

1. NameNode 页面可看到 HDFS 正常运行。
2. HDFS `/warehouse/air_quality/clean` 下存在 `air_quality_clean.csv`。
3. Hive 查询 `SELECT COUNT(*) FROM air_quality_clean_csv;` 返回 1,051,200。
4. Spark Master 页面可看到 `air-quality-spark-etl` 作业执行记录。
5. HDFS `/warehouse/air_quality/spark` 下存在 Parquet 和 CSV 分析结果。

## 5. 停止平台

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_down.ps1
```

## 6. 与评分点的对应关系

| 评分要求 | 项目证据 |
|---|---|
| Hadoop 平台部署 | 已有 NameNode、DataNode、YARN 配置；容器运行待验收 |
| HDFS 数据存储 | 已有百万级 CSV 和上传脚本；HDFS 文件存在性待验收 |
| Hive 数据仓库 | 已有外部表、月聚合表、Top-N SQL；真实查询结果待验收 |
| Spark 数据处理 | 已有读取 HDFS、清洗、缓存、分区写 Parquet 作业；执行结果待验收 |
| 可验证部署 | 已有一键证据脚本；当前摘要状态为 `failed`，原因为缺少 Docker |

## 7. 当前可写入报告的结论

本项目已完成 Hadoop/Hive/Spark 实验平台的拓扑设计、Docker Compose 配置、HDFS 上传脚本、Hive SQL、Spark ETL 和验收脚本。百万级 CSV 前置检查已通过，但当前机器缺少 Docker，尚未获得容器运行、HDFS 文件、Hive 行数查询和 Spark 输出证据，因此平台部署评分项仍处于“材料就绪、运行待验收”状态。
