import { useQuery } from '@tanstack/react-query';
import { fetchBatteryGroup, fetchBatteryHistory } from '../api/battery';
import type { DatePeriod } from '../lib/electricity';
import type { BatteryGroupDto, BatteryHistoryDto } from '../types/battery';
import { STALE_TIME, toQueryResult } from './queryResult';
import type { QueryResult } from './queryResult';

export function useBatteryGroup(groupId: string): QueryResult<BatteryGroupDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['batteryGroup', groupId],
      queryFn: ({ signal }) => fetchBatteryGroup(groupId, signal),
      staleTime: STALE_TIME,
    }),
  );
}

export function useBatteryHistory(
  groupId: string,
  sensorId: string,
  period: DatePeriod | null,
): QueryResult<BatteryHistoryDto> {
  return toQueryResult(
    useQuery({
      queryKey: ['batteryHistory', groupId, sensorId, period],
      queryFn: ({ signal }) => {
        if (!period) throw new Error('Periodo no válido.');
        return fetchBatteryHistory(groupId, sensorId, period, signal);
      },
      enabled: period !== null,
      staleTime: STALE_TIME,
      placeholderData: (previous) => previous,
    }),
  );
}
