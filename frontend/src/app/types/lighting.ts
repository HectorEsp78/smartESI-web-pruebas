import type { DashboardRange } from './range';

export type LightingRange = DashboardRange;

export interface LightingPointDto {
  timestamp: string;
  lighting: number;
  other: number;
  total: number;
  occupancy_pct: number;
  daylight_hours: number;
}

export interface LightingConsumptionDto {
  range: LightingRange;
  building_id: string;
  unit: string;
  total: number;
  lighting_total: number;
  other_total: number;
  lighting_share: number;
  cost_eur: number;
  co2_kg: number;
  series: LightingPointDto[];
}

export interface LightingSpaceDto {
  space_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;
  area_m2: number;
  lighting: number;
  share_of_lighting: number;
  share_of_building: number;
  cost_eur: number;
}

export interface LightingBySpaceDto {
  range: LightingRange;
  building_id: string;
  unit: string;
  lighting_total: number;
  spaces: LightingSpaceDto[];
}

export interface LightingWasteSpaceDto {
  space_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;
  total_lighting: number;
  empty_lighting: number;
  waste_pct: number;
  cost_eur: number;
  annualized_cost_eur: number;
  empty_hours: number;
  avg_daily_empty_cost: number;
}

export interface LightingWasteDto {
  range: LightingRange;
  building_id: string;
  total_lighting: number;
  waste_lighting: number;
  waste_share: number;
  waste_cost_eur: number;
  annualized_cost_eur: number;
  avg_daily_empty_cost: number;
  spaces: LightingWasteSpaceDto[];
}
