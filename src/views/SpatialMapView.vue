<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getSpatialAnalysis, type SpatialAnalysisResult, type SpatialCity } from '../api'
import chinaGeoJson from '../assets/maps/china.geo.json'

echarts.registerMap('china', chinaGeoJson as never)

type ChinaFeature = { properties?: { name?: string } }
const provincePalette = ['#f8d7da', '#d9ead3', '#fff2cc', '#d9eaf7', '#eadcf8', '#fce5cd', '#d0e0e3', '#f4cccc', '#d9d2e9', '#cfe2f3', '#e2f0d9', '#fde9d9']
const chinaRegions = ((chinaGeoJson as { features: ChinaFeature[] }).features ?? []).flatMap((feature, index) => {
  const name = feature.properties?.name
  return name ? [{ name, itemStyle: { areaColor: provincePalette[index % provincePalette.length] } }] : []
})

const chartEl = ref<HTMLElement | null>(null)
const result = ref<SpatialAnalysisResult | null>(null)
const loading = ref(true)
const error = ref('')
const mode = ref<'aqi' | 'lisa'>('lisa')
const selectedCity = ref<SpatialCity | null>(null)
const citySearch = ref('')
const cityIndexPage = ref(1)
const cityIndexPageSize = 10
const lisaPage = ref(1)
const lisaPageSize = 10
let chart: echarts.ECharts | null = null
let chartObserver: ResizeObserver | null = null
let updateFrame = 0

const colors: Record<string, string> = {
  'High-High': '#e11d48',
  'Low-Low': '#0d9488',
  'High-Low': '#f59e0b',
  'Low-High': '#6366f1',
  'Not significant': '#94a3b8',
}

const significantCities = computed(() => result.value?.cities.filter((city) => city.significant) ?? [])
const sortedCities = computed(() => [...(result.value?.cities ?? [])].sort((a, b) => b.local_moran_i - a.local_moran_i))
const lisaTotalPages = computed(() => Math.max(1, Math.ceil(sortedCities.value.length / lisaPageSize)))
const pagedLisaCities = computed(() => sortedCities.value.slice((lisaPage.value - 1) * lisaPageSize, lisaPage.value * lisaPageSize))
const lisaPageNumbers = computed(() => Array.from({ length: lisaTotalPages.value }, (_, index) => index + 1))
const filteredCities = computed(() => {
  const query = citySearch.value.trim().toLocaleLowerCase()
  return sortedCities.value.filter((city) => !query || city.city.toLocaleLowerCase().includes(query) || city.province.toLocaleLowerCase().includes(query))
})
const cityIndexTotalPages = computed(() => Math.max(1, Math.ceil(filteredCities.value.length / cityIndexPageSize)))
const pagedIndexCities = computed(() => filteredCities.value.slice((cityIndexPage.value - 1) * cityIndexPageSize, cityIndexPage.value * cityIndexPageSize))
const cityIndexPageNumbers = computed(() => Array.from({ length: cityIndexTotalPages.value }, (_, index) => index + 1))

function fixed(value: number, digits = 3) {
  return value.toFixed(digits)
}

function clusterName(cluster: string) {
  return {
    'High-High': '高—高聚集',
    'Low-Low': '低—低聚集',
    'High-Low': '高—低异常',
    'Low-High': '低—高异常',
    'Not significant': '不显著',
  }[cluster] ?? cluster
}

