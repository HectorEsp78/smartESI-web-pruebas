import { QueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';

const MAX_RETRIES = 2;

/**
 * Retry only what can recover by itself. A 4xx answer (invalid period, unknown
 * room) will fail the same way, so the user sees the message right away.
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < MAX_RETRIES;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: shouldRetry } },
  });
}
