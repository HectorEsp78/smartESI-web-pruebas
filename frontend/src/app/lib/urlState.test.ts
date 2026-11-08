import { describe, expect, it } from 'vitest';
import { dashboardUrl, parseDashboardUrlState } from './urlState';

describe('parseDashboardUrlState', () => {
  it('reads a valid tab and range', () => {
    expect(parseDashboardUrlState('?tab=iluminacion&range=month')).toEqual({
      tab: 'iluminacion',
      range: 'month',
    });
    expect(parseDashboardUrlState('?tab=infraestructura&range=week')).toEqual({
      tab: 'infraestructura',
      range: 'week',
    });
    expect(parseDashboardUrlState('?tab=mantenimiento&days=90')).toEqual({
      tab: 'mantenimiento',
      range: 'day',
    });
    expect(parseDashboardUrlState('?tab=medio-ambiente&days=90')).toEqual({
      tab: 'medio-ambiente',
      range: 'day',
    });
  });

  it('falls back to the defaults for unknown or removed values', () => {
    expect(parseDashboardUrlState('?tab=desconocida&range=decada')).toEqual({
      tab: 'electricidad',
      range: 'day',
    });
    expect(parseDashboardUrlState('')).toEqual({ tab: 'electricidad', range: 'day' });
  });
});

describe('dashboardUrl', () => {
  it('merges the tab/range and keeps unrelated query params', () => {
    const url = new URL(
      dashboardUrl(
        { tab: 'iluminacion', range: 'year' },
        'https://example.test/panel?foo=bar&range=week',
      ),
    );

    expect(url.pathname).toBe('/panel');
    expect(url.searchParams.get('foo')).toBe('bar');
    expect(url.searchParams.get('tab')).toBe('iluminacion');
    expect(url.searchParams.get('range')).toBe('year');
  });
});
