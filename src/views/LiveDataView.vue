<script setup lang="ts">
import { computed } from 'vue'
import liveSnapshot from '../../data/live/open_meteo_latest.json'

interface LiveRecord {
  city_code: string
  city: string
  province: string
  weather_observed_at: string
  air_quality_observed_at: string
  temperature_c: number
  relative_humidity_pct: number
  precipitation_mm: number
  weather_code_wmo: number
  wind_speed_kmh: number
  european_aqi: number
  us_aqi: number
  pm10_ug_m3: number
  pm25_ug_m3: number
  no2_ug_m3: number
  so2_ug_m3: number
  o3_ug_m3: number
}

interface LiveSnapshot {
  generated_at_utc: string
  source: string
  data_kind: string
  disclaimer: string
  records: LiveRecord[]
}

const snapshot = liveSnapshot as LiveSnapshot
const records = computed(() => snapshot.records)
const generatedAt = computed(() =>
  new Date(snapshot.generated_at_utc).toLocaleString('zh-CN', {
    hour12: false,
    timeZone: 'Asia/Shanghai',
  }),
)

function aqiClass(aqi: number) {
  if (aqi <= 20) return 'bg-emerald-100 text-emerald-700'
  if (aqi <= 40) return 'bg-lime-100 text-lime-700'
  if (aqi <= 60) return 'bg-amber-100 text-amber-700'
  if (aqi <= 80) return 'bg-orange-100 text-orange-700'
  return 'bg-rose-100 text-rose-700'
}
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p class="text-sm font-semibold text-teal-600">Open-Meteo Daily Snapshot</p>
          <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">最新天气与空气质量</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            当前展示自动采集链路最近一次成功快照。天气为模型当前值；空气质量来自 CAMS 全球大气模型，不是地面监测站实测值。
          </p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-right">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-400">数据生成时间（北京时间）</p>
          <p class="mt-1 font-mono text-sm font-bold text-slate-700">{{ generatedAt }}</p>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="record in records"
        :key="record.city_code"
        class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"
      >
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-xl font-bold text-slate-900">{{ record.city }}</h2>
            <p class="mt-1 text-xs text-slate-400">{{ record.province }} · {{ record.weather_observed_at }}</p>
          </div>
          <span class="rounded-full px-3 py-1 text-xs font-bold" :class="aqiClass(record.european_aqi)">
            EU AQI {{ record.european_aqi }}
          </span>
        </div>

        <div class="mt-5 grid grid-cols-3 gap-3">
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="text-xs text-slate-400">温度</p>
            <p class="mt-1 font-mono text-lg font-bold text-slate-800">{{ record.temperature_c }}°C</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="text-xs text-slate-400">湿度</p>
            <p class="mt-1 font-mono text-lg font-bold text-slate-800">{{ record.relative_humidity_pct }}%</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="text-xs text-slate-400">风速</p>
            <p class="mt-1 font-mono text-lg font-bold text-slate-800">{{ record.wind_speed_kmh }}</p>
            <p class="text-[10px] text-slate-400">km/h</p>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-2 gap-x-5 gap-y-3 border-t border-slate-100 pt-4 text-sm">
          <div class="flex justify-between"><span class="text-slate-400">PM2.5</span><strong>{{ record.pm25_ug_m3 }}</strong></div>
          <div class="flex justify-between"><span class="text-slate-400">PM10</span><strong>{{ record.pm10_ug_m3 }}</strong></div>
          <div class="flex justify-between"><span class="text-slate-400">NO₂</span><strong>{{ record.no2_ug_m3 }}</strong></div>
          <div class="flex justify-between"><span class="text-slate-400">SO₂</span><strong>{{ record.so2_ug_m3 }}</strong></div>
          <div class="flex justify-between"><span class="text-slate-400">O₃</span><strong>{{ record.o3_ug_m3 }}</strong></div>
          <div class="flex justify-between"><span class="text-slate-400">降水</span><strong>{{ record.precipitation_mm }} mm</strong></div>
        </div>
      </article>
    </section>

    <p class="text-center text-xs text-slate-400">
      Weather and air-quality model data by Open-Meteo · AQI 标准为 European AQI
    </p>
  </div>
</template>
