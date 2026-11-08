import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';
import type { DatePeriod } from '../lib/electricity';
import { defaultEnvironmentPeriod } from '../lib/environment';

export interface EnvironmentPeriodState {
  period: DatePeriod;
  setPeriod: (period: DatePeriod) => void;
}

/**
 * Keep the custom Infrastructure period in the URL so links to a room and
 * shared bookmarks keep the same dates. The default is the last 7 days.
 */
export function useEnvironmentPeriod(): EnvironmentPeriodState {
  const [searchParams, setSearchParams] = useSearchParams();
  const fallback = useMemo(() => defaultEnvironmentPeriod(), []);
  const start = searchParams.get('start') ?? fallback.start;
  const end = searchParams.get('end') ?? fallback.end;
  const period = useMemo<DatePeriod>(() => ({ start, end }), [end, start]);

  const setPeriod = useCallback(
    (next: DatePeriod) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current);
          params.set('start', next.start);
          params.set('end', next.end);
          return params;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  return { period, setPeriod };
}
