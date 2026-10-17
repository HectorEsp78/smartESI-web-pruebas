export type DashboardTabId =
  | 'resumen'
  | 'electricidad'
  | 'iluminacion'
  | 'climatizacion'
  | 'ocupacion-aire'
  | 'decisiones';

export interface DashboardTab {
  id: DashboardTabId;
  label: string;
}

export const DASHBOARD_TABS: DashboardTab[] = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'electricidad', label: 'Electricidad' },
  { id: 'iluminacion', label: 'Iluminación' },
  { id: 'climatizacion', label: 'Climatización y gas' },
  { id: 'ocupacion-aire', label: 'Ocupación y aire' },
  { id: 'decisiones', label: 'Decisiones' },
];

export const DEFAULT_TAB_ID: DashboardTabId = 'resumen';

export function isDashboardTabId(value: string): value is DashboardTabId {
  return DASHBOARD_TABS.some((tab) => tab.id === value);
}
