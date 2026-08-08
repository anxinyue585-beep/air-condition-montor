# 平台验收证据索引

## 最新运行：20260711-123557

当前结论：**前置数据通过，平台验收未通过。**

已确认：

- 百万级 CSV 已成功生成。
- 文件大小为 224,981,786 bytes。
- SHA256 为 `28CABB6358C1C6D7491687BA39095427A989485AB780F9D1E111F5B05AF34F70`。
- 质量报告记录 1,051,200 条、60 个城市、120 个监测点，清洗后无缺失值。

阻塞项：

- 当前 Windows 系统找不到 `docker` 命令。
- 常见 Docker Desktop 安装路径、Docker 服务和相关进程均不存在。
- WSL 尚未安装，无法使用 WSL 内的 Docker Engine。

证据：

- `20260711-123557/02-dataset-evidence.log`：文件信息、SHA256 和数据质量报告。
- `20260711-123557/03-docker-preflight.log`：Docker CLI 缺失错误。
- `20260711-123557/full-transcript.log`：完整运行输出。
- `20260711-123557/verification-summary.json`：机器可读验收摘要。

Docker Desktop 安装并启动后，重新运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\platform_verify_and_capture.ps1
```

成功运行会继续完成 HDFS 上传、Hive 建表与行数校验、Spark ETL、输出目录检查和容器镜像状态记录。
