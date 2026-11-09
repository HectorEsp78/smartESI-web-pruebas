import { useQuery } from '@tanstack/react-query';
import {
  fetchElectricityCompareMany,
  fetchElectricityMeta,
  fetchElectricityStats,
} from '../api/electricity';
import type { ElectricityPeriod, ElectricityQuery } from '../api/electricity';
import type {
  ElectricityCompareManyDto,
  ElectricityDto,
  ElectricityGranularity,
  ElectricityMetaDto,
  ElectricityMetric,
} from '../types/electricity';
import { CATALOGUE_STALE_TIME, STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useElectricityMeta(): QueryResult<ElectricityMetaDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['electricityMeta'],
      queryFn: ({ signal }) => fetchElectricityMeta(signal),
      staleTime: CATALOGUE_STALE_TIME,
    }),
  );
}

export function useElectricityStats(query: ElectricityQuery | null): QueryResult<ElectricityDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['electricity', query],
      queryFn: ({ signal }) => {
        if (!query) throw new Error('Periodo no válido.');
        return fetchElectricityStats(query, signal);
      },
      enabled: query !== null,
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}

export interface ElectricityCompareManyQuery {
  periods: ElectricityPeriod[];
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  building: string;
  sector?: string;
}

export function useElectricityCompareMany(
  query: ElectricityCompareManyQuery | null,
): QueryResult<ElectricityCompareManyDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['electricityCompareMany', query],
      queryFn: ({ signal }) => {
        if (!query) throw new Error('Periodo no válido.');
        return fetchElectricityCompareMany(
          query.periods,
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
    }),
  );
}
