# Open-Meteo 每日真实数据链路

## 1. 定位与数据口径

本链路用于逐步替换项目中的合成演示数据，并为后续接入监测站实测数据建立统一入口。第一阶段使用 Open-Meteo：

- 天气数据来自 Open-Meteo 天气预报接口。
- 空气质量数据来自 Open-Meteo 对 CAMS 全球大气模型的封装。
- 空气质量属于模型估算/预报数据，不是地面监测站实测数据。
- 当前保存 European AQI 和 US AQI，不将它们伪装成中国 HJ 633 AQI。

官方文档：

- 天气接口：https://open-meteo.com/en/docs
- 空气质量接口：https://open-meteo.com/en/docs/air-quality-api

## 2. 第一阶段城市

配置文件为 `config/open_meteo_cities.json`，当前覆盖北京、上海、广州、深圳、成都、杭州。城市使用固定 WGS84 坐标，避免每天重复调用地理编码服务。

## 3. 数据输出

| 输出 | 用途 | 是否提交 Git |
|---|---|---|
| `data/raw/open_meteo/YYYY-MM-DD/` | 保存供应商原始 JSON，支持审计和重放 | 否，由 Actions Artifact 临时保存 |
| `data/live/open_meteo_observations.csv` | 规范化历史记录，按城市与观测时间幂等更新 | 是 |
| `data/live/open_meteo_latest.json` | 每个城市本次运行的最新快照，供前端或 API 使用 | 是 |
| `data/live/open_meteo_run_report.json` | 本次成功数、失败数和错误信息 | 是 |

唯一键由 `source + city_code + weather_observed_at + air_quality_observed_at` 组成。相同观测时间重复运行时会更新原记录，不会重复追加。

## 4. 本地运行

无需第三方 Python 包：

```powershell
python scripts\fetch_open_meteo_daily.py
```

只抓取部分城市：

```powershell
python scripts\fetch_open_meteo_daily.py --cities beijing,shanghai
```

测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## 5. 自动调度

`.github/workflows/fetch-open-meteo.yml` 每天北京时间 02:30 运行，也支持在 GitHub Actions 页面手动触发。工作流执行以下步骤：

1. 运行单元测试。
2. 调用 Open-Meteo 获取6城最新数据。
3. 上传原始 JSON 为短期 Actions Artifact。
4. 将标准化历史、最新快照和运行报告提交回当前分支。
5. 使用最新快照构建 Vue 前端，并上传可部署的 `dist` Artifact。

前端通过 `/live` 路由展示最近一次成功快照。数据在构建时写入页面，因此 GitHub Actions 每次采集后都会重新执行生产构建。

GitHub 的定时任务使用 UTC，`18:30 UTC` 对应次日 `02:30 Asia/Shanghai`。GitHub 可能在高峰期延迟执行，因此 `fetched_at_utc` 与观测时间应作为真实时间依据。

## 6. 失败处理

- 单次 HTTP 请求默认最多执行3次，间隔按 1、2 秒递增。
- 任意城市失败时，默认返回非零状态并使 Actions 任务失败。
- 成功城市的原始响应和运行报告仍会保留，便于定位故障。
- 不建议在正式任务中使用 `--allow-partial`，避免静默提交不完整的全国快照。

## 7. 后续迁移

注册和风天气或获得其他监测站 API 后，应新增供应商适配器，而不是修改现有标准化字段。真实监测数据使用新的 `source` 和 `data_kind=station_observation`，与 Open-Meteo 模型数据并存，便于对比模型值和实测值。
