import { useQuery } from '@tanstack/react-query';
import { fetchMeta } from '../api/meta';
import type { MetaDto } from '../types/meta';

interface UseBuildingsResult {
  meta: MetaDto | null;
  isLoading: boolean;
  error: Error | null;
  retry: () => void;
}

export function useBuildings(): UseBuildingsResult {
  const { data = null, isLoading, error, refetch } = useQuery({
    queryKey: ['meta', 'buildings'],
    queryFn: ({ signal }) => fetchMeta(signal),
    staleTime: 30 * 60 * 1000,
  });

  return { meta: data, isLoading, error: error as Error | null, retry: refetch };
}
