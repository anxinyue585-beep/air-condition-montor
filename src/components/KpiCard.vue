<script setup lang="ts">
defineProps<{
  title: string
  value: number | string
  unit: string
  textColor: string
  colorClass: string
  index: number
}>()
</script>

<template>
  <div
    class="animate-fade-in-up relative flex flex-col justify-between overflow-hidden rounded-xl border border-slate-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
    :style="{ animationDelay: `${index * 0.1}s` }"
  >
    <div class="absolute -right-4 -top-4 h-16 w-16 rounded-full opacity-10" :class="colorClass" />
    <span class="text-sm font-medium text-slate-500">{{ title }}</span>
    <div class="mt-2 flex items-baseline gap-2">
      <span class="text-3xl font-bold" :class="textColor">{{ value }}</span>
      <span class="text-xs font-medium text-slate-400">{{ unit }}</span>
    </div>
  </div>
</template>
