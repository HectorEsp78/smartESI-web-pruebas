import { useQuery } from '@tanstack/react-query';
import { fetchDecisions } from '../api/decisions';
import type { DecisionRange, DecisionsDto } from '../types/decisions';

interface UseDecisionsResult {
  data: DecisionsDto | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function useDecisions(
  range: DecisionRange,
  building: string,
): UseDecisionsResult {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['decisions', range, building],
    queryFn: ({ signal }) => fetchDecisions(range, building, signal),
    staleTime: 60 * 1000,
    placeholderData: (previous) => previous,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
