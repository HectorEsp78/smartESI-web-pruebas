export type EnergyRange = 'day' | 'week' | 'month' | 'year';
export type EnergyMetric = 'kwh' | 'cost' | 'co2';

export const ENERGY_RANGES: EnergyRange[] = ['day', 'week', 'month', 'year'];
export const ENERGY_METRICS: EnergyMetric[] = ['kwh', 'cost', 'co2'];
export const DEFAULT_ENERGY_RANGE: EnergyRange = 'day';
export const DEFAULT_ENERGY_METRIC: EnergyMetric = 'kwh';
export const ALL_BUILDINGS = 'all';

export const METRIC_LABEL: Record<EnergyMetric, string> = {
  kwh: 'Consumo',
  cost: 'Coste',
  co2: 'Emisiones',
};

export interface EnergyPointDto {
  timestamp: string;
  value: number;
}

export interface EnergyConsumptionDto {
  range: EnergyRange;
  metric: EnergyMetric;
  unit: string;
  granularity: string;
  building_id: string;
  total: number;
  average: number;
  peak: EnergyPointDto | null;
  series: EnergyPointDto[];
}

export interface BuildingShareDto {
  building_id: string;
  label: string;
  total: number;
  share: number;
}

export interface SpaceShareDto {
  space_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;
  total: number;
  share: number;
}

export interface EnergyByBuildingDto {
  range: EnergyRange;
  metric: EnergyMetric;
  unit: string;
  total: number;
  submetered_total: number;
  unmetered_total: number;
  coverage: number;
  buildings: BuildingShareDto[];
  spaces: SpaceShareDto[];
}

export interface EnergyBreakdownPointDto {
  timestamp: string;
  base: number;
  activity: number;
  lighting: number;
  other: number;
}

export interface EnergyBreakdownDto {
  range: EnergyRange;
  unit: string;
  building_id: string;
  total: number;
  base_total: number;
  activity_total: number;
  lighting_total: number;
  other_total: number;
  base_share: number;
  lighting_share: number;
  series: EnergyBreakdownPointDto[];
}

export interface EnergyComparePointDto {
  timestamp: string;
  current: number;
  previous: number;
}

export interface EnergyCompareDto {
  range: EnergyRange;
  metric: EnergyMetric;
  unit: string;
  building_id: string;
  current_total: number;
  previous_total: number;
  delta_pct: number;
  series: EnergyComparePointDto[];
}

export interface BuildingEfficiencyDto {
  building_id: string;
  label: string;
  area_m2: number;
  total: number;
  cost_eur: number;
  occupancy_hours: number;
  kwh_per_m2: number;
  kwh_per_person_hour: number;
  share: number;
}

export interface SpaceEfficiencyDto {
  space_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;
  area_m2: number;
  total: number;
  cost_eur: number;
  occupancy_hours: number;
  kwh_per_m2: number;
  kwh_per_person_hour: number;
  share: number;
}

export interface EnergyEfficiencyDto {
  range: EnergyRange;
  unit: string;
  total: number;
  submetered_total: number;
  unmetered_total: number;
  coverage: number;
  avg_kwh_per_m2: number;
  buildings: BuildingEfficiencyDto[];
  spaces: SpaceEfficiencyDto[];
}
