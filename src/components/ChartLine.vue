<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  filteredData: AirRecord[]
  selectedCity: string
  cities: readonly string[]
  dateLabels: string[]
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function buildOption() {
  const isAll = props.selectedCity === 'all'
  const dates = props.dateLabels

  const lineSeries = isAll
    ? props.cities.map((city) => ({
        name: city,
        type: 'line' as const,
        smooth: true,
        data: props.rawData
          .filter((d) => d.city === city)
          .sort((a, b) => dates.indexOf(a.date) - dates.indexOf(b.date))
          .map((d) => d.aqi),
      }))
    : [
        {
          name: props.selectedCity,
          type: 'line' as const,
          smooth: true,
          areaStyle: { opacity: 0.1 },
          data: [...props.filteredData]
            .sort((a, b) => dates.indexOf(a.date) - dates.indexOf(b.date))
            .map((d) => d.aqi),
        },
      ]

  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: isAll ? [...props.cities] : [props.selectedCity], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value' },
    series: lineSeries,
    color: ['#34d399', '#fbbf24', '#f43f5e'],
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
  () => [props.rawData, props.filteredData, props.selectedCity, props.dateLabels],
  () => {
    nextTick(render)
  },
  { deep: true }
)
</script>

<template>
  <div class="w-full">
    <h3 class="mb-4 text-base font-bold text-slate-800">AQI 时序趋势</h3>
    <div ref="elRef" class="h-[300px] w-full" />
  </div>
</template>
