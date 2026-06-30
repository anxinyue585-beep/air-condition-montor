import dataset from '../../data/processed/air_quality_frontend_sample.json'
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

function levelFromAqi(aqi: number): DatasetLevel {
  if (aqi <= 50) return '优'
  if (aqi <= 100) return '良'
  return '污染'
}

const SOURCE: DatasetRecord[] = (dataset as DatasetRecord[]).map((item) => ({
  ...item,
  level: levelFromAqi(item.aqi),
}))
const EXTENDED_SOURCE: DatasetRecord[] = [...SOURCE]

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
    result = result.filter((item) => levelFromAqi(item.aqi) === level)
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
