<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AirRecord } from '../types/air'

const props = defineProps<{
  rawData: AirRecord[]
  cities: readonly string[]
}>()

const elRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function buildOption() {
  const barData = props.cities.map((city) => {
    const cityData = props.rawData.filter((d) => d.city === city)
    return {
      excellent: cityData.filter((d) => d.aqi <= 50).length,
      good: cityData.filter((d) => d.aqi > 50 && d.aqi <= 100).length,
      polluted: cityData.filter((d) => d.aqi > 100).length,
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(99, 102, 241, 0.05)',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: [10, 15],
      textStyle: { color: '#334155', fontWeight: 500 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;',
    },
    legend: {
      data: ['优', '良', '污染'],
      bottom: 0,
      icon: 'circle',
      itemGap: 24,
      textStyle: { color: '#64748b', fontSize: 13 },
    },
    grid: { left: '2%', right: '2%', bottom: '14%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [...props.cities],
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisTick: { show: false },
      axisLabel: { color: '#475569', fontSize: 14, fontWeight: 'bold', margin: 15 },
    },
    yAxis: {
      type: 'value',
      name: '天数',
      nameTextStyle: { color: '#94a3b8', padding: [0, 0, 0, -20] },
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
      axisLabel: { color: '#94a3b8' },
    },
    color: ['#10B981', '#F59E0B', '#EF4444'],
    series: [
      {
        name: '优',
        type: 'bar',
        barGap: '15%',
        barCategoryGap: '35%',
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: barData.map((d) => d.excellent),
      },
      {
        name: '良',
        type: 'bar',
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: barData.map((d) => d.good),
      },
      {
        name: '污染',
        type: 'bar',
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: barData.map((d) => d.polluted),
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
  () => props.rawData,
  () => nextTick(render),
  { deep: true }
)
</script>

<template>
  <div class="w-full">
    <h3 class="mb-4 text-base font-bold text-slate-800">城市空气质量级别天数统计</h3>
    <div ref="elRef" class="h-[300px] w-full" />
  </div>
</template>
