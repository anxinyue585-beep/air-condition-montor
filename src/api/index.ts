import dataset from './dataset.json'
import type { DatasetLevel, DatasetRecord } from '../types/air'

export interface FetchDatasetParams {
  page: number
  pageSize: number
  keyword?: string
  city?: string
  level?: DatasetLevel | ''
  quarter?: '' | 'Q1' | 'Q2' | 'Q3' | 'Q4'
  sortKey?: keyof DatasetRecord
  sortOrder?: 1 | -1
}

export interface FetchDatasetResult {
  items: DatasetRecord[]
  total: number
  meta: {
    latestDate: string
    cityCount: number
    totalRecords: number
  }
}

const SOURCE: DatasetRecord[] = dataset as DatasetRecord[]

function getLevelByAqi(aqi: number): DatasetLevel {
  if (aqi <= 50) return '优'
  if (aqi <= 100) return '良'
  return '污染'
}

function buildLongRangeDataset() {
  const baseCities = [...new Set(SOURCE.map((item) => item.city))]
  const cityBaseAqi: Record<string, number> = Object.fromEntries(
    baseCities.map((city) => {
      const cityRows = SOURCE.filter((item) => item.city === city)
      const avg = Math.round(cityRows.reduce((sum, item) => sum + item.aqi, 0) / Math.max(1, cityRows.length))
      return [city, avg]
    }),
  )

  const start = new Date('2026-01-01')
  const end = new Date('2026-06-30')
  const rows: DatasetRecord[] = []
  let seq = 1

  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const date = d.toISOString().slice(0, 10)
    const day = d.getDate()
    const month = d.getMonth() + 1

    for (const city of baseCities) {
      const baseline = cityBaseAqi[city] ?? 80
      const cityFactor = city.charCodeAt(0) % 7
      const seasonal = Math.round(Math.sin((month / 12) * Math.PI * 2) * 12)
      const fluctuation = ((day * 7 + cityFactor * 11) % 23) - 11
      const aqi = Math.max(25, baseline + seasonal + fluctuation)
      const pm25 = Math.max(8, Math.round(aqi * 0.7 + (day % 5) - 2))
      const pm10 = Math.max(15, Math.round(aqi * 1.15 + (month % 4) * 2))
      const so2 = Math.max(3, Math.round(aqi * 0.09) + (cityFactor % 3))
      const no2 = Math.max(8, Math.round(aqi * 0.2) + (day % 4))
      const trend = Array.from({ length: 10 }, (_, i) => {
        const wave = Math.round(Math.sin((i + day) / 2.5) * 6)
        return Math.max(10, pm25 + wave + ((i * cityFactor) % 5) - 2)
      })

      rows.push({
        id: `AQ-${String(3000 + seq).padStart(4, '0')}`,
        city,
        date,
        aqi,
        level: getLevelByAqi(aqi),
        pm25,
        pm10,
        so2,
        no2,
        trend,
      })
      seq += 1
    }
  }

  return rows
}

const EXTENDED_SOURCE: DatasetRecord[] = buildLongRangeDataset()

function compareValue(a: DatasetRecord, b: DatasetRecord, key: keyof DatasetRecord, order: 1 | -1) {
  const av = a[key]
  const bv = b[key]
  if (typeof av === 'number' && typeof bv === 'number') {
    return (av - bv) * order
  }
  return String(av).localeCompare(String(bv), 'zh') * order
}

export async function fetchAirQualityData(params: FetchDatasetParams): Promise<FetchDatasetResult> {
  const {
    page,
    pageSize,
    keyword = '',
    city = '',
    level = '',
    quarter = '',
    sortKey = 'date',
    sortOrder = -1,
  } = params

  let result = [...EXTENDED_SOURCE]
  const q = keyword.trim().toLowerCase()

  if (q) {
    result = result.filter(
      (item) =>
        item.id.toLowerCase().includes(q) ||
        item.city.toLowerCase().includes(q) ||
        item.date.toLowerCase().includes(q),
    )
  }
  if (city) {
    result = result.filter((item) => item.city === city)
  }
  if (level) {
    result = result.filter((item) => item.level === level)
  }
  if (quarter) {
    const quarterMonths: Record<'Q1' | 'Q2' | 'Q3' | 'Q4', [number, number]> = {
      Q1: [1, 3],
      Q2: [4, 6],
      Q3: [7, 9],
      Q4: [10, 12],
    }
    const [startMonth, endMonth] = quarterMonths[quarter]
    result = result.filter((item) => {
      const month = Number(item.date.slice(5, 7))
      return month >= startMonth && month <= endMonth
    })
  }

  result.sort((a, b) => compareValue(a, b, sortKey, sortOrder))

  const total = result.length
  const start = (page - 1) * pageSize
  const items = result.slice(start, start + pageSize)

  const latestDate = [...EXTENDED_SOURCE].sort((a, b) => b.date.localeCompare(a.date, 'zh'))[0]?.date ?? '-'
  const cityCount = new Set(EXTENDED_SOURCE.map((item) => item.city)).size

  await new Promise((resolve) => setTimeout(resolve, 550))

  return {
    items,
    total,
    meta: {
      latestDate,
      cityCount,
      totalRecords: EXTENDED_SOURCE.length,
    },
  }
}

export function getDatasetCities() {
  return [...new Set(EXTENDED_SOURCE.map((item) => item.city))]
}
