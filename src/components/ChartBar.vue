<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord, TimeDimension } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  cities: readonly string[]
  timeDimension: TimeDimension
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function average(values: number[]) {
  if (!values.length) return 0
  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1))
}

function countUnit() {
  return props.timeDimension === 'year' ? '月' : '天'
}

function countUnitName() {
  return props.timeDimension === 'year' ? '月数' : '天数'
}

function cityLevelRows() {
  return props.cities
    .map((city) => {
      const rows = props.rawData.filter((item) => item.city === city)
      const excellent = rows.filter((item) => item.aqi <= 50).length
      const good = rows.filter((item) => item.aqi > 50 && item.aqi <= 100).length
      const polluted = rows.filter((item) => item.aqi > 100).length
      const total = rows.length
      return {
        city,
        clear: excellent + good,
        polluted,
        total,
        pollutedRate: total ? Math.round((polluted / total) * 100) : 0,
        avgAqi: average(rows.map((item) => item.aqi)),
      }
    })
    .filter((item) => item.total > 0)
    .sort((a, b) => b.polluted - a.polluted || b.avgAqi - a.avgAqi)
    .slice(0, 10)
    .reverse()
}

function buildOption() {
  const rows = cityLevelRows()
  const maxCount = Math.max(...rows.map((item) => item.total), 1)
  const unit = countUnit()
  const unitName = countUnitName()
  const clearName = `优良${unitName}`
  const pollutedName = `污染${unitName}`

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: [10, 12],
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); border-radius: 8px;',
      formatter: (params: Array<{ marker: string; seriesName: string; value: number; dataIndex: number }>) => {
        const row = rows[params[0]?.dataIndex ?? 0]
        const lines = params
          .map((item) => `${item.marker}${item.seriesName}: ${item.value} ${unit}`)
          .join('<br/>')
        return `${row.city}<br/>平均 AQI: ${row.avgAqi}<br/>污染率: ${row.pollutedRate}%<br/>${lines}`
      },
    },
    legend: {
      top: 0,
      right: 0,
      icon: 'roundRect',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#64748b', fontSize: 12 },
      data: [clearName, pollutedName],
    },
    grid: { left: 12, right: 86, top: 46, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      max: maxCount,
      splitNumber: 4,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', formatter: `{value}${unit}` },
      splitLine: { lineStyle: { color: '#eef2f7', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.city),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#475569', fontSize: 12, fontWeight: 600 },
    },
    series: [
      {
        name: clearName,
        type: 'bar',
        stack: 'quality',
        barWidth: 14,
        itemStyle: {
          borderRadius: [7, 0, 0, 7],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#34d399' },
            { offset: 1, color: '#059669' },
          ]),
        },
        emphasis: { focus: 'series' },
        data: rows.map((item) => item.clear),
      },
      {
        name: pollutedName,
        type: 'bar',
        stack: 'quality',
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 7, 7, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#fb7185' },
            { offset: 1, color: '#ef4444' },
          ]),
        },
        label: {
          show: true,
          position: 'right',
          color: '#64748b',
          fontSize: 11,
          formatter: (params: { dataIndex: number }) => `${rows[params.dataIndex].pollutedRate}%`,
        },
        emphasis: { focus: 'series' },
        data: rows.map((item) => item.polluted),
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
  () => [props.rawData, props.timeDimension],
  () => nextTick(render),
  { deep: true },
)
</script>

<template>
  <div class="w-full">
    <div class="mb-4 flex items-end justify-between gap-3">
      <div>
        <h3 class="text-base font-bold text-slate-800">城市空气质量结构 Top 10</h3>
        <p class="mt-1 text-xs text-slate-500">
          {{ timeDimension === 'year' ? '绿色为优良月份，红色为污染月份' : '绿色为优良天数，红色为污染天数' }}
        </p>
      </div>
      <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
        {{ timeDimension === 'year' ? '优良/污染月份' : '优良/污染天数' }}
      </span>
    </div>
    <div ref="elRef" class="h-[340px] w-full" />
  </div>
</template>
