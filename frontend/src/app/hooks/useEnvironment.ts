import { useQuery } from '@tanstack/react-query';
import {
  fetchEnvironmentOverview,
  fetchEnvironmentRoom,
} from '../api/environment';
import type { EnvironmentPeriod } from '../api/environment';
import type {
  EnvironmentOverviewDto,
  EnvironmentRoomDetailDto,
} from '../types/environment';

interface Result<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

const STALE_TIME = 60 * 1000;

export function useEnvironmentOverview(period: EnvironmentPeriod | null): Result<EnvironmentOverviewDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['environmentOverview', period],
    queryFn: ({ signal }) => {
      if (!period) throw new Error('Periodo no válido.');
      return fetchEnvironmentOverview(period, signal);
    },
    enabled: period !== null,
    staleTime: STALE_TIME,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}

export function useEnvironmentRoom(
  roomId: string,
  period: EnvironmentPeriod | null,
): Result<EnvironmentRoomDetailDto> {
  const { data = null, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['environmentRoom', roomId, period],
    queryFn: ({ signal }) => {
      if (!period) throw new Error('Periodo no válido.');
      return fetchEnvironmentRoom(roomId, period, signal);
    },
    enabled: period !== null,
    staleTime: STALE_TIME,
  });
  return { data, isLoading, isFetching, error: error as Error | null, retry: refetch };
}
