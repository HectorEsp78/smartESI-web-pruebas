import { useQuery } from '@tanstack/react-query';
import {
  fetchElectricityCompare,
  fetchElectricityMeta,
  fetchElectricityStats,
} from '../api/electricity';
import type { ElectricityPeriod, ElectricityQuery } from '../api/electricity';
import type {
  ElectricityCompareDto,
  ElectricityDto,
  ElectricityGranularity,
  ElectricityMetaDto,
  ElectricityMetric,
} from '../types/electricity';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useElectricityMeta(): Result<ElectricityMetaDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['electricityMeta'],
    queryFn: ({ signal }) => fetchElectricityMeta(signal),
    staleTime: 30 * 60 * 1000,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useElectricityStats(query: ElectricityQuery | null): Result<ElectricityDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['electricity', query],
    queryFn: ({ signal }) => {
      if (!query) throw new Error('Periodo no válido.');
      return fetchElectricityStats(query, signal);
    },
    enabled: query !== null,
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export interface ElectricityCompareQuery {
  periodA: ElectricityPeriod;
  periodB: ElectricityPeriod;
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  building: string;
  sector?: string;
}

export function useElectricityCompare(
  query: ElectricityCompareQuery | null,
): Result<ElectricityCompareDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['electricityCompare', query],
    queryFn: ({ signal }) => {
      if (!query) throw new Error('Periodo no válido.');
      return fetchElectricityCompare(
        query.periodA,
        query.periodB,
        query.granularity,
        query.metric,
        query.building,
        query.sector,
        signal,
      );
    },
    enabled: query !== null,
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
