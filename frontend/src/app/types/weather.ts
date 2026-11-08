/** Types for the Environment (weather station) tab. */

export type WeatherGranularity = 'hour' | 'day';
export type WeatherStatus = 'ok' | 'stale' | 'missing';

export interface WeatherCurrentDto {
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  pressure_station_hpa: number | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  battery_pct: number | null;
  last_updated: string | null;
  age_hours: number | null;
  status: WeatherStatus;
  dew_point_c: number | null;
  absolute_humidity_g_m3: number | null;
  heat_index_c: number | null;
  pressure_trend_3h_hpa: number | null;
  pressure_trend_24h_hpa: number | null;
  pm25_pm10_ratio: number | null;
}

export interface WeatherSummaryDto {
  samples: number;
  coverage_pct: number | null;
  median_interval_hours: number | null;
  outage_hours: number | null;
  battery_min_pct: number | null;
  battery_avg_pct: number | null;
  temperature_avg_c: number | null;
  temperature_min_c: number | null;
  temperature_max_c: number | null;
  temperature_amplitude_avg_c: number | null;
  humidity_avg_pct: number | null;
  humidity_min_pct: number | null;
  humidity_max_pct: number | null;
  pressure_avg_hpa: number | null;
  pressure_min_hpa: number | null;
  pressure_max_hpa: number | null;
  pressure_range_hpa: number | null;
  dew_point_avg_c: number | null;
  absolute_humidity_avg_g_m3: number | null;
  pm1_avg: number | null;
  pm25_avg: number | null;
  pm10_avg: number | null;
  pm25_max: number | null;
  hot_hours: number | null;
  cold_hours: number | null;
  dry_hours: number | null;
  humid_hours: number | null;
  tropical_nights: number;
  heat_index_max_c: number | null;
  heating_degree_days: number | null;
  cooling_degree_days: number | null;
}

export interface WeatherSeriesPointDto {
  timestamp: string;
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  dew_point_c: number | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  indoor_temperature_c: number | null;
  indoor_humidity_pct: number | null;
  indoor_co2_ppm: number | null;
  indoor_tvoc: number | null;
  aemet_temperature_c: number | null;
  aemet_humidity_pct: number | null;
  aemet_pressure_hpa: number | null;
  gas_m3: number | null;
  electricity_kwh: number | null;
}

export interface WeatherDailyPointDto {
  date: string;
  samples: number;
  coverage_pct: number | null;
  temperature_min_c: number | null;
  temperature_avg_c: number | null;
  temperature_max_c: number | null;
  humidity_avg_pct: number | null;
  pressure_avg_hpa: number | null;
  pm25_avg: number | null;
  pm25_max: number | null;
  indoor_temperature_avg_c: number | null;
  gas_m3: number | null;
  electricity_kwh: number | null;
  heating_degree_days: number | null;
  cooling_degree_days: number | null;
}

export interface WeatherIndoorCrossDto {
  available: boolean;
  samples: number;
  current_temperature_c: number | null;
  current_humidity_pct: number | null;
  current_co2_ppm: number | null;
  current_tvoc: number | null;
  current_pressure_hpa: number | null;
  current_updated_at: string | null;
  avg_temperature_c: number | null;
  avg_humidity_pct: number | null;
  avg_co2_ppm: number | null;
  avg_tvoc: number | null;
  avg_pressure_hpa: number | null;
  outdoor_minus_indoor_c: number | null;
  outdoor_minus_indoor_humidity_pct: number | null;
  temperature_correlation: number | null;
  humidity_correlation: number | null;
  pressure_bias_hpa: number | null;
}

export interface WeatherAemetHourlyBiasDto {
  hour: number;
  temperature_bias_c: number | null;
}

export interface WeatherAemetCrossDto {
  available: boolean;
  stale: boolean;
  samples: number;
  last_updated: string | null;
  temperature_bias_c: number | null;
  temperature_mae_c: number | null;
  temperature_correlation: number | null;
  humidity_bias_pct: number | null;
  humidity_mae_pct: number | null;
  humidity_correlation: number | null;
  pressure_bias_hpa: number | null;
  pressure_correlation: number | null;
  daytime_temperature_bias_c: number | null;
  nighttime_temperature_bias_c: number | null;
  precipitation_mm: number | null;
  visibility_min_km: number | null;
  hourly_bias: WeatherAemetHourlyBiasDto[];
}

export interface WeatherEnergyCrossDto {
  available: boolean;
  days: number;
  excluded_days: number;
  gas_m3: number | null;
  gas_cost_eur: number | null;
  electricity_kwh: number | null;
  heating_degree_days: number | null;
  cooling_degree_days: number | null;
  gas_per_degree_day: number | null;
  electricity_per_degree_day: number | null;
  temperature_gas_correlation: number | null;
  temperature_electricity_correlation: number | null;
  heating_degree_gas_correlation: number | null;
  cooling_degree_electricity_correlation: number | null;
}

export interface WeatherPmCrossDto {
  available: boolean;
  pm25_avg: number | null;
  pm10_avg: number | null;
  pm25_pm10_ratio: number | null;
  pm1_pm25_ratio: number | null;
  humidity_correlation: number | null;
  temperature_correlation: number | null;
  co2_correlation: number | null;
  tvoc_correlation: number | null;
  caveat: string;
}

export interface WeatherOverviewDto {
  start: string;
  end: string;
  days: number;
  granularity: WeatherGranularity;
  generated_at: string;
  current: WeatherCurrentDto;
  summary: WeatherSummaryDto;
  series: WeatherSeriesPointDto[];
  daily: WeatherDailyPointDto[];
  indoor_cross: WeatherIndoorCrossDto;
  aemet_cross: WeatherAemetCrossDto;
  energy_cross: WeatherEnergyCrossDto;
  pm_cross: WeatherPmCrossDto;
  data_source: 'mock' | 'database';
  notes: string[];
}
