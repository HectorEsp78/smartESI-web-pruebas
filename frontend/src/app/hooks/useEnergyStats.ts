import { useQuery } from '@tanstack/react-query';
import {
  fetchEnergyBreakdown,
  fetchEnergyCompare,
  fetchEnergyEfficiency,
} from '../api/energy';
import type {
  EnergyBreakdownDto,
  EnergyCompareDto,
  EnergyEfficiencyDto,
  EnergyMetric,
  EnergyRange,
} from '../types/energy';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useEnergyBreakdown(
  range: EnergyRange,
  building: string,
): Result<EnergyBreakdownDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['energyBreakdown', range, building],
    queryFn: ({ signal }) => fetchEnergyBreakdown(range, building, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useEnergyCompare(
  range: EnergyRange,
  building: string,
  metric: EnergyMetric,
): Result<EnergyCompareDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['energyCompare', range, building, metric],
    queryFn: ({ signal }) => fetchEnergyCompare(range, building, metric, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useEnergyEfficiency(range: EnergyRange): Result<EnergyEfficiencyDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['energyEfficiency', range],
    queryFn: ({ signal }) => fetchEnergyEfficiency(range, signal),
    staleTime: STALE_TIME,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
