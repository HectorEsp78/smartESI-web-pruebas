import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchWeatherOverview } from './weather';

describe('weather api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the overview for the selected dates', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchWeatherOverview({ start: '2026-10-01', end: '2026-10-31' });

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/weather/overview');
    expect(calledUrl.searchParams.get('start')).toBe('2026-10-01');
    expect(calledUrl.searchParams.get('end')).toBe('2026-10-31');
  });
});
