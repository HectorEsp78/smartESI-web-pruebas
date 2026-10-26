import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import type { DashboardRange } from '../types/range';

export const RANGE_LABEL: Record<DashboardRange, string> = {
  day: 'Día',
  week: 'Semana',
  month: 'Mes',
  year: 'Año',
};

interface RangeFormatting {
  title: string;
  subtitle: string;
  tickPattern: string;
  tooltipPattern: string;
}

export const RANGE_FORMATTING: Record<DashboardRange, RangeFormatting> = {
  day: {
    title: 'Últimas 24 horas',
    subtitle: 'Agregación por hora',
    tickPattern: 'HH:mm',
    tooltipPattern: "EEEE d MMM, HH:mm",
  },
  week: {
    title: 'Últimos 7 días',
    subtitle: 'Agregación por día',
    tickPattern: 'EEE d',
    tooltipPattern: 'EEEE d MMM',
  },
  month: {
    title: 'Últimos 30 días',
    subtitle: 'Agregación por día',
    tickPattern: 'd MMM',
    tooltipPattern: 'd MMM yyyy',
  },
  year: {
    title: 'Últimos 12 meses',
    subtitle: 'Agregación por mes',
    tickPattern: 'MMM',
    tooltipPattern: 'MMMM yyyy',
  },
};

export function formatTimestamp(value: string | number, pattern: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return format(date, pattern, { locale: es });
}

function numberFormatter(digits: number): Intl.NumberFormat {
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatNumber(value: number, digits = 0): string {
  return numberFormatter(digits).format(value);
}

export function formatPercent(value: number, digits = 0): string {
  return `${formatNumber(value, digits)} %`;
}

export function formatEuro(value: number, digits = 0): string {
  return `${formatNumber(value, digits)} €`;
}

export function formatSignedPercent(value: number, digits = 1): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, digits)} %`;
}

export function formatKwh(value: number, digits = 0): string {
  return `${formatNumber(value, digits)} kWh`;
}
