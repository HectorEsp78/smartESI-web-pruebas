import { formatNumber, formatPercent } from './format';
import type {
  BatteryBucket,
  BatteryStatus,
  DataStatus,
  MaintenanceBatteryInfoDto,
  MaintenanceDeviceSummaryDto,
  MaintenanceHeatmapCellDto,
  MatrixCategory,
  OutageScope,
  PriorityLabel,
} from '../types/maintenance';

export const MAINTENANCE_DAYS_OPTIONS = [7, 30, 90] as const;
export type MaintenanceDays = (typeof MAINTENANCE_DAYS_OPTIONS)[number];
export const DEFAULT_MAINTENANCE_DAYS: MaintenanceDays = 30;

export function parseMaintenanceDays(
  value: string | null | undefined,
): MaintenanceDays {
  const parsed = Number(value);
  return (MAINTENANCE_DAYS_OPTIONS as readonly number[]).includes(parsed)
    ? (parsed as MaintenanceDays)
    : DEFAULT_MAINTENANCE_DAYS;
}

export function maintenanceDaysLabel(days: MaintenanceDays): string {
  if (days === 7) return 'Últimos 7 días';
  if (days === 90) return 'Últimos 90 días';
  return 'Últimos 30 días';
}

export function formatDurationHours(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '—';
  if (value < 1) return `${formatNumber(value * 60, 0)} min`;
  if (value < 48) return `${formatNumber(value, 1)} h`;
  return `${formatNumber(value / 24, 1)} d`;
}

export function formatBatteryValue(
  battery: MaintenanceBatteryInfoDto | null,
): string {
  if (!battery || battery.status === 'unknown' || battery.value === null) {
    return '—';
  }
  if (battery.unit === 'millivolt') {
    return `${formatNumber(battery.value, 0)} mV`;
  }
  return `${formatNumber(battery.value, 0)} %`;
}

export function formatBatteryPercent(
  battery: MaintenanceBatteryInfoDto | null,
): string {
  if (!battery || battery.estimated_pct === null) return '—';
  return formatPercent(battery.estimated_pct, 0);
}

export function formatBatteryAge(
  battery: MaintenanceBatteryInfoDto | null,
): string {
  if (!battery || battery.reading_at === null || battery.age_hours === null) {
    return 'Sin lectura';
  }
  return `hace ${formatDurationHours(battery.age_hours)}`;
}

export function formatFrequency(value: number | null): string {
  if (value === null) return '—';
  return `${formatNumber(value, 1)}/día`;
}

