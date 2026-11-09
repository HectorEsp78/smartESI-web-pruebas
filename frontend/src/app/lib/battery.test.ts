import { describe, expect, it } from 'vitest';
import {
  batteryBarPct,
  defaultHistoryPeriod,
  formatBatteryValue,
  historyPeriodError,
  historyShortcuts,
  historyYDomain,
  isBatteryGroupId,
} from './battery';
import type { BatterySensorDto } from '../types/battery';

const SENSOR: BatterySensorDto = {
  id: 'a11',
  label: 'Aula A11',
  entity_id: 'sensor.sensor_bateria_a11',
  unit: 'millivolt',
  value: 3450,
  estimated_pct: 70,
  level: 'medium',
  reading_at: '2026-11-09T10:00:00Z',
  age_hours: 1,
  is_current: true,
};

describe('battery helpers', () => {
  it('recognises the three group pages', () => {
    expect(isBatteryGroupId('shellys')).toBe(true);
    expect(isBatteryGroupId('valvulas')).toBe(true);
    expect(isBatteryGroupId('aulas')).toBe(true);
    expect(isBatteryGroupId('otros')).toBe(false);
    expect(isBatteryGroupId(undefined)).toBe(false);
  });

  it('formats each unit', () => {
    expect(formatBatteryValue(3641, 'millivolt')).toBe('3641 mV');
    expect(formatBatteryValue(51, 'percent')).toBe('51 %');
    expect(formatBatteryValue(null, 'percent')).toBe('—');
  });

  it('draws the bar from the reading or from the estimate', () => {
    expect(batteryBarPct(SENSOR)).toBe(70);
    expect(batteryBarPct({ ...SENSOR, unit: 'percent', value: 25, estimated_pct: null })).toBe(25);
    expect(batteryBarPct({ ...SENSOR, estimated_pct: null })).toBe(0);
  });

  it('opens the last 90 days for a sensor that still reports', () => {
    expect(defaultHistoryPeriod('2026-11-08T10:00:00Z', '2026-11-09')).toEqual({
      start: '2026-08-12',
      end: '2026-11-09',
    });
    expect(defaultHistoryPeriod(null, '2026-11-09').start).toBe('2026-08-12');
  });

  it('moves the period back so a retired sensor still shows its last readings', () => {
    expect(defaultHistoryPeriod('2024-04-03T13:21:18Z', '2026-11-09')).toEqual({
      start: '2024-01-05',
      end: '2026-11-09',
    });
  });

  it('offers a shortcut with the whole history', () => {
    const all = historyShortcuts('2026-11-09').at(-1);
    expect(all?.label).toBe('Todo');
    expect(all?.period).toEqual({ start: '2023-01-01', end: '2026-11-09' });
  });

  it('validates the period', () => {
    const today = '2026-11-09';
    expect(historyPeriodError({ start: '2026-01-01', end: today }, today)).toBeNull();
    expect(historyPeriodError({ start: '', end: today }, today)).not.toBeNull();
    expect(historyPeriodError({ start: '2026-11-09', end: '2026-11-01' }, today)).not.toBeNull();
    expect(historyPeriodError({ start: '2026-11-01', end: '2026-11-10' }, today)).not.toBeNull();
  });

  it('keeps the critical line inside the voltage axis', () => {
    expect(historyYDomain('percent', 20, 80, 20)).toEqual([0, 100]);
    expect(historyYDomain('millivolt', 3620, 3660, 3200)).toEqual([3100, 3800]);
    expect(historyYDomain('millivolt', null, null, 3200)).toEqual([3100, 3300]);
  });
});
