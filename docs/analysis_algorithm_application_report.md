# 数据分析算法应用报告

## 1. 指标目标

课程评分细则要求课程大作业至少实现一种数据分析算法，并对算法原理、实现过程、参数设置及实验结果进行分析。本项目在城市空气质量数据集上实现了 4 类分析算法：

| 算法类别 | 算法 | 评分对应 |
|---|---|---|
| A 类基础算法 | Top-N 城市污染风险排名 | 基础统计、排名算法 |
| B 类数据挖掘算法 | K-Means 城市污染画像聚类 | 数据挖掘算法 |
| C 类机器学习算法 | Logistic Regression 下月污染风险分类 | 机器学习算法 |
| 预测创新项 | Ridge Regression 下月 AQI 预测 | 时间序列预测 |

运行脚本：

```text
scripts/run_data_analysis_algorithms.py
```

运行命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_data_analysis_algorithms.ps1
```

总结果报告：

```text
data/analysis_results/analysis_algorithm_report.json
```

## 2. 输入数据与特征

输入数据使用城市月度聚合表：

```text
data/warehouse/air_quality_city_month.csv
```

该表由 1,051,200 条小时级空气质量数据聚合得到，共 720 条城市月度记录，覆盖 60 个城市和 12 个月。

主要特征包括：

- `avg_aqi`：月平均 AQI。
- `max_aqi`：月最高 AQI。
- `good_rate`：优良率。
- `avg_pm25`、`avg_pm10`、`avg_so2`、`avg_no2`：主要污染物月均值。
- `month_sin`、`month_cos`：月份周期特征。
- `region_*`：区域独热编码。

监督学习任务采用“当前月特征预测下月结果”的方式构造样本，共 660 条。为避免未来信息泄漏，按目标月份顺序划分为训练集 420 条（2—8月）、验证集 120 条（9—10月）和测试集 120 条（11—12月）。标准化参数只由训练集计算；超参数只在验证集选择；选定参数后使用训练集与验证集重新拟合，测试集仅用于一次最终评价。

## 3. Top-N 城市污染风险排名

### 3.1 算法原理

Top-N 排名用于从城市画像中识别污染风险较高的城市。风险分数综合考虑平均 AQI、最高 AQI、污染率和 PM2.5 水平。

风险评分公式：

```text
risk_score =
100 * (
  0.35 * norm(avg_aqi)
  + 0.20 * norm(max_aqi)
  + 0.25 * norm(polluted_rate)
  + 0.20 * norm(avg_pm25)
)
```

其中 `norm` 为 Min-Max 归一化。

### 3.2 实验结果

输出文件：

```text
data/analysis_results/city_risk_ranking.csv
```

风险排名前 10 的城市为：

| 排名 | 城市 | 区域 | 风险分 | 平均 AQI | 污染率 |
|---:|---|---|---:|---:|---:|
| 1 | 石家庄 | 华北 | 100.0000 | 117.42 | 0.8178 |
| 2 | 太原 | 华北 | 80.7844 | 103.86 | 0.5598 |
| 3 | 乌鲁木齐 | 西北 | 78.9906 | 102.72 | 0.5438 |
| 4 | 西安 | 西北 | 72.1489 | 98.49 | 0.4590 |
| 5 | 郑州 | 华中 | 71.6030 | 97.83 | 0.4483 |
| 6 | 北京 | 华北 | 65.0602 | 92.57 | 0.3496 |
| 7 | 兰州 | 西北 | 62.1978 | 91.07 | 0.3126 |
| 8 | 洛阳 | 华中 | 61.0972 | 90.68 | 0.2973 |
| 9 | 天津 | 华北 | 58.5743 | 88.06 | 0.2626 |
| 10 | 呼和浩特 | 华北 | 52.5225 | 83.53 | 0.1841 |

结论：华北和西北城市在风险榜中占比较高，说明冬春季污染强度和 PM2.5 水平对城市风险评分影响较明显。

## 4. K-Means 城市污染画像聚类

### 4.1 算法原理

K-Means 是一种无监督聚类算法。算法通过最小化样本到所属簇中心的平方距离，将城市划分为若干污染画像类型。

目标函数：

```text
min Σ ||x_i - μ_c||²
```

其中 `x_i` 为城市污染特征向量，`μ_c` 为簇中心。

使用特征：

```text
avg_aqi, max_aqi, polluted_rate, avg_pm25, avg_pm10, avg_so2, avg_no2
```

所有特征在聚类前进行了 Z-Score 标准化。

### 4.2 参数设置

测试 `k = 2, 3, 4, 5, 6`，使用 SSE 和轮廓系数进行评估。

输出文件：

```text
data/analysis_results/kmeans_parameter_eval.csv
```

参数结果：

| k | SSE | 轮廓系数 | 迭代次数 |
|---:|---:|---:|---:|
| 2 | 139.567913 | 0.592283 | 8 |
| 3 | 61.752170 | 0.574013 | 7 |
| 4 | 34.247630 | 0.590085 | 5 |
| 5 | 30.214977 | 0.525011 | 7 |
| 6 | 21.311855 | 0.512301 | 3 |

本项目选择 `k = 3` 作为最终模型，因为它可以直接对应低污染、中等波动、高污染风险三类业务画像，解释性更强。

### 4.3 聚类结果

输出文件：

```text
data/analysis_results/city_cluster_assignments.csv
data/analysis_results/cluster_summary.csv
```

聚类摘要：

| 类型 | 城市数 | 平均 AQI | 最高 AQI | 平均污染率 | 代表城市 |
|---|---:|---:|---:|---:|---|
| 低污染稳定型 | 30 | 44.98 | 93.00 | 0.0000 | 杭州、无锡、烟台、苏州、绵阳 |
| 中等波动型 | 21 | 70.93 | 128.00 | 0.0350 | 呼和浩特、哈尔滨、济南、宝鸡、沈阳 |
| 高污染风险型 | 9 | 98.08 | 162.00 | 0.4501 | 石家庄、太原、乌鲁木齐、西安、郑州 |

结论：K-Means 将城市分为较清晰的三类，高污染风险型城市数量较少但污染率明显更高，适合作为重点监测对象。

## 5. Logistic Regression 下月污染风险分类

### 5.1 算法原理

Logistic Regression 是监督式机器学习分类算法，用于预测下月城市是否进入污染风险状态。

标签定义：

```text
target_polluted = 1 if next_month_avg_aqi >= 100 else 0
```

预测函数：

```text
p = 1 / (1 + exp(-(w·x + b)))
```

当 `p >= 0.5` 时，预测为下月污染风险。

### 5.2 参数设置

对 L2 正则化参数进行对比：

```text
lambda = 0, 0.001, 0.01, 0.1, 1.0
```

输出文件：

```text
data/analysis_results/logistic_parameter_eval.csv
data/analysis_results/logistic_predictions.csv
```

### 5.3 实验结果

训练集用于拟合候选模型，验证集 120 条、其中正样本 4 条，用于选择正则化参数。不同参数在验证集上的结果如下：

| lambda | Accuracy | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| 0.000 | 0.9750 | 1.0000 | 0.2500 | 0.4000 |
| 0.001 | 0.9750 | 1.0000 | 0.2500 | 0.4000 |
| 0.010 | 0.9750 | 1.0000 | 0.2500 | 0.4000 |
| 0.100 | 0.9750 | 1.0000 | 0.2500 | 0.4000 |
| 1.000 | 0.9750 | 1.0000 | 0.2500 | 0.4000 |

验证集各组参数表现相同，按“F1、Recall、Accuracy、较小正则项”顺序选择 `lambda = 0.0`。使用训练集与验证集重新拟合后，最终测试集 120 条、其中正样本 17 条；测试 Accuracy 为 0.9583，Precision 为 1.0000，Recall 为 0.7059，F1 为 0.8276。验证期正样本仅 4 条，参数区分度有限，后续引入多年真实数据后应改用滚动时间验证。

## 6. Ridge Regression 下月 AQI 预测

### 6.1 算法原理

Ridge Regression 是带 L2 正则项的线性回归模型，用于预测下月城市平均 AQI。

目标函数：

```text
min Σ(y - Xw)² + alpha * Σw²
```

相比普通线性回归，Ridge Regression 可以缓解特征之间高度相关带来的过拟合问题。

### 6.2 参数设置

对正则化参数进行对比：

```text
alpha = 0, 0.1, 1, 10, 100
```

输出文件：

```text
data/analysis_results/ridge_parameter_eval.csv
data/analysis_results/aqi_prediction_predictions.csv
data/analysis_results/ridge_coefficients.csv
```

### 6.3 实验结果

| alpha | MAE | RMSE | R2 |
|---:|---:|---:|---:|
| 0.0 | 1.2438 | 1.5192 | 0.9947 |
| 0.1 | 1.2277 | 1.5006 | 0.9948 |
| 1.0 | 1.2556 | 1.5327 | 0.9946 |
| 10.0 | 1.4484 | 1.7330 | 0.9931 |
| 100.0 | 3.7926 | 4.5908 | 0.9514 |

验证集 RMSE 最低的参数为 `alpha = 0.1`。使用训练集与验证集重新拟合后，最终测试集 MAE 为 0.9579，RMSE 为 1.1784，R2 为 0.9972。相比“直接用当前月 AQI 预测下月 AQI”的基线模型，测试集 RMSE 从 7.3321 降低到 1.1784。

结论：污染物均值、优良率、月份周期和区域特征对下月 AQI 具有较强预测能力。验证集上 `alpha = 100` 时误差明显升高，说明过强正则化会造成欠拟合；最终指标来自完全隔离的11—12月测试集。

## 7. 结果文件清单

| 文件 | 内容 |
|---|---|
| `data/analysis_results/analysis_algorithm_report.json` | 分析算法总报告 |
| `data/analysis_results/city_risk_ranking.csv` | 城市污染风险 Top-N |
| `data/analysis_results/kmeans_parameter_eval.csv` | K-Means 参数评估 |
| `data/analysis_results/city_cluster_assignments.csv` | 城市聚类归属 |
| `data/analysis_results/cluster_summary.csv` | 聚类摘要 |
| `data/analysis_results/logistic_parameter_eval.csv` | Logistic Regression 参数评估 |
| `data/analysis_results/logistic_predictions.csv` | 污染风险分类预测结果 |
| `data/analysis_results/ridge_parameter_eval.csv` | Ridge Regression 参数评估 |
| `data/analysis_results/aqi_prediction_predictions.csv` | 下月 AQI 预测结果 |
| `data/analysis_results/ridge_coefficients.csv` | Ridge 模型系数 |

## 8. 报告可写入结论

本项目已完成数据分析算法应用指标：基础层实现 Top-N 风险排名，数据挖掘层实现 K-Means 城市污染画像聚类，机器学习层实现 Logistic Regression 下月污染风险分类，并额外实现 Ridge Regression 下月 AQI 时间序列预测。监督学习采用严格的时间顺序训练/验证/测试划分，参数对比仅使用验证集，最终指标仅使用隔离测试集，避免测试集调参造成的结果高估。
