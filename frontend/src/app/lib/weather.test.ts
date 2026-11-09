import { describe, expect, it } from 'vitest';
import {
  aemetNotice,
  formatAge,
  formatCorrelation,
  formatHumidity,
  formatPmIndex,
  formatSigned,
  formatTemperature,
  solarExposureHint,
  weatherPeriodError,
} from './weather';
import type { AemetAvailabilityDto, AemetLatestDto } from '../types/weather';

function availability(overrides: Partial<AemetAvailabilityDto> = {}): AemetAvailabilityDto {
  return {
    coverage: 'complete',
    period_hours: 100,
    observed_hours: 100,
    compared_hours: 100,
    coverage_pct: 100,
    first_observation: '2026-10-01T00:00:00Z',
    last_observation: '2026-10-05T00:00:00Z',
    gaps: [],
    ...overrides,
  };
}

function latest(overrides: Partial<AemetLatestDto> = {}): AemetLatestDto {
  return {
    temperature_c: 20,
    humidity_pct: 40,
    pressure_hpa: 948,
    observed_at: '2026-10-29T17:00:00Z',
    age_hours: 1,
    stale: false,
    ...overrides,
  };
}

describe('weather formatting', () => {
  it('formats values and missing data', () => {
    expect(formatTemperature(21.55)).toBe('21,6 °C');
    expect(formatTemperature(null)).toBe('—');
    expect(formatHumidity(47.2)).toBe('47,2 %');
    expect(formatPmIndex(4384.4)).toBe('4384');
    expect(formatCorrelation(0.976)).toBe('0,98');
  });

  it('shows the sign of a difference', () => {
    expect(formatSigned(2.5, '°C')).toBe('+2,5 °C');
    expect(formatSigned(-2.3, 'hPa')).toBe('-2,3 hPa');
    expect(formatSigned(null, '°C')).toBe('—');
  });

  it('adapts the age to its size', () => {
    expect(formatAge(0.5)).toBe('30 min');
    expect(formatAge(5)).toBe('5,0 h');
    expect(formatAge(264)).toBe('11 días');
  });
});

describe('weather period', () => {
  it('rejects reversed, future and too long periods', () => {
    expect(weatherPeriodError({ start: '2026-10-10', end: '2026-10-01' })).toContain('anterior');
    expect(weatherPeriodError({ start: '2099-01-01', end: '2099-01-02' })).toContain('futura');
    expect(weatherPeriodError({ start: '2024-01-01', end: '2025-12-31' })).toContain('366');
  });
});

describe('aemetNotice', () => {
  it('stays quiet when the whole period can be compared', () => {
    expect(aemetNotice(availability(), latest())).toBeNull();
  });

  it('warns when there is nothing to compare, and says until when there was', () => {
    const notice = aemetNotice(
      availability({ coverage: 'none', compared_hours: 0, coverage_pct: 0 }),
      latest({ stale: true }),
    );
    expect(notice?.tone).toBe('warning');
    expect(notice?.title).toContain('No hay datos de AEMET');
    expect(notice?.detail).toContain('2026');
  });

  it('reports the coverage and the gaps of a partial comparison', () => {
    const notice = aemetNotice(
      availability({
        coverage: 'partial',
        compared_hours: 365,
        coverage_pct: 38.5,
        gaps: [
          { start: '2026-10-29T18:00:00Z', end: '2026-11-09T09:00:00Z', hours: 256 },
          { start: '2026-10-24T01:00:00Z', end: '2026-10-24T06:00:00Z', hours: 6 },
        ],
      }),
      latest(),
    );
    expect(notice?.title).toContain('39 %');
    expect(notice?.detail).toContain('365 horas');
    expect(notice?.detail).toContain('2 huecos');
    expect(notice?.detail).toContain('11 días');
  });

  it('points out a past period that is complete while AEMET has stopped', () => {
    const notice = aemetNotice(availability(), latest({ stale: true }));
    expect(notice?.tone).toBe('info');
    expect(notice?.title).toContain('no se está actualizando');
  });
});

describe('solarExposureHint', () => {
  it('only appears with a clearly warmer day', () => {
    expect(solarExposureHint(3.4, 1.4)).toContain('sol directo');
    expect(solarExposureHint(0.4, 0.8)).toBeNull();
    expect(solarExposureHint(null, 0.8)).toBeNull();
  });
});
