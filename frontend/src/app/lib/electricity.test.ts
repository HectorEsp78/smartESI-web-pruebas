import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  defaultElectricityPeriod,
  formatElectricityValue,
  formatPeriod,
  granularityForPeriod,
  isValidPeriod,
  periodDays,
  previousYearPeriod,
} from './electricity';

describe('electricity date helpers', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('builds a period ending today with the requested number of days', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 25, 12, 0, 0));

    const period = defaultElectricityPeriod(30);

    expect(period).toEqual({ start: '2026-09-26', end: '2026-10-25' });
    expect(periodDays(period)).toBe(30);
  });

  it('chooses the granularity from the selected range', () => {
    expect(granularityForPeriod({ start: '2026-10-01', end: '2026-10-31' })).toBe('day');
    expect(granularityForPeriod({ start: '2026-08-01', end: '2026-10-31' })).toBe('week');
    expect(granularityForPeriod({ start: '2026-01-01', end: '2026-12-31' })).toBe('month');
    expect(granularityForPeriod({ start: '2020-01-01', end: '2026-12-31' })).toBe('year');
    expect(granularityForPeriod({ start: '', end: '' })).toBe('day');
  });

  it('moves a period back one year and handles leap days', () => {
    expect(previousYearPeriod({ start: '2026-10-01', end: '2026-10-07' })).toEqual({
      start: '2025-10-01',
      end: '2025-10-07',
    });
    expect(previousYearPeriod({ start: '2024-02-29', end: '2024-03-01' })).toEqual({
      start: '2023-02-28',
      end: '2023-03-01',
    });
  });

  it('rejects an inverted or empty period without crashing the label helpers', () => {
    const invalid = { start: '', end: '2026-10-01' };
    expect(isValidPeriod(invalid)).toBe(false);
    expect(formatPeriod(invalid)).toBe('Periodo incompleto');
    expect(previousYearPeriod(invalid)).toEqual(invalid);
    expect(periodDays(invalid)).toBe(0);
    expect(isValidPeriod({ start: '2026-10-07', end: '2026-10-01' })).toBe(false);
    expect(isValidPeriod({ start: '2026-10-01', end: '2026-10-01' })).toBe(true);
  });

  it('formats energy and cost with the right precision', () => {
    expect(formatElectricityValue(1.234, '€')).toBe('1,23 €');
    expect(formatElectricityValue(1234, 'kWh')).toContain('kWh');
  });
});
