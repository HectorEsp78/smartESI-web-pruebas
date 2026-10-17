import { buildQuery, getJson } from './http';
import type {
  LightingBySpaceDto,
  LightingConsumptionDto,
  LightingRange,
  LightingWasteDto,
} from '../types/lighting';

export function fetchLightingConsumption(
  range: LightingRange,
  building: string,
  signal?: AbortSignal,
): Promise<LightingConsumptionDto> {
  const query = buildQuery({ range, building });
  return getJson<LightingConsumptionDto>(`/api/v1/lighting/consumption?${query}`, signal);
}

export function fetchLightingBySpace(
  range: LightingRange,
  building: string,
  signal?: AbortSignal,
): Promise<LightingBySpaceDto> {
  const query = buildQuery({ range, building });
  return getJson<LightingBySpaceDto>(`/api/v1/lighting/by-space?${query}`, signal);
}

export function fetchLightingWaste(
  range: LightingRange,
  building: string,
  signal?: AbortSignal,
): Promise<LightingWasteDto> {
  const query = buildQuery({ range, building });
  return getJson<LightingWasteDto>(`/api/v1/lighting/waste?${query}`, signal);
}
