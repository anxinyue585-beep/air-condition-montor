<script setup lang="ts">
import type { DatasetLevel } from '../types/air'

defineProps<{ level: DatasetLevel }>()

function getBadgeClass(level: DatasetLevel) {
  if (level === '优') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (level === '良') return 'border-amber-200 bg-amber-50 text-amber-700'
  return 'border-rose-200 bg-rose-50 text-rose-700'
}
</script>

<template>
  <span :class="getBadgeClass(level)" class="rounded-full border px-2.5 py-1 text-xs font-bold">
    {{ level }}
  </span>
</template>
