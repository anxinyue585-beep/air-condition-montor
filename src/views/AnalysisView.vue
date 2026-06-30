<script setup lang="ts">
import analysisReport from '../../data/analysis_results/analysis_algorithm_report.json'
import clusterCsv from '../../data/analysis_results/cluster_summary.csv?raw'
import kmeansCsv from '../../data/analysis_results/kmeans_parameter_eval.csv?raw'
import logisticCsv from '../../data/analysis_results/logistic_parameter_eval.csv?raw'
import ridgeCsv from '../../data/analysis_results/ridge_parameter_eval.csv?raw'
import predictionCsv from '../../data/analysis_results/aqi_prediction_predictions.csv?raw'

interface RiskCity {
  rank: number
  city: string
  province: string
  region: string
  risk_score: number
  avg_aqi: number
  max_aqi: number
  polluted_rate: number
  avg_pm25: number
}

interface ClusterSummary {
  cluster_id: string
  cluster_name: string
  city_count: string
  avg_aqi: string
  max_aqi: string
  avg_polluted_rate: string
  representative_cities: string
}

interface MetricRow {
  [key: string]: string
}

const report = analysisReport
const riskCities = report.top_risk_cities as RiskCity[]
const kmeansRows = parseCsv(kmeansCsv)
const logisticRows = parseCsv(logisticCsv)
const ridgeRows = parseCsv(ridgeCsv)
const predictionRows = parseCsv(predictionCsv).slice(0, 8)
const clusterRows = parseCsv(clusterCsv) as unknown as ClusterSummary[]

const logistic = report.supervised_learning.logistic_regression
const ridge = report.supervised_learning.ridge_regression
const dataset = report.supervised_learning.dataset
const topCity = riskCities[0]
const maxRisk = Math.max(...riskCities.map((item) => item.risk_score))
const bestKmeans = kmeansRows.find((row) => isSameNumber(row.k, report.kmeans.selected_k))
const bestRidge = ridgeRows.find((row) => isSameNumber(row.alpha, ridge.best_alpha))
const bestLogistic = logisticRows.find((row) => isSameNumber(row.lambda, logistic.best_lambda))

function parseCsv(csv: string): MetricRow[] {
  const [headerLine, ...lines] = csv.trim().split(/\r?\n/)
  const headers = headerLine.split(',')
  return lines
    .filter(Boolean)
    .map((line) => {
      const values = line.split(',')
      return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? '']))
    })
}

function percent(value: number | string) {
  return `${(Number(value) * 100).toFixed(1)}%`
}

function fixed(value: number | string, digits = 2) {
  return Number(value).toFixed(digits)
}

function isSameNumber(value: number | string, target: number | string) {
  return Number(value) === Number(target)
}

function riskWidth(value: number) {
  return `${Math.max(4, (value / maxRisk) * 100)}%`
}

