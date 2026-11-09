import { useQuery } from '@tanstack/react-query';
import { fetchMeta } from '../api/meta';
import type { MetaDto } from '../types/meta';
import { CATALOGUE_STALE_TIME } from './queryResult';

interface UseBuildingsResult {
  meta: MetaDto | null;
}

export function useBuildings(): UseBuildingsResult {
  const { data } = useQuery({
    queryKey: ['meta', 'buildings'],
    queryFn: ({ signal }) => fetchMeta(signal),
    staleTime: CATALOGUE_STALE_TIME,
  });

  return { meta: data ?? null };
}
