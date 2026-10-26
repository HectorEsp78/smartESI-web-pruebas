import { buildQuery, getJson } from './http';
import type {
  ElectricityCompareDto,
  ElectricityDto,
  ElectricityGranularity,
  ElectricityMetaDto,
  ElectricityMetric,
} from '../types/electricity';

export interface ElectricityPeriod {
  start: string;
  end: string;
}

export interface ElectricityQuery extends ElectricityPeriod {
  granularity: ElectricityGranularity;
  metric: ElectricityMetric;
  building: string;
  sector?: string;
}

export function fetchElectricityStats(
  query: ElectricityQuery,
  signal?: AbortSignal,
): Promise<ElectricityDto> {
  const params: Record<string, string> = {
    start: query.start,
    end: query.end,
    granularity: query.granularity,
    metric: query.metric,
    building: query.building,
  };
  if (query.sector) params.sector = query.sector;
  return getJson<ElectricityDto>(`/api/v1/energy/electricity?${buildQuery(params)}`, signal);
}

export function fetchElectricityCompare(
  periodA: ElectricityPeriod,
  periodB: ElectricityPeriod,
  granularity: ElectricityGranularity,
  metric: ElectricityMetric,
  building: string,
  sector?: string,
  signal?: AbortSignal,
): Promise<ElectricityCompareDto> {
  const params: Record<string, string> = {
    start_a: periodA.start,
    end_a: periodA.end,
    start_b: periodB.start,
    end_b: periodB.end,
    granularity,
    metric,
    building,
  };
  if (sector) params.sector = sector;
  return getJson<ElectricityCompareDto>(
    `/api/v1/energy/electricity/compare?${buildQuery(params)}`,
    signal,
  );
}

export function fetchElectricityMeta(signal?: AbortSignal): Promise<ElectricityMetaDto> {
  return getJson<ElectricityMetaDto>('/api/v1/energy/electricity/meta', signal);
}
