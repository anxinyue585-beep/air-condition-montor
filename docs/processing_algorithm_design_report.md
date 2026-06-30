# 数据处理算法设计报告

## 1. 指标目标

课程评分细则要求“数据处理算法设计”至少采用 3 种数据处理算法或方法，并重点考察清洗、转换、聚合、筛选和优化。本项目已按 5 个评分项完整实现，每项均有可运行脚本和输出结果。

处理脚本：

```text
scripts/run_data_processing_algorithms.py
```

运行命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_data_processing_algorithms.ps1
```

总报告：

```text
data/processing_results/processing_algorithm_report.json
```

## 2. 评分点对应关系

| 评分项 | 分值 | 已实现方法 | 证据文件 |
|---|---:|---|---|
| 数据清洗 | 4 | 去重、缺失值填充、异常值截断、等级重算 | `data/processing_results/cleaning_algorithm_result.json` |
| 数据转换 | 4 | Min-Max 归一化、Z-Score 标准化、类别编码、时间字段派生 | `data/processing_results/air_quality_feature_sample.csv` |
| 数据聚合 | 4 | 城市月度 GroupBy、区域月度 GroupBy、城市 AQI Top-N | `data/warehouse/air_quality_region_month.csv`、`data/warehouse/air_quality_city_topn_processing.csv` |
| 数据筛选 | 4 | 多条件过滤、高污染样本抽取、早晚高峰污染统计 | `data/processing_results/high_pollution_filter_sample.csv` |
| 数据优化 | 4 | year_month + region 分区索引、Spark repartition、Spark cache、Parquet 输出 | `data/warehouse/air_quality_partition_index.csv`、`scripts/spark_air_quality_etl.py` |

## 3. 数据清洗算法

### 3.1 设计目标

清洗算法用于保证后续统计与算法分析的输入质量，处理重复、缺失、异常和字段不一致问题。

### 3.2 处理规则

1. 按 `id + city + date` 或 `record_id` 去重。
2. 对 AQI、PM2.5、PM10、SO2、NO2 等数值字段进行缺失值填充。
3. 将负数污染物浓度修正为 0。
4. 将 AQI 超过 500 的异常值截断为 500。
5. 根据清洗后的 AQI 重新计算等级：优、良、污染。

### 3.3 运行结果

清洗演示样本 `data/raw/air_quality_raw_dirty_sample.csv` 共 41 行，检测到：

- 重复记录：1 行。
- 缺失单元格：2 个。
- 负数单元格：1 个。
- AQI 异常值：1 行。

清洗后样本保留 40 行；完整清洗数据 `data/processed/air_quality_clean.csv` 共 1,051,200 行，重复记录数为 0，等级不一致记录数为 0。

## 4. 数据转换算法

### 4.1 设计目标

转换算法将原始业务字段转化为适合统计、机器学习和可视化使用的特征字段。

### 4.2 转换方法

- Min-Max 归一化：

```text
x_norm = (x - min(x)) / (max(x) - min(x))
```

- Z-Score 标准化：

```text
x_z = (x - mean(x)) / std(x)
```

- 类别编码：

```text
优 = 0，良 = 1，污染 = 2
```

- 时间字段派生：

```text
year_month、hour、is_rush_hour、is_heavy_pollution
```

### 4.3 运行结果

脚本输出 20,000 行特征样本：

```text
data/processing_results/air_quality_feature_sample.csv
```

样本字段包括 `aqi_minmax`、`aqi_zscore`、`pm25_minmax`、`pm10_minmax`、`level_code`、`is_rush_hour` 和 `is_heavy_pollution`。

## 5. 数据聚合算法

### 5.1 设计目标

聚合算法用于从小时级明细数据中提取城市、区域、月份维度的统计指标，为可视化和分析算法提供宽表。

### 5.2 聚合指标

对城市/月、区域/月等维度进行 GroupBy，计算：

- 记录数 `record_count`
- 平均 AQI `avg_aqi`
- 最大 AQI `max_aqi`
- 优良率 `good_rate`
- 污染率 `polluted_rate`
- PM2.5、PM10、SO2、NO2 均值

### 5.3 运行结果

- 城市月度聚合：720 行。
- 区域月度聚合：84 行。
- 城市 AQI Top-N：20 行。

输出文件：

```text
data/warehouse/air_quality_region_month.csv
data/warehouse/air_quality_city_topn_processing.csv
```

当前平均 AQI Top 城市包括石家庄、太原、乌鲁木齐、西安、郑州等，适合在后续报告中作为污染对比分析材料。

## 6. 数据筛选算法

### 6.1 设计目标

筛选算法用于从百万级数据中抽取重点风险样本，支持污染预警、异常分析和答辩展示。

### 6.2 筛选条件

高污染样本规则：

```text
aqi >= 101 and pm25 >= 75
```

早晚高峰污染统计：

```text
hour in (7, 8, 18, 19)
```

### 6.3 运行结果

- 高污染样本命中：19,922 条。
- 早晚高峰高污染样本：5,872 条。
- 输出抽样记录：500 条。

输出文件：

```text
data/processing_results/high_pollution_filter_sample.csv
```

## 7. 数据优化算法

### 7.1 设计目标

优化算法用于提升大数据环境下的查询、聚合和分布式处理效率。

### 7.2 优化策略

1. 分区设计：按 `year_month + region` 建立 84 个逻辑分区。
2. Spark 重分区：在 `scripts/spark_air_quality_etl.py` 中按 `year_month` 和 `region` 执行 `repartition`。
3. Spark 缓存：对清洗后的 DataFrame 使用 `cache()`，避免多次聚合重复扫描。
4. 列式存储：Spark 输出 Parquet，便于 Hive/Spark 后续读取。
5. Shuffle 参数：`spark.sql.shuffle.partitions = 24`。

### 7.3 运行结果

分区索引文件：

```text
data/warehouse/air_quality_partition_index.csv
```

当前共有 84 个分区，示例路径：

```text
year_month=2025-01/region=华北
year_month=2025-01/region=华东
year_month=2025-01/region=华南
```

## 8. Hive/Spark 实现证据

Hive 版处理算法 SQL：

```text
sql/data_processing_algorithms.sql
```

该 SQL 包含：

- 去重清洗表 `air_quality_clean_dedup`
- 特征转换表 `air_quality_feature_view`
- 区域月度聚合表 `air_quality_region_month`
- 高污染筛选表 `air_quality_high_pollution`
- 分区 Parquet 表 `air_quality_partitioned`

Spark 版处理算法：

```text
scripts/spark_air_quality_etl.py
```

该作业读取 HDFS 上的 CSV，执行清洗、转换、聚合、Top-N、分区 Parquet 输出。

## 9. 报告可写入结论

本项目的数据处理算法设计覆盖了清洗、转换、聚合、筛选和优化 5 类方法，超过“至少 3 种数据处理算法或方法”的最低要求。处理过程包含去重、缺失值处理、异常值处理、标准化、归一化、类别编码、GroupBy 聚合、多条件查询、分区设计、Spark 缓存和 Parquet 输出，可支撑评分细则中数据处理算法设计部分的满分材料。
