<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import JsonDrawer from '../components/JsonDrawer.vue'
import { fetchAirQualityData, getDatasetCities } from '../api'
import type { DatasetLevel, DatasetRecord } from '../types/air'

const loading = ref(true)
const rows = ref<DatasetRecord[]>([])
const keyword = ref('')
const selectedCity = ref('')
const selectedLevel = ref<DatasetLevel | ''>('')
const selectedQuarter = ref<'' | 'Q1' | 'Q2' | 'Q3' | 'Q4'>('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const sortKey = ref<keyof DatasetRecord>('date')
const sortOrder = ref<1 | -1>(-1)
const cities = ref<string[]>(getDatasetCities())
const latestDate = ref('-')

const drawerOpen = ref(false)
const selectedRow = ref<DatasetRecord | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const pageStart = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const pageEnd = computed(() => Math.min(page.value * pageSize.value, total.value))
const visiblePages = computed<(number | '...')[]>(() => {
  const totalPageCount = totalPages.value
  const current = page.value

  if (totalPageCount <= 7) {
    return Array.from({ length: totalPageCount }, (_, i) => i + 1)
  }

  if (current <= 4) {
    return [1, 2, 3, 4, 5, '...', totalPageCount]
  }

  if (current >= totalPageCount - 3) {
    return [1, '...', totalPageCount - 4, totalPageCount - 3, totalPageCount - 2, totalPageCount - 1, totalPageCount]
  }

  return [1, '...', current - 1, current, current + 1, '...', totalPageCount]
})

async function loadData() {
  loading.value = true
  const result = await fetchAirQualityData({
    page: page.value,
    pageSize: pageSize.value,
    keyword: keyword.value,
    city: selectedCity.value,
    level: selectedLevel.value,
    quarter: selectedQuarter.value,
    sortKey: sortKey.value,
    sortOrder: sortOrder.value,
  })
  rows.value = result.items
  total.value = result.total
  latestDate.value = result.meta.latestDate
  loading.value = false
}

function onSort(key: keyof DatasetRecord) {
  if (sortKey.value === key) {
    sortOrder.value = (sortOrder.value === 1 ? -1 : 1) as 1 | -1
  } else {
    sortKey.value = key
    sortOrder.value = -1
  }
}

function openDrawer(row: DatasetRecord) {
  selectedRow.value = row
  drawerOpen.value = true
}

function exportCsv() {
  const header = ['id', 'city', 'date', 'aqi', 'level', 'pm25', 'pm10', 'so2', 'no2']
  const lines = rows.value.map((r) => [r.id, r.city, r.date, r.aqi, r.level, r.pm25, r.pm10, r.so2, r.no2])
  const csv = [header.join(','), ...lines.map((l) => l.join(','))].join('\r\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `dataset-page-${page.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function exportJson() {
  const blob = new Blob([JSON.stringify(rows.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `dataset-page-${page.value}.json`
  a.click()
  URL.revokeObjectURL(url)
}

watch([keyword, selectedCity, selectedLevel, selectedQuarter], () => {
  page.value = 1
})

watch([keyword, selectedCity, selectedLevel, selectedQuarter, page, pageSize, sortKey, sortOrder], loadData)

onMounted(loadData)
</script>

<template>
  <div class="relative mx-auto w-full animate-fade-in-up">
    <div class="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">数据明细中心</h1>
        <p class="mt-1 text-sm text-slate-500">全局空气质量数据集检索与导出</p>
      </div>
      <div class="flex gap-4">
        <div class="flex flex-col items-end rounded-lg border border-slate-200 bg-white px-4 py-2 shadow-sm">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">总数据条数</span>
          <span class="font-mono text-lg font-bold text-slate-900">{{ total }}</span>
        </div>
        <div class="flex flex-col items-end rounded-lg border border-slate-200 bg-white px-4 py-2 shadow-sm">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">覆盖城市</span>
          <span class="font-mono text-lg font-bold text-slate-900">{{ cities.length }}</span>
        </div>
        <div class="hidden flex-col items-end rounded-lg border border-slate-200 bg-white px-4 py-2 shadow-sm sm:flex">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">最新日期</span>
          <span class="font-mono text-lg font-bold text-slate-900">{{ latestDate }}</span>
        </div>
      </div>
    </div>

    <div class="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-4 rounded-t-xl border border-b-0 border-slate-200 bg-white p-4">
      <div class="flex min-w-[300px] flex-1 flex-wrap items-center gap-3">
        <div class="relative w-64">
          <svg class="absolute left-3 top-2.5 h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索城市或日期 (Ctrl+K)"
            class="glass-input w-full rounded-lg border border-slate-200 py-2 pl-9 pr-4 text-sm outline-none transition-shadow focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500"
          />
        </div>
        <select v-model="selectedCity" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none focus:ring-cyan-500">
          <option value="">所有城市</option>
          <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
        </select>
        <select v-model="selectedLevel" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none focus:ring-cyan-500">
          <option value="">所有等级</option>
          <option value="优">优</option>
          <option value="良">良</option>
          <option value="污染">污染</option>
        </select>
        <select v-model="selectedQuarter" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none focus:ring-cyan-500">
          <option value="">全部季度</option>
          <option value="Q1">Q1 (1-3月)</option>
          <option value="Q2">Q2 (4-6月)</option>
          <option value="Q3">Q3 (7-9月)</option>
          <option value="Q4">Q4 (10-12月)</option>
        </select>
      </div>
      <div class="flex gap-2">
        <button class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition-colors hover:bg-slate-50 hover:text-cyan-600" @click="exportCsv">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </button>
        <button class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white shadow-md transition-colors hover:bg-slate-800" @click="exportJson">
          导出 JSON
        </button>
      </div>
    </div>

    <DataTable :loading="loading" :rows="rows" :sort-key="sortKey" :sort-order="sortOrder" @sort="onSort" @select="openDrawer" />

    <div class="mt-4 flex flex-col justify-between gap-4 rounded-xl bg-slate-50/80 px-6 py-5 sm:flex-row sm:items-center">
      <div class="flex flex-wrap items-center gap-4 text-sm text-slate-500">
        <span>
          显示第 <span class="font-mono font-bold text-slate-900">{{ pageStart }}</span>
          到 <span class="font-mono font-bold text-slate-900">{{ pageEnd }}</span> 条
        </span>
        <label class="flex items-center gap-2">
          <span class="text-slate-500">每页</span>
          <select
            v-model="pageSize"
            class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm text-slate-700 outline-none transition-colors hover:border-slate-300 focus:border-emerald-500"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="30">30</option>
          </select>
          <span class="text-slate-500">条</span>
        </label>
      </div>

      <div class="flex items-center gap-1.5">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page === 1"
          @click="page--"
          aria-label="上一页"
        >
          &lt;
        </button>

        <template v-for="(item, idx) in visiblePages" :key="`${item}-${idx}`">
          <span
            v-if="item === '...'"
            class="flex h-9 min-w-9 items-center justify-center px-1 text-sm text-slate-400"
          >
            ...
          </span>
          <button
            v-else
            class="h-9 min-w-9 rounded-lg px-3 text-sm font-medium font-mono transition-colors"
            :class="
              item === page
                ? 'bg-emerald-500 text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-800'
            "
            @click="page = item"
          >
            {{ item }}
          </button>
        </template>

        <button
          class="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page === totalPages"
          @click="page++"
          aria-label="下一页"
        >
          &gt;
        </button>
      </div>
    </div>

    <JsonDrawer :open="drawerOpen" :record="selectedRow" @close="drawerOpen = false" />
  </div>
</template>
