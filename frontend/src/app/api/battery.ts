import { buildQuery, getJson } from './http';
import type { DatePeriod } from '../lib/electricity';
import type { BatteryGroupDto, BatteryHistoryDto } from '../types/battery';

const BASE_PATH = '/api/v1/maintenance/batteries';

export function fetchBatteryGroup(groupId: string, signal?: AbortSignal): Promise<BatteryGroupDto> {
  return getJson<BatteryGroupDto>(`${BASE_PATH}/${encodeURIComponent(groupId)}`, signal);
}

export function fetchBatteryHistory(
  groupId: string,
  sensorId: string,
  period: DatePeriod,
  signal?: AbortSignal,
): Promise<BatteryHistoryDto> {
  const query = buildQuery({ start: period.start, end: period.end });
  const path = `${encodeURIComponent(groupId)}/${encodeURIComponent(sensorId)}`;
  return getJson<BatteryHistoryDto>(`${BASE_PATH}/${path}/history?${query}`, signal);
}
