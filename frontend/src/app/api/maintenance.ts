import { buildQuery, getJson } from './http';
import type {
  MaintenanceDeviceDetailDto,
  MaintenanceOverviewDto,
} from '../types/maintenance';

export function fetchMaintenanceOverview(
  days: number,
  signal?: AbortSignal,
): Promise<MaintenanceOverviewDto> {
  const query = buildQuery({ days: String(days) });
  return getJson<MaintenanceOverviewDto>(
    `/api/v1/maintenance/overview?${query}`,
    signal,
  );
}

export function fetchMaintenanceDevice(
  deviceId: string,
  days: number,
  signal?: AbortSignal,
): Promise<MaintenanceDeviceDetailDto> {
  const query = buildQuery({ days: String(days) });
  return getJson<MaintenanceDeviceDetailDto>(
    `/api/v1/maintenance/devices/${encodeURIComponent(deviceId)}?${query}`,
    signal,
  );
}
