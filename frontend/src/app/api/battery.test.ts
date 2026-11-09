import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchBatteryGroup, fetchBatteryHistory } from './battery';

describe('battery api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function stubFetch() {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);
    return fetchMock;
  }

  it('requests the sensors of a group', async () => {
    const fetchMock = stubFetch();

    await fetchBatteryGroup('valvulas');

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/maintenance/batteries/valvulas');
  });

  it('requests the history of a sensor for the selected dates', async () => {
    const fetchMock = stubFetch();

    await fetchBatteryHistory('aulas', 'a11', { start: '2026-10-01', end: '2026-10-31' });

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/maintenance/batteries/aulas/a11/history');
    expect(calledUrl.searchParams.get('start')).toBe('2026-10-01');
    expect(calledUrl.searchParams.get('end')).toBe('2026-10-31');
  });
});
