import { computed, ref, watch } from 'vue'
import dataset from '../../data/processed/air_quality_frontend_sample.json'
import cityMonthCsv from '../../data/warehouse/air_quality_city_month.csv?raw'
import type { AirRecord, DatasetRecord, KpiItem, TimeDimension } from '../types/air'

const SOURCE = dataset as DatasetRecord[]
const ALL_DATA: AirRecord[] = SOURCE.map(({ city, date, aqi, pm25, pm10, so2, no2 }) => ({
  city,
  date,
  aqi,
  pm25,
  pm10,
  so2,
  no2,
}))

export const CITIES: readonly string[] = [...new Set(SOURCE.map((item) => item.city))]

interface CityMonthRow {
  city: string
  year_month: string
  avg_aqi: string
  avg_pm25: string
  avg_pm10: string
  avg_so2: string
  avg_no2: string
}

function parseCityMonthCsv(csv: string): CityMonthRow[] {
  const [headerLine, ...lines] = csv.trim().split(/\r?\n/)
  const headers = headerLine.split(',')

  return lines
    .filter(Boolean)
    .map((line) => {
      const values = line.split(',')
      return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])) as unknown as CityMonthRow
    })
}

function toMonthlyAirRecords(csv: string) {
  const allowedCities = new Set(CITIES)
  const cityOrder = new Map(CITIES.map((city, index) => [city, index]))

  return parseCityMonthCsv(csv)
    .filter((row) => allowedCities.has(row.city))
    .map((row) => ({
      city: row.city,
      date: row.year_month,
      aqi: Math.round(Number(row.avg_aqi)),
      pm25: Math.round(Number(row.avg_pm25)),
      pm10: Math.round(Number(row.avg_pm10)),
      so2: Math.round(Number(row.avg_so2)),
      no2: Math.round(Number(row.avg_no2)),
    }))
    .sort((a, b) => {
      const cityOrderDiff = (cityOrder.get(a.city) ?? 0) - (cityOrder.get(b.city) ?? 0)
      if (cityOrderDiff !== 0) return cityOrderDiff
      return a.date.localeCompare(b.date, 'zh')
    })
}

const YEAR_MONTH_DATA: AirRecord[] = toMonthlyAirRecords(cityMonthCsv)

const rawData = ref<AirRecord[]>([])
const allData = ref<AirRecord[]>(ALL_DATA)
const selectedCity = ref<string>('all')
const selectedTime = ref<TimeDimension>('week')

function uniqueDates(rows: AirRecord[]) {
  return [...new Set(rows.map((item) => item.date))].sort((a, b) => a.localeCompare(b, 'zh'))
}

function average(rows: AirRecord[], field: keyof Pick<AirRecord, 'aqi' | 'pm25' | 'pm10' | 'so2' | 'no2'>) {
  if (!rows.length) return 0
  return Math.round(rows.reduce((sum, item) => sum + item[field], 0) / rows.length)
}

function aggregateByMonth(rows: AirRecord[]) {
  const grouped = new Map<string, AirRecord[]>()
  for (const row of rows) {
    const month = row.date.slice(0, 7)
    const key = `${row.city}|${month}`
    const bucket = grouped.get(key) ?? []
    bucket.push(row)
    grouped.set(key, bucket)
  }

  return [...grouped.entries()]
    .map(([key, rows]) => {
      const [city, month] = key.split('|')
      return {
        city,
        date: month,
        aqi: average(rows, 'aqi'),
        pm25: average(rows, 'pm25'),
        pm10: average(rows, 'pm10'),
        so2: average(rows, 'so2'),
        no2: average(rows, 'no2'),
      }
    })
    .sort((a, b) => {
      const cityOrder = CITIES.indexOf(a.city) - CITIES.indexOf(b.city)
      if (cityOrder !== 0) return cityOrder
      return a.date.localeCompare(b.date, 'zh')
    })
}

function buildDataByDimension(dim: TimeDimension): AirRecord[] {
  if (dim === 'year') {
    return YEAR_MONTH_DATA.length ? YEAR_MONTH_DATA : aggregateByMonth(ALL_DATA)
  }

  const dates = uniqueDates(ALL_DATA)
  const size = dim === 'week' ? 7 : 30
  const selectedDates = new Set(dates.slice(-size))
  return ALL_DATA.filter((item) => selectedDates.has(item.date))
}

function refreshData() {
  rawData.value = buildDataByDimension(selectedTime.value)
}

watch(selectedTime, () => {
  refreshData()
})

refreshData()

export function useAirQualityData() {
  const dateLabels = computed(() => uniqueDates(rawData.value))

  const filteredData = computed(() => {
    if (selectedCity.value === 'all') return rawData.value
    return rawData.value.filter((d) => d.city === selectedCity.value)
  })

  const kpiData = computed<KpiItem[]>(() => {
    const data = filteredData.value
    if (!data.length) return []

    const avgAqi = average(data, 'aqi')
    const avgPm25 = average(data, 'pm25')
    const avgPm10 = average(data, 'pm10')
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
        title: selectedTime.value === 'year' ? '优良月份占比' : '优良天数占比',
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
    allData,
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
