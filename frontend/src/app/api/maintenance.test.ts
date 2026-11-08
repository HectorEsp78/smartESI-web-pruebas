import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  fetchMaintenanceDevice,
  fetchMaintenanceOverview,
} from './maintenance';

describe('maintenance api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the overview for the selected window', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchMaintenanceOverview(7);

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/maintenance/overview');
    expect(calledUrl.searchParams.get('days')).toBe('7');
  });

  it('requests one device detail with the same window', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await fetchMaintenanceDevice('shelly 1', 90);

    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost');
    expect(calledUrl.pathname).toBe('/api/v1/maintenance/devices/shelly%201');
    expect(calledUrl.searchParams.get('days')).toBe('90');
  });
});
