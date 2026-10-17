import { useQuery } from '@tanstack/react-query';
import { fetchEnergyConsumption } from '../api/energy';
import { DEFAULT_ENERGY_METRIC } from '../types/energy';
import type { EnergyConsumptionDto, EnergyMetric, EnergyRange } from '../types/energy';
import { ALL_BUILDINGS } from '../types/energy';

interface UseEnergyConsumptionResult {
  data: EnergyConsumptionDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function useEnergyConsumption(
  range: EnergyRange,
  building: string = ALL_BUILDINGS,
  metric: EnergyMetric = DEFAULT_ENERGY_METRIC,
): UseEnergyConsumptionResult {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['energyConsumption', range, building, metric],
    queryFn: ({ signal }) => fetchEnergyConsumption(range, building, metric, signal),
    staleTime: 60 * 1000,
    // Keep showing the previous series while the new range loads (avoids flicker).
    placeholderData: (previous) => previous,
  });

  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
