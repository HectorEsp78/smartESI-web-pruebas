import { useQuery } from '@tanstack/react-query';
import {
  fetchMaintenanceDevice,
  fetchMaintenanceOverview,
} from '../api/maintenance';
import type {
  MaintenanceDeviceDetailDto,
  MaintenanceOverviewDto,
} from '../types/maintenance';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useMaintenanceOverview(
  days: number | null,
): Result<MaintenanceOverviewDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['maintenanceOverview', days],
    queryFn: ({ signal }) => {
      if (days === null) throw new Error('Periodo no válido.');
      return fetchMaintenanceOverview(days, signal);
    },
    enabled: days !== null,
    staleTime: STALE_TIME,
  });
  return {
    data,
    isLoading,
    isFetching,
    error: error as Error | null,
    retry: refetch,
  };
}

export function useMaintenanceDevice(
  deviceId: string | null,
  days: number | null,
): Result<MaintenanceDeviceDetailDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['maintenanceDevice', deviceId, days],
    queryFn: ({ signal }) => {
      if (!deviceId || days === null) throw new Error('Dispositivo no válido.');
      return fetchMaintenanceDevice(deviceId, days, signal);
    },
    enabled: deviceId !== null && days !== null,
    staleTime: STALE_TIME,
  });
  return {
    data,
    isLoading,
    isFetching,
    error: error as Error | null,
    retry: refetch,
  };
}
