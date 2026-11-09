import { useQuery } from '@tanstack/react-query';
import { fetchWeatherOverview } from '../api/weather';
import type { WeatherPeriod } from '../api/weather';
import type { WeatherOverviewDto } from '../types/weather';
import { STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useWeatherOverview(period: WeatherPeriod | null): QueryResult<WeatherOverviewDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['weatherOverview', period],
      queryFn: ({ signal }) => {
        if (!period) throw new Error('Periodo no válido.');
        return fetchWeatherOverview(period, signal);
      },
      enabled: period !== null,
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}
