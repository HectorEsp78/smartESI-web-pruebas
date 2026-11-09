import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';
import { defaultElectricityPeriod } from '../lib/electricity';
import type { DatePeriod } from '../lib/electricity';

export interface DatePeriodState {
  period: DatePeriod;
  setPeriod: (period: DatePeriod) => void;
}

/**
 * Keep a custom period in `?start=&end=` so links and bookmarks keep the same
 * dates. Without them, the period is the last `defaultDays` days.
 */
export function useDatePeriod(defaultDays: number): DatePeriodState {
  const [searchParams, setSearchParams] = useSearchParams();
  const fallback = useMemo(() => defaultElectricityPeriod(defaultDays), [defaultDays]);
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
