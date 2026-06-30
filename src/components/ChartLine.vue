<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord, TimeDimension } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  filteredData: AirRecord[]
  selectedCity: string
  timeDimension: TimeDimension
  cities: readonly string[]
  dateLabels: string[]
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const palette = ['#0f766e', '#dc2626', '#f59e0b', '#2563eb', '#16a34a', '#22c55e']
const highLineColors = ['#dc2626', '#f59e0b', '#2563eb']
const lowLineColors = ['#16a34a', '#22c55e']

function average(values: number[]) {
  if (!values.length) return 0
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1))
}

function recordsByCity(city: string) {
  const dateOrder = new Map(props.dateLabels.map((date, index) => [date, index]))
  return props.rawData
    .filter((item) => item.city === city)
    .sort((a, b) => (dateOrder.get(a.date) ?? 0) - (dateOrder.get(b.date) ?? 0))
}

function getFocusedCities() {
  const overallAvg = average(props.rawData.map((item) => item.aqi))
  const stats = props.cities
    .map((city) => {
      const rows = recordsByCity(city)
      return {
        city,
        avgAqi: average(rows.map((item) => item.aqi)),
        count: rows.length,
      }
    })
    .filter((item) => item.count > 0)

  const highCities = [...stats]
    .filter((item) => item.avgAqi >= overallAvg)
    .sort((a, b) => b.avgAqi - a.avgAqi)
    .slice(0, 3)

  const highCityNames = new Set(highCities.map((item) => item.city))
  const lowCandidates = [...stats]
    .filter((item) => item.avgAqi < overallAvg && !highCityNames.has(item.city))
    .sort((a, b) => a.avgAqi - b.avgAqi)

  const fallbackLowCities = [...stats]
    .filter((item) => !highCityNames.has(item.city))
    .sort((a, b) => a.avgAqi - b.avgAqi)

  const lowCities = (lowCandidates.length ? lowCandidates : fallbackLowCities).slice(0, 2)

  return [...highCities, ...lowCities].map((item) => item.city)
}

function buildOption() {
  const dates = props.dateLabels
  const isAll = props.selectedCity === 'all'
  const focusCities = isAll ? getFocusedCities() : [props.selectedCity]

  const averageLine = dates.map((date) => average(props.rawData.filter((item) => item.date === date).map((item) => item.aqi)))
  const overallAvg = average(props.rawData.map((item) => item.aqi))
  const cityAvgMap = new Map(focusCities.map((city) => [city, average(recordsByCity(city).map((item) => item.aqi))]))
  const lowCities = focusCities.filter((city) => (cityAvgMap.get(city) ?? 0) < overallAvg)

  const series = [
    ...(isAll
      ? [
          {
            name: '整体平均',
            type: 'line' as const,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 3, color: palette[0] },
            areaStyle: { color: 'rgba(15, 118, 110, 0.08)' },
            data: averageLine,
            markLine: {
              symbol: 'none',
              silent: true,
              lineStyle: { color: '#f97316', type: 'dashed', width: 1 },
              label: {
                color: '#f97316',
                formatter: 'AQI 100',
                position: 'start',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: [2, 6],
                borderRadius: 4,
                distance: 8,
              },
              data: [{ yAxis: 100 }],
            },
          },
        ]
      : []),
    ...focusCities.map((city, index) => {
      const isLowCity = (cityAvgMap.get(city) ?? 0) < overallAvg
      const cityColor = isLowCity
        ? lowLineColors[Math.max(0, lowCities.indexOf(city)) % lowLineColors.length]
        : highLineColors[index % highLineColors.length]

      return {
        name: city,
        type: 'line' as const,
        smooth: true,
        symbol: 'none',
        itemStyle: { color: cityColor },
        lineStyle: { width: isAll ? 2 : 3, opacity: isAll ? 0.76 : 1, color: cityColor },
        areaStyle: isAll ? undefined : { opacity: 0.12, color: cityColor },
        emphasis: { focus: 'series' as const },
        data: recordsByCity(city).map((item) => item.aqi),
        markLine:
          isAll || index > 0
            ? undefined
            : {
                symbol: 'none',
                silent: true,
                lineStyle: { color: '#f97316', type: 'dashed', width: 1 },
                label: {
                  color: '#f97316',
                  formatter: 'AQI 100',
                  position: 'start',
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  padding: [2, 6],
                  borderRadius: 4,
                  distance: 8,
                },
                data: [{ yAxis: 100 }],
              },
      }
    }),
  ]

  return {
    color: palette,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#cbd5e1' } },
      valueFormatter: (value: number) => `${value} AQI`,
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: [10, 12],
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); border-radius: 8px;',
    },
    legend: {
      type: 'scroll',
      top: 0,
      right: 0,
      itemWidth: 10,
      itemHeight: 10,
      icon: 'circle',
      textStyle: { color: '#64748b', fontSize: 12 },
      data: series.map((item) => item.name),
    },
    grid: { left: 76, right: 36, bottom: dates.length > 12 ? 60 : 40, top: 44, containLabel: false },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
      axisLabel: {
        color: '#64748b',
        fontSize: 11,
        rotate: dates.length > 12 ? 35 : 0,
        hideOverlap: true,
        interval: dates.length > 18 ? Math.ceil(dates.length / 8) : 0,
      },
    },
    yAxis: {
      type: 'value',
      name: 'AQI',
      nameTextStyle: { color: '#94a3b8', align: 'right' },
      splitNumber: 4,
      axisLabel: { color: '#94a3b8', margin: 10 },
      splitLine: { lineStyle: { color: '#eef2f7', type: 'dashed' } },
    },
    dataZoom:
      dates.length > 18
        ? [
            { type: 'inside', throttle: 80 },
            { type: 'slider', height: 18, bottom: 12, borderColor: 'transparent', fillerColor: 'rgba(20, 184, 166, 0.16)' },
          ]
        : [{ type: 'inside', throttle: 80 }],
    series,
  }
}

function subtitleText() {
  if (props.selectedCity !== 'all') return `${props.selectedCity} 趋势`
  return props.timeDimension === 'year' ? '全年月度均值、高值城市与低值城市对比' : '整体均值、高值城市与低值城市对比'
}

function timeCountText() {
  return props.timeDimension === 'year' ? `${props.dateLabels.length} 个月` : `${props.dateLabels.length} 个时间点`
}

function render() {
  if (!elRef.value || !chart) return
  chart.setOption(buildOption(), true)
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  nextTick(() => {
    if (!elRef.value) return
    chart = echarts.init(elRef.value)
    render()
    window.addEventListener('resize', resize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
  chart = null
})

watch(
  () => [props.rawData, props.filteredData, props.selectedCity, props.dateLabels, props.timeDimension],
  () => nextTick(render),
  { deep: true },
)
</script>

<template>
  <div class="w-full">
    <div class="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h3 class="text-base font-bold text-slate-800">AQI 趋势概览</h3>
        <p class="mt-1 text-xs text-slate-500">{{ subtitleText() }}</p>
      </div>
      <span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700">
        {{ timeCountText() }}
      </span>
    </div>
    <div ref="elRef" class="h-[360px] w-full" />
  </div>
</template>
