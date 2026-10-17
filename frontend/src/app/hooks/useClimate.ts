import { useQuery } from '@tanstack/react-query';
import { fetchEmptySpaces, fetchGas, fetchValves } from '../api/climate';
import type { ClimateRange, EmptySpacesDto, GasDto, ValvesDto } from '../types/climate';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useGas(range: ClimateRange, building: string): Result<GasDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['gas', range, building],
    queryFn: ({ signal }) => fetchGas(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useValves(range: ClimateRange, building: string): Result<ValvesDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['valves', range, building],
    queryFn: ({ signal }) => fetchValves(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useEmptySpaces(
  range: ClimateRange,
  building: string,
): Result<EmptySpacesDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['emptySpaces', range, building],
    queryFn: ({ signal }) => fetchEmptySpaces(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
