import { buildQuery, getJson } from './http';
import type { CorrelationRange, OccupancyAirQualityDto } from '../types/correlation';

export function fetchOccupancyAirQuality(
  range: CorrelationRange,
  building: string,
  signal?: AbortSignal,
): Promise<OccupancyAirQualityDto> {
  const query = buildQuery({ range, building });
  return getJson<OccupancyAirQualityDto>(
    `/api/v1/correlation/occupancy-air-quality?${query}`,
    signal,
  );
}
