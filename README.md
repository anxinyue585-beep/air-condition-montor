# 城市空气质量全景洞察

这是一个面向《互联网大数据应用技术实践》课程大作业的城市空气质量数据分析与可视化项目。前端基于 Vue 3、TypeScript、Vite 和 ECharts，实现数据大屏、数据明细、筛选排序、分页导出和多图表展示。

## 数据集建设

本项目已补齐课程评分中的数据集建设材料：

- 原始种子数据：`data/raw/air_quality_seed.csv`
- 清洗演示样本：`data/raw/air_quality_raw_dirty_sample.csv`
- 百万级清洗后数据：`data/processed/air_quality_clean.csv`
- 城市日聚合表：`data/warehouse/air_quality_city_day.csv`
- 城市月聚合表：`data/warehouse/air_quality_city_month.csv`
- 前端抽样数据：`data/processed/air_quality_frontend_sample.json`
- 数据质量报告：`data/processed/data_quality_report.json`
- 数据集清单：`data/processed/dataset_manifest.json`
- 字段字典：`docs/data_dictionary.md`
- 数据来源说明：`docs/data_source.md`
- 数据建设报告：`docs/data_construction_report.md`
- Hive 建表 SQL：`sql/hive_air_quality.sql`

核心数据规模：60 个城市、120 个监测点、2025 全年小时级记录，共 1,051,200 条，满足课程建议的 CSV 100 万条以上要求。

## 重新生成数据

安装 Python 后运行：

```powershell
python scripts\build_air_quality_dataset.py
```

脚本会重新生成 raw、processed、warehouse 三层数据文件，并输出质量报告。

## Hadoop/Hive/Spark 平台部署

平台部署材料已经放在项目中：

- Docker Compose 集群配置：`platform/docker-compose.yml`
- HDFS 上传脚本：`scripts/upload_to_hdfs.ps1`
- Hive 建表与查询脚本：`scripts/run_hive_air_quality.ps1`
- Spark ETL 作业：`scripts/spark_air_quality_etl.py`
- Spark 作业提交脚本：`scripts/run_spark_air_quality.ps1`
- 平台冒烟检查脚本：`scripts/platform_smoke_check.ps1`
- 平台停止脚本：`scripts/platform_down.ps1`
- 平台部署报告：`docs/platform_deployment_report.md`
- 验收记录模板：`docs/platform_verification_record.md`

前置条件：已安装 Docker Desktop 或 Docker Engine，并启用 Docker Compose v2。首次启动需要联网拉取镜像。

启动平台：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_up.ps1
powershell -ExecutionPolicy Bypass -File scripts\upload_to_hdfs.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_hive_air_quality.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_spark_air_quality.ps1
```

停止平台：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_down.ps1
```

## 数据处理算法设计

本项目已补齐评分细则中的数据处理算法设计材料，覆盖清洗、转换、聚合、筛选、优化 5 个评分项：

- 处理脚本：`scripts/run_data_processing_algorithms.py`
- 一键运行：`scripts/run_data_processing_algorithms.ps1`
- 总报告：`data/processing_results/processing_algorithm_report.json`
- 清洗结果：`data/processing_results/cleaning_algorithm_result.json`
- 特征转换样本：`data/processing_results/air_quality_feature_sample.csv`
- 高污染筛选样本：`data/processing_results/high_pollution_filter_sample.csv`
- 区域月聚合表：`data/warehouse/air_quality_region_month.csv`
- 城市 AQI Top-N：`data/warehouse/air_quality_city_topn_processing.csv`
- 分区索引：`data/warehouse/air_quality_partition_index.csv`
- 算法设计报告：`docs/processing_algorithm_design_report.md`
- Hive 版算法 SQL：`sql/data_processing_algorithms.sql`

运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_data_processing_algorithms.ps1
```

## 数据分析算法应用

本项目已补齐评分细则中的数据分析算法应用材料，包含基础排名、数据挖掘、机器学习和预测分析：

- 分析脚本：`scripts/run_data_analysis_algorithms.py`
- 一键运行：`scripts/run_data_analysis_algorithms.ps1`
- 总报告：`data/analysis_results/analysis_algorithm_report.json`
- 城市风险排名：`data/analysis_results/city_risk_ranking.csv`
- K-Means 参数评估：`data/analysis_results/kmeans_parameter_eval.csv`
- 城市聚类结果：`data/analysis_results/city_cluster_assignments.csv`
- 聚类摘要：`data/analysis_results/cluster_summary.csv`
- Logistic Regression 参数评估：`data/analysis_results/logistic_parameter_eval.csv`
- 下月污染风险预测：`data/analysis_results/logistic_predictions.csv`
- Ridge Regression 参数评估：`data/analysis_results/ridge_parameter_eval.csv`
- 下月 AQI 预测结果：`data/analysis_results/aqi_prediction_predictions.csv`
- 模型系数：`data/analysis_results/ridge_coefficients.csv`
- 算法应用报告：`docs/analysis_algorithm_application_report.md`

运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_data_analysis_algorithms.ps1
```

## 前端运行

```powershell
npm install
npm run dev
```

构建检查：

```powershell
npm run build
```
