import { DEFAULT_MAINTENANCE_DAYS, parseMaintenanceDays } from '../lib/maintenance';
import type { MaintenanceDays } from '../lib/maintenance';
import { useDaysParam } from './useDaysParam';
import type { DaysParamState } from './useDaysParam';

/** Keep the 7/30/90-day maintenance window in the URL so links are shareable. */
export function useMaintenanceDays(): DaysParamState<MaintenanceDays> {
  return useDaysParam<MaintenanceDays>(parseMaintenanceDays, DEFAULT_MAINTENANCE_DAYS);
}
