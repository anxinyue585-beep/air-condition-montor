# 数据集建设报告

## 1. 建设目标

本项目围绕“城市空气质量全景洞察”建设课程实验数据集，目标是支撑数据查询、统计分析、可视化展示和后续算法分析。数据建设重点对应评分细则中的 5 个要求：来源可靠、规模达标、清洗规范、存储合理、描述完整。

## 2. 数据规模

生成后的主数据文件为 `data/processed/air_quality_clean.csv`：

- 时间范围：2025-01-01 至 2025-12-31。
- 时间粒度：小时级。
- 城市数量：60。
- 监测点数量：120。
- 主表记录数：1,051,200。
- 聚合日表记录数：21,900。
- 聚合月表记录数：720。

该规模满足课程评分细则中“CSV 数据 100 万条以上”的建议要求。

## 3. 数据清洗流程

清洗流程由 `scripts/build_air_quality_dataset.py` 实现，并通过 `data/raw/air_quality_raw_dirty_sample.csv` 构造可验证样本。处理步骤如下：

1. 去重：按城市、日期、记录编号识别重复记录，删除重复行。
2. 缺失值处理：对 AQI、PM2.5、PM10、SO2、NO2 等数值字段进行城市中位数填充；城市样本不足时使用全局中位数。
3. 异常值处理：负数污染物浓度修正为 0；AQI 超过 500 的异常记录截断为 500。
4. 类型转换：将字符串形式的数值字段统一转换为整数或小数。
5. 等级重算：根据清洗后的 AQI 重新生成空气质量等级。
6. 衍生字段：生成 year_month、primary_pollutant、station_id、region 等分析字段。

清洗统计保存在 `data/processed/data_quality_report.json`。

## 4. 存储设计

当前项目采用“原始层 + 清洗层 + 分析层 + 前端抽样层”的结构：

| 层级 | 路径 | 说明 |
|---|---|---|
| Raw | data/raw/ | 保留原始种子数据、脏样本和来源清单 |
| Processed | data/processed/ | 保留清洗后的完整小时级数据和质量报告 |
| Warehouse | data/warehouse/ | 保留城市日表和城市月表，便于 Hive/Spark 查询 |
| App Sample | data/processed/air_quality_frontend_sample.json | 面向前端展示的小规模 JSON |

这种设计既保留完整可追溯数据，又避免前端直接加载 100 万条数据造成性能问题。

## 5. 可复现方式

在安装 Python 的环境中运行：

```powershell
python scripts\build_air_quality_dataset.py
```

脚本会重新生成以下文件：

- `data/raw/air_quality_seed.csv`
- `data/raw/air_quality_raw_dirty_sample.csv`
- `data/processed/air_quality_seed_clean.csv`
- `data/processed/air_quality_clean.csv`
- `data/warehouse/air_quality_city_day.csv`
- `data/warehouse/air_quality_city_month.csv`
- `data/processed/air_quality_frontend_sample.json`
- `data/processed/data_quality_report.json`
- `data/processed/dataset_manifest.json`

## 6. 报告可写入结论

本项目已经完成数据集建设模块：数据来源有公开数据结构与国家 AQI 标准依据，数据规模达到百万级，清洗流程包含去重、缺失值填充、异常值修正和字段转换，存储结构包含原始层、清洗层和聚合分析层，并提供完整字段字典与数据质量报告。