function clusterAccent(name: string) {
  if (name.includes('低污染')) return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (name.includes('高污染')) return 'border-rose-200 bg-rose-50 text-rose-700'
  return 'border-amber-200 bg-amber-50 text-amber-700'
}
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p class="text-sm font-semibold text-teal-600">Analysis Workspace</p>
          <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">算法分析中心</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            基于城市月度空气质量数据，展示 Top-N 风险排名、K-Means 聚类、Logistic 风险分类与 Ridge AQI 预测结果。
          </p>
        </div>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
            <p class="text-xs text-slate-500">训练样本</p>
            <p class="mt-1 font-mono text-xl font-bold text-slate-900">{{ dataset.train_count }}</p>
          </div>
          <div class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
            <p class="text-xs text-slate-500">测试样本</p>
            <p class="mt-1 font-mono text-xl font-bold text-slate-900">{{ dataset.test_count }}</p>
          </div>
          <div class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
            <p class="text-xs text-slate-500">聚类数 K</p>
            <p class="mt-1 font-mono text-xl font-bold text-slate-900">{{ report.kmeans.selected_k }}</p>
          </div>
          <div class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
            <p class="text-xs text-slate-500">最高风险城市</p>
            <p class="mt-1 text-xl font-bold text-rose-600">{{ topCity.city }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-2">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900">城市污染风险 Top-N</h2>
            <p class="mt-1 text-sm text-slate-500">综合平均 AQI、最高 AQI、污染率与 PM2.5 计算风险分。</p>
          </div>
          <span class="rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-rose-600">Top 10</span>
        </div>
        <div class="space-y-3">
          <div v-for="city in riskCities" :key="city.city" class="grid grid-cols-[72px_1fr_72px] items-center gap-3">
            <div>
              <p class="font-mono text-xs text-slate-400">#{{ city.rank }}</p>
              <p class="text-sm font-bold text-slate-900">{{ city.city }}</p>
            </div>
            <div class="h-3 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-500" :style="{ width: riskWidth(city.risk_score) }" />
            </div>
            <p class="text-right font-mono text-sm font-bold text-slate-700">{{ fixed(city.risk_score, 1) }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">模型核心指标</h2>
        <div class="mt-5 space-y-4">
          <div class="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-700">Logistic Regression</p>
            <div class="mt-3 grid grid-cols-2 gap-3 text-sm">
              <span class="text-slate-500">Accuracy</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ fixed(logistic.accuracy, 4) }}</span>
              <span class="text-slate-500">F1</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ fixed(logistic.f1, 4) }}</span>
              <span class="text-slate-500">Recall</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ fixed(logistic.recall, 4) }}</span>
            </div>
          </div>
          <div class="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-700">Ridge Regression</p>
            <div class="mt-3 grid grid-cols-2 gap-3 text-sm">
              <span class="text-slate-500">Alpha</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ ridge.best_alpha }}</span>
              <span class="text-slate-500">RMSE</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ fixed(ridge.rmse, 4) }}</span>
              <span class="text-slate-500">R2</span>
              <span class="text-right font-mono font-bold text-slate-900">{{ fixed(ridge.r2, 4) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div
        v-for="cluster in clusterRows"
        :key="cluster.cluster_id"
        class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm"
      >
        <span class="rounded-full border px-3 py-1 text-xs font-bold" :class="clusterAccent(cluster.cluster_name)">
          {{ cluster.cluster_name }}
        </span>
        <div class="mt-5 grid grid-cols-3 gap-3">
          <div>
            <p class="text-xs text-slate-500">城市数</p>
            <p class="font-mono text-xl font-bold text-slate-900">{{ cluster.city_count }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-500">平均 AQI</p>
            <p class="font-mono text-xl font-bold text-slate-900">{{ cluster.avg_aqi }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-500">污染率</p>
            <p class="font-mono text-xl font-bold text-slate-900">{{ percent(cluster.avg_polluted_rate) }}</p>
          </div>
        </div>
        <p class="mt-5 text-sm leading-6 text-slate-500">{{ cluster.representative_cities }}</p>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">参数对比</h2>
        <div class="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-700">K-Means</p>
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="row in kmeansRows" :key="row.k" class="border-t border-slate-100">
                  <td class="py-2 text-slate-500">k={{ row.k }}</td>
                  <td class="py-2 text-right font-mono" :class="isSameNumber(row.k, report.kmeans.selected_k) ? 'font-bold text-teal-600' : 'text-slate-700'">
                    {{ row.silhouette }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="bestKmeans" class="mt-2 text-xs text-slate-400">选用 k={{ bestKmeans.k }}，轮廓系数 {{ bestKmeans.silhouette }}</p>
          </div>
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-700">Logistic</p>
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="row in logisticRows" :key="row.lambda" class="border-t border-slate-100">
                  <td class="py-2 text-slate-500">λ={{ row.lambda }}</td>
                  <td class="py-2 text-right font-mono" :class="isSameNumber(row.lambda, logistic.best_lambda) ? 'font-bold text-teal-600' : 'text-slate-700'">
                    F1 {{ row.f1 }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="bestLogistic" class="mt-2 text-xs text-slate-400">最佳 λ={{ bestLogistic.lambda }}，准确率 {{ bestLogistic.accuracy }}</p>
          </div>
          <div>
            <p class="mb-2 text-sm font-semibold text-slate-700">Ridge</p>
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="row in ridgeRows" :key="row.alpha" class="border-t border-slate-100">
                  <td class="py-2 text-slate-500">α={{ row.alpha }}</td>
                  <td class="py-2 text-right font-mono" :class="isSameNumber(row.alpha, ridge.best_alpha) ? 'font-bold text-teal-600' : 'text-slate-700'">
                    RMSE {{ row.rmse }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="bestRidge" class="mt-2 text-xs text-slate-400">最佳 α={{ bestRidge.alpha }}，R2 {{ bestRidge.r2 }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900">下月 AQI 预测样本</h2>
            <p class="mt-1 text-sm text-slate-500">Ridge Regression 测试集部分预测结果。</p>
          </div>
          <span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700">RMSE {{ fixed(ridge.rmse, 2) }}</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[620px] text-left text-sm">
            <thead class="border-b border-slate-100 text-xs text-slate-500">
              <tr>
                <th class="py-3">城市</th>
                <th class="py-3">月份</th>
                <th class="py-3 text-right">实际 AQI</th>
                <th class="py-3 text-right">预测 AQI</th>
                <th class="py-3 text-right">误差</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in predictionRows" :key="`${row.city}-${row.target_month}`" class="border-b border-slate-50">
                <td class="py-3 font-bold text-slate-900">{{ row.city }}</td>
                <td class="py-3 font-mono text-slate-500">{{ row.target_month }}</td>
                <td class="py-3 text-right font-mono text-slate-700">{{ fixed(row.actual_next_avg_aqi) }}</td>
                <td class="py-3 text-right font-mono text-slate-700">{{ fixed(row.predicted_next_avg_aqi) }}</td>
                <td class="py-3 text-right font-mono font-bold text-teal-600">{{ fixed(row.absolute_error) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>
