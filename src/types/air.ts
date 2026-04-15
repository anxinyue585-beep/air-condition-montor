export type TimeDimension = 'week' | 'month' | 'year'

export interface AirRecord {
  date: string
  city: string
  aqi: number
  pm25: number
  pm10: number
  so2: number
  no2: number
}

export interface KpiItem {
  title: string
  value: number | string
  unit: string
  textColor: string
  colorClass: string
}

export type DatasetLevel = '优' | '良' | '污染'

export interface DatasetRecord {
  id: string
  city: string
  date: string
  aqi: number
  level: DatasetLevel
  pm25: number
  pm10: number
  so2: number
  no2: number
  trend: number[]
}
