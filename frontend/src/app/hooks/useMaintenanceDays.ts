import { useCallback } from 'react';
import { useSearchParams } from 'react-router';
import {
  DEFAULT_MAINTENANCE_DAYS,
  parseMaintenanceDays,
} from '../lib/maintenance';
import type { MaintenanceDays } from '../lib/maintenance';

export interface MaintenanceDaysState {
  days: MaintenanceDays;
  setDays: (days: MaintenanceDays) => void;
}

/** Keep the 7/30/90-day maintenance window in the URL so links are shareable. */
export function useMaintenanceDays(): MaintenanceDaysState {
  const [searchParams, setSearchParams] = useSearchParams();
  const days = parseMaintenanceDays(searchParams.get('days'));

  const setDays = useCallback(
    (next: MaintenanceDays) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current);
          if (next === DEFAULT_MAINTENANCE_DAYS) {
            params.delete('days');
          } else {
            params.set('days', String(next));
          }
          return params;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  return { days, setDays };
}
