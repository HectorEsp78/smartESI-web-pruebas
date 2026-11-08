import { buildQuery, getJson } from './http';
import type {
  EnvironmentOverviewDto,
  EnvironmentRoomDetailDto,
} from '../types/environment';

export interface EnvironmentPeriod {
  start: string;
  end: string;
}

export function fetchEnvironmentOverview(
  period: EnvironmentPeriod,
  signal?: AbortSignal,
): Promise<EnvironmentOverviewDto> {
  const query = buildQuery({ start: period.start, end: period.end });
  return getJson<EnvironmentOverviewDto>(`/api/v1/environment/overview?${query}`, signal);
}

export function fetchEnvironmentRoom(
  roomId: string,
  period: EnvironmentPeriod,
  signal?: AbortSignal,
): Promise<EnvironmentRoomDetailDto> {
  const query = buildQuery({ start: period.start, end: period.end });
  return getJson<EnvironmentRoomDetailDto>(
    `/api/v1/environment/rooms/${encodeURIComponent(roomId)}?${query}`,
    signal,
  );
}
