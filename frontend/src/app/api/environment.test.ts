import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchEnvironmentOverview, fetchEnvironmentRoom } from './environment';

const period = { start: '2026-10-01', end: '2026-10-07' };

describe('environment api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the custom period for the compact index', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchEnvironmentOverview(period);

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/environment/overview');
    expect(calledUrl.searchParams.get('start')).toBe('2026-10-01');
    expect(calledUrl.searchParams.get('end')).toBe('2026-10-07');
  });

  it('requests one room detail with the same period', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchEnvironmentRoom('A11', period);

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/environment/rooms/A11');
    expect(calledUrl.searchParams.get('start')).toBe('2026-10-01');
    expect(calledUrl.searchParams.get('end')).toBe('2026-10-07');
  });
});
