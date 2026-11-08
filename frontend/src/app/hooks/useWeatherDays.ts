import { useCallback } from 'react';
import { useSearchParams } from 'react-router';
import {
  DEFAULT_WEATHER_DAYS,
  parseWeatherDays,
} from '../lib/weather';
import type { WeatherDays } from '../lib/weather';

export interface WeatherDaysState {
  days: WeatherDays;
  setDays: (days: WeatherDays) => void;
}

/** Keep the 7/30/90-day weather window in the URL so links are shareable. */
export function useWeatherDays(): WeatherDaysState {
  const [searchParams, setSearchParams] = useSearchParams();
  const days = parseWeatherDays(searchParams.get('days'));

  const setDays = useCallback(
    (next: WeatherDays) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current);
          if (next === DEFAULT_WEATHER_DAYS) {
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
