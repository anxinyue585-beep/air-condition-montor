<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  cities: readonly string[]
  selectedCity: string
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

type MetricKey = keyof Pick<AirRecord, 'aqi' | 'pm25' | 'pm10' | 'so2' | 'no2'>

const metrics: Array<{ key: MetricKey; name: string; fallbackMax: number }> = [
  { key: 'aqi', name: 'AQI', fallbackMax: 160 },
  { key: 'pm25', name: 'PM2.5', fallbackMax: 90 },
  { key: 'pm10', name: 'PM10', fallbackMax: 140 },
  { key: 'no2', name: 'NO2', fallbackMax: 70 },
  { key: 'so2', name: 'SO2', fallbackMax: 40 },
]

function average(values: number[]) {
  if (!values.length) return 0
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1))
}

function rowsForCity(city: string) {
  return props.rawData.filter((item) => item.city === city)
}

function cityStats() {
  return props.cities
    .map((city) => {
      const rows = rowsForCity(city)
      return {
        city,
        rows,
        avgAqi: average(rows.map((item) => item.aqi)),
      }
    })
    .filter((item) => item.rows.length > 0)
}

function focusedCities() {
  if (props.selectedCity !== 'all') return [props.selectedCity]
  return cityStats()
    .sort((a, b) => b.avgAqi - a.avgAqi)
    .slice(0, 3)
    .map((item) => item.city)
}

function maxForMetric(key: MetricKey, fallback: number) {
  const maxValue = Math.max(...props.rawData.map((item) => item[key]), fallback)
  return Math.ceil((maxValue * 1.15) / 10) * 10
}

function buildOption() {
  const cities = focusedCities()
  const data = cities.map((city) => {
    const rows = rowsForCity(city)
    return {
      name: city,
      value: metrics.map((metric) => average(rows.map((item) => item[metric.key]))),
    }
  })

  if (props.selectedCity !== 'all' && props.rawData.length) {
    data.unshift({
      name: '整体平均',
      value: metrics.map((metric) => average(props.rawData.map((item) => item[metric.key]))),
    })
  }

  return {
    color: ['#0f766e', '#dc2626', '#f59e0b', '#2563eb'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); border-radius: 8px;',
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#64748b', fontSize: 12 },
      data: data.map((item) => item.name),
    },
    radar: {
      center: ['50%', '48%'],
      radius: '62%',
      shape: 'polygon',
      indicator: metrics.map((metric) => ({
        name: metric.name,
        max: maxForMetric(metric.key, metric.fallbackMax),
      })),
      axisName: { color: '#64748b', fontSize: 12 },
      splitNumber: 4,
      splitArea: { areaStyle: { color: ['#f8fafc', '#ffffff'] } },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [
      {
        name: '污染物雷达',
        type: 'radar',
        symbolSize: 3,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.08 },
        emphasis: { focus: 'series' },
        data,
      },
    ],
  }
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
  () => [props.rawData, props.selectedCity],
  () => nextTick(render),
  { deep: true },
)
</script>

<template>
  <div class="w-full">
    <div class="mb-4">
      <h3 class="text-base font-bold text-slate-800">污染物特征雷达</h3>
      <p class="mt-1 text-xs text-slate-500">
        {{ selectedCity === 'all' ? '高风险城市对比' : '所选城市与整体均值对比' }}
      </p>
    </div>
    <div ref="elRef" class="h-[340px] w-full" />
  </div>
</template>
