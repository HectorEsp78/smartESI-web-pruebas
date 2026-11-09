export type BatteryUnit = 'percent' | 'millivolt';
export type BatteryLevel = 'ok' | 'medium' | 'low' | 'critical' | 'unknown';
export type BatteryGranularity = 'hour' | 'day';

export interface BatterySensorDto {
  id: string;
  label: string;
  entity_id: string;
  unit: BatteryUnit;
  value: number | null;
  estimated_pct: number | null;
  level: BatteryLevel;
  reading_at: string | null;
  age_hours: number | null;
  is_current: boolean;
}

export interface BatteryGroupDto {
  group: string;
  label: string;
  unit: BatteryUnit;
  generated_at: string;
  summary: {
    total: number;
    low: number;
    critical: number;
    without_current_reading: number;
  };
  sensors: BatterySensorDto[];
  data_source: 'mock' | 'database';
}

export interface BatteryHistoryPointDto {
  timestamp: string;
  value: number | null;
  estimated_pct: number | null;
}

export interface BatteryHistoryDto {
  group: string;
  sensor_id: string;
  label: string;
  unit: BatteryUnit;
  start: string;
  end: string;
  granularity: BatteryGranularity;
  low_threshold: number;
  critical_threshold: number;
  min_value: number | null;
  max_value: number | null;
  points: BatteryHistoryPointDto[];
  data_source: 'mock' | 'database';
}
