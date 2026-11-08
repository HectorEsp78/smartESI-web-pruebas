import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  fetchElectricityCompare,
  fetchElectricityCompareMany,
  fetchElectricityMeta,
  fetchElectricityStats,
} from './electricity';

describe('electricity api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('builds the stats URL with the selected dates, metric and sector', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchElectricityStats({
      start: '2026-10-01',
      end: '2026-10-07',
      granularity: 'day',
      metric: 'cost',
      building: 'FerminCaballero',
      sector: 'CPD',
    });

    const calledUrl = String(fetchMock.mock.calls[0][0]);
    expect(calledUrl).toContain('/api/v1/energy/electricity');
    expect(calledUrl).toContain('start=2026-10-01');
    expect(calledUrl).toContain('end=2026-10-07');
    expect(calledUrl).toContain('granularity=day');
    expect(calledUrl).toContain('metric=cost');
    expect(calledUrl).toContain('building=FerminCaballero');
    expect(calledUrl).toContain('sector=CPD');
  });

  it('builds the comparison URL with both independent periods', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchElectricityCompare(
      { start: '2026-10-01', end: '2026-10-07' },
      { start: '2025-10-01', end: '2025-10-07' },
      'day',
      'kwh',
      'ModuloA',
    );

    const calledUrl = String(fetchMock.mock.calls[0][0]);
    expect(calledUrl).toContain('/api/v1/energy/electricity/compare');
    expect(calledUrl).toContain('start_a=2026-10-01');
    expect(calledUrl).toContain('end_a=2026-10-07');
    expect(calledUrl).toContain('start_b=2025-10-01');
    expect(calledUrl).toContain('end_b=2025-10-07');
    expect(calledUrl).toContain('building=ModuloA');
  });

  it('loads the electricity metadata endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchElectricityMeta();

    expect(String(fetchMock.mock.calls[0][0])).toContain(
      '/api/v1/energy/electricity/meta',
    );
  });

  it('builds a multi-period comparison URL with repeated start and end params', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchElectricityCompareMany(
      [
        { start: '2026-10-01', end: '2026-10-31' },
        { start: '2025-10-01', end: '2025-10-31' },
        { start: '2024-10-01', end: '2024-10-31' },
      ],
      'day',
      'cost',
      'FerminCaballero',
      'CPD',
    );

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/energy/electricity/compare-many');
    expect(calledUrl.searchParams.getAll('start')).toEqual([
      '2026-10-01',
      '2025-10-01',
      '2024-10-01',
    ]);
    expect(calledUrl.searchParams.getAll('end')).toEqual([
      '2026-10-31',
      '2025-10-31',
      '2024-10-31',
    ]);
    expect(calledUrl.searchParams.get('granularity')).toBe('day');
    expect(calledUrl.searchParams.get('metric')).toBe('cost');
    expect(calledUrl.searchParams.get('building')).toBe('FerminCaballero');
    expect(calledUrl.searchParams.get('sector')).toBe('CPD');
  });

  it('surfaces the backend detail on validation errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Los dos periodos deben tener el mismo número de intervalos.' }),
      }),
    );

    await expect(
      fetchElectricityCompare(
        { start: '2026-10-01', end: '2026-10-07' },
        { start: '2025-10-01', end: '2025-10-06' },
        'day',
        'kwh',
        'all',
      ),
    ).rejects.toThrow('mismo número de intervalos');
  });
});
