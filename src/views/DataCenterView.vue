<script setup lang="ts">
import { computed, ref } from 'vue'
import { CITIES, useAirQualityData } from '../composables/useAirQualityData'

const { rawData, getAqiLevelText, getAqiLevelClass } = useAirQualityData()

const filterCity = ref<string>('all')
const filterLevel = ref<'all' | 'excellent' | 'good' | 'polluted'>('all')

function levelOf(aqi: number): 'excellent' | 'good' | 'polluted' {
  if (aqi <= 50) return 'excellent'
  if (aqi <= 100) return 'good'
  return 'polluted'
}

const filteredRows = computed(() => {
  let rows = [...rawData.value]
  if (filterCity.value !== 'all') {
    rows = rows.filter((r) => r.city === filterCity.value)
  }
  if (filterLevel.value !== 'all') {
    rows = rows.filter((r) => levelOf(r.aqi) === filterLevel.value)
  }
  return rows.sort((a, b) => {
    const c = a.city.localeCompare(b.city, 'zh')
    if (c !== 0) return c
    return a.date.localeCompare(b.date, 'zh')
  })
})

function exportCsv() {
  const header = ['日期', '城市', 'AQI', 'PM2.5', 'PM10', '级别']
  const lines = filteredRows.value.map((r) => [
    r.date,
    r.city,
    String(r.aqi),
    String(r.pm25),
    String(r.pm10),
    getAqiLevelText(r.aqi),
  ])
  const csv = [header.join(','), ...lines.map((l) => l.join(','))].join('\r\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `air-quality-${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="animate-fade-in-up rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h2 class="text-lg font-bold text-slate-800">原始数据查询</h2>
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="text-sm text-slate-500">城市</span>
          <select
            v-model="filterCity"
            class="rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm text-slate-700"
          >
            <option value="all">全部</option>
            <option v-for="c in CITIES" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-slate-500">级别</span>
          <select
            v-model="filterLevel"
            class="rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm text-slate-700"
          >
            <option value="all">全部</option>
            <option value="excellent">优</option>
            <option value="good">良</option>
            <option value="polluted">污染</option>
          </select>
        </div>
        <button
          type="button"
          class="flex items-center gap-2 rounded-lg bg-teal-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-600"
          @click="exportCsv"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          导出 CSV
        </button>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-500">
        <thead class="border-b bg-slate-50 text-xs uppercase text-slate-700">
          <tr>
            <th class="px-6 py-3">日期</th>
            <th class="px-6 py-3">城市</th>
            <th class="px-6 py-3">AQI</th>
            <th class="px-6 py-3">PM2.5</th>
            <th class="px-6 py-3">PM10</th>
            <th class="px-6 py-3">级别</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in filteredRows"
            :key="`${row.city}-${row.date}-${index}`"
            class="border-b bg-white hover:bg-slate-50"
          >
            <td class="px-6 py-4">{{ row.date }}</td>
            <td class="px-6 py-4 font-medium text-slate-900">{{ row.city }}</td>
            <td class="px-6 py-4">{{ row.aqi }}</td>
            <td class="px-6 py-4">{{ row.pm25 }}</td>
            <td class="px-6 py-4">{{ row.pm10 }}</td>
            <td class="px-6 py-4">
              <span
                class="rounded px-2 py-1 text-xs font-medium text-white"
                :class="getAqiLevelClass(row.aqi)"
              >
                {{ getAqiLevelText(row.aqi) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!filteredRows.length" class="py-8 text-center text-slate-400">暂无数据</p>
  </div>
</template>
