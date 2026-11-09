import { parseISO } from 'date-fns';
import { formatNumber, formatPercent } from './format';
import {
  defaultElectricityPeriod,
  formatDateInputLabel,
  isValidPeriod,
  periodDays,
  todayIso,
} from './electricity';
import type { DatePeriod } from './electricity';
import type { EnvironmentHeatmapCellDto } from '../types/environment';

const DEFAULT_ENVIRONMENT_DAYS = 1;
const MAX_ENVIRONMENT_DAYS = 366;

export function defaultEnvironmentPeriod(): DatePeriod {
  return defaultElectricityPeriod(DEFAULT_ENVIRONMENT_DAYS);
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
