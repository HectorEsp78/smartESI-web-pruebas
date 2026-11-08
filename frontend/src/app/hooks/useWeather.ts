import { useQuery } from '@tanstack/react-query';
import { fetchWeatherOverview } from '../api/weather';
import type { WeatherOverviewDto } from '../types/weather';

interface Result {
  data: WeatherOverviewDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useWeatherOverview(days: number): Result {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['weatherOverview', days],
    queryFn: ({ signal }) => fetchWeatherOverview(days, signal),
    staleTime: STALE_TIME,
  });
  return {
    data,
    isLoading,
    isFetching,
    error: error as Error | null,
    retry: refetch,
  };
}
