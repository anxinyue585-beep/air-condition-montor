<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getHiveMonthly, getLineage, getProcessingStatus } from '../api'
import type { HiveMonthlyResult, LineageResult, ProcessingStatus } from '../api'

const lineage = ref<LineageResult | null>(null)
const processing = ref<ProcessingStatus | null>(null)
const hive = ref<HiveMonthlyResult | null>(null)
const loading = ref(true)
const errorMessage = ref('')

const sourceLabel = computed(() =>
  processing.value?.current_query_source === 'spark_export' ? 'Spark 城市日输出' : '本地 Warehouse 回退',
)

function statusClass(status: string) {
  if (status === 'passed') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (status === 'failed') return 'border-rose-200 bg-rose-50 text-rose-700'
  return 'border-amber-200 bg-amber-50 text-amber-700'
}

function statusText(status: string) {
  if (status === 'passed') return '已通过'
  if (status === 'failed') return '失败'
  return '待处理'
}

function localTime(value: string | null | undefined) {
  if (!value) return '暂无'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function refresh() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [lineageResult, processingResult, hiveResult] = await Promise.all([
      getLineage(),
      getProcessingStatus(),
      getHiveMonthly(),
    ])
    lineage.value = lineageResult
    processing.value = processingResult
    hive.value = hiveResult
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '处理状态加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p class="text-sm font-semibold text-teal-600">Data Lineage & Processing Status</p>
          <h1 class="mt-1 text-2xl font-bold text-slate-900">数据血缘与处理状态</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            展示数据从来源、清洗、HDFS、Hive/Spark、FastAPI 到 Vue 的流转，并明确当前页面实际读取的数据源。
          </p>
        </div>
        <button type="button" class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white hover:bg-slate-800" @click="refresh">
          刷新状态
        </button>
      </div>
    </section>

    <div v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ errorMessage }}</div>
    <div v-if="loading" class="rounded-xl bg-white p-10 text-center text-sm text-slate-400">正在读取处理状态...</div>

    <template v-else-if="lineage && processing">
      <section class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-400">当前可视化查询源</p>
          <p class="mt-2 text-xl font-bold" :class="processing.platform_export_available ? 'text-teal-600' : 'text-amber-600'">{{ sourceLabel }}</p>
          <p class="mt-2 text-xs text-slate-400">更新时间：{{ localTime(processing.current_query_updated_at) }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-400">平台验收</p>
          <p class="mt-2 text-xl font-bold" :class="lineage.verification_status === 'passed' ? 'text-emerald-600' : 'text-rose-600'">
            {{ statusText(lineage.verification_status) }}
          </p>
          <p class="mt-2 line-clamp-2 text-xs text-slate-400">{{ lineage.verification_message }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-400">Open-Meteo</p>
          <p class="mt-2 text-xl font-bold" :class="processing.open_meteo.available ? 'text-emerald-600' : 'text-rose-600'">
            {{ processing.open_meteo.available ? '快照可用' : '暂无快照' }}
          </p>
          <p class="mt-2 text-xs text-slate-400">更新时间：{{ localTime(processing.open_meteo.updated_at) }}</p>
        </div>
      </section>

      <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">处理链路</h2>
        <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-7">
          <div v-for="(node, index) in lineage.nodes" :key="node.id" class="relative">
            <div class="h-full rounded-lg border p-4" :class="statusClass(node.status)">
              <div class="flex items-center justify-between gap-2">
                <p class="font-bold">{{ node.label }}</p>
                <span class="text-[10px] font-bold">{{ statusText(node.status) }}</span>
              </div>
              <p class="mt-2 text-xs leading-5 opacity-80">{{ node.detail }}</p>
            </div>
            <span v-if="index < lineage.nodes.length - 1" class="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 text-slate-300 xl:block">→</span>
          </div>
        </div>
      </section>

      <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex items-end justify-between gap-4">
          <div>
            <h2 class="text-lg font-bold text-slate-900">Hive 城市月度输出</h2>
            <p class="mt-1 text-sm text-slate-500">仅展示真实 Hive 导出文件，不使用本地 CSV 伪造结果。</p>
          </div>
          <span class="rounded-full px-3 py-1 text-xs font-bold" :class="hive?.available ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
            {{ hive?.available ? `已导出 ${hive.total} 条` : '等待 Hive 验收' }}
          </span>
        </div>
        <div v-if="hive?.available" class="mt-5 overflow-x-auto">
          <table class="w-full min-w-[760px] text-left text-sm">
            <thead class="border-b border-slate-100 text-xs text-slate-400">
              <tr><th class="py-3">城市</th><th>月份</th><th class="text-right">平均AQI</th><th class="text-right">最高AQI</th><th class="text-right">优良率</th><th class="text-right">PM2.5</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in hive.items" :key="`${row.city}-${row.year_month}`" class="border-b border-slate-50">
                <td class="py-3 font-bold text-slate-900">{{ row.city }}</td><td>{{ row.year_month }}</td><td class="text-right">{{ row.avg_aqi }}</td><td class="text-right">{{ row.max_aqi }}</td><td class="text-right">{{ row.good_rate }}</td><td class="text-right">{{ row.avg_pm25 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="mt-5 rounded-lg border border-dashed border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-700">
          当前机器缺少 Docker，尚无真实 Hive 查询导出。安装并跑通平台后，执行验收脚本会生成 `data/platform_exports/hive/air_quality_city_month.csv`，本页随后自动显示结果。
        </div>
      </section>
    </template>
  </div>
</template>
