<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import JsonDrawer from '../components/JsonDrawer.vue'
import PaginationControls from '../components/PaginationControls.vue'
import { fetchAirQualityData, getDatasetCities } from '../api'
import type { DatasetLevel, DatasetRecord } from '../types/air'

const loading = ref(true)
const errorMessage = ref('')
const rows = ref<DatasetRecord[]>([])
const keyword = ref('')
const selectedCity = ref('')
const selectedLevel = ref<DatasetLevel | ''>('')
const selectedQuarter = ref<'' | 'Q1' | 'Q2' | 'Q3' | 'Q4'>('')
const page = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
const total = ref(0)
const sortKey = ref<keyof DatasetRecord>('date')
const sortOrder = ref<1 | -1>(-1)
const cities = ref<string[]>([])
const latestDate = ref('-')
const querySource = ref('-')
const sourceUpdatedAt = ref<string | null>(null)

const drawerOpen = ref(false)
const selectedRow = ref<DatasetRecord | null>(null)
const hasActiveFilters = computed(() => Boolean(keyword.value || selectedCity.value || selectedLevel.value || selectedQuarter.value))

const levelOptions: Array<{ value: DatasetLevel | ''; label: string }> = [
  { value: '', label: '全部等级' },
  { value: '优' as DatasetLevel, label: '优' },
  { value: '良' as DatasetLevel, label: '良' },
  { value: '污染' as DatasetLevel, label: '污染' },
]

async function loadData() {
  loading.value = true
  errorMessage.value = ''
  try {
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
    querySource.value = result.meta.querySource
    sourceUpdatedAt.value = result.meta.sourceUpdatedAt
  } catch (error) {
    rows.value = []
    total.value = 0
    errorMessage.value = error instanceof Error ? error.message : '后端查询失败'
  } finally {
    loading.value = false
  }
}

async function initialize() {
  try {
    cities.value = await getDatasetCities()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '城市列表加载失败'
  }
  await loadData()
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

function resetFilters() {
  keyword.value = ''
  selectedCity.value = ''
  selectedLevel.value = ''
  selectedQuarter.value = ''
}

function exportCsv() {
  const header = ['id', 'city', 'date', 'aqi', 'level', 'pm25', 'pm10', 'so2', 'no2']
  const lines = rows.value.map((row) => [row.id, row.city, row.date, row.aqi, row.level, row.pm25, row.pm10, row.so2, row.no2])
  const csv = [header.join(','), ...lines.map((line) => line.join(','))].join('\r\n')
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

onMounted(initialize)
</script>

<template>
  <div class="relative mx-auto w-full animate-fade-in-up">
    <div v-if="errorMessage" class="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}。请确认后端服务运行在 http://127.0.0.1:8000。
    </div>
    <div class="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">数据集展示中心</h1>
        <p class="mt-1 text-sm text-slate-500">全局空气质量数据集检索、分页浏览与导出</p>
      </div>
        <div class="flex gap-4">
        <div class="flex flex-col items-end rounded-lg border border-slate-200 bg-white px-4 py-2 shadow-sm">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">当前查询源</span>
          <span class="text-sm font-bold" :class="querySource === 'spark_export' ? 'text-teal-600' : 'text-amber-600'">
            {{ querySource === 'spark_export' ? 'Spark 输出' : '本地仓库回退' }}
          </span>
          <span v-if="sourceUpdatedAt" class="mt-0.5 text-[10px] text-slate-400">{{ new Date(sourceUpdatedAt).toLocaleString('zh-CN', { hour12: false }) }}</span>
        </div>
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

    <section class="rounded-t-xl border border-b-0 border-slate-200 bg-white p-4">
      <div class="mb-4 flex flex-col justify-between gap-3 lg:flex-row lg:items-center">
        <div>
          <h2 class="text-base font-bold text-slate-800">筛选条件</h2>
          <p class="mt-1 text-xs text-slate-500">按关键字、城市、等级和季节筛选数据集记录。</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700">
            匹配 {{ total }} 条
          </span>
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-600 transition-colors hover:border-teal-300 hover:text-teal-600 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!hasActiveFilters"
            @click="resetFilters"
          >
            重置筛选
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label class="space-y-1.5">
          <span class="text-xs font-bold text-slate-500">关键字</span>
          <div class="relative">
            <svg class="absolute left-3 top-2.5 h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="keyword"
              type="text"
              placeholder="城市 / 日期 / ID"
              class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm text-slate-700 outline-none transition-colors focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </label>
        <label class="space-y-1.5">
          <span class="text-xs font-bold text-slate-500">城市</span>
          <select
            v-model="selectedCity"
            class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition-colors focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500"
          >
            <option value="">全部城市</option>
            <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
          </select>
        </label>
        <label class="space-y-1.5">
          <span class="text-xs font-bold text-slate-500">空气质量等级</span>
          <select
            v-model="selectedLevel"
            class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition-colors focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500"
          >
            <option v-for="option in levelOptions" :key="option.label" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label class="space-y-1.5">
          <span class="text-xs font-bold text-slate-500">季节</span>
          <select
            v-model="selectedQuarter"
            class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition-colors focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500"
          >
            <option value="">全部季节</option>
            <option value="Q1">春季（1-3月）</option>
            <option value="Q2">夏季（4-6月）</option>
            <option value="Q3">秋季（7-9月）</option>
            <option value="Q4">冬季（10-12月）</option>
          </select>
        </label>
      </div>

      <div class="mt-4 flex gap-2">
        <button
          class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition-colors hover:bg-slate-50 hover:text-teal-600"
          @click="exportCsv"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </button>
        <button class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white shadow-md transition-colors hover:bg-slate-800" @click="exportJson">
          导出 JSON
        </button>
      </div>
    </section>

    <DataTable :loading="loading" :rows="rows" :sort-key="sortKey" :sort-order="sortOrder" @sort="onSort" @select="openDrawer" />

    <PaginationControls
      v-model:page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-size-options="pageSizeOptions"
    />

    <JsonDrawer :open="drawerOpen" :record="selectedRow" @close="drawerOpen = false" />
  </div>
</template>
