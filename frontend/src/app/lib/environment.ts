import { parseISO } from 'date-fns';
import { formatNumber, formatPercent, formatTimestamp } from './format';
import {
  defaultElectricityPeriod,
  formatDateInputLabel,
  isValidPeriod,
  periodDays,
  todayIso,
} from './electricity';
import type { DatePeriod } from './electricity';
import type {
  EnvironmentHeatmapCellDto,
  EnvironmentQuality,
} from '../types/environment';

export const ENVIRONMENT_ROOM_COLORS: Record<string, string> = {
  A11: '#0497d7',
  A12: '#1f6f9a',
  A21: '#cf6c2e',
  A22: '#2b8b57',
  'F0.2': '#7c3aed',
  ALU: '#0891b2',
  AnitaBorg: '#b30139',
};

const FALLBACK_COLORS = [
  '#0497d7',
  '#1f6f9a',
  '#cf6c2e',
  '#2b8b57',
  '#7c3aed',
  '#0891b2',
  '#b30139',
];

export const DEFAULT_ENVIRONMENT_DAYS = 7;
export const MAX_ENVIRONMENT_DAYS = 366;

export const ENVIRONMENT_WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
export const ENVIRONMENT_HOURS = Array.from({ length: 24 }, (_, hour) => hour);

export function roomColor(roomId: string, index = 0): string {
  return ENVIRONMENT_ROOM_COLORS[roomId] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

export function defaultEnvironmentPeriod(): DatePeriod {
  return defaultElectricityPeriod(DEFAULT_ENVIRONMENT_DAYS);
}

export function isValidEnvironmentPeriod(period: DatePeriod): boolean {
  return (
    isValidPeriod(period) &&
    period.end <= todayIso() &&
    periodDays(period) <= MAX_ENVIRONMENT_DAYS
  );
}

export function environmentPeriodError(period: DatePeriod): string | null {
  if (!isValidPeriod(period)) {
    const start = parseISO(period.start);
    const end = parseISO(period.end);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      return 'El periodo no es válido.';
    }
    return 'La fecha final no puede ser anterior a la inicial.';
  }
  if (period.end > todayIso()) return 'La fecha final no puede ser futura.';
  if (periodDays(period) > MAX_ENVIRONMENT_DAYS) return 'El periodo máximo es de un año (366 días).';
  return null;
}

export function formatEnvironmentPeriod(period: DatePeriod): string {
  return `${formatDateInputLabel(period.start)} – ${formatDateInputLabel(period.end)}`;
}

export const QUALITY_TEXT_CLASS: Record<EnvironmentQuality, string> = {
  good: 'text-success',
  moderate: 'text-warning',
  poor: 'text-orange-600',
  bad: 'text-destructive',
  unknown: 'text-slate-500',
};

export const QUALITY_BG_CLASS: Record<EnvironmentQuality, string> = {
  good: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  moderate: 'bg-amber-50 text-amber-800 border-amber-200',
  poor: 'bg-orange-50 text-orange-800 border-orange-200',
  bad: 'bg-red-50 text-red-700 border-red-200',
  unknown: 'bg-slate-50 text-slate-600 border-slate-200',
};

export const QUALITY_DOT_CLASS: Record<EnvironmentQuality, string> = {
  good: 'bg-success',
  moderate: 'bg-warning',
  poor: 'bg-orange-500',
  bad: 'bg-destructive',
  unknown: 'bg-slate-400',
};

export function formatTemperature(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} °C`;
}

export function formatHumidity(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} %`;
}

export function formatCo2(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 0)} ppm`;
}

export function formatPresence(value: boolean | null): string {
  if (value === null) return '—';
  return value ? 'Sí' : 'No';
}

export function formatOccupancy(value: number | null): string {
  return value === null ? '—' : formatPercent(value, 0);
}

export function formatHours(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} h`;
}

export function formatGasCost(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 2)} €`;
}

export function formatGasVolume(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} m³`;
}

export function formatCorrelation(value: number | null): string {
  return value === null ? '—' : formatNumber(value, 2);
}

export function formatRecoveryHours(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} h`;
}

export function formatUpdatedAt(value: string | null): string {
  return value ? formatTimestamp(value, 'd MMM HH:mm') : 'Sin dato';
}

/** True when the last reading is old enough to be shown as stale. */
export function isStaleTimestamp(
  value: string | null,
  maxAgeHours = 6,
  now = Date.now(),
): boolean {
  if (!value) return true;
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return true;
  return now - time > maxAgeHours * 60 * 60 * 1000;
}

export type EnvironmentHeatmapMatrix = Array<Array<EnvironmentHeatmapCellDto | null>>;

/** Pivot the server's 7×24 list into weekday rows. */
export function heatmapMatrix(cells: EnvironmentHeatmapCellDto[]): EnvironmentHeatmapMatrix {
  const matrix: EnvironmentHeatmapMatrix = Array.from({ length: 7 }, () =>
    Array.from({ length: 24 }, () => null),
  );
  for (const cell of cells) {
    if (cell.weekday >= 0 && cell.weekday < 7 && cell.hour >= 0 && cell.hour < 24) {
      matrix[cell.weekday][cell.hour] = cell;
    }
  }
  return matrix;
}

/** Colour scale for a 0–100 heatmap value. */
export function heatmapColor(value: number | null, reverse = false): string {
  if (value === null) return '#f1f5f9';
  const ratio = Math.max(0, Math.min(1, value / 100));
  const strength = reverse ? 1 - ratio : ratio;
  const alpha = 0.08 + strength * 0.72;
  return reverse ? `rgba(179, 1, 57, ${alpha})` : `rgba(4, 151, 215, ${alpha})`;
}
