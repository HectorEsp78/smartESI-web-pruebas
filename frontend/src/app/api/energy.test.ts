import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchEnergyByBuilding, fetchEnergyConsumption } from './energy';

describe('energy api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('builds the consumption URL with query params', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ series: [] }) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchEnergyConsumption('week', 'ModuloB', 'cost');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = String(fetchMock.mock.calls[0][0]);
    expect(calledUrl).toContain('/api/v1/energy/consumption');
    expect(calledUrl).toContain('range=week');
    expect(calledUrl).toContain('building=ModuloB');
    expect(calledUrl).toContain('metric=cost');
  });

  it('throws a friendly error on 404', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    await expect(fetchEnergyByBuilding('day', 'kwh')).rejects.toThrow('No se encontró');
  });
});
