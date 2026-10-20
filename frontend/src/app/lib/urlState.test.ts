import { describe, expect, it } from 'vitest';
import { dashboardUrl, parseDashboardUrlState } from './urlState';

describe('parseDashboardUrlState', () => {
  it('reads a valid tab and range', () => {
    expect(parseDashboardUrlState('?tab=electricidad&range=month')).toEqual({
      tab: 'electricidad',
      range: 'month',
    });
  });

  it('falls back to the defaults for unknown values', () => {
    expect(parseDashboardUrlState('?tab=no-existe&range=decada')).toEqual({
      tab: 'resumen',
      range: 'day',
    });
    expect(parseDashboardUrlState('')).toEqual({ tab: 'resumen', range: 'day' });
  });
});

describe('dashboardUrl', () => {
  it('merges the tab/range and keeps unrelated query params', () => {
    const url = new URL(
      dashboardUrl(
        { tab: 'climatizacion', range: 'year' },
        'https://example.test/panel?foo=bar&range=week',
      ),
    );

    expect(url.pathname).toBe('/panel');
    expect(url.searchParams.get('foo')).toBe('bar');
    expect(url.searchParams.get('tab')).toBe('climatizacion');
    expect(url.searchParams.get('range')).toBe('year');
  });
});
