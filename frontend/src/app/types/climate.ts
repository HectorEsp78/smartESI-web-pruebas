export type ClimateRange = 'day' | 'week' | 'month' | 'year';

export interface GasPointDto {
  timestamp: string;
  gas: number;
  degree_days: number;
  outdoor_temperature: number;
  indoor_temperature: number;
  valve_open_pct: number;
}

export interface GasStatsDto {
  total_gas: number;
  cost_eur: number;
  co2_kg: number;
  total_degree_days: number;
  gas_per_degree_day: number;
  correlation_degree_days: number;
  avg_outdoor_temperature: number;
  avg_indoor_temperature: number;
  avg_valve_open_pct: number;
}

export interface GasDto {
  range: ClimateRange;
  building_id: string;
  unit: string;
  stats: GasStatsDto;
  series: GasPointDto[];
}

export interface ValvePointDto {
  timestamp: string;
  valve_open_pct: number;
  avg_temperature: number;
  setpoint_c: number;
  outdoor_temperature: number;
}

export type ValveStatus = 'ok' | 'fria' | 'valvula_abierta' | 'valvula_cerrada';

export interface ValveSpaceDto {
  space_id: string;
  label: string;
  building_id: string;
  kind: string;
  setpoint_c: number;
  avg_temperature: number;
  avg_outdoor_temperature: number;
  valve_open_pct: number;
  sample_hours: number;
  hours_valve_open: number;
  hours_below_setpoint: number;
  deviation_c: number;
  status: ValveStatus;
}

export interface ValvesDto {
  range: ClimateRange;
  building_id: string;
  setpoint_c: number;
  series: ValvePointDto[];
  spaces: ValveSpaceDto[];
}

export interface EmptySpaceDto {
  space_id: string;
  label: string;
  building_id: string;
  building_label: string;
  kind: string;
  avg_temperature_unoccupied: number;
  outdoor_temperature: number;
  heated_unoccupied_hours: number;
  gas_estimate: number;
  cost_eur: number;
  annualized_cost_eur: number;
}

export interface EmptySpacesDto {
  range: ClimateRange;
  building_id: string;
  heat_base_temperature_c: number;
  total_gas_estimate: number;
  total_cost_eur: number;
  total_annualized_cost_eur: number;
  total_heated_unoccupied_hours: number;
  spaces: EmptySpaceDto[];
}
