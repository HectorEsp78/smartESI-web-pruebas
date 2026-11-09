import { format, subDays } from 'date-fns';
import { formatNumber } from './format';
import { defaultElectricityPeriod, todayIso } from './electricity';
import type { DatePeriod } from './electricity';
import type { BatteryLevel, BatterySensorDto, BatteryUnit } from '../types/battery';

export interface BatteryGroupPage {
  id: string;
  label: string;
  description: string;
}

/** One page per group, each one at `/mantenimiento/<id>`. */
export const BATTERY_GROUP_PAGES: BatteryGroupPage[] = [
  { id: 'shellys', label: 'Shellys', description: 'Batería de los sensores Shelly.' },
  { id: 'valvulas', label: 'Válvulas', description: 'Batería de las válvulas de radiador.' },
  { id: 'aulas', label: 'Aulas', description: 'Batería de los sensores de las aulas.' },
];

export const DEFAULT_BATTERY_GROUP = BATTERY_GROUP_PAGES[0].id;

const DEFAULT_HISTORY_DAYS = 90;
/** Before the first battery row of the recorder (February 2023). */
const FULL_HISTORY_START = '2023-01-01';

export const BATTERY_LEVEL_LABEL: Record<BatteryLevel, string> = {
  ok: 'Bien',
  medium: 'Media',
  low: 'Baja',
  critical: 'Crítica',
  unknown: 'Sin lectura actual',
};

export function isBatteryGroupId(value: string | undefined): value is string {
  return BATTERY_GROUP_PAGES.some((page) => page.id === value);
}

export function formatBatteryValue(value: number | null, unit: BatteryUnit, digits = 0): string {
  if (value === null) return '—';
  return `${formatNumber(value, digits)} ${unit === 'millivolt' ? 'mV' : '%'}`;
}

/** Width of the level bar: the reading itself, or the estimate for millivolts. */
export function batteryBarPct(sensor: BatterySensorDto): number {
  const pct = sensor.unit === 'millivolt' ? sensor.estimated_pct : sensor.value;
  return Math.min(100, Math.max(0, pct ?? 0));
}

/** Last 90 days, moved back if the sensor stopped reporting before them. */
export function defaultHistoryPeriod(
  readingAt: string | null,
  today: string = todayIso(),
): DatePeriod {
  const start = format(subDays(new Date(`${today}T12:00:00`), DEFAULT_HISTORY_DAYS - 1), 'yyyy-MM-dd');
  if (!readingAt || format(new Date(readingAt), 'yyyy-MM-dd') >= start) {
    return { start, end: today };
  }
  return {
    start: format(subDays(new Date(readingAt), DEFAULT_HISTORY_DAYS - 1), 'yyyy-MM-dd'),
    end: today,
  };
}

export function historyShortcuts(today: string = todayIso()): Array<{
  label: string;
  period: DatePeriod;
}> {
  return [
    { label: '30 días', period: defaultElectricityPeriod(30) },
    { label: '90 días', period: defaultElectricityPeriod(90) },
    { label: '1 año', period: defaultElectricityPeriod(365) },
    { label: 'Todo', period: { start: FULL_HISTORY_START, end: today } },
  ];
}

export function historyPeriodError(period: DatePeriod, today: string = todayIso()): string | null {
  if (!period.start || !period.end) return 'Indica las dos fechas del periodo.';
  if (period.start > period.end) return 'La fecha inicial no puede ser posterior a la final.';
  if (period.end > today) return 'La fecha final no puede ser futura.';
  return null;
}

export function historyYDomain(
  unit: BatteryUnit,
  minValue: number | null,
  maxValue: number | null,
  criticalThreshold: number,
): [number, number] {
  if (unit === 'percent') return [0, 100];
  const margin = 50;
  const low = Math.min(minValue ?? criticalThreshold, criticalThreshold) - margin;
  const high = Math.max(maxValue ?? criticalThreshold, criticalThreshold) + margin;
  return [Math.floor(low / 100) * 100, Math.ceil(high / 100) * 100];
}
