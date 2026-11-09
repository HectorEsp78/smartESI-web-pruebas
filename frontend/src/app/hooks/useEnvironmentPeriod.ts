import { useDatePeriod } from './useDatePeriod';
import type { DatePeriodState } from './useDatePeriod';

const DEFAULT_ENVIRONMENT_PERIOD_DAYS = 1;

/** Infrastructure period in the URL. The default is today. */
export function useEnvironmentPeriod(): DatePeriodState {
  return useDatePeriod(DEFAULT_ENVIRONMENT_PERIOD_DAYS);
}
