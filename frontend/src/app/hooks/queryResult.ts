import type { UseQueryResult } from '@tanstack/react-query';

/** Default freshness of the chart data, in milliseconds. */
export const STALE_TIME = 60 * 1000;
/** Catalogues (buildings, sectors) barely change. */
export const CATALOGUE_STALE_TIME = 30 * 60 * 1000;

/** What the charts need from a query. */
export interface QueryResult<T> {
  data: T | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  retry: () => void;
}

export function toQueryResult<T>(query: UseQueryResult<T, Error>): QueryResult<T> {
  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    retry: () => {
      void query.refetch();
    },
  };
}
