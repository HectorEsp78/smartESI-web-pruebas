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
import { STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useLightingConsumption(
  range: LightingRange,
  building: string,
): QueryResult<LightingConsumptionDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['lightingConsumption', range, building],
      queryFn: ({ signal }) => fetchLightingConsumption(range, building, signal),
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}

export function useLightingBySpace(
  range: LightingRange,
  building: string,
): QueryResult<LightingBySpaceDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['lightingBySpace', range, building],
      queryFn: ({ signal }) => fetchLightingBySpace(range, building, signal),
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}

export function useLightingWaste(
  range: LightingRange,
  building: string,
): QueryResult<LightingWasteDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['lightingWaste', range, building],
      queryFn: ({ signal }) => fetchLightingWaste(range, building, signal),
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}