export function formatSignedPoints(value: number | null): string {
  if (value === null) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, 1)} pp/30 d`;
}

export function formatDaysToCritical(value: number | null): string {
  if (value === null) return 'Sin previsión';
  if (value <= 0) return 'Crítica ahora';
  return `en ${formatNumber(value, 0)} d`;
}

export function formatAvailability(value: number | null): string {
  return value === null ? '—' : formatPercent(value, 0);
}

export function formatDateRange(start: string, end: string): string {
  const formatter = new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return '—';
  }
  return `${formatter.format(startDate)} – ${formatter.format(endDate)}`;
}

export const BATTERY_BG_CLASS: Record<BatteryStatus, string> = {
  critical: 'bg-red-50 text-red-700 border-red-200',
  low: 'bg-orange-50 text-orange-800 border-orange-200',
  medium: 'bg-amber-50 text-amber-800 border-amber-200',
  ok: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  unknown: 'bg-slate-50 text-slate-600 border-slate-200',
};

export const BATTERY_DOT_CLASS: Record<BatteryStatus, string> = {
  critical: 'bg-red-500',
  low: 'bg-orange-500',
  medium: 'bg-amber-500',
  ok: 'bg-emerald-500',
  unknown: 'bg-slate-400',
};

export const PRIORITY_BG_CLASS: Record<PriorityLabel, string> = {
  urgent: 'bg-red-50 text-red-700 border-red-200',
  high: 'bg-orange-50 text-orange-800 border-orange-200',
  medium: 'bg-amber-50 text-amber-800 border-amber-200',
  low: 'bg-slate-50 text-slate-600 border-slate-200',
};

export const PRIORITY_DOT_CLASS: Record<PriorityLabel, string> = {
  urgent: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-amber-500',
  low: 'bg-slate-400',
};

export const DATA_STATUS_BG_CLASS: Record<DataStatus, string> = {
  ok: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  device_silent: 'bg-red-50 text-red-700 border-red-200',
  global_outage: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  group_outage: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  unknown: 'bg-slate-50 text-slate-600 border-slate-200',
};

export const MATRIX_BG_CLASS: Record<MatrixCategory, string> = {
  correcto: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  revisar_dispositivo: 'bg-amber-50 text-amber-800 border-amber-200',
  cambiar_bateria: 'bg-orange-50 text-orange-800 border-orange-200',
  bateria_y_dispositivo: 'bg-red-50 text-red-700 border-red-200',
  sin_lectura_bateria: 'bg-slate-50 text-slate-600 border-slate-200',
  revisar_sin_datos: 'bg-red-50 text-red-700 border-red-200',
};

export const OUTAGE_SCOPE_BG_CLASS: Record<OutageScope, string> = {
  global: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  group: 'bg-sky-50 text-sky-700 border-sky-200',
  individual: 'bg-slate-50 text-slate-600 border-slate-200',
};

export type MaintenanceFilter = 'all' | 'priority' | 'low_battery' | 'no_data';

export function filterMaintenanceDevices(
  devices: MaintenanceDeviceSummaryDto[],
  filter: MaintenanceFilter,
): MaintenanceDeviceSummaryDto[] {
  if (filter === 'priority') {
    return devices.filter(
      (device) =>
        device.priority_label === 'urgent' || device.priority_label === 'high',
    );
  }
  if (filter === 'low_battery') {
    return devices.filter(
      (device) => device.has_battery && device.battery_bucket === 'low',
    );
  }
  if (filter === 'no_data') {
    return devices.filter((device) => !device.data_ok);
  }
  return devices;
}

export function maintenanceFilterCount(
  devices: MaintenanceDeviceSummaryDto[],
  filter: MaintenanceFilter,
): number {
  return filterMaintenanceDevices(devices, filter).length;
}

export interface MaintenanceMatrixCounts {
  ok_ok: number;
  ok_no_data: number;
  low_ok: number;
  low_no_data: number;
  unknown_ok: number;
  unknown_no_data: number;
  wired_total: number;
  wired_no_data: number;
}

export function maintenanceMatrixCounts(
  devices: MaintenanceDeviceSummaryDto[],
): MaintenanceMatrixCounts {
  const withBattery = devices.filter((device) => device.has_battery);
  const count = (bucket: BatteryBucket, dataOk: boolean) =>
    withBattery.filter(
      (device) =>
        device.battery_bucket === bucket && device.data_ok === dataOk,
    ).length;
  const wired = devices.filter((device) => !device.has_battery);
  return {
    ok_ok: count('ok', true),
    ok_no_data: count('ok', false),
    low_ok: count('low', true),
    low_no_data: count('low', false),
    unknown_ok: count('unknown', true),
    unknown_no_data: count('unknown', false),
    wired_total: wired.length,
    wired_no_data: wired.filter((device) => !device.data_ok).length,
  };
}

export interface MaintenanceHeatmapRow {
  deviceId: string;
  label: string;
  priority: PriorityLabel;
  cells: Array<MaintenanceHeatmapCellDto | null>;
}

export interface MaintenanceHeatmapData {
  dates: string[];
  rows: MaintenanceHeatmapRow[];
}

export function maintenanceHeatmap(
  devices: MaintenanceDeviceSummaryDto[],
  cells: MaintenanceHeatmapCellDto[],
): MaintenanceHeatmapData {
  const dates = Array.from(new Set(cells.map((cell) => cell.date))).sort();
  const byDevice = new Map<string, Map<string, MaintenanceHeatmapCellDto>>();
  for (const cell of cells) {
    if (!byDevice.has(cell.device_id)) {
      byDevice.set(cell.device_id, new Map());
    }
    byDevice.get(cell.device_id)!.set(cell.date, cell);
  }
  const rows = devices
    .filter((device) => device.mode === 'periodic' && byDevice.has(device.id))
    .map((device) => {
      const deviceCells = byDevice.get(device.id)!;
      return {
        deviceId: device.id,
        label: device.label,
        priority: device.priority_label,
        cells: dates.map((date) => deviceCells.get(date) ?? null),
      };
    });
  return { dates, rows };
}

export function availabilityColor(value: number | null): string {
  if (value === null) return '#f1f5f9';
  const ratio = Math.max(0, Math.min(1, value / 100));
  if (ratio >= 0.9) return `rgba(16, 185, 129, ${0.15 + ratio * 0.55})`;
  if (ratio >= 0.6) return `rgba(245, 158, 11, ${0.25 + ratio * 0.35})`;
  return `rgba(239, 68, 68, ${0.25 + (1 - ratio) * 0.5})`;
}
