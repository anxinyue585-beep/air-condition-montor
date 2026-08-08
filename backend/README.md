# 后端查询服务

后端采用 FastAPI，提供只读查询，不修改原始数据。服务通过文件修改时间自动刷新内存缓存，因此 Open-Meteo 定时任务更新文件后无需重启。

## 启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
powershell -ExecutionPolicy Bypass -File scripts\start_backend.ps1
```

- API 根地址：`http://127.0.0.1:8000/api`
- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 数据文件可用性 |
| GET | `/api/overview` | 百万级数据集总览 |
| GET | `/api/cities` | 60个城市列表 |
| GET | `/api/lineage` | 数据血缘节点、边和平台验收状态 |
| GET | `/api/processing/status` | 当前查询源、更新时间和平台导出状态 |
| GET | `/api/records` | 城市日数据分页、筛选和排序 |
| GET | `/api/platform/hive/monthly` | 真实 Hive 月度导出预览 |
| GET | `/api/analysis/risk-ranking` | 城市风险排名 |
| GET | `/api/analysis/predictions` | Ridge 或 Logistic 测试集预测 |
| GET | `/api/live/latest` | Open-Meteo 最近快照 |
| GET | `/api/live/history` | Open-Meteo 历史分页查询 |

`/api/records` 查询粒度为城市日，共21,900条；`/api/overview` 中的 `clean_rows=1,051,200` 表示完整小时级数据规模。接口不会把21,900条聚合记录伪装成百万级明细。

当 `data/platform_exports/platform_run_manifest.json` 的状态为 `passed` 且 Spark 城市日导出存在时，`/api/records` 自动切换到 `spark_export`；否则使用 `local_warehouse_fallback` 并在响应元数据和血缘页面中明确显示。Hive接口只读取真实导出，不提供伪造回退。

## CORS

默认允许：

- `http://localhost:5173`
- `http://127.0.0.1:5173`

生产环境通过逗号分隔的 `AQ_API_CORS_ORIGINS` 环境变量覆盖。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```
