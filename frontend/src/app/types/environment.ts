/** Types for the Infrastructure (room environment) tab. */

export type EnvironmentGranularity = 'hour' | 'day' | 'week';
export type EnvironmentQuality = 'good' | 'moderate' | 'poor' | 'bad' | 'unknown';

export interface EnvironmentRoomSummaryDto {
  room_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;

  has_temperature: boolean;
  has_humidity: boolean;
  has_co2: boolean;
  has_presence: boolean;

  current_temperature_c: number | null;
  temperature_updated_at: string | null;
  current_humidity_pct: number | null;
  humidity_updated_at: string | null;
  current_co2_ppm: number | null;
  co2_updated_at: string | null;
  current_presence: boolean | null;
  presence_updated_at: string | null;
  last_updated: string | null;

  temperature_status: EnvironmentQuality;
  humidity_status: EnvironmentQuality;
  co2_status: EnvironmentQuality;
  comfort_status: EnvironmentQuality;

  avg_temperature_c: number | null;
  min_temperature_c: number | null;
  max_temperature_c: number | null;
  avg_humidity_pct: number | null;
  min_humidity_pct: number | null;
  max_humidity_pct: number | null;
  avg_co2_ppm: number | null;
  peak_co2_ppm: number | null;
  peak_co2_at: string | null;
  co2_above_800_pct: number | null;
  co2_above_1000_pct: number | null;
  occupancy_pct: number | null;
  occupied_hours: number | null;
  empty_hours: number | null;
  comfort_good_pct: number | null;
}

export interface EnvironmentSeriesPointDto {
  timestamp: string;
  temperature_c: number | null;
  humidity_pct: number | null;
  co2_ppm: number | null;
  presence_pct: number | null;
  ambient_temperature_c: number | null;
  gas_m3: number | null;
  gas_cost_eur: number | null;
}

export interface EnvironmentHeatmapCellDto {
  weekday: number;
  hour: number;
  presence_pct: number | null;
  co2_ppm: number | null;
}

export interface EnvironmentCo2OccupancyDto {
  occupied_co2_ppm: number | null;
  empty_co2_ppm: number | null;
  lift_pct: number | null;
  correlation: number | null;
  occupied_hours: number | null;
  empty_hours: number | null;
}

export interface EnvironmentThermalRecoveryDto {
  baseline_temperature_c: number | null;
  transitions: number;
  median_recovery_hours: number | null;
  median_change_per_hour_c: number | null;
  no_recovery_count: number;
}

export interface EnvironmentBenchmarkDto {
  avg_temperature_c: number | null;
  avg_humidity_pct: number | null;
  avg_co2_ppm: number | null;
  occupancy_pct: number | null;
  rooms_temperature: number;
  rooms_humidity: number;
  rooms_co2: number;
  rooms_presence: number;
}

export interface EnvironmentContextDto {
  current_ambient_temperature_c: number | null;
  ambient_updated_at: string | null;
  avg_ambient_temperature_c: number | null;
  avg_indoor_minus_ambient_c: number | null;
  gas_m3: number | null;
  gas_cost_eur: number | null;
  gas_cost_per_day_eur: number | null;
  gas_days: number | null;
  has_gas: boolean;
}

export interface EnvironmentSummaryDto {
  rooms_total: number;
  occupied_now: number;
  rooms_with_presence: number;
  rooms_with_climate: number;
  rooms_with_co2: number;
  avg_temperature_c: number | null;
  avg_humidity_pct: number | null;
  avg_co2_ppm: number | null;
  co2_alert_rooms: number;
  comfort_good_rooms: number;
  occupancy_pct: number | null;
}

export interface EnvironmentOverviewDto {
  start: string;
  end: string;
  granularity: EnvironmentGranularity;
  generated_at: string;
  rooms: EnvironmentRoomSummaryDto[];
  summary: EnvironmentSummaryDto;
  data_source: 'mock' | 'database';
  notes: string[];
}

export interface EnvironmentRoomDetailDto {
  start: string;
  end: string;
  granularity: EnvironmentGranularity;
  generated_at: string;
  room: EnvironmentRoomSummaryDto;
  benchmark: EnvironmentBenchmarkDto;
  context: EnvironmentContextDto;
  series: EnvironmentSeriesPointDto[];
  heatmap: EnvironmentHeatmapCellDto[];
  co2_occupancy: EnvironmentCo2OccupancyDto;
  thermal_recovery: EnvironmentThermalRecoveryDto;
  data_source: 'mock' | 'database';
  notes: string[];
}

export const ENVIRONMENT_QUALITY_LABEL: Record<EnvironmentQuality, string> = {
  good: 'Bueno',
  moderate: 'Moderado',
  poor: 'Malo',
  bad: 'Muy malo',
  unknown: 'Sin dato',
};

export const ENVIRONMENT_QUALITY_ORDER: EnvironmentQuality[] = [
  'good',
  'moderate',
  'poor',
  'bad',
  'unknown',
];

export function worstQuality(...qualities: EnvironmentQuality[]): EnvironmentQuality {
  const rank: Record<EnvironmentQuality, number> = {
    good: 0,
    moderate: 1,
    poor: 2,
    bad: 3,
    unknown: -1,
  };
  const known = qualities.filter((quality) => quality !== 'unknown');
  if (known.length === 0) return 'unknown';
  return known.reduce((worst, quality) => (rank[quality] > rank[worst] ? quality : worst));
}
