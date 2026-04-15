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

// CO / O3 没有数据字段，使用与城市绑定的合理固定 mock 值
const CITY_EXTRAS: Record<string, { co: number; o3: number }> = {
  北京: { co: 2.1, o3: 102 },
  上海: { co: 1.2, o3: 135 },
  广州: { co: 0.8, o3: 110 },
}

function avg(arr: number[]) {
  if (!arr.length) return 0
  return Math.round(arr.reduce((s, v) => s + v, 0) / arr.length)
}

function buildOption() {
  const seriesData = props.cities.map((city) => {
    const cityData = props.rawData.filter((d) => d.city === city)
    const extras = CITY_EXTRAS[city] ?? { co: 1.0, o3: 100 }
    return {
      value: [
        avg(cityData.map((d) => d.pm25)),
        avg(cityData.map((d) => d.pm10)),
        avg(cityData.map((d) => d.no2)),
        avg(cityData.map((d) => d.so2)),
        extras.co,
        extras.o3,
      ],
      name: city,
    }
  })

  return {
    color: ['#f43f5e', '#fbbf24', '#10b981'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: [10, 15],
      textStyle: { color: '#0f172a', fontFamily: 'monospace' },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 8px;',
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      itemGap: 20,
      textStyle: { color: '#64748b', fontWeight: 'bold' },
      data: [...props.cities],
    },
    radar: {
      indicator: [
        { name: 'PM2.5', max: 200 },
        { name: 'PM10',  max: 200 },
        { name: 'NO2',   max: 100 },
        { name: 'SO2',   max: 100 },
        { name: 'CO',    max: 5   },
        { name: 'O3',    max: 200 },
      ],
      shape: 'polygon',
      radius: '65%',
      axisName: {
        color: '#64748b',
        fontWeight: 'bold',
        fontFamily: 'monospace',
      },
      splitArea: {
        areaStyle: { color: ['#f8fafc', '#ffffff'] },
      },
      axisLine:  { lineStyle: { color: '#e2e8f0' } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [
      {
        name: '城市污染物对比',
        type: 'radar',
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.15 },
        data: seriesData,
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
  { deep: true },
)
</script>

<template>
  <div class="w-full">
    <h3 class="mb-1 text-base font-bold text-slate-800">多维污染物因子对抗分析</h3>
    <p class="mb-4 text-xs text-slate-500">六项主要污染物指标分布视图 · 雷达交叠对比</p>
    <div ref="elRef" class="h-[320px] w-full" />
  </div>
</template>
