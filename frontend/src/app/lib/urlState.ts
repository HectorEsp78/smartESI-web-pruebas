import { DEFAULT_TAB_ID, isDashboardTabId } from './sections';
import type { DashboardTabId } from './sections';
import { DEFAULT_ENERGY_RANGE, ENERGY_RANGES } from '../types/energy';
import type { EnergyRange } from '../types/energy';

/** Dashboard state that can be shared through the URL. */
export interface DashboardUrlState {
  tab: DashboardTabId;
  range: EnergyRange;
}

const TAB_PARAM = 'tab';
const RANGE_PARAM = 'range';

function isEnergyRange(value: string): value is EnergyRange {
  return (ENERGY_RANGES as readonly string[]).includes(value);
}

/** Parse `?tab=electricidad&range=month`, falling back to the defaults. */
export function parseDashboardUrlState(search: string): DashboardUrlState {
  const params = new URLSearchParams(search);
  const tab = params.get(TAB_PARAM) ?? '';
  const range = params.get(RANGE_PARAM) ?? '';

  return {
    tab: isDashboardTabId(tab) ? tab : DEFAULT_TAB_ID,
    range: isEnergyRange(range) ? range : DEFAULT_ENERGY_RANGE,
  };
}

/** Current URL with the given tab/range merged in (other params are kept). */
export function dashboardUrl(
  state: Partial<DashboardUrlState>,
  href: string = window.location.href,
): string {
  const url = new URL(href);
  const current = parseDashboardUrlState(url.search);
  const next = { ...current, ...state };

  url.searchParams.set(TAB_PARAM, next.tab);
  url.searchParams.set(RANGE_PARAM, next.range);
  return url.toString();
}

/**
 * Update the address bar without adding a history entry: tab/period changes
 * are view state, not navigation, and a shared link is all we need.
 */
export function updateDashboardUrl(state: Partial<DashboardUrlState>): void {
  if (typeof window === 'undefined') return;
  window.history.replaceState(null, '', dashboardUrl(state));
}
