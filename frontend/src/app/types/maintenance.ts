/** Types for the Maintenance tab. */

export type MaintenanceMode = 'periodic' | 'event';
export type BatteryUnit = 'percent' | 'millivolt';
export type BatteryStatus = 'critical' | 'low' | 'medium' | 'ok' | 'unknown';
export type BatteryBucket = 'ok' | 'low' | 'unknown';
export type HeartbeatStatus = 'ok' | 'late' | 'silent' | 'event' | 'unknown';
export type DataStatus =
  | 'ok'
  | 'device_silent'
  | 'global_outage'
  | 'group_outage'
  | 'unknown';
export type MatrixCategory =
  | 'correcto'
  | 'revisar_dispositivo'
  | 'cambiar_bateria'
  | 'bateria_y_dispositivo'
  | 'sin_lectura_bateria'
  | 'revisar_sin_datos';
export type PriorityLabel = 'urgent' | 'high' | 'medium' | 'low';
export type OutageScope = 'global' | 'group' | 'individual';

export interface MaintenanceBatteryInfoDto {
  value: number | null;
  unit: BatteryUnit | null;
  estimated_pct: number | null;
  status: BatteryStatus;
  reading_at: string | null;
  age_hours: number | null;
  stale: boolean;
  trend_30d_pct: number | null;
  replacement_detected: boolean;
  replacement_at: string | null;
  replacement_in_period: boolean;
  days_to_critical: number | null;
  forecast_30d_pct: number | null;
  forecast_60d_pct: number | null;
  forecast_90d_pct: number | null;
  forecast_replacement_at: string | null;
}

export interface MaintenanceHeartbeatInfoDto {
  last_at: string | null;
  silence_hours: number | null;
  updates_per_day: number | null;
  expected_per_day: number | null;
  ratio: number | null;
  median_interval_hours: number | null;
  p95_interval_hours: number | null;
  threshold_hours: number | null;
  status: HeartbeatStatus;
}

export interface MaintenanceAvailabilityInfoDto {
  availability_pct: number | null;
  outages_total: number;
  outages_individual: number;
  outages_global: number;
  outages_group: number;
  downtime_hours: number | null;
  mtbf_hours: number | null;
  mttr_hours: number | null;
}

export interface MaintenanceDeviceSummaryDto {
  id: string;
  label: string;
  type: string;
  location: string | null;
  mode: MaintenanceMode;
  has_battery: boolean;
  notes: string | null;
  battery: MaintenanceBatteryInfoDto | null;
  heartbeat: MaintenanceHeartbeatInfoDto;
  availability: MaintenanceAvailabilityInfoDto;
  battery_bucket: BatteryBucket;
  data_status: DataStatus;
  data_ok: boolean;
  matrix_category: MatrixCategory;
  priority: number;
  priority_label: PriorityLabel;
  decision: string;
  reasons: string[];
}

export interface MaintenanceOutageDto {
  scope: OutageScope;
  start: string;
  end: string;
  duration_hours: number;
  device_count: number;
  device_ids: string[];
  ongoing: boolean;
}

export interface MaintenanceHeatmapCellDto {
  device_id: string;
  date: string;
  updates: number;
  expected: number | null;
  availability_pct: number | null;
}

export interface MaintenanceSummaryDto {
  devices_total: number;
  devices_periodic: number;
  devices_event: number;
  with_battery: number;
  low_battery: number;
  critical_battery: number;
  unknown_battery: number;
  no_data: number;
  global_outages: number;
  group_outages: number;
  individual_outages: number;
  avg_availability_pct: number | null;
  replacements_detected: number;
  forecast_replace_30d: number;
  forecast_replace_60d: number;
  forecast_replace_90d: number;
}

export interface MaintenanceOverviewDto {
  start: string;
  end: string;
  days: number;
  generated_at: string;
  summary: MaintenanceSummaryDto;
  devices: MaintenanceDeviceSummaryDto[];
  outages: MaintenanceOutageDto[];
  heatmap: MaintenanceHeatmapCellDto[];
  data_source: 'mock' | 'database';
  notes: string[];
}

export interface MaintenanceBatteryPointDto {
  timestamp: string;
  value: number | null;
  unit: BatteryUnit | null;
  estimated_pct: number | null;
}

export interface MaintenanceDailyPointDto {
  date: string;
  updates: number;
  expected: number | null;
  availability_pct: number | null;
}

export interface MaintenanceDeviceDetailDto {
  start: string;
  end: string;
  days: number;
  generated_at: string;
  device: MaintenanceDeviceSummaryDto;
  battery_history: MaintenanceBatteryPointDto[];
  daily: MaintenanceDailyPointDto[];
  outages: MaintenanceOutageDto[];
  data_source: 'mock' | 'database';
  notes: string[];
}

export const BATTERY_STATUS_LABEL: Record<BatteryStatus, string> = {
  critical: 'Crítica',
  low: 'Baja',
  medium: 'Media',
  ok: 'OK',
  unknown: 'Sin dato',
};

export const BATTERY_BUCKET_LABEL: Record<BatteryBucket, string> = {
  ok: 'Batería OK',
  low: 'Batería baja',
  unknown: 'Batería sin lectura',
};

export const HEARTBEAT_STATUS_LABEL: Record<HeartbeatStatus, string> = {
  ok: 'Transmite',
  late: 'Retrasado',
  silent: 'Sin datos',
  event: 'Por eventos',
  unknown: 'Sin dato',
};

export const DATA_STATUS_LABEL: Record<DataStatus, string> = {
  ok: 'Datos OK',
  device_silent: 'Sin datos',
  global_outage: 'Corte global',
  group_outage: 'Corte de grupo',
  unknown: 'Sin dato',
};

export const MATRIX_CATEGORY_LABEL: Record<MatrixCategory, string> = {
  correcto: 'Correcto',
  revisar_dispositivo: 'Revisar dispositivo',
  cambiar_bateria: 'Cambiar batería',
  bateria_y_dispositivo: 'Batería y dispositivo',
  sin_lectura_bateria: 'Batería sin lectura',
  revisar_sin_datos: 'Revisión urgente',
};

export const PRIORITY_LABEL: Record<PriorityLabel, string> = {
  urgent: 'Urgente',
  high: 'Alta',
  medium: 'Media',
  low: 'Baja',
};

export const OUTAGE_SCOPE_LABEL: Record<OutageScope, string> = {
  global: 'Global',
  group: 'De grupo',
  individual: 'Individual',
};
