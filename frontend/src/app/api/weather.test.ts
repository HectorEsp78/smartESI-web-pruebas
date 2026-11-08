import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchWeatherOverview } from './weather';

describe('weather api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the overview for the selected window', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchWeatherOverview(90);

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/weather/overview');
    expect(calledUrl.searchParams.get('days')).toBe('90');
  });
});
