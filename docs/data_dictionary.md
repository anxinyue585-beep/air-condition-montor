# 数据字段字典

主数据文件：`data/processed/air_quality_clean.csv`

| 字段名 | 类型 | 示例 | 说明 |
|---|---|---|---|
| record_id | string | AQ2025-001-1-00001 | 唯一记录编号 |
| city | string | 北京 | 城市名称 |
| province | string | 北京市 | 省份或直辖市 |
| region | string | 华北 | 区域分组 |
| station_id | string | 001-1 | 监测点编号 |
| station_name | string | 北京监测点1 | 监测点名称 |
| datetime | datetime | 2025-01-01 00:00:00 | 采集时间 |
| date | date | 2025-01-01 | 日期 |
| hour | integer | 0 | 小时，范围 0-23 |
| year_month | string | 2025-01 | 年月分区字段 |
| aqi | integer | 103 | 空气质量指数 |
| level | string | 污染 | 空气质量等级，取值为优、良、污染 |
| primary_pollutant | string | PM2.5 | 首要污染物 |
| pm25 | integer | 68 | PM2.5 浓度 |
| pm10 | integer | 117 | PM10 浓度 |
| so2 | integer | 10 | SO2 浓度 |
| no2 | integer | 24 | NO2 浓度 |
| co | number | 1.24 | CO 浓度 |
| o3 | integer | 91 | O3 浓度 |
| temperature | number | 4.2 | 温度 |
| humidity | integer | 72 | 相对湿度 |
| wind_speed | number | 2.8 | 风速 |
| source | string | course_reproducible_dataset_based_on_open_air_quality_schema | 数据来源标识 |

## 衍生数据文件

| 文件 | 行数 | 用途 |
|---|---:|---|
| data/raw/air_quality_seed.csv | 36 | 项目原始种子样本 |
| data/raw/air_quality_raw_dirty_sample.csv | 41 | 带重复、缺失、异常值的清洗演示样本 |
| data/processed/air_quality_seed_clean.csv | 40 | 清洗后的种子样本 |
| data/processed/air_quality_clean.csv | 1,051,200 | 小时级完整清洗数据 |
| data/warehouse/air_quality_city_day.csv | 21,900 | 城市日聚合宽表 |
| data/warehouse/air_quality_city_month.csv | 720 | 城市月聚合宽表 |
| data/processed/air_quality_frontend_sample.json | 504 | 前端展示抽样数据 |
| data/processed/data_quality_report.json | - | 数据质量报告 |
| data/processed/dataset_manifest.json | - | 数据集清单 |
