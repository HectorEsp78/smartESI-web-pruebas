/** Types for the Environment tab (school weather station vs AEMET). */

export type WeatherGranularity = 'hour' | 'day';
export type WeatherStatus = 'ok' | 'stale' | 'missing';
export type AemetCoverage = 'complete' | 'partial' | 'none';

export interface WeatherCurrentDto {
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  battery_pct: number | null;
  last_updated: string | null;
  age_hours: number | null;
  status: WeatherStatus;
}

export interface AemetLatestDto {
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  observed_at: string | null;
  age_hours: number | null;
  stale: boolean;
}

export interface AemetGapDto {
  start: string;
  end: string;
  hours: number;
}

export interface AemetAvailabilityDto {
  coverage: AemetCoverage;
  period_hours: number;
  observed_hours: number;
  compared_hours: number;
  coverage_pct: number;
  first_observation: string | null;
  last_observation: string | null;
  gaps: AemetGapDto[];
}

export interface MetricComparisonDto {
  samples: number;
  station_avg: number | null;
  aemet_avg: number | null;
  bias: number | null;
  mean_absolute_error: number | null;
  correlation: number | null;
}

export interface TemperatureComparisonDto extends MetricComparisonDto {
  daytime_bias: number | null;
  nighttime_bias: number | null;
}

export interface HumidityComparisonDto extends MetricComparisonDto {
  saturated_pct: number | null;
  unsaturated_bias: number | null;
}

export interface HourlyBiasDto {
  hour: number;
  temperature_bias_c: number | null;
}

export interface WeatherComparisonDto {
  temperature: TemperatureComparisonDto;
  humidity: HumidityComparisonDto;
  pressure: MetricComparisonDto;
  hourly_bias: HourlyBiasDto[];
}

export interface WeatherSummaryDto {
  samples: number;
  coverage_pct: number | null;
  temperature_avg_c: number | null;
  temperature_min_c: number | null;
  temperature_max_c: number | null;
  humidity_avg_pct: number | null;
  humidity_min_pct: number | null;
  humidity_max_pct: number | null;
  pressure_avg_hpa: number | null;
  pm25_avg: number | null;
  pm10_avg: number | null;
  battery_min_pct: number | null;
  aemet_precipitation_mm: number | null;
  aemet_rainy_hours: number;
}

export interface WeatherSeriesPointDto {
  timestamp: string;
  station_temperature_c: number | null;
  aemet_temperature_c: number | null;
  station_humidity_pct: number | null;
  aemet_humidity_pct: number | null;
  station_pressure_hpa: number | null;
  aemet_pressure_hpa: number | null;
  aemet_precipitation_mm: number | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  battery_pct: number | null;
}

export interface WeatherOverviewDto {
  start: string;
  end: string;
  granularity: WeatherGranularity;
  generated_at: string;
  current: WeatherCurrentDto;
  aemet_latest: AemetLatestDto;
  aemet_availability: AemetAvailabilityDto;
  comparison: WeatherComparisonDto;
  summary: WeatherSummaryDto;
  series: WeatherSeriesPointDto[];
  data_source: 'mock' | 'database';
  notes: string[];
}
