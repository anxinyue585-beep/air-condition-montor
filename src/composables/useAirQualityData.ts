import { computed, ref, watch } from 'vue'
import type { AirRecord, KpiItem, TimeDimension } from '../types/air'

export const CITIES = ['北京', '上海', '广州'] as const

const rawData = ref<AirRecord[]>([])
const selectedCity = ref<string>('all')
const selectedTime = ref<TimeDimension>('week')

function getDateLabels(dim: TimeDimension): string[] {
  if (dim === 'week') {
    return ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  }
  if (dim === 'month') {
    return Array.from({ length: 4 }, (_, i) => `第${i + 1}周`)
  }
  return Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
}

function generateMockData(dim: TimeDimension): AirRecord[] {
  const data: AirRecord[] = []
  const baseAqi: Record<string, number> = { 北京: 80, 上海: 55, 广州: 45 }
  const dates = getDateLabels(dim)

  for (const city of CITIES) {
    for (const date of dates) {
      const randomFluctuation = Math.floor(Math.random() * 40) - 10
      const aqi = Math.max(20, (baseAqi[city] ?? 60) + randomFluctuation)
      data.push({
        city,
        date,
        aqi,
        pm25: Math.floor(aqi * 0.7),
        pm10: Math.floor(aqi * 1.1),
        so2: Math.floor(Math.random() * 15 + 5),
        no2: Math.floor(Math.random() * 25 + 10),
      })
    }
  }
  return data
}

function refreshData() {
  rawData.value = generateMockData(selectedTime.value)
}

watch([selectedCity, selectedTime], () => {
  refreshData()
})

export function useAirQualityData() {
  const dateLabels = computed(() => getDateLabels(selectedTime.value))

  const filteredData = computed(() => {
    if (selectedCity.value === 'all') return rawData.value
    return rawData.value.filter((d) => d.city === selectedCity.value)
  })

  const kpiData = computed<KpiItem[]>(() => {
    const data = filteredData.value
    if (!data.length) return []

    const avgAqi = Math.round(data.reduce((sum, d) => sum + d.aqi, 0) / data.length)
    const avgPm25 = Math.round(data.reduce((sum, d) => sum + d.pm25, 0) / data.length)
    const avgPm10 = Math.round(data.reduce((sum, d) => sum + d.pm10, 0) / data.length)
    const goodDays = data.filter((d) => d.aqi <= 100).length
    const complianceRate = Math.round((goodDays / data.length) * 100)

    const getAqiColor = (val: number) => {
      if (val <= 50) return { text: 'text-emerald-500', bg: 'bg-emerald-500' }
      if (val <= 100) return { text: 'text-amber-500', bg: 'bg-amber-500' }
      return { text: 'text-rose-500', bg: 'bg-rose-500' }
    }

    const aqiColors = getAqiColor(avgAqi)

    return [
      {
        title: '平均 AQI',
        value: avgAqi,
        unit: '指数',
        textColor: aqiColors.text,
        colorClass: aqiColors.bg,
      },
      {
        title: 'PM2.5 均值',
        value: avgPm25,
        unit: 'μg/m³',
        textColor: 'text-slate-800',
        colorClass: 'bg-blue-500',
      },
      {
        title: 'PM10 均值',
        value: avgPm10,
        unit: 'μg/m³',
        textColor: 'text-slate-800',
        colorClass: 'bg-indigo-500',
      },
      {
        title: '优良天数占比',
        value: complianceRate,
        unit: '%',
        textColor: 'text-teal-600',
        colorClass: 'bg-teal-500',
      },
    ]
  })

  function getAqiLevelText(aqi: number) {
    if (aqi <= 50) return '优'
    if (aqi <= 100) return '良'
    if (aqi <= 150) return '轻度污染'
    return '中度以上污染'
  }

  function getAqiLevelClass(aqi: number) {
    if (aqi <= 50) return 'bg-emerald-500'
    if (aqi <= 100) return 'bg-amber-500'
    if (aqi <= 150) return 'bg-orange-500'
    return 'bg-rose-500'
  }

  function initData() {
    refreshData()
  }

  return {
    rawData,
    selectedCity,
    selectedTime,
    dateLabels,
    filteredData,
    kpiData,
    getAqiLevelText,
    getAqiLevelClass,
    initData,
    CITIES,
  }
}
