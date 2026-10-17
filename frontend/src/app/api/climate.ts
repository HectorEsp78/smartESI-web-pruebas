import { buildQuery, getJson } from './http';
import type {
  ClimateRange,
  EmptySpacesDto,
  GasDto,
  ValvesDto,
} from '../types/climate';

export function fetchGas(
  range: ClimateRange,
  building: string,
  signal?: AbortSignal,
): Promise<GasDto> {
  const query = buildQuery({ range, building });
  return getJson<GasDto>(`/api/v1/climate/gas?${query}`, signal);
}

export function fetchValves(
  range: ClimateRange,
  building: string,
  signal?: AbortSignal,
): Promise<ValvesDto> {
  const query = buildQuery({ range, building });
  return getJson<ValvesDto>(`/api/v1/climate/valves?${query}`, signal);
}

export function fetchEmptySpaces(
  range: ClimateRange,
  building: string,
  signal?: AbortSignal,
): Promise<EmptySpacesDto> {
  const query = buildQuery({ range, building });
  return getJson<EmptySpacesDto>(`/api/v1/climate/empty-spaces?${query}`, signal);
}
