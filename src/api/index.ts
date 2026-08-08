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
    queryGranularity: string
    querySource: string
    sourceUpdatedAt: string | null
  }
}

export interface LineageNode {
  id: string
  label: string
  detail: string
  status: 'passed' | 'pending' | 'failed'
}

export interface LineageResult {
  generated_at_utc: string
  current_query_source: string
  nodes: LineageNode[]
  edges: [string, string][]
  last_verified_at: string | null
  verification_status: string
  verification_message: string
}

export interface ProcessingStatus {
  current_query_source: string
  current_query_updated_at: string | null
  platform_export_available: boolean
  platform_manifest: Record<string, unknown> | null
  latest_platform_verification: Record<string, unknown> | null
  open_meteo: { available: boolean; updated_at: string | null }
}

export interface HiveMonthlyResult {
  available: boolean
  source: string
  updated_at: string | null
  items: Array<Record<string, string>>
  total: number
}

export interface SpatialCity {
  city: string
  province: string
  region: string
  longitude: number
  latitude: number
  avg_aqi: number
  avg_pm25: number
  avg_pm10: number
  z_aqi: number
  spatial_lag_z: number
  local_moran_i: number
  p_value: number
  significant: boolean
  cluster: 'High-High' | 'Low-Low' | 'High-Low' | 'Low-High' | 'Not significant'
  neighbors: string[]
}

export interface SpatialAnalysisResult {
  status: string
  method: {
    year: number
    indicator: string
    city_count: number
    spatial_weights: string
    k: number
    distance: string
    permutations: number
    random_seed: number
    significance_threshold: number
    source: string
  }
  global_moran: {
    observed_i: number
    expected_i: number
    pseudo_p_value: number
    significant: boolean
    interpretation: string
    permutation_mean: number
  }
  cluster_counts: Record<string, number>
  cities: SpatialCity[]
  generated_at_utc: string
}

export interface WarningFactor { feature: string; label: string; value: number; contribution: number; direction: 'increase' | 'decrease' }
export interface WarningCity {
  datetime: string; city: string; province: string; region: string; current_aqi: number; current_stage: string
  probability: number; warning_level: 'red' | 'orange' | 'yellow' | 'blue' | 'none'; predicted: number; actual: number
  explanations: WarningFactor[]; explanation_text: string; timeline: Array<{ datetime: string; probability: number; actual: number }>
}
export interface PollutionWarningResult {
  status: string; generated_at_utc: string; task: string
  model: { algorithm: string; split: string; selected_lambda: number; selected_threshold: number; test_metrics: Record<string, number> }
  summary: { city_count: number; warning_level_counts: Record<string, number>; highest_risk_city: string; highest_probability: number }
  cities: WarningCity[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function getJson<T>(path: string, params?: URLSearchParams): Promise<T> {
  const query = params?.toString()
  const response = await fetch(`${API_BASE}${path}${query ? `?${query}` : ''}`)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`API ${response.status}: ${detail}`)
  }
  return response.json() as Promise<T>
}

export function fetchAirQualityData(params: FetchDatasetParams): Promise<FetchDatasetResult> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
    keyword: params.keyword ?? '',
    city: params.city ?? '',
    level: params.level ?? '',
    quarter: params.quarter ?? '',
    sort_key: String(params.sortKey ?? 'date'),
    sort_order: (params.sortOrder ?? -1) === 1 ? 'asc' : 'desc',
  })
  return getJson<FetchDatasetResult>('/records', query)
}

export async function getDatasetCities(): Promise<string[]> {
  const result = await getJson<{ items: string[]; total: number }>('/cities')
  return result.items
}

export function getLineage(): Promise<LineageResult> {
  return getJson<LineageResult>('/lineage')
}

export function getProcessingStatus(): Promise<ProcessingStatus> {
  return getJson<ProcessingStatus>('/processing/status')
}

export function getHiveMonthly(limit = 12): Promise<HiveMonthlyResult> {
  return getJson<HiveMonthlyResult>('/platform/hive/monthly', new URLSearchParams({ limit: String(limit) }))
}

export function getSpatialAnalysis(): Promise<SpatialAnalysisResult> {
  return getJson<SpatialAnalysisResult>('/analysis/spatial')
}

export function getPollutionWarnings(): Promise<PollutionWarningResult> {
  return getJson<PollutionWarningResult>('/analysis/pollution-warning')
}
