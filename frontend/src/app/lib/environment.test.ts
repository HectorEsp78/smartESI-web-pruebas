import { describe, expect, it } from 'vitest';
import {
  defaultEnvironmentPeriod,
  environmentPeriodError,
  formatCo2,
  formatHumidity,
  formatOccupancy,
  formatPresence,
  formatTemperature,
  heatmapMatrix,
  isStaleTimestamp,
} from './environment';
import { periodDays } from './electricity';

describe('environment period', () => {
  it('defaults to today only', () => {
    expect(periodDays(defaultEnvironmentPeriod())).toBe(1);
  });

  it('rejects reversed and longer-than-a-year periods', () => {
    expect(environmentPeriodError({ start: '2026-10-10', end: '2026-10-01' })).toContain(
      'anterior',
    );
    expect(environmentPeriodError({ start: '2024-01-01', end: '2025-12-31' })).toContain(
      '366',
    );
    expect(environmentPeriodError({ start: '2099-01-01', end: '2099-01-02' })).toContain(
      'futura',
    );
  });
});

describe('environment formatting', () => {
  it('formats the basic room metrics', () => {
    expect(formatTemperature(21.55)).toBe('21,6 °C');
    expect(formatHumidity(47.2)).toBe('47,2 %');
    expect(formatCo2(812.4)).toBe('812 ppm');
    expect(formatPresence(true)).toBe('Sí');
    expect(formatPresence(null)).toBe('—');
    expect(formatOccupancy(29.4)).toBe('29 %');
  });

  it('marks missing or old timestamps as stale', () => {
    const now = new Date('2026-10-30T12:00:00Z').getTime();
    expect(isStaleTimestamp(null, 6, now)).toBe(true);
    expect(isStaleTimestamp('2026-10-30T10:00:00Z', 6, now)).toBe(false);
    expect(isStaleTimestamp('2026-10-30T04:00:00Z', 6, now)).toBe(true);
  });
});

describe('environment heatmap', () => {
  it('pivots the 7×24 cells into weekday rows', () => {
    const matrix = heatmapMatrix([
      { weekday: 2, hour: 14, presence_pct: 50, co2_ppm: 800 },
    ]);

    expect(matrix).toHaveLength(7);
    expect(matrix[2]).toHaveLength(24);
    expect(matrix[2][14]?.co2_ppm).toBe(800);
    expect(matrix[0][0]).toBeNull();
  });
});
