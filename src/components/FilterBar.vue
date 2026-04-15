<script setup lang="ts">
import type { TimeDimension } from '../types/air'
import { CITIES } from '../composables/useAirQualityData'

const selectedCity = defineModel<string>('city', { required: true })
const selectedTime = defineModel<TimeDimension>('time', { required: true })
</script>

<template>
  <div
    class="animate-fade-in-up flex flex-wrap items-center gap-4 rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
  >
    <div class="flex items-center gap-2">
      <span class="text-sm font-medium text-slate-500">城市选择:</span>
      <select
        v-model="selectedCity"
        class="block rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm text-slate-700 outline-none focus:border-teal-500 focus:ring-teal-500"
      >
        <option value="all">所有城市对比</option>
        <option v-for="city in CITIES" :key="city" :value="city">{{ city }}</option>
      </select>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-sm font-medium text-slate-500">时间维度:</span>
      <select
        v-model="selectedTime"
        class="block rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm text-slate-700 outline-none focus:border-teal-500 focus:ring-teal-500"
      >
        <option value="week">本周</option>
        <option value="month">本月</option>
        <option value="year">全年</option>
      </select>
    </div>
  </div>
</template>
