import { useQuery } from '@tanstack/react-query';
import { fetchEnvironmentOverview, fetchEnvironmentRoom } from '../api/environment';
import type { EnvironmentPeriod } from '../api/environment';
import type { EnvironmentOverviewDto, EnvironmentRoomDetailDto } from '../types/environment';
import { STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useEnvironmentOverview(
  period: EnvironmentPeriod | null,
): QueryResult<EnvironmentOverviewDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['environmentOverview', period],
      queryFn: ({ signal }) => {
        if (!period) throw new Error('Periodo no válido.');
        return fetchEnvironmentOverview(period, signal);
      },
      enabled: period !== null,
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}

export function useEnvironmentRoom(
  roomId: string,
  period: EnvironmentPeriod | null,
): QueryResult<EnvironmentRoomDetailDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['environmentRoom', roomId, period],
      queryFn: ({ signal }) => {
        if (!period) throw new Error('Periodo no válido.');
        return fetchEnvironmentRoom(roomId, period, signal);
      },
      enabled: period !== null,
      staleTime: STALE_TIME,
      // Keep the charts while another period loads, but never show another room.
      placeholderData: (previous) => (previous?.room.room_id === roomId ? previous : undefined),
    }),
  );
}
