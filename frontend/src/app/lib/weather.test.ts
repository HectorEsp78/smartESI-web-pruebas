import { describe, expect, it } from 'vitest';
import {
  aemetExposureLabel,
  currentStatusLabel,
  currentStatusTone,
  formatAgeHours,
  formatBattery,
  formatCorrelation,
  formatHours,
  formatHumidity,
  formatKm,
  formatMm,
  formatPmIndex,
  formatPressure,
  formatSigned,
  formatSignedPressure,
  formatSignedTemperature,
  formatTemperature,
  parseWeatherDays,
  pressureTrendLabel,
  weatherDaysLabel,
} from './weather';
import type { WeatherAemetCrossDto } from '../types/weather';

function aemet(
  overrides: Partial<WeatherAemetCrossDto> = {},
): WeatherAemetCrossDto {
  return {
    available: true,
    stale: false,
    samples: 24,
    last_updated: '2026-11-01T10:00:00Z',
    temperature_bias_c: 2,
    temperature_mae_c: 2.4,
    temperature_correlation: 0.9,
    humidity_bias_pct: -5,
    humidity_mae_pct: 6,
    humidity_correlation: 0.8,
    pressure_bias_hpa: -2.3,
    pressure_correlation: 0.99,
    daytime_temperature_bias_c: 5.1,
    nighttime_temperature_bias_c: 0.3,
    precipitation_mm: 0,
    visibility_min_km: 10,
    hourly_bias: [],
    ...overrides,
  };
}

describe('weather period', () => {
  it('accepts only 7, 30 or 90 days and defaults to 30', () => {
    expect(parseWeatherDays('7')).toBe(7);
    expect(parseWeatherDays('90')).toBe(90);
    expect(parseWeatherDays('14')).toBe(30);
    expect(parseWeatherDays(null)).toBe(30);
  });

  it('labels the selected window', () => {
    expect(weatherDaysLabel(7)).toBe('Últimos 7 días');
    expect(weatherDaysLabel(30)).toBe('Últimos 30 días');
    expect(weatherDaysLabel(90)).toBe('Últimos 90 días');
  });
});

describe('weather formatting', () => {
  it('formats the station metrics with Spanish separators', () => {
    expect(formatTemperature(21.55)).toBe('21,6 °C');
    expect(formatHumidity(47.2)).toBe('47,2 %');
    expect(formatPressure(1013.25)).toBe('1013,3 hPa');
    expect(formatPmIndex(1234)).toBe('1234');
    expect(formatBattery(85.4)).toBe('85 %');
    expect(formatCorrelation(-0.575)).toBe('-0,58');
  });

  it('handles missing values consistently', () => {
    expect(formatTemperature(null)).toBe('—');
    expect(formatHumidity(null)).toBe('—');
    expect(formatPressure(null)).toBe('—');
    expect(formatPmIndex(null)).toBe('—');
    expect(formatBattery(null)).toBe('—');
    expect(formatCorrelation(null)).toBe('—');
    expect(formatMm(null)).toBe('—');
    expect(formatKm(null)).toBe('—');
  });

  it('formats durations at minute, hour and day scale', () => {
    expect(formatHours(0.5)).toBe('30 min');
    expect(formatHours(3.5)).toBe('3,5 h');
    expect(formatHours(72)).toBe('3,0 d');
    expect(formatHours(null)).toBe('—');
    expect(formatAgeHours(0.5)).toBe('30 min');
    expect(formatAgeHours(3.5)).toBe('3,5 h');
  });

  it('formats signed values and pressure trends', () => {
    expect(formatSigned(2.34)).toBe('+2,3');
    expect(formatSigned(-2.34)).toBe('-2,3');
    expect(formatSigned(null)).toBe('—');
    expect(formatSignedPressure(1.2)).toBe('+1,2 hPa');
    expect(formatSignedTemperature(-3.9)).toBe('-3,9 °C');
    expect(pressureTrendLabel(1)).toBe('Subiendo');
    expect(pressureTrendLabel(-1)).toBe('Bajando');
    expect(pressureTrendLabel(0.2)).toBe('Estable');
    expect(pressureTrendLabel(null)).toBe('Sin datos');
  });
});

describe('weather status', () => {
  it('maps station status to a label and tone', () => {
    expect(currentStatusLabel('ok')).toBe('En directo');
    expect(currentStatusLabel('stale')).toBe('Datos desfasados');
    expect(currentStatusLabel('missing')).toBe('Sin datos');
    expect(currentStatusTone('ok')).toBe('success');
    expect(currentStatusTone('stale')).toBe('warning');
    expect(currentStatusTone('missing')).toBe('neutral');
  });
});

describe('AEMET exposure hint', () => {
  it('flags a much larger daytime bias', () => {
    expect(aemetExposureLabel(aemet())).toContain('Posible exposición solar');
  });

  it('flags a larger nighttime bias', () => {
    expect(
      aemetExposureLabel(
        aemet({
          daytime_temperature_bias_c: 1,
          nighttime_temperature_bias_c: 4,
        }),
      ),
    ).toContain('sesgo nocturno');
  });

  it('does not over-interpret a small difference', () => {
    expect(
      aemetExposureLabel(
        aemet({
          daytime_temperature_bias_c: 1,
          nighttime_temperature_bias_c: 1,
        }),
      ),
    ).toContain('Sin un sesgo');
  });

  it('returns null when the hourly biases are missing', () => {
    expect(
      aemetExposureLabel(
        aemet({
          daytime_temperature_bias_c: null,
          nighttime_temperature_bias_c: null,
        }),
      ),
    ).toBeNull();
  });
});
