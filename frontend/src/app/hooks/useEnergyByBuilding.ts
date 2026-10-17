import { useQuery } from '@tanstack/react-query';
import { fetchEnergyByBuilding } from '../api/energy';
import { DEFAULT_ENERGY_METRIC } from '../types/energy';
import type { EnergyByBuildingDto, EnergyMetric, EnergyRange } from '../types/energy';

interface UseEnergyByBuildingResult {
  data: EnergyByBuildingDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function useEnergyByBuilding(
  range: EnergyRange,
  metric: EnergyMetric = DEFAULT_ENERGY_METRIC,
): UseEnergyByBuildingResult {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['energyByBuilding', range, metric],
    queryFn: ({ signal }) => fetchEnergyByBuilding(range, metric, signal),
    staleTime: 60 * 1000,
    placeholderData: (previous) => previous,
  });

  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
