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

// CO / O3 与雷达图保持一致的城市固定 mock 值
const CITY_EXTRAS: Record<string, { co: number; o3: number }> = {
  北京: { co: 2.1, o3: 85 },
  上海: { co: 1.2, o3: 165 },
  广州: { co: 0.8, o3: 105 },
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
      name: city,
      type: 'parallel' as const,
      lineStyle: { width: 3, opacity: 0.6, type: 'solid' as const },
      emphasis: { lineStyle: { width: 6, opacity: 1 } },
      data: [
        [
          avg(cityData.map((d) => d.pm25)),
          avg(cityData.map((d) => d.pm10)),
          avg(cityData.map((d) => d.no2)),
          avg(cityData.map((d) => d.so2)),
          extras.co,
          extras.o3,
        ],
      ],
    }
  })

  return {
    color: ['#f43f5e', '#fbbf24', '#10b981'],
    tooltip: {
      padding: 10,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#0f172a', fontFamily: 'monospace' },
      extraCssText:
        'box-shadow: 0 10px 15px -3px rgba(6, 182, 212, 0.1); border-radius: 8px;',
    },
    parallelAxis: [
      { dim: 0, name: 'PM2.5', max: 200 },
      { dim: 1, name: 'PM10', max: 200 },
      { dim: 2, name: 'NO2', max: 100 },
      { dim: 3, name: 'SO2', max: 100 },
      { dim: 4, name: 'CO', max: 5 },
      { dim: 5, name: 'O3', max: 200 },
    ],
    parallel: {
      left: '8%',
      right: '8%',
      bottom: 30,
      top: 40,
      parallelAxisDefault: {
        type: 'value',
        nameLocation: 'end',
        nameGap: 15,
        nameTextStyle: {
          color: '#64748b',
          fontSize: 12,
          fontFamily: 'monospace',
          fontWeight: 'bold',
        },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#94a3b8', fontFamily: 'monospace' },
      },
    },
    series: seriesData,
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
    <div class="mb-4 flex items-end justify-between">
      <div>
        <h3 class="text-base font-bold text-slate-800">城市污染物平行坐标交叉分析</h3>
        <p class="mt-0.5 text-xs text-slate-500">线条交叉越密集，代表城市间的污染特征差异越"针锋相对"</p>
      </div>
      <div class="flex items-center gap-4 text-xs font-bold font-mono">
        <span
          v-for="(city, i) in cities"
          :key="city"
          class="flex items-center gap-1.5 text-slate-800"
        >
          <span
            class="inline-block h-2 w-2 rounded-full"
            :style="{ background: ['#f43f5e', '#fbbf24', '#10b981'][i] }"
          />
          {{ city.toUpperCase() }}
        </span>
      </div>
    </div>
    <div ref="elRef" class="h-[320px] w-full" />
  </div>
</template>
