export type DashboardTabId = 'electricidad' | 'iluminacion';

export interface DashboardTab {
  id: DashboardTabId;
  label: string;
}

export const DASHBOARD_TABS: DashboardTab[] = [
  { id: 'electricidad', label: 'Electricidad' },
  { id: 'iluminacion', label: 'Iluminación' },
];

export const DEFAULT_TAB_ID: DashboardTabId = 'electricidad';

export function isDashboardTabId(value: string): value is DashboardTabId {
  return DASHBOARD_TABS.some((tab) => tab.id === value);
}