function renderChart() {
  if (!chartEl.value || !result.value) return
  if (chartEl.value.clientWidth === 0 || chartEl.value.clientHeight === 0) return
  chart ??= echarts.init(chartEl.value)
  const cities = result.value.cities
  const series: echarts.SeriesOption[] = mode.value === 'aqi'
      ? [{
        id: 'city-aqi-points',
        name: '城市年均 AQI',
        type: 'scatter' as const,
        coordinateSystem: 'geo' as const,
        data: cities.map((city) => ({ name: city.city, value: [city.longitude, city.latitude, city.avg_aqi], city })),
        symbolSize: (value: number[]) => Math.max(7, Math.min(15, 7 + (value[2] - 40) / 10)),
        itemStyle: { borderColor: '#fff', borderWidth: 1.2, shadowBlur: 3, shadowColor: 'rgba(15,23,42,.16)' },
        emphasis: { scale: 1.35, itemStyle: { shadowBlur: 10, shadowColor: 'rgba(15,23,42,.28)' } },
      }]
    : Object.keys(colors).map((cluster) => ({
        id: `city-lisa-${cluster}`,
        name: clusterName(cluster),
        type: 'scatter' as const,
        coordinateSystem: 'geo' as const,
        data: cities.filter((city) => city.cluster === cluster).map((city) => ({ name: city.city, value: [city.longitude, city.latitude, city.avg_aqi], city })),
        symbolSize: (value: number[]) => Math.max(7, Math.min(13, value[2] / 8)),
        itemStyle: { color: colors[cluster], borderColor: '#fff', borderWidth: 1.2, shadowBlur: 2, shadowColor: 'rgba(15,23,42,.14)' },
        emphasis: { scale: 1.4, itemStyle: { shadowBlur: 10, shadowColor: 'rgba(15,23,42,.3)' } },
      }))

  if (selectedCity.value) {
    const selected = selectedCity.value
    const byName = new Map(cities.map((city) => [city.city, city]))
    series.unshift({
      id: 'neighbor-lines',
      name: 'K=6 邻接关系',
      type: 'lines',
      coordinateSystem: 'geo',
      silent: true,
      z: 1,
      data: selected.neighbors.map((name) => {
        const neighbor = byName.get(name)!
        return { coords: [[selected.longitude, selected.latitude], [neighbor.longitude, neighbor.latitude]] }
      }),
      lineStyle: { color: '#0f766e', width: 1.5, opacity: 0.55, type: 'dashed', curveness: 0.08 },
    })
    series.push({
      id: 'selected-city',
      name: '当前城市',
      type: 'effectScatter',
      coordinateSystem: 'geo',
      z: 10,
      data: [{ name: selected.city, value: [selected.longitude, selected.latitude, selected.avg_aqi] }],
      symbolSize: 15,
      rippleEffect: { scale: 2.1, period: 3.5, number: 2, brushType: 'stroke' },
      label: { show: true, position: 'top', formatter: selected.city, color: '#0f172a', fontWeight: 'bold', backgroundColor: 'rgba(255,255,255,.9)', padding: [3, 6], borderRadius: 4 },
      itemStyle: { color: '#0f172a', borderColor: '#fff', borderWidth: 2 },
    })
  }

  chart.setOption({
    backgroundColor: '#dff3fa',
    animationDuration: 420,
    animationDurationUpdate: 260,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    toolbox: { right: 8, bottom: 8, feature: { restore: {}, saveAsImage: { title: '保存地图' } } },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.12,
      top: 52,
      bottom: 18,
      left: 20,
      right: 20,
      scaleLimit: { min: 0.85, max: 8 },
      regions: chinaRegions,
      label: { show: true, color: '#9f1239', fontSize: 9, fontWeight: 500 },
      itemStyle: { areaColor: '#f1f5f9', borderColor: '#64748b', borderWidth: 1 },
      emphasis: { label: { show: true, color: '#0f172a', fontWeight: 'bold' }, itemStyle: { areaColor: '#fef08a', borderColor: '#334155', borderWidth: 1.4 } },
      select: { itemStyle: { areaColor: '#99f6e4' } },
    },
    legend: mode.value === 'lisa' ? { top: 8, textStyle: { color: '#64748b' } } : undefined,
    visualMap: mode.value === 'aqi' ? {
      min: Math.floor(Math.min(...cities.map((city) => city.avg_aqi))),
      max: Math.ceil(Math.max(...cities.map((city) => city.avg_aqi))),
      right: 10,
      top: 20,
      text: ['高 AQI', '低 AQI'],
      calculable: true,
      inRange: { color: ['#14b8a6', '#facc15', '#f97316', '#e11d48'] },
    } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: (params: { data?: { city?: SpatialCity } }) => {
        const city = params.data?.city
        if (!city) return ''
        return `<b>${city.city}</b><br/>2025 年均 AQI：${city.avg_aqi}<br/>LISA：${clusterName(city.cluster)}<br/>Local I：${city.local_moran_i}<br/>p：${city.p_value}`
      },
    },
    series,
  }, { notMerge: false, lazyUpdate: true, replaceMerge: ['series', 'legend', 'visualMap'] })
  chart.off('click')
  chart.on('click', (params) => {
    const data = params.data as { city?: SpatialCity } | undefined
    const city = data?.city ?? result.value?.cities.find((item) => item.city === params.name)
    if (city) selectedCity.value = city
  })
}

