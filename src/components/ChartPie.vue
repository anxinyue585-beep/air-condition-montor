<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  filteredData: AirRecord[]
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function buildOption() {
  const fd = props.filteredData
  if (!fd.length) {
    return {
      series: [{ type: 'pie', data: [] }],
    }
  }

  const avgData = {
    pm25: fd.reduce((s, d) => s + d.pm25, 0) / fd.length,
    pm10: fd.reduce((s, d) => s + d.pm10, 0) / fd.length,
    so2: fd.reduce((s, d) => s + d.so2, 0) / fd.length,
    no2: fd.reduce((s, d) => s + d.no2, 0) / fd.length,
  }

  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: '0', left: 'center' },
    series: [
      {
        name: '污染物占比',
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        data: [
          { value: Number(avgData.pm25.toFixed(1)), name: 'PM2.5' },
          { value: Number(avgData.pm10.toFixed(1)), name: 'PM10' },
          { value: Number(avgData.so2.toFixed(1)), name: 'SO2' },
          { value: Number(avgData.no2.toFixed(1)), name: 'NO2' },
        ],
      },
    ],
    color: ['#60a5fa', '#818cf8', '#a78bfa', '#f472b6'],
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
  () => props.filteredData,
  () => nextTick(render),
  { deep: true }
)
</script>

<template>
  <div class="w-full">
    <h3 class="mb-4 text-base font-bold text-slate-800">核心污染物占比</h3>
    <div ref="elRef" class="h-[300px] w-full" />
  </div>
</template>
