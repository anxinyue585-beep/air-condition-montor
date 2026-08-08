<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getLineage, getProcessingStatus } from '../api'
import type { LineageResult, ProcessingStatus } from '../api'

const lineage = ref<LineageResult | null>(null)
const processing = ref<ProcessingStatus | null>(null)
const errorMessage = ref('')
let timer: ReturnType<typeof setInterval> | undefined

const querySource = computed(() =>
  processing.value?.current_query_source === 'spark_export' ? 'Spark 城市日输出' : '本地 Warehouse 回退',
)

function localTime(value: string | null | undefined) {
  if (!value) return '暂无'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function refresh() {
  try {
    const [lineageResult, processingResult] = await Promise.all([getLineage(), getProcessingStatus()])
    lineage.value = lineageResult
    processing.value = processingResult
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '状态接口不可用'
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 60_000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <section class="overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm">
    <div class="flex flex-col border-b border-slate-100 px-5 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-2">
        <span class="h-2.5 w-2.5 rounded-full" :class="errorMessage ? 'bg-rose-500' : 'animate-pulse bg-teal-500'" />
        <h2 class="text-sm font-bold text-slate-800">数据服务状态</h2>
      </div>
      <RouterLink to="/lineage" class="mt-2 text-xs font-bold text-teal-600 hover:text-teal-700 sm:mt-0">查看完整数据血缘 →</RouterLink>
    </div>

    <div v-if="errorMessage" class="bg-rose-50 px-5 py-3 text-xs text-rose-700">
      {{ errorMessage }}。请确认 FastAPI 服务已启动。
    </div>
    <div v-else class="grid grid-cols-1 divide-y divide-slate-100 sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
      <div class="px-5 py-4">
        <p class="text-xs text-slate-400">后端查询源</p>
        <p class="mt-1 font-bold" :class="processing?.platform_export_available ? 'text-teal-600' : 'text-amber-600'">{{ querySource }}</p>
      </div>
      <div class="px-5 py-4">
        <p class="text-xs text-slate-400">查询数据更新时间</p>
        <p class="mt-1 font-mono text-sm font-bold text-slate-700">{{ localTime(processing?.current_query_updated_at) }}</p>
      </div>
      <div class="px-5 py-4">
        <p class="text-xs text-slate-400">Hadoop/Hive/Spark处理</p>
        <p class="mt-1 font-bold" :class="lineage?.verification_status === 'passed' ? 'text-emerald-600' : 'text-rose-600'">
          {{ lineage?.verification_status === 'passed' ? '平台验收通过' : '平台尚未通过' }}
        </p>
      </div>
      <div class="px-5 py-4">
        <p class="text-xs text-slate-400">Open-Meteo更新时间</p>
        <p class="mt-1 font-mono text-sm font-bold text-slate-700">{{ localTime(processing?.open_meteo.updated_at) }}</p>
      </div>
    </div>
  </section>
</template>