function selectCity(city: SpatialCity) {
  selectedCity.value = city
}

function goToLisaPage(next: number) {
  lisaPage.value = Math.min(lisaTotalPages.value, Math.max(1, next))
}

function goToCityIndexPage(next: number) {
  cityIndexPage.value = Math.min(cityIndexTotalPages.value, Math.max(1, next))
}

function resize() {
  chart?.resize()
}

onMounted(async () => {
  try {
    result.value = await getSpatialAnalysis()
    selectedCity.value = result.value.cities.find((city) => city.cluster === 'High-High') ?? result.value.cities[0]
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : String(reason)
  } finally {
    loading.value = false
    await nextTick()
    chartObserver = new ResizeObserver(() => {
      if (!chart && result.value) renderChart()
      else chart?.resize()
    })
    if (chartEl.value) chartObserver.observe(chartEl.value)
    requestAnimationFrame(() => requestAnimationFrame(renderChart))
    window.addEventListener('resize', resize)
  }
})

watch([mode, selectedCity], () => {
  cancelAnimationFrame(updateFrame)
  updateFrame = requestAnimationFrame(renderChart)
})
watch(citySearch, () => { cityIndexPage.value = 1 })
onBeforeUnmount(() => {
  cancelAnimationFrame(updateFrame)
  window.removeEventListener('resize', resize)
  chartObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div class="space-y-6">
    <section class="overflow-hidden rounded-xl border border-slate-100 bg-white p-7 shadow-sm">
      <div class="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <div>
          <p class="text-sm font-semibold text-teal-600">Spatial Intelligence · Innovation Module</p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">城市空气质量空间相关性</h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
            基于 2025 年全国 60 城市平均 AQI，使用 K=6 行标准化近邻权重与 999 次 Monte Carlo 置换检验识别空间聚集和异常城市。
          </p>
        </div>
        <div v-if="result" class="flex gap-3">
          <button v-for="item in [{ key: 'lisa', label: 'LISA 聚类' }, { key: 'aqi', label: 'AQI 热度' }]" :key="item.key" type="button"
            class="rounded-lg border px-4 py-2 text-sm font-bold transition" :class="mode === item.key ? 'border-teal-500 bg-teal-500 text-white shadow-sm' : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-teal-200 hover:bg-teal-50 hover:text-teal-700'"
            @click="mode = item.key as 'aqi' | 'lisa'">{{ item.label }}</button>
        </div>
      </div>
    </section>

    <div v-if="loading" class="rounded-xl bg-white p-12 text-center text-slate-500 shadow-sm">正在加载空间分析结果…</div>
    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-700">{{ error }}</div>
    <template v-else-if="result">
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">全局 Moran's I</p><p class="mt-2 font-mono text-2xl font-bold text-teal-700">{{ fixed(result.global_moran.observed_i, 4) }}</p></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">置换伪 p 值</p><p class="mt-2 font-mono text-2xl font-bold text-rose-600">{{ fixed(result.global_moran.pseudo_p_value, 3) }}</p></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">High–High</p><p class="mt-2 font-mono text-2xl font-bold text-rose-600">{{ result.cluster_counts['High-High'] ?? 0 }}</p></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">Low–Low</p><p class="mt-2 font-mono text-2xl font-bold text-teal-600">{{ result.cluster_counts['Low-Low'] ?? 0 }}</p></div>
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"><p class="text-xs text-slate-500">显著城市</p><p class="mt-2 font-mono text-2xl font-bold text-slate-900">{{ significantCities.length }} / 60</p></div>
      </section>

      <section class="grid items-stretch gap-6 xl:grid-cols-[minmax(0,1.8fr)_minmax(300px,1fr)_minmax(300px,1fr)]">
        <div class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <div class="mb-3 flex items-center justify-between"><div><h2 class="text-lg font-bold text-slate-900">全国城市空间分布地图</h2><p class="text-sm text-slate-500">地图常驻显示；滚轮缩放、拖拽平移，点击城市查看完整数据。</p></div><span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700">交互地图</span></div>
          <div ref="chartEl" class="w-full" style="width: 100%; height: 640px; min-height: 560px" />
        </div>
        <aside v-if="selectedCity" class="h-full rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between"><div><p class="text-xs font-bold uppercase tracking-wider text-slate-400">Selected city</p><h2 class="mt-1 text-2xl font-bold text-slate-900">{{ selectedCity.city }}</h2><p class="text-sm text-slate-500">{{ selectedCity.province }} · {{ selectedCity.region }}</p></div><span class="rounded-full px-3 py-1 text-xs font-bold text-white" :style="{ backgroundColor: colors[selectedCity.cluster] }">{{ clusterName(selectedCity.cluster) }}</span></div>
          <dl class="mt-6 grid grid-cols-2 gap-4">
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">年均 AQI</dt><dd class="mt-1 font-mono text-xl font-bold">{{ selectedCity.avg_aqi }}</dd></div>
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">Local Moran's I</dt><dd class="mt-1 font-mono text-xl font-bold">{{ fixed(selectedCity.local_moran_i) }}</dd></div>
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">空间滞后 Z</dt><dd class="mt-1 font-mono text-xl font-bold">{{ fixed(selectedCity.spatial_lag_z) }}</dd></div>
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">置换 p 值</dt><dd class="mt-1 font-mono text-xl font-bold">{{ fixed(selectedCity.p_value) }}</dd></div>
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">PM2.5</dt><dd class="mt-1 font-mono text-xl font-bold">{{ selectedCity.avg_pm25 }}</dd></div>
            <div class="rounded-lg bg-slate-50 p-4"><dt class="text-xs text-slate-500">PM10</dt><dd class="mt-1 font-mono text-xl font-bold">{{ selectedCity.avg_pm10 }}</dd></div>
          </dl>
          <div class="mt-6"><p class="text-sm font-bold text-slate-800">K=6 最近邻城市</p><div class="mt-3 flex flex-wrap gap-2"><span v-for="city in selectedCity.neighbors" :key="city" class="rounded-lg bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">{{ city }}</span></div></div>
          <div class="mt-6 rounded-lg border border-teal-100 bg-teal-50 p-4 text-sm leading-6 text-teal-900">该城市的 AQI 标准化值为 {{ fixed(selectedCity.z_aqi) }}，邻域平均标准化值为 {{ fixed(selectedCity.spatial_lag_z) }}。局部聚类结果为“{{ clusterName(selectedCity.cluster) }}”。</div>
        </aside>
        <div class="flex h-full min-h-0 flex-col rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
          <div class="flex items-center justify-between"><div><h3 class="font-bold text-slate-900">60 城市数据索引</h3><p class="text-xs text-slate-500">选择任意城市并在地图中定位</p></div><span class="font-mono text-xs text-slate-400">{{ filteredCities.length }}/60</span></div>
          <input v-model="citySearch" type="search" placeholder="搜索城市或省份" class="mt-4 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none transition focus:border-teal-400 focus:bg-white" />
          <div class="mt-3 min-h-0 flex-1 space-y-1">
            <button v-for="city in pagedIndexCities" :key="city.city" type="button" class="grid w-full grid-cols-[1fr_auto] items-center gap-3 rounded-lg px-3 py-2 text-left transition" :class="selectedCity?.city === city.city ? 'bg-teal-50 ring-1 ring-teal-200' : 'hover:bg-slate-50'" @click="selectCity(city)">
              <span><span class="font-bold text-slate-800">{{ city.city }}</span><span class="ml-2 text-xs text-slate-400">{{ city.province }}</span></span>
              <span class="flex items-center gap-2"><span class="font-mono text-xs font-bold text-slate-600">AQI {{ city.avg_aqi }}</span><span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: colors[city.cluster] }" /></span>
            </button>
          </div>
          <div class="mt-auto border-t border-slate-100 pt-3"><p class="mb-2 text-[11px] text-slate-500">第 {{ cityIndexPage }} / {{ cityIndexTotalPages }} 页，每页 {{ cityIndexPageSize }} 条</p><div class="flex flex-nowrap items-center gap-0.5 whitespace-nowrap"><button class="h-7 rounded-md border border-slate-200 px-2 text-[10px] disabled:cursor-not-allowed disabled:opacity-40" :disabled="cityIndexPage === 1" @click="goToCityIndexPage(cityIndexPage - 1)">上一页</button><button v-for="number in cityIndexPageNumbers" :key="number" class="h-7 min-w-6 rounded-md px-1 text-[10px] font-bold" :class="cityIndexPage === number ? 'bg-slate-950 text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'" @click="goToCityIndexPage(number)">{{ number }}</button><button class="h-7 rounded-md border border-slate-200 px-2 text-[10px] disabled:cursor-not-allowed disabled:opacity-40" :disabled="cityIndexPage === cityIndexTotalPages" @click="goToCityIndexPage(cityIndexPage + 1)">下一页</button></div></div>
        </div>
      </section>

      <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex flex-col justify-between gap-3 sm:flex-row"><div><h2 class="text-lg font-bold text-slate-900">LISA 城市明细</h2><p class="text-sm text-slate-500">按 Local Moran's I 从高到低排列，p&lt;0.05 判定显著。</p></div><p class="text-xs text-slate-400">生成时间 {{ result.generated_at_utc }}</p></div>
        <div class="mt-5 overflow-x-auto"><table class="w-full min-w-[820px] text-left text-sm"><thead class="border-b text-xs text-slate-500"><tr><th class="py-3">城市</th><th>AQI</th><th>Local I</th><th>空间滞后 Z</th><th>p 值</th><th>聚类</th><th>显著性</th></tr></thead><tbody><tr v-for="city in pagedLisaCities" :key="city.city" class="cursor-pointer border-b border-slate-50 hover:bg-slate-50" @click="selectCity(city)"><td class="py-3 font-bold">{{ city.city }}</td><td class="font-mono">{{ city.avg_aqi }}</td><td class="font-mono">{{ fixed(city.local_moran_i) }}</td><td class="font-mono">{{ fixed(city.spatial_lag_z) }}</td><td class="font-mono">{{ fixed(city.p_value) }}</td><td><span class="rounded-full px-2.5 py-1 text-xs font-bold text-white" :style="{ backgroundColor: colors[city.cluster] }">{{ clusterName(city.cluster) }}</span></td><td :class="city.significant ? 'font-bold text-rose-600' : 'text-slate-400'">{{ city.significant ? 'p < 0.05' : '不显著' }}</td></tr></tbody></table></div>
        <div class="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><p class="text-xs text-slate-500">共 {{ sortedCities.length }} 条，第 {{ lisaPage }} / {{ lisaTotalPages }} 页，每页 {{ lisaPageSize }} 条</p><div class="flex flex-wrap items-center gap-1"><button class="rounded-lg border border-slate-200 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40" :disabled="lisaPage === 1" @click="goToLisaPage(lisaPage - 1)">上一页</button><button v-for="number in lisaPageNumbers" :key="number" class="h-8 min-w-8 rounded-lg px-2 text-xs font-bold" :class="lisaPage === number ? 'bg-slate-950 text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'" @click="goToLisaPage(number)">{{ number }}</button><button class="rounded-lg border border-slate-200 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40" :disabled="lisaPage === lisaTotalPages" @click="goToLisaPage(lisaPage + 1)">下一页</button></div></div>
      </section>
    </template>
  </div>
</template>
