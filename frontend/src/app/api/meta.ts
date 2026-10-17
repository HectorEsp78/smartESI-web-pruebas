import { getJson } from './http';
import type { MetaDto } from '../types/meta';

export function fetchMeta(signal?: AbortSignal): Promise<MetaDto> {
  return getJson<MetaDto>('/api/v1/meta/buildings', signal);
}
