import { formatNumber } from './format';
import type { WeatherAemetCrossDto, WeatherStatus } from '../types/weather';

export const WEATHER_DAYS_OPTIONS = [7, 30, 90] as const;
export type WeatherDays = (typeof WEATHER_DAYS_OPTIONS)[number];
export const DEFAULT_WEATHER_DAYS: WeatherDays = 30;

export function parseWeatherDays(value: string | null | undefined): WeatherDays {
  const parsed = Number(value);
  return (WEATHER_DAYS_OPTIONS as readonly number[]).includes(parsed)
    ? (parsed as WeatherDays)
    : DEFAULT_WEATHER_DAYS;
}

export function weatherDaysLabel(days: WeatherDays): string {
  if (days === 7) return 'Últimos 7 días';
  if (days === 90) return 'Últimos 90 días';
  return 'Últimos 30 días';
}

export function formatTemperature(value: number | null, digits = 1): string {
  return value === null ? '—' : `${formatNumber(value, digits)} °C`;
}

export function formatHumidity(value: number | null, digits = 1): string {
  return value === null ? '—' : `${formatNumber(value, digits)} %`;
}

export function formatPressure(value: number | null, digits = 1): string {
  return value === null ? '—' : `${formatNumber(value, digits)} hPa`;
}

export function formatPmIndex(value: number | null): string {
  return value === null ? '—' : formatNumber(value, 0);
}

export function formatBattery(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 0)} %`;
}

export function formatCorrelation(value: number | null): string {
  return value === null ? '—' : formatNumber(value, 2);
}

export function formatHours(value: number | null): string {
  if (value === null) return '—';
  if (value < 1) return `${formatNumber(value * 60, 0)} min`;
  if (value < 48) return `${formatNumber(value, 1)} h`;
  return `${formatNumber(value / 24, 1)} d`;
}

export function formatAgeHours(value: number | null): string {
  if (value === null) return '—';
  if (value < 1) return `${formatNumber(value * 60, 0)} min`;
  return `${formatNumber(value, 1)} h`;
}

export function formatSigned(value: number | null, digits = 1): string {
  if (value === null) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, digits)}`;
}

export function formatSignedPressure(value: number | null): string {
  if (value === null) return '—';
  return `${formatSigned(value, 1)} hPa`;
}

export function formatSignedTemperature(value: number | null): string {
  if (value === null) return '—';
  return `${formatSigned(value, 1)} °C`;
}

export function pressureTrendLabel(value: number | null): string {
  if (value === null) return 'Sin datos';
  if (value > 0.5) return 'Subiendo';
  if (value < -0.5) return 'Bajando';
  return 'Estable';
}

export function currentStatusLabel(status: WeatherStatus): string {
  if (status === 'ok') return 'En directo';
  if (status === 'stale') return 'Datos desfasados';
  return 'Sin datos';
}

export function currentStatusTone(
  status: WeatherStatus,
): 'success' | 'warning' | 'neutral' {
  if (status === 'ok') return 'success';
  if (status === 'stale') return 'warning';
  return 'neutral';
}

export function aemetExposureLabel(cross: WeatherAemetCrossDto): string | null {
  if (
    cross.daytime_temperature_bias_c === null ||
    cross.nighttime_temperature_bias_c === null
  ) {
    return null;
  }
  const difference =
    cross.daytime_temperature_bias_c - cross.nighttime_temperature_bias_c;
  if (difference >= 3) {
    return 'Posible exposición solar: el sesgo diurno es mucho mayor que el nocturno.';
  }
  if (difference <= -3) {
    return 'El sesgo nocturno es mayor que el diurno; revisa la ubicación del sensor.';
  }
  return 'Sin un sesgo diurno claro frente a AEMET.';
}

export function formatMm(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} mm`;
}

export function formatKm(value: number | null): string {
  return value === null ? '—' : `${formatNumber(value, 1)} km`;
}
