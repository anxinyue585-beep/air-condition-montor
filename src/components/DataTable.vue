<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'
import type { DatasetRecord } from '../types/air'

const props = defineProps<{
  loading: boolean
  rows: DatasetRecord[]
  sortKey: keyof DatasetRecord
  sortOrder: 1 | -1
}>()

const emit = defineEmits<{
  sort: [key: keyof DatasetRecord]
  select: [row: DatasetRecord]
}>()

const columns: Array<{ key: keyof DatasetRecord; label: string }> = [
  { key: 'id', label: '节点 ID' },
  { key: 'city', label: '监测城市' },
  { key: 'date', label: '采集时间' },
  { key: 'aqi', label: 'AQI 指数' },
  { key: 'level', label: '污染级别' },
  { key: 'pm25', label: 'PM2.5 浓度' },
]

function toSparklinePoints(trend: number[]) {
  const width = 100
  const height = 24
  const min = Math.min(...trend)
  const max = Math.max(...trend)
  const range = Math.max(1, max - min)
  return trend
    .map((v, i) => {
      const x = (i / (trend.length - 1)) * width
      const y = height - ((v - min) / range) * (height - 4) - 2
      return `${x},${y}`
    })
    .join(' ')
}
</script>

<template>
  <div class="relative overflow-hidden rounded-b-xl border border-slate-200 bg-white shadow-sm">
    <div v-if="loading" class="absolute inset-0 z-10 bg-white p-4">
      <div v-for="i in 8" :key="i" class="mb-4 flex animate-pulse-fast">
        <div class="mr-4 h-8 w-1/6 rounded bg-slate-100" />
        <div class="mr-4 h-8 w-1/4 rounded bg-slate-100" />
        <div class="mr-4 h-8 w-1/6 rounded bg-slate-100" />
        <div class="h-8 w-full rounded bg-slate-100" />
      </div>
    </div>

    <table class="w-full border-collapse text-left">
      <thead class="sticky top-0 z-[1] border-b border-slate-200 bg-slate-50">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="group cursor-pointer px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 transition-colors hover:text-slate-800"
            @click="emit('sort', col.key)"
          >
            <div class="flex items-center gap-1">
              {{ col.label }}
              <svg
                v-if="props.sortKey === col.key"
                :class="{ 'rotate-180': props.sortOrder === -1 }"
                class="h-3 w-3 text-cyan-500 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
              </svg>
              <svg
                v-else
                class="h-3 w-3 opacity-0 group-hover:opacity-100"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
              </svg>
            </div>
          </th>
          <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
            PM2.5 近期波动 (Sparkline)
          </th>
        </tr>
      </thead>
      <tbody class="relative">
        <tr
          v-for="row in rows"
          :key="row.id"
          class="group cursor-pointer border-b border-slate-100 transition-all duration-300 odd:bg-white even:bg-slate-50/40 hover:bg-slate-50 hover:shadow-[inset_4px_0_0_0_#06b6d4] hover:shadow-cyan-500/10"
          @click="emit('select', row)"
        >
          <td class="px-6 py-4 font-mono text-sm text-slate-600">{{ row.id }}</td>
          <td class="px-6 py-4 text-sm font-bold text-slate-900">{{ row.city }}</td>
          <td class="px-6 py-4 font-mono text-sm text-slate-600">{{ row.date }}</td>
          <td class="px-6 py-4 font-mono text-sm font-bold text-slate-900">{{ row.aqi }}</td>
          <td class="px-6 py-4 text-sm">
            <StatusBadge :level="row.level" />
          </td>
          <td class="px-6 py-4 font-mono text-sm text-slate-600"><span class="mr-1 text-slate-400">μg</span>{{ row.pm25 }}</td>
          <td class="px-6 py-2 align-middle">
            <svg width="100" height="24" class="overflow-visible">
              <polyline
                fill="none"
                stroke="#cbd5e1"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :points="toSparklinePoints(row.trend)"
                class="transition-colors group-hover:stroke-cyan-500"
              />
            </svg>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="!loading && !rows.length" class="p-12 text-center text-slate-500">暂无匹配的数据记录。</div>
  </div>
</template>
