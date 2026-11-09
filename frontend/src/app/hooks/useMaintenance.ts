import { useQuery } from '@tanstack/react-query';
import { fetchMaintenanceDevice, fetchMaintenanceOverview } from '../api/maintenance';
import type { MaintenanceDeviceDetailDto, MaintenanceOverviewDto } from '../types/maintenance';
import { STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useMaintenanceOverview(days: number | null): QueryResult<MaintenanceOverviewDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['maintenanceOverview', days],
      queryFn: ({ signal }) => {
        if (days === null) throw new Error('Periodo no válido.');
        return fetchMaintenanceOverview(days, signal);
      },
      enabled: days !== null,
      staleTime: STALE_TIME,
    }),
  );
}

export function useMaintenanceDevice(
  deviceId: string | null,
  days: number | null,
): QueryResult<MaintenanceDeviceDetailDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['maintenanceDevice', deviceId, days],
      queryFn: ({ signal }) => {
        if (!deviceId || days === null) throw new Error('Dispositivo no válido.');
        return fetchMaintenanceDevice(deviceId, days, signal);
      },
      enabled: deviceId !== null && days !== null,
      staleTime: STALE_TIME,
    }),
  );
}
