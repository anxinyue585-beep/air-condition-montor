<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getPollutionWarnings, type PollutionWarningResult, type WarningCity } from '../api'

const result = ref<PollutionWarningResult | null>(null)
const selected = ref<WarningCity | null>(null)
const loading = ref(true)
const query = ref('')
const page = ref(1)
const pageSize = 10
const distributionEl = ref<HTMLElement | null>(null)
const riskEl = ref<HTMLElement | null>(null)
const confusionEl = ref<HTMLElement | null>(null)
const timelineEl = ref<HTMLElement | null>(null)
let charts: echarts.ECharts[] = []
let timelineChart: echarts.ECharts | null = null

const levelMeta = {
  red: { label: '红色预警', style: 'bg-rose-100 text-rose-800 ring-1 ring-inset ring-rose-200', color: '#e11d48' },
  orange: { label: '橙色预警', style: 'bg-orange-100 text-orange-800 ring-1 ring-inset ring-orange-200', color: '#f97316' },
  yellow: { label: '黄色预警', style: 'bg-amber-100 text-amber-900 ring-1 ring-inset ring-amber-200', color: '#facc15' },
  blue: { label: '蓝色预警', style: 'bg-sky-100 text-sky-800 ring-1 ring-inset ring-sky-200', color: '#0ea5e9' },
  none: { label: '暂无预警', style: 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200', color: '#cbd5e1' },
} as const
const warningKeys = ['red', 'orange', 'yellow', 'blue'] as const
const cities = computed(() => (result.value?.cities ?? [])
  .filter((item) => !query.value || item.city.includes(query.value.trim()) || item.province.includes(query.value.trim()))
  .sort((a, b) => b.probability - a.probability))
const totalPages = computed(() => Math.max(1, Math.ceil(cities.value.length / pageSize)))
const pagedCities = computed(() => cities.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const pageNumbers = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1))
const metrics = computed(() => result.value?.model.test_metrics ?? {})

function percent(value: number) { return `${(value * 100).toFixed(1)}%` }
function stage(value: string) { return ({ forming: '形成期', persistent: '持续期', dissipating: '消散期', normal: '正常' } as Record<string, string>)[value] ?? value }
function factorWidth(value: number) { return `${Math.min(100, Math.max(8, Math.abs(value) * 20))}%` }
function goToPage(next: number) { page.value = Math.min(totalPages.value, Math.max(1, next)) }

function createChart(el: HTMLElement | null, option: echarts.EChartsOption) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function renderCharts() {
  if (!result.value) return
  charts.forEach((chart) => chart.dispose())
  charts = []
  const counts = result.value.summary.warning_level_counts
  createChart(distributionEl.value, {
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 个城市（{d}%）' },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    series: [{ type: 'pie', radius: ['48%', '72%'], center: ['50%', '43%'], label: { formatter: '{c}', fontWeight: 700 },
      data: (Object.keys(levelMeta) as Array<keyof typeof levelMeta>).map((key) => ({ value: counts[key] ?? 0, name: levelMeta[key].label, itemStyle: { color: levelMeta[key].color } })) }],
  })
  const top = result.value.cities.slice().sort((a, b) => b.probability - a.probability).slice(0, 10).reverse()
  createChart(riskEl.value, {
    grid: { left: 48, right: 42, top: 12, bottom: 28 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => percent(Number(value)) },
    xAxis: { type: 'value', max: 1, axisLabel: { formatter: (value: number) => `${value * 100}%` }, splitLine: { lineStyle: { color: '#eef2f7' } } },
    yAxis: { type: 'category', data: top.map((item) => item.city), axisTick: { show: false }, axisLine: { show: false } },
    series: [{ type: 'bar', data: top.map((item) => item.probability), barWidth: 14, itemStyle: { color: '#14b8a6', borderRadius: [0, 7, 7, 0] }, label: { show: true, position: 'right', formatter: ({ value }) => percent(Number(value)) } }],
  })
  const tn = Number(metrics.value.tn ?? 0), fp = Number(metrics.value.fp ?? 0)
  const fn = Number(metrics.value.fn ?? 0), tp = Number(metrics.value.tp ?? 0)
  createChart(confusionEl.value, {
    tooltip: { formatter: ({ data }: any) => `样本数：${data[2]}` },
    grid: { left: 72, right: 30, top: 18, bottom: 48 },
    xAxis: { type: 'category', data: ['预测正常', '预测污染'], splitArea: { show: true } },
    yAxis: { type: 'category', data: ['实际正常', '实际污染'], splitArea: { show: true } },
    visualMap: { show: false, min: 0, max: Math.max(tn, fp, fn, tp, 1), inRange: { color: ['#ecfeff', '#14b8a6', '#115e59'] } },
    series: [{ type: 'heatmap', data: [[0, 0, tn], [1, 0, fp], [0, 1, fn], [1, 1, tp]], label: { show: true, color: '#0f172a', fontSize: 15, fontWeight: 700 } }],
  })
}

