<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  cities: readonly string[]
  selectedCity: string
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

type MetricKey = keyof Pick<AirRecord, 'aqi' | 'pm25' | 'pm10' | 'so2' | 'no2'>
type CityProfile = {
  city: string
  values: number[]
  avgAqi: number
  count: number
}

const metrics: Array<{ key: MetricKey; name: string; fallbackMax: number }> = [
  { key: 'aqi', name: 'AQI', fallbackMax: 160 },
  { key: 'pm25', name: 'PM2.5', fallbackMax: 90 },
  { key: 'pm10', name: 'PM10', fallbackMax: 140 },
  { key: 'no2', name: 'NO2', fallbackMax: 70 },
  { key: 'so2', name: 'SO2', fallbackMax: 40 },
]

const lineColors = ['#dc2626', '#f97316', '#f59e0b', '#16a34a', '#0ea5e9', '#6366f1', '#8b5cf6', '#14b8a6']

function lineColor(index: number) {
  return lineColors[index % lineColors.length]
}

function average(values: number[]) {
  if (!values.length) return 0
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1))
}

function rowsForCity(city: string) {
  return props.rawData.filter((item) => item.city === city)
}

function cityProfiles(): CityProfile[] {
  return props.cities
    .map((city) => {
      const rows = rowsForCity(city)
      const values = metrics.map((metric) => average(rows.map((item) => item[metric.key])))
      return {
        city,
        values,
        avgAqi: values[0],
        count: rows.length,
      }
    })
    .filter((item) => item.count > 0)
    .sort((a, b) => b.avgAqi - a.avgAqi)
}

function focusedProfiles() {
  if (props.selectedCity === 'all') return cityProfiles().slice(0, 8)
  const selected = cityProfiles().find((item) => item.city === props.selectedCity)
  const peers = cityProfiles().filter((item) => item.city !== props.selectedCity).slice(0, 7)
  return selected ? [selected, ...peers] : peers
}

const visibleProfiles = computed(() => focusedProfiles())

function maxForMetric(key: MetricKey, fallback: number) {
  const maxValue = Math.max(...props.rawData.map((item) => item[key]), fallback)
  return Math.ceil((maxValue * 1.15) / 10) * 10
}

function buildOption() {
  const profiles = visibleProfiles.value

  return {
    color: lineColors,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); border-radius: 8px;',
    },
    parallelAxis: metrics.map((metric, index) => ({
      dim: index,
      name: metric.name,
      max: maxForMetric(metric.key, metric.fallbackMax),
    })),
    parallel: {
      left: 38,
      right: 34,
      top: 34,
      bottom: 28,
      parallelAxisDefault: {
        type: 'value',
        nameLocation: 'end',
        nameGap: 12,
        nameTextStyle: { color: '#475569', fontSize: 12, fontWeight: 600 },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        splitLine: { show: false },
      },
    },
    series: profiles.map((item, index) => ({
      name: item.city,
      type: 'parallel',
      smooth: true,
      lineStyle: {
        width: index === 0 ? 3.2 : 2.5,
        opacity: index === 0 ? 0.9 : 0.74,
        color: lineColor(index),
      },
      emphasis: {
        focus: 'series',
        lineStyle: { width: 4.2, opacity: 1, color: lineColor(index) },
      },
      data: [
        {
          name: item.city,
          value: item.values,
        },
      ],
    })),
  }
}

function subtitleText() {
  return props.selectedCity === 'all' ? 'AQI 高值城市 Top 8' : '所选城市与高风险城市参照'
}

function indicatorText() {
  return `${metrics.length} 项指标`
}

function legendStyle(index: number) {
  return {
    borderLeftColor: lineColor(index),
    borderLeftWidth: '3px',
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
    <div class="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h3 class="text-base font-bold text-slate-800">重点城市污染画像</h3>
        <p class="mt-1 text-xs text-slate-500">{{ subtitleText() }}</p>
      </div>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
        {{ indicatorText() }}
      </span>
    </div>
    <div class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
      <div
        v-for="(profile, index) in visibleProfiles"
        :key="profile.city"
        class="flex min-w-0 items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 px-2.5 py-2"
        :style="legendStyle(index)"
      >
        <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ backgroundColor: lineColor(index) }" />
        <span class="truncate text-xs font-bold text-slate-700">{{ profile.city }}</span>
        <span class="ml-auto shrink-0 text-[11px] font-semibold text-slate-500">AQI {{ profile.avgAqi }}</span>
      </div>
    </div>
    <div ref="elRef" class="h-[340px] w-full" />
  </div>
</template>
