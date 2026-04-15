<script setup lang="ts">
import type { DatasetRecord } from '../types/air'

defineProps<{
  open: boolean
  record: DatasetRecord | null
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 overflow-hidden"
    aria-labelledby="dataset-drawer-title"
    role="dialog"
    aria-modal="true"
  >
    <div class="absolute inset-0 bg-slate-900/20 backdrop-blur-sm transition-opacity" @click="emit('close')" />
    <div class="fixed inset-y-0 right-0 flex w-full max-w-md">
      <div class="flex w-full transform flex-col border-l border-slate-200 bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-5">
          <h2 id="dataset-drawer-title" class="text-lg font-bold text-slate-900">原始数据节点 (JSON)</h2>
          <button class="text-slate-400 hover:text-slate-600" @click="emit('close')">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto bg-[#0F172A] p-6">
          <pre class="text-sm leading-relaxed text-cyan-400"><code>{{ JSON.stringify(record, null, 2) }}</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>
