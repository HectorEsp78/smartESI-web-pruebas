import { differenceInCalendarDays, format, isAfter, parseISO, subDays, subYears } from 'date-fns';
import { es } from 'date-fns/locale';
import type { ElectricityGranularity, ElectricityMetric } from '../types/electricity';

export interface DatePeriod {
  start: string;
  end: string;
}

export const ELECTRICITY_TICK_PATTERN: Record<ElectricityGranularity, string> = {
  day: 'd MMM',
  week: 'd MMM',
  month: 'MMM yy',
  year: 'yyyy',
};

export const ELECTRICITY_TOOLTIP_PATTERN: Record<ElectricityGranularity, string> = {
  day: 'EEEE d MMM yyyy',
  week: "'Semana del' d MMM yyyy",
  month: 'MMMM yyyy',
  year: 'yyyy',
};

export function localIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function todayIso(): string {
  return localIsoDate(new Date());
}

export function defaultElectricityPeriod(days = 30): DatePeriod {
  const end = new Date();
  const start = subDays(end, Math.max(0, days - 1));
  return { start: localIsoDate(start), end: localIsoDate(end) };
}

export function previousYearPeriod(period: DatePeriod): DatePeriod {
  const start = parseISO(period.start);
  const end = parseISO(period.end);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return period;
  return {
    start: localIsoDate(subYears(start, 1)),
    end: localIsoDate(subYears(end, 1)),
  };
}

export function periodDays(period: DatePeriod): number {
  const start = parseISO(period.start);
  const end = parseISO(period.end);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  return differenceInCalendarDays(end, start) + 1;
}

export function isValidPeriod(period: DatePeriod): boolean {
  const start = parseISO(period.start);
  const end = parseISO(period.end);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return false;
  return !isAfter(start, end);
}

/**
 * The UI no longer exposes a "group by" control: the aggregation is derived
 * from the selected period so the charts stay readable without asking the user
 * to reason about buckets. Short ranges keep daily detail; long ranges are
 * grouped into weeks, months or years.
 */
export function granularityForPeriod(period: DatePeriod): ElectricityGranularity {
  const days = periodDays(period);
  if (days <= 31) return 'day';
  if (days <= 120) return 'week';
  if (days <= 1095) return 'month';
  return 'year';
}

export function formatPeriod(period: DatePeriod): string {
  const start = parseISO(period.start);
  const end = parseISO(period.end);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return 'Periodo incompleto';
  }
  return `${format(start, 'd MMM yyyy', { locale: es })} – ${format(end, 'd MMM yyyy', { locale: es })}`;
}

export function formatDateInputLabel(value: string): string {
  const date = parseISO(value);
  if (Number.isNaN(date.getTime())) return value;
  return format(date, 'd MMM yyyy', { locale: es });
}

export function formatElectricityValue(value: number, unit: string): string {
  const digits = unit === '€' ? 2 : Math.abs(value) >= 100 ? 0 : 1;
  return `${new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)} ${unit}`;
}

export function metricLabel(metric: ElectricityMetric): string {
  return metric === 'cost' ? 'Coste' : 'Consumo';
}
