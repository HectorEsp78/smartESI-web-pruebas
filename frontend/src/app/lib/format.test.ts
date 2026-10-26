import { describe, expect, it } from 'vitest';
import {
  formatEuro,
  formatKwh,
  formatNumber,
  formatPercent,
  formatSignedPercent,
  formatTimestamp,
} from './format';

describe('format helpers', () => {
  it('formats numbers with Spanish decimal separator', () => {
    expect(formatNumber(12.5, 1)).toBe('12,5');
  });

  it('formats percentages', () => {
    expect(formatPercent(12.5, 1)).toBe('12,5 %');
  });

  it('formats euros, kilowatt-hours and signed percentages', () => {
    expect(formatEuro(1234)).toBe(`${formatNumber(1234)} €`);
    expect(formatKwh(1234.5, 1)).toBe(`${formatNumber(1234.5, 1)} kWh`);
    expect(formatSignedPercent(4.2)).toBe(`+${formatNumber(4.2, 1)} %`);
    expect(formatSignedPercent(-4.2)).toBe(`${formatNumber(-4.2, 1)} %`);
  });

  it('returns an empty string for an invalid timestamp', () => {
    expect(formatTimestamp('not-a-date', 'HH:mm')).toBe('');
  });

  it('formats a valid timestamp', () => {
    expect(formatTimestamp('2026-01-15T08:30:00Z', 'yyyy')).toBe('2026');
  });
});
