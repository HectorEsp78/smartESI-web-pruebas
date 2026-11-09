import { useCallback } from 'react';
import { useSearchParams } from 'react-router';

export interface DaysParamState<T extends number> {
  days: T;
  setDays: (days: T) => void;
}

/** Keep a fixed analysis window in `?days=`, omitting the default so links stay short. */
export function useDaysParam<T extends number>(
  parse: (value: string | null) => T,
  defaultDays: T,
): DaysParamState<T> {
  const [searchParams, setSearchParams] = useSearchParams();
  const days = parse(searchParams.get('days'));

  const setDays = useCallback(
    (next: T) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current);
          if (next === defaultDays) {
            params.delete('days');
          } else {
            params.set('days', String(next));
          }
          return params;
        },
        { replace: true },
      );
    },
    [defaultDays, setSearchParams],
  );

  return { days, setDays };
}
