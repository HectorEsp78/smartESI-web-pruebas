import { useQuery } from '@tanstack/react-query';
import { fetchOccupancyAirQuality } from '../api/correlation';
import type { CorrelationRange, OccupancyAirQualityDto } from '../types/correlation';
import { ALL_BUILDINGS } from '../types/energy';

interface UseOccupancyAirQualityResult {
  data: OccupancyAirQualityDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function useOccupancyAirQuality(
  range: CorrelationRange,
  building: string = ALL_BUILDINGS,
): UseOccupancyAirQualityResult {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['occupancyAirQuality', range, building],
    queryFn: ({ signal }) => fetchOccupancyAirQuality(range, building, signal),
    staleTime: 60 * 1000,
    placeholderData: (previous) => previous,
  });

  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
