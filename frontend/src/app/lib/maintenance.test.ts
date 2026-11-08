import { describe, expect, it } from 'vitest';
import {
  availabilityColor,
  filterMaintenanceDevices,
  formatBatteryAge,
  formatBatteryPercent,
  formatBatteryValue,
  formatDurationHours,
  maintenanceFilterCount,
  maintenanceHeatmap,
  maintenanceMatrixCounts,
  parseMaintenanceDays,
} from './maintenance';
import type {
  MaintenanceBatteryInfoDto,
  MaintenanceDeviceSummaryDto,
  MaintenanceHeatmapCellDto,
} from '../types/maintenance';

function battery(
  overrides: Partial<MaintenanceBatteryInfoDto> = {},
): MaintenanceBatteryInfoDto {
  return {
    value: 85,
    unit: 'percent',
    estimated_pct: 85,
    status: 'ok',
    reading_at: '2026-11-01T10:00:00Z',
    age_hours: 2,
    stale: false,
    trend_30d_pct: null,
    replacement_detected: false,
    replacement_at: null,
    replacement_in_period: false,
    days_to_critical: null,
    forecast_30d_pct: null,
    forecast_60d_pct: null,
    forecast_90d_pct: null,
    forecast_replacement_at: null,
    ...overrides,
  };
}

function device(
  overrides: Partial<MaintenanceDeviceSummaryDto> = {},
): MaintenanceDeviceSummaryDto {
  return {
    id: 'shelly1',
    label: 'Shelly 1',
    type: 'Shelly H&T',
    location: null,
    mode: 'periodic',
    has_battery: true,
    notes: null,
    battery: battery(),
    heartbeat: {
      last_at: '2026-11-01T10:00:00Z',
      silence_hours: 1,
      updates_per_day: 12,
      expected_per_day: 12,
      ratio: 1,
      median_interval_hours: 2,
      p95_interval_hours: 2.5,
      threshold_hours: 6,
      status: 'ok',
    },
    availability: {
      availability_pct: 99,
      outages_total: 0,
      outages_individual: 0,
      outages_global: 0,
      outages_group: 0,
      downtime_hours: 0,
      mtbf_hours: null,
      mttr_hours: null,
    },
    battery_bucket: 'ok',
    data_status: 'ok',
    data_ok: true,
    matrix_category: 'correcto',
    priority: 0,
    priority_label: 'low',
    decision: 'Todo correcto.',
    reasons: [],
    ...overrides,
  };
}

describe('maintenance period', () => {
  it('accepts only 7, 30 or 90 days and defaults to 30', () => {
    expect(parseMaintenanceDays('7')).toBe(7);
    expect(parseMaintenanceDays('90')).toBe(90);
    expect(parseMaintenanceDays('15')).toBe(30);
    expect(parseMaintenanceDays(null)).toBe(30);
  });
});

describe('maintenance formatting', () => {
  it('formats durations at minute, hour and day scale', () => {
    expect(formatDurationHours(0.5)).toBe('30 min');
    expect(formatDurationHours(3.5)).toBe('3,5 h');
    expect(formatDurationHours(72)).toBe('3,0 d');
    expect(formatDurationHours(null)).toBe('—');
  });

  it('shows millivolts and their approximate percentage', () => {
    const mvBattery = battery({
      value: 3450,
      unit: 'millivolt',
      estimated_pct: 70,
    });
    expect(formatBatteryValue(mvBattery)).toBe('3450 mV');
    expect(formatBatteryPercent(mvBattery)).toBe('70 %');
  });

  it('formats battery age and missing readings', () => {
    expect(formatBatteryAge(battery({ age_hours: 72 }))).toBe('hace 3,0 d');
    expect(formatBatteryAge(battery({ reading_at: null, age_hours: null }))).toBe(
      'Sin lectura',
    );
  });
});

describe('maintenance filters', () => {
  const devices = [
    device({ id: 'ok', priority_label: 'low' }),
    device({ id: 'urgent', priority_label: 'urgent', priority: 90 }),
    device({
      id: 'low',
      battery_bucket: 'low',
      battery: battery({ status: 'low', value: 30 }),
    }),
    device({
      id: 'silent',
      data_ok: false,
      data_status: 'device_silent',
    }),
  ];

  it('counts each filter independently', () => {
    expect(maintenanceFilterCount(devices, 'all')).toBe(4);
    expect(maintenanceFilterCount(devices, 'priority')).toBe(1);
    expect(maintenanceFilterCount(devices, 'low_battery')).toBe(1);
    expect(maintenanceFilterCount(devices, 'no_data')).toBe(1);
  });

  it('returns the matching devices', () => {
    expect(filterMaintenanceDevices(devices, 'no_data').map((item) => item.id)).toEqual([
      'silent',
    ]);
  });
});

describe('maintenance matrix', () => {
  it('crosses battery buckets with data availability', () => {
    const counts = maintenanceMatrixCounts([
      device({ id: 'ok-ok' }),
      device({ id: 'ok-no-data', data_ok: false, battery_bucket: 'ok' }),
      device({ id: 'low-ok', battery_bucket: 'low' }),
      device({ id: 'low-no-data', battery_bucket: 'low', data_ok: false }),
      device({ id: 'unknown-ok', battery_bucket: 'unknown' }),
      device({ id: 'unknown-no-data', battery_bucket: 'unknown', data_ok: false }),
      device({ id: 'wired', has_battery: false, battery: null }),
    ]);

    expect(counts).toMatchObject({
      ok_ok: 1,
      ok_no_data: 1,
      low_ok: 1,
      low_no_data: 1,
      unknown_ok: 1,
      unknown_no_data: 1,
      wired_total: 1,
      wired_no_data: 0,
    });
  });
});

describe('maintenance heatmap', () => {
  const cells: MaintenanceHeatmapCellDto[] = [
    {
      device_id: 'shelly1',
      date: '2026-11-02',
      updates: 12,
      expected: 12,
      availability_pct: 100,
    },
    {
      device_id: 'shelly1',
      date: '2026-11-01',
      updates: 6,
      expected: 12,
      availability_pct: 50,
    },
    {
      device_id: 'event',
      date: '2026-11-01',
      updates: 1,
      expected: null,
      availability_pct: null,
    },
  ];

  it('sorts dates and keeps only periodic devices with cells', () => {
    const data = maintenanceHeatmap(
      [
        device({ id: 'shelly1', label: 'Shelly 1' }),
        device({ id: 'event', mode: 'event' }),
        device({ id: 'no-cells', label: 'Sin celdas' }),
      ],
      cells,
    );

    expect(data.dates).toEqual(['2026-11-01', '2026-11-02']);
    expect(data.rows).toHaveLength(1);
    expect(data.rows[0].label).toBe('Shelly 1');
    expect(data.rows[0].cells.map((cell) => cell?.availability_pct ?? null)).toEqual([
      50,
      100,
    ]);
  });

  it('uses a neutral colour for missing availability', () => {
    expect(availabilityColor(null)).toBe('#f1f5f9');
    expect(availabilityColor(95)).toContain('16, 185, 129');
    expect(availabilityColor(70)).toContain('245, 158, 11');
    expect(availabilityColor(20)).toContain('239, 68, 68');
  });
});
