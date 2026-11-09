import { environmentPeriodError } from './environment';
import { formatNumber, formatTimestamp } from './format';
import type {
  AemetAvailabilityDto,
  AemetLatestDto,
  WeatherGranularity,
  WeatherStatus,
} from '../types/weather';

export const DEFAULT_WEATHER_PERIOD_DAYS = 30;
export const WEATHER_PERIOD_SHORTCUTS = [7, 30, 90] as const;

export const STATION_COLOR = '#0497d7';
export const AEMET_COLOR = '#b30139';

/** Same rules as Infrastructure: valid dates, not in the future, at most a year. */
export const weatherPeriodError = environmentPeriodError;

const AEMET_DATE_PATTERN = 'd MMM yyyy, HH:mm';

export function weatherTickPattern(granularity: WeatherGranularity): string {
  return granularity === 'hour' ? "d MMM HH'h'" : 'd MMM';
}

export function weatherTooltipPattern(granularity: WeatherGranularity): string {
  return granularity === 'hour' ? 'EEEE d MMM, HH:mm' : 'EEEE d MMM yyyy';
}

function withUnit(value: number | null, unit: string, digits = 1): string {
  return value === null ? '—' : `${formatNumber(value, digits)} ${unit}`;
}

export const formatTemperature = (value: number | null) => withUnit(value, '°C');
export const formatHumidity = (value: number | null) => withUnit(value, '%');
export const formatPressure = (value: number | null) => withUnit(value, 'hPa');
export const formatMm = (value: number | null) => withUnit(value, 'mm');
export const formatPercent = (value: number | null) => withUnit(value, '%', 0);

export function formatPmIndex(value: number | null): string {
  return value === null ? '—' : formatNumber(value, 0);
}

export function formatCorrelation(value: number | null): string {
  return value === null ? '—' : formatNumber(value, 2);
}

export function formatSigned(value: number | null, unit: string): string {
  if (value === null) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, 1)} ${unit}`;
}

export function formatAge(hours: number | null): string {
  if (hours === null) return '—';
  if (hours < 1) return `${formatNumber(hours * 60, 0)} min`;
  if (hours < 48) return `${formatNumber(hours, 1)} h`;
  return `${formatNumber(hours / 24, 0)} días`;
}

export function currentStatusLabel(status: WeatherStatus): string {
  if (status === 'ok') return 'En directo';
  if (status === 'stale') return 'Datos desfasados';
  return 'Sin datos';
}

export interface AemetNotice {
  tone: 'info' | 'warning';
  title: string;
  detail: string;
}

/** Explain how much of the period can be compared, or `null` if all of it can. */
export function aemetNotice(
  availability: AemetAvailabilityDto,
  latest: AemetLatestDto,
): AemetNotice | null {
  const lastRecorded = latest.observed_at
    ? `La última observación guardada es del ${formatTimestamp(latest.observed_at, AEMET_DATE_PATTERN)}.`
    : 'No hay ninguna observación guardada.';

  if (availability.coverage === 'none') {
    return {
      tone: 'warning',
      title: 'No hay datos de AEMET en este periodo',
      detail: `Se muestra solo la estación del centro. ${lastRecorded} Elige un periodo anterior para compararlas.`,
    };
  }
  if (availability.coverage === 'partial') {
    const longest = availability.gaps.reduce<number>((max, gap) => Math.max(max, gap.hours), 0);
    const gaps =
      longest > 0
        ? ` Hay ${availability.gaps.length} ${availability.gaps.length === 1 ? 'hueco' : 'huecos'} de 6 h o más; el mayor dura ${formatAge(longest)}.`
        : '';
    return {
      tone: 'warning',
      title: `La comparación cubre el ${formatNumber(availability.coverage_pct, 0)} % del periodo`,
      detail: `Solo se comparan las ${formatNumber(availability.compared_hours, 0)} horas con datos de ambas fuentes.${gaps}`,
    };
  }
  if (latest.stale) {
    return {
      tone: 'info',
      title: 'AEMET no se está actualizando',
      detail: `Este periodo está completo, pero el registro no recibe datos nuevos. ${lastRecorded}`,
    };
  }
  return null;
}

/** Read the daytime and night-time bias: a warmer day points to direct sun. */
export function solarExposureHint(
  daytimeBias: number | null,
  nighttimeBias: number | null,
): string | null {
  if (daytimeBias === null || nighttimeBias === null) return null;
  return daytimeBias - nighttimeBias >= 1.5
    ? 'La estación se calienta más que AEMET de día que de noche: puede recibir sol directo.'
    : null;
}