function renderTimeline() {
  if (!timelineEl.value || !selected.value) return
  timelineChart?.dispose()
  const points = selected.value.timeline
  timelineChart = echarts.init(timelineEl.value)
  timelineChart.setOption({
    grid: { left: 46, right: 18, top: 26, bottom: 48 },
    tooltip: {
      trigger: 'axis',
      formatter: (items: any) => {
        const item = Array.isArray(items) ? items[0] : items
        const point = points[item.dataIndex]
        return `${point.datetime}<br/>风险概率：${percent(point.probability)}<br/>实际：${point.actual ? '污染过程' : '正常'}`
      },
    },
    xAxis: { type: 'category', data: points.map((point) => point.datetime.slice(5, 16)), axisLabel: { interval: 4, color: '#64748b', fontSize: 10 }, axisTick: { show: false } },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { formatter: (value: number) => `${value * 100}%`, color: '#64748b' }, splitLine: { lineStyle: { color: '#eef2f7' } } },
    series: [{
      name: '风险概率',
      type: 'bar',
      barMaxWidth: 20,
      data: points.map((point) => ({ value: point.probability, itemStyle: { color: point.actual ? '#f43f5e' : '#14b8a6', borderRadius: [4, 4, 0, 0] } })),
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#f59e0b', type: 'dashed', width: 2 },
        label: { formatter: '预警阈值 50%', position: 'insideEndTop', color: '#92400e', backgroundColor: 'rgba(255,255,255,0.9)', padding: [2, 5], borderRadius: 3 },
        data: [{ yAxis: 0.5 }],
      },
    }],
  })
}

