import { buildQuery, getJson } from './http';
import type { DecisionRange, DecisionsDto } from '../types/decisions';

export function fetchDecisions(
  range: DecisionRange,
  building: string,
  signal?: AbortSignal,
): Promise<DecisionsDto> {
  const query = buildQuery({ range, building });
  return getJson<DecisionsDto>(`/api/v1/decisions/opportunities?${query}`, signal);
}
