<script setup lang="ts">
import ChartBar from '../components/ChartBar.vue'
import ChartLine from '../components/ChartLine.vue'
import ChartParallel from '../components/ChartParallel.vue'
import ChartPie from '../components/ChartPie.vue'
import ChartRadar from '../components/ChartRadar.vue'
import FilterBar from '../components/FilterBar.vue'
import KpiCard from '../components/KpiCard.vue'
import { useAirQualityData } from '../composables/useAirQualityData'

const {
  selectedCity,
  selectedTime,
  rawData,
  filteredData,
  kpiData,
  dateLabels,
  CITIES,
} = useAirQualityData()
</script>

<template>
  <div class="space-y-6">
    <FilterBar v-model:city="selectedCity" v-model:time="selectedTime" />

    <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        v-for="(kpi, index) in kpiData"
        :key="kpi.title"
        :title="kpi.title"
        :value="kpi.value"
        :unit="kpi.unit"
        :text-color="kpi.textColor"
        :color-class="kpi.colorClass"
        :index="index"
      />
    </div>

    <div class="grid grid-cols-1 gap-6">
      <div
        class="animate-fade-in-up overflow-hidden rounded-xl border border-slate-100 bg-white p-6 shadow-sm"
        style="animation-delay: 0.35s"
      >
        <ChartLine
          :raw-data="rawData"
          :filtered-data="filteredData"
          :selected-city="selectedCity"
          :time-dimension="selectedTime"
          :cities="CITIES"
          :date-labels="dateLabels"
        />
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div
        class="animate-fade-in-up overflow-hidden rounded-xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-3"
        style="animation-delay: 0.45s"
      >
        <ChartBar :raw-data="rawData" :cities="CITIES" :time-dimension="selectedTime" />
      </div>
      <div
        class="animate-fade-in-up overflow-hidden rounded-xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-2"
        style="animation-delay: 0.55s"
      >
        <ChartPie :filtered-data="filteredData" />
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div
        class="animate-fade-in-up overflow-hidden rounded-xl border border-slate-100 bg-white p-6 shadow-sm"
        style="animation-delay: 0.65s"
      >
        <ChartRadar :raw-data="rawData" :cities="CITIES" :selected-city="selectedCity" />
      </div>
      <div
        class="animate-fade-in-up overflow-hidden rounded-xl border border-slate-100 bg-white p-6 shadow-sm"
        style="animation-delay: 0.75s"
      >
        <ChartParallel :raw-data="rawData" :cities="CITIES" :selected-city="selectedCity" />
      </div>
    </div>
  </div>
</template>
