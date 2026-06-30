<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  filteredData: AirRecord[]
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function average(rows: AirRecord[], field: keyof Pick<AirRecord, 'pm25' | 'pm10' | 'so2' | 'no2'>) {
  if (!rows.length) return 0
  return Number((rows.reduce((sum, item) => sum + item[field], 0) / rows.length).toFixed(1))
}

function buildOption() {
  const rows = props.filteredData
  const data = [
    { value: average(rows, 'pm25'), name: 'PM2.5' },
    { value: average(rows, 'pm10'), name: 'PM10' },
    { value: average(rows, 'no2'), name: 'NO2' },
    { value: average(rows, 'so2'), name: 'SO2' },
  ].filter((item) => item.value > 0)

  return {
    color: ['#2563eb', '#14b8a6', '#f59e0b', '#8b5cf6'],
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>{c} ug/m3 ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); border-radius: 8px;',
    },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      icon: 'circle',
      textStyle: { color: '#64748b', fontSize: 12 },
    },
    series: [
      {
        name: '污染物占比',
        type: 'pie',
        radius: ['50%', '72%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        minAngle: 8,
        label: {
          formatter: '{b}\n{d}%',
          color: '#475569',
          fontSize: 11,
        },
        labelLine: {
          length: 8,
          length2: 6,
          lineStyle: { color: '#cbd5e1' },
        },
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
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
  () => props.filteredData,
  () => nextTick(render),
  { deep: true },
)
</script>

<template>
  <div class="w-full">
    <div class="mb-4">
      <h3 class="text-base font-bold text-slate-800">污染物均值结构</h3>
      <p class="mt-1 text-xs text-slate-500">当前筛选范围</p>
    </div>
    <div ref="elRef" class="h-[340px] w-full" />
  </div>
</template>
