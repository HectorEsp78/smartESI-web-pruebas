import type { EnergyRange } from './energy';

export type CorrelationRange = EnergyRange;

export interface CorrelationPointDto {
  timestamp: string;
  occupancy: number;
  capacity: number;
  occupancy_pct: number;
  co2: number;
  temperature: number;
  humidity: number;
}

export interface CorrelationStatsDto {
  sample_size: number;
  pearson_r: number;
  slope: number;
  intercept: number;
  avg_occupancy: number;
  avg_occupancy_pct: number;
  avg_co2: number;
  max_co2: number;
  good_pct: number;
  moderate_pct: number;
  poor_pct: number;
}

export interface OccupancyAirQualityDto {
  range: CorrelationRange;
  building_id: string;
  points: CorrelationPointDto[];
  stats: CorrelationStatsDto;
}
