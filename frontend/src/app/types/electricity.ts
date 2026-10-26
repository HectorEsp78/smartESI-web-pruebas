/** Types for the new Electricity tab (explicit dates + building/sector scope). */

export type ElectricityMetric = 'kwh' | 'cost';
export type ElectricityGranularity = 'day' | 'week' | 'month' | 'year';

export const ELECTRICITY_METRICS: ElectricityMetric[] = ['kwh', 'cost'];
export const ELECTRICITY_ALL = 'all';
export const DEFAULT_ELECTRICITY_METRIC: ElectricityMetric = 'kwh';

export const ELECTRICITY_METRIC_LABEL: Record<ElectricityMetric, string> = {
  kwh: 'Consumo',
  cost: 'Coste',
};

export const ELECTRICITY_GRANULARITY_NOUN: Record<ElectricityGranularity, string> = {
  day: 'día',
  week: 'semana',
  month: 'mes',
  year: 'año',
};

export interface ElectricityStatsDto {
  total: number;
  average: number;
  minimum: number;
  maximum: number;
  baseline_hourly: number;
  baseline_total: number;
  buckets: number;
  unit: string;
}

export interface ElectricityPointDto {
  timestamp: string;
  value: number;
  baseline: number;
}

export interface ElectricityBuildingStatsDto {
  building_id: string;
  label: string;
  kind: string;
  total: number;
  average: number;
  minimum: number;
  maximum: number;
  baseline_total: number;
  share: number;
  note: string;
  series: ElectricityPointDto[];
}

export interface ElectricitySectorStatsDto {
  sector_id: string;
  label: string;
  building_id: string;
  building_label: string;
  floor: string;
  total: number;
  average: number;
  minimum: number;
  maximum: number;
  share_of_building: number;
  has_data: boolean;
  note: string;
  series: ElectricityPointDto[];
}

export interface ElectricityDto {
  start: string;
  end: string;
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  unit: string;
  scope: string;
  scope_label: string;
  building_id: string | null;
  sector_id: string | null;
  series: ElectricityPointDto[];
  stats: ElectricityStatsDto;
  buildings: ElectricityBuildingStatsDto[];
  sectors: ElectricitySectorStatsDto[];
  site_total: number;
  fermin_total: number;
  sectors_total: number;
  unmetered_total: number;
  sector_coverage: number;
  data_start: string;
}

export interface ElectricityComparePointDto {
  index: number;
  timestamp_a: string;
  timestamp_b: string;
  period_a: number;
  period_b: number;
  baseline: number;
}

export interface ElectricityCompareDto {
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  unit: string;
  scope: string;
  scope_label: string;
  building_id: string | null;
  sector_id: string | null;
  start_a: string;
  end_a: string;
  start_b: string;
  end_b: string;
  period_a_days: number;
  period_b_days: number;
  period_a: ElectricityStatsDto;
  period_b: ElectricityStatsDto;
  baseline_hourly: number;
  delta_pct: number;
  series: ElectricityComparePointDto[];
}

export interface ElectricityBuildingRefDto {
  id: string;
  label: string;
  kind: string;
  note: string;
}

export interface ElectricitySectorRefDto {
  id: string;
  label: string;
  building_id: string;
  building_label: string;
  floor: string;
  available: boolean;
  note: string;
}

export interface ElectricityMetaDto {
  buildings: ElectricityBuildingRefDto[];
  sectors: ElectricitySectorRefDto[];
  data_start: string;
  price_eur_per_kwh: number;
  data_source: 'mock' | 'database';
}
