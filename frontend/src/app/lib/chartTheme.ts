import type { CSSProperties } from 'react';
import type { EnergyMetric } from '../types/energy';

// Institutional palette (see styles/theme.css).
export const CHART_PRIMARY = '#0497d7';
export const CHART_ACCENT = '#b30139';

export const SERIES_COLORS = ['#0497d7', '#1f6f9a', '#cf6c2e', '#2b8b57', '#b30139'];

const BUILDING_COLORS: Record<string, string> = {
  FerminCaballero: '#0497d7',
  ModuloB: '#1f6f9a',
};

export function buildingColor(id: string, index = 0): string {
  return BUILDING_COLORS[id] ?? SERIES_COLORS[index % SERIES_COLORS.length];
}

export const METRIC_COLOR: Record<EnergyMetric, string> = {
  kwh: '#0497d7',
  cost: '#cf6c2e',
  co2: '#2b8b57',
};

export const AXIS_TICK = { fill: '#64748b', fontSize: 12 } as const;
export const AXIS_LINE = { stroke: '#cbd5e1' } as const;

export const TOOLTIP_STYLE: CSSProperties = {
  border: '1px solid #cbd5e1',
  borderRadius: '4px',
  boxShadow: 'none',
  color: '#173247',
  fontSize: '12px',
  background: '#ffffff',
};
