import { useQuery } from '@tanstack/react-query';
import {
  fetchLightingBySpace,
  fetchLightingConsumption,
  fetchLightingWaste,
} from '../api/lighting';
import type {
  LightingBySpaceDto,
  LightingConsumptionDto,
  LightingRange,
  LightingWasteDto,
} from '../types/lighting';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useLightingConsumption(
  range: LightingRange,
  building: string,
): Result<LightingConsumptionDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['lightingConsumption', range, building],
    queryFn: ({ signal }) => fetchLightingConsumption(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useLightingBySpace(
  range: LightingRange,
  building: string,
): Result<LightingBySpaceDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['lightingBySpace', range, building],
    queryFn: ({ signal }) => fetchLightingBySpace(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useLightingWaste(
  range: LightingRange,
  building: string,
): Result<LightingWasteDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['lightingWaste', range, building],
    queryFn: ({ signal }) => fetchLightingWaste(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