function resizeCharts() { charts.forEach((chart) => chart.resize()); timelineChart?.resize() }
watch(query, () => { page.value = 1 })
watch(selected, async () => { await nextTick(); requestAnimationFrame(renderTimeline) })
onMounted(async () => {
  result.value = await getPollutionWarnings()
  selected.value = result.value.cities[0] ?? null
  loading.value = false
  await nextTick()
  requestAnimationFrame(() => requestAnimationFrame(() => { renderCharts(); renderTimeline() }))
  window.addEventListener('resize', resizeCharts)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  charts.forEach((chart) => chart.dispose())
  timelineChart?.dispose()
})
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-xl border border-slate-100 bg-white p-7 shadow-sm">
      <p class="text-sm font-semibold text-teal-600">Early Warning · Explainable AI</p>
      <div class="mt-1 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div><h1 class="text-3xl font-bold text-slate-900">污染过程预警与可解释性分析</h1><p class="mt-3 max-w-3xl text-sm leading-6 text-slate-500">预测未来 6 小时内是否出现连续 3 小时 AQI &gt; 100，并分解每项特征对风险概率的正负贡献。</p></div>
        <span v-if="result" class="rounded-full bg-teal-50 px-4 py-2 text-xs font-bold text-teal-700">{{ result.model.algorithm }}</span>
      </div>
    </section>
    <div v-if="loading" class="rounded-xl bg-white p-12 text-center text-slate-500">正在加载预警模型结果…</div>
    <template v-else-if="result && selected">
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-6">
        <div class="rounded-xl bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">最高风险城市</p><p class="mt-2 text-xl font-bold text-rose-600">{{ result.summary.highest_risk_city }}</p></div>
        <div v-for="key in warningKeys" :key="key" class="rounded-xl bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">{{ levelMeta[key].label }}</p><p class="mt-2 font-mono text-2xl font-bold">{{ result.summary.warning_level_counts[key] ?? 0 }}</p></div>
        <div class="rounded-xl bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">测试集 F1 / Recall</p><p class="mt-2 font-mono text-lg font-bold text-teal-700">{{ Number(metrics.f1).toFixed(3) }} / {{ Number(metrics.recall).toFixed(3) }}</p></div>
      </section>

      <section class="grid gap-6 xl:grid-cols-3">
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><h2 class="font-bold text-slate-900">四级预警分布</h2><p class="mt-1 text-xs text-slate-500">60 个城市的当前预警等级构成</p><div ref="distributionEl" class="mt-2" style="height: 300px" /></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><h2 class="font-bold text-slate-900">城市风险 Top 10</h2><p class="mt-1 text-xs text-slate-500">按污染过程发生概率排序</p><div ref="riskEl" class="mt-2" style="height: 300px" /></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><h2 class="font-bold text-slate-900">测试集混淆矩阵</h2><p class="mt-1 text-xs text-slate-500">展示模型预测与实际标签的对应关系</p><div ref="confusionEl" class="mt-2" style="height: 300px" /></div>
      </section>

      <section class="grid grid-cols-[250px_minmax(0,1fr)] items-stretch gap-4 lg:grid-cols-[320px_minmax(0,1fr)] lg:gap-6">
        <aside class="h-full rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <h2 class="font-bold text-slate-900">高风险城市速览</h2>
          <div class="mt-3 space-y-1"><button v-for="city in cities.slice(0, 10)" :key="city.city" class="grid w-full grid-cols-[1fr_auto] items-center rounded-lg px-3 py-2.5 text-left" :class="selected.city === city.city ? 'bg-teal-50 ring-1 ring-teal-200' : 'hover:bg-slate-50'" @click="selected = city"><span><b>{{ city.city }}</b><small class="ml-2 text-slate-400">{{ stage(city.current_stage) }}</small></span><span class="rounded-full px-2 py-1 text-xs font-bold" :class="levelMeta[city.warning_level].style">{{ percent(city.probability) }}</span></button></div>
        </aside>
        <div class="space-y-6">
          <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm"><div class="flex flex-col justify-between gap-3 sm:flex-row"><div><p class="text-xs font-bold uppercase text-slate-400">Selected city</p><h2 class="mt-1 text-3xl font-bold text-slate-900">{{ selected.city }}</h2><p class="text-sm text-slate-500">{{ selected.province }} · {{ selected.datetime }} · {{ stage(selected.current_stage) }}</p></div><div class="text-right"><span class="rounded-full px-4 py-2 text-sm font-bold" :class="levelMeta[selected.warning_level].style">{{ levelMeta[selected.warning_level].label }}</span><p class="mt-3 font-mono text-3xl font-bold text-slate-900">{{ percent(selected.probability) }}</p></div></div><p class="mt-6 rounded-lg border border-teal-100 bg-teal-50 p-4 text-sm leading-6 text-teal-900">{{ selected.explanation_text }}</p></section>
          <section class="grid gap-6 lg:grid-cols-2">
            <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm"><h3 class="font-bold text-slate-900">为什么触发预警</h3><p class="mt-1 text-xs text-slate-500">标准化特征 × Logistic 系数，红色抬升风险，绿色降低风险。</p><div class="mt-5 space-y-4"><div v-for="factor in selected.explanations" :key="factor.feature"><div class="mb-1 flex justify-between text-sm"><span class="font-semibold">{{ factor.label }} <small class="text-slate-400">{{ factor.value }}</small></span><span class="font-mono" :class="factor.direction === 'increase' ? 'text-rose-600' : 'text-emerald-600'">{{ factor.contribution > 0 ? '+' : '' }}{{ factor.contribution.toFixed(3) }}</span></div><div class="h-2 overflow-hidden rounded-full bg-slate-100"><div class="h-full rounded-full" :class="factor.direction === 'increase' ? 'bg-rose-500' : 'bg-emerald-500'" :style="{ width: factorWidth(factor.contribution) }" /></div></div></div></div>
            <div class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm"><h3 class="font-bold text-slate-900">近期风险时间轴</h3><p class="mt-1 text-xs text-slate-500">测试时段最近 20 个六小时间隔预测；红色代表实际发生污染过程，绿色代表实际正常。</p><div ref="timelineEl" class="mt-3 w-full" style="height: 260px" /></div>
          </section>
        </div>
      </section>

      <section class="overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm">
        <div class="flex flex-col gap-3 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between"><div><h2 class="font-bold text-slate-900">城市风险数据排行</h2><p class="mt-1 text-xs text-slate-500">共 {{ cities.length }} 条结果，每页 {{ pageSize }} 条；点击行可切换城市详情</p></div><input v-model="query" class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-teal-400 sm:w-60" placeholder="搜索城市或省份" /></div>
        <div class="overflow-x-auto"><table class="w-full min-w-[820px] text-left text-sm"><thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="px-5 py-3">排名</th><th class="px-5 py-3">城市</th><th class="px-5 py-3">省份</th><th class="px-5 py-3">过程阶段</th><th class="px-5 py-3">当前 AQI</th><th class="px-5 py-3">风险概率</th><th class="px-5 py-3">预警等级</th><th class="px-5 py-3">实际标签</th></tr></thead><tbody class="divide-y divide-slate-100"><tr v-for="(city, index) in pagedCities" :key="city.city" class="cursor-pointer transition-colors hover:bg-teal-50/60" :class="selected.city === city.city ? 'bg-teal-50' : ''" @click="selected = city"><td class="px-5 py-3 font-mono text-slate-400">{{ (page - 1) * pageSize + index + 1 }}</td><td class="px-5 py-3 font-bold text-slate-900">{{ city.city }}</td><td class="px-5 py-3 text-slate-500">{{ city.province }}</td><td class="px-5 py-3">{{ stage(city.current_stage) }}</td><td class="px-5 py-3 font-mono">{{ city.current_aqi.toFixed(1) }}</td><td class="px-5 py-3 font-mono font-bold text-teal-700">{{ percent(city.probability) }}</td><td class="px-5 py-3"><span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="levelMeta[city.warning_level].style">{{ levelMeta[city.warning_level].label }}</span></td><td class="px-5 py-3"><span :class="city.actual ? 'text-rose-600' : 'text-emerald-600'">{{ city.actual ? '污染过程' : '正常' }}</span></td></tr><tr v-if="!pagedCities.length"><td colspan="8" class="px-5 py-12 text-center text-slate-400">没有匹配的城市</td></tr></tbody></table></div>
        <div class="flex flex-col gap-3 border-t border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-xs text-slate-500">第 {{ page }} / {{ totalPages }} 页</p><div class="flex flex-wrap items-center gap-1"><button class="rounded-lg border border-slate-200 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40" :disabled="page === 1" @click="goToPage(page - 1)">上一页</button><button v-for="number in pageNumbers" :key="number" class="h-8 min-w-8 rounded-lg px-2 text-xs font-bold" :class="page === number ? 'bg-slate-950 text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'" @click="goToPage(number)">{{ number }}</button><button class="rounded-lg border border-slate-200 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40" :disabled="page === totalPages" @click="goToPage(page + 1)">下一页</button></div></div>
      </section>
    </template>
  </div>
</template>
