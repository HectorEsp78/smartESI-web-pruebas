import type { CSSProperties } from 'react';

// Institutional palette (see styles/theme.css).
export const CHART_PRIMARY = '#0497d7';
export const CHART_ACCENT = '#b30139';

export const SERIES_COLORS = ['#0497d7', '#1f6f9a', '#cf6c2e', '#2b8b57', '#b30139'];

const BUILDING_COLORS: Record<string, string> = {
  FerminCaballero: '#0497d7',
  ModuloB: '#1f6f9a',
};

// Electricity uses its own building order and colours so the Lighting charts
// keep their existing palette.
export const ELECTRICITY_BUILDING_COLORS: Record<string, string> = {
  ModuloA: '#cf6c2e',
  ModuloB: '#1f6f9a',
  FerminCaballero: '#0497d7',
};

// Enough distinct colours for the nine Fermín sectors (eight floor panels plus
// the CPD). The neutral grey is reserved for the "No desglosado" segment.
export const SECTOR_COLORS = [
  '#0497d7',
  '#1f6f9a',
  '#cf6c2e',
  '#2b8b57',
  '#b30139',
  '#7c3aed',
  '#0891b2',
  '#4d7c0f',
  '#be123c',
];

export const UNMETERED_COLOR = '#94a3b8';

export function buildingColor(id: string, index = 0): string {
  return BUILDING_COLORS[id] ?? SERIES_COLORS[index % SERIES_COLORS.length];
}

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
